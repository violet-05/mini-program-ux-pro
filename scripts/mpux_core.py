#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MPUX Pro 本地设计知识检索核心。

只使用 Python 标准库。检索基于可解释的 BM25、字符 bigram、中英文同义词扩展
和名称/ID 精确匹配加权；所有结果都来自 data/ 下的 CSV，不调用网络或 AI API。
"""

from __future__ import annotations

import csv
import difflib
import math
import os
import re
import sys
import unicodedata
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MAX_RESULTS = 5
PRODUCT_IDENTITY_FIELDS = frozenset(
    {"name", "aliases", "summary", "target_users", "scenarios", "core_tasks"}
)
MIN_PRODUCT_MATCH_SCORE = 10.0

DOMAIN_CONFIG: dict[str, dict[str, Any]] = {
    "product": {
        "file": "products.csv",
        "id": "product_id",
        "name_fields": ("name",),
        "search_fields": {
            "name": 6.0,
            "aliases": 5.0,
            "summary": 3.0,
            "target_users": 2.0,
            "scenarios": 2.0,
            "core_tasks": 3.0,
            "home_structure": 2.0,
            "nav_pattern": 1.5,
            "typical_component_ids": 1.0,
            "recommended_style_ids": 1.0,
            "avoid": 1.0,
            "design_reasoning": 1.0,
        },
        "label": "产品类型",
    },
    "style": {
        "file": "styles.csv",
        "id": "style_id",
        "name_fields": ("name_zh", "name_en"),
        "search_fields": {
            "name_zh": 6.0,
            "name_en": 5.0,
            "keywords": 5.0,
            "visual_traits": 3.0,
            "recommended_scenarios": 3.0,
            "typography_rules": 1.0,
            "component_traits": 2.0,
            "avoid_scenarios": 2.0,
            "common_errors": 1.5,
            "combination_notes": 1.0,
        },
        "label": "设计风格",
    },
    "color": {
        "file": "colors.csv",
        "id": "palette_id",
        "name_fields": ("name",),
        "search_fields": {
            "name": 6.0,
            "business_fit": 5.0,
            "usage": 3.0,
            "contrast_notes": 1.0,
            "style_ids": 1.0,
        },
        "label": "配色方案",
    },
    "layout": {
        "file": "layouts.csv",
        "id": "layout_id",
        "name_fields": ("page_type",),
        "search_fields": {
            "page_type": 6.0,
            "goal": 4.0,
            "hierarchy": 3.0,
            "primary_regions": 3.0,
            "secondary_regions": 2.0,
            "navigation": 2.0,
            "action_order": 2.0,
            "mobile_notes": 2.0,
            "common_errors": 2.0,
        },
        "label": "页面布局",
    },
    "component": {
        "file": "components.csv",
        "id": "component_id",
        "name_fields": ("name",),
        "search_fields": {
            "name": 6.0,
            "use_cases": 4.0,
            "visual_rules": 3.0,
            "interaction_rules": 3.0,
            "states": 2.0,
            "accessibility": 2.0,
            "native_implementation": 2.0,
            "common_errors": 2.0,
        },
        "label": "组件",
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "id": "rule_id",
        "name_fields": ("name",),
        "search_fields": {
            "name": 6.0,
            "category": 3.0,
            "scenario": 3.0,
            "problem": 3.0,
            "recommendation": 3.0,
            "bad_example": 1.0,
            "how_to_check": 2.0,
            "fix": 2.0,
        },
        "label": "UX 规则",
    },
    "mini-program": {
        "file": "mini-program-rules.csv",
        "id": "rule_id",
        "name_fields": ("name",),
        "search_fields": {
            "name": 6.0,
            "category": 3.0,
            "scenario": 3.0,
            "platform_behavior": 3.0,
            "recommendation": 3.0,
            "implementation": 2.0,
            "how_to_verify": 2.0,
        },
        "label": "微信小程序规则",
    },
    "anti-pattern": {
        "file": "anti-patterns.csv",
        "id": "anti_pattern_id",
        "name_fields": ("name",),
        "search_fields": {
            "name": 6.0,
            "manifestation": 4.0,
            "root_cause": 3.0,
            "scenario": 3.0,
            "detection": 3.0,
            "fix": 3.0,
        },
        "label": "反模式",
    },
    "typography": {
        "file": "typography.csv",
        "id": "typography_id",
        "name_fields": ("name",),
        "search_fields": {
            "name": 6.0,
            "moods": 3.0,
            "best_for": 3.0,
            "scale_rationale": 2.0,
            "mini_program_notes": 2.0,
        },
        "label": "字体与排版",
    },
    "reasoning": {
        "file": "ui-reasoning.csv",
        "id": "reasoning_id",
        "name_fields": ("scenario",),
        "search_fields": {
            "scenario": 6.0,
            "product_tags": 4.0,
            "conditions": 3.0,
            "explanation": 3.0,
        },
        "label": "设计推理",
    },
}

STACK_CONFIG: dict[str, dict[str, str]] = {
    "wechat-native": {
        "file": "stacks/wechat-native.csv",
        "label": "微信原生小程序",
    },
    "uni-app": {
        "file": "stacks/uni-app.csv",
        "label": "uni-app",
    },
    "taro": {
        "file": "stacks/taro.csv",
        "label": "Taro",
    },
}

STACK_SEARCH_FIELDS: dict[str, float] = {
    "category": 2.0,
    "guideline": 5.0,
    "description": 3.0,
    "do": 3.0,
    "don_t": 2.0,
    "code_good": 1.0,
    "code_bad": 1.0,
}

DOMAIN_ALIASES = {
    "products": "product",
    "styles": "style",
    "colors": "color",
    "palettes": "color",
    "layouts": "layout",
    "components": "component",
    "ux-guidelines": "ux",
    "mini": "mini-program",
    "mini-program-rules": "mini-program",
    "miniprogram": "mini-program",
    "anti": "anti-pattern",
    "anti-patterns": "anti-pattern",
    "typography": "typography",
    "reasoning": "reasoning",
    "all": "all",
}

UNTRUNCATED_FIELDS = {
    "code_good",
    "code_bad",
    "implementation",
    "native_implementation",
    "how_to_verify",
    "how_to_check",
    "recommendation",
}

# 只在查询和文档两侧同时扩展，保证召回一致性；不调用分词服务。
PHRASE_SYNONYMS: tuple[tuple[str, str], ...] = tuple(
    sorted(
        {
            "底部安全区域": "底部安全区 安全区域 safe-area safe area safe-area-inset-bottom",
            "底部安全区": "底部安全区域 安全区域 safe-area safe area safe-area-inset-bottom",
            "安全区域": "安全区 safe-area safe area 安全区适配",
            "安全区": "安全区域 safe-area safe area 安全区适配",
            "自定义导航栏": "自定义导航 navigationStyle custom 胶囊",
            "导航栏": "导航 navigation nav bar 标题栏",
            "底部标签栏": "bottom tabbar tab-bar 标签栏",
            "标签栏": "tabbar tab bar 标签页",
            "触控区域": "点击区域 触摸区域 touch target hit area",
            "点击区域": "触控区域 触摸区域 touch target hit area",
            "触摸目标": "点击区域 触控区域 touch target",
            "商品卡片": "商品卡 商品列表 product card",
            "商品列表": "商品卡片 product list listing",
            "配色方案": "配色 色板 色彩 palette color scheme",
            "配色": "色彩 色板 palette color",
            "设计风格": "风格 style aesthetic",
            "排版": "字体 字号 行高 typography font type",
            "布局": "页面结构 页面布局 layout page structure",
            "反模式": "anti-pattern anti pattern 常见错误",
            "小程序": "微信小程序 mini program wechat miniprogram",
            "微信小程序": "小程序 wechat miniprogram mini program",
            "原生小程序": "微信原生 wechat-native native mini program",
            "电商": "电商购物 ecommerce e-commerce shopping retail",
            "外卖": "点餐 food delivery takeout",
            "生鲜": "果蔬 grocery fresh produce",
            "旅游": "旅行 travel trip tourism",
            "酒店": "民宿 hotel booking stay",
            "票务": "演出票 ticketing tickets",
            "音乐": "播放器 音频 music player audio",
            "短视频": "视频流 short video feed",
            "社交": "社区 互动 social community",
            "教育": "学习 课程 education learning course",
            "记账": "预算 财务 personal finance expense budget",
            "金融": "银行 理财 保险 finance banking insurance",
            "企业": "办公 审批 enterprise business workflow",
            "看板": "数据 报表 dashboard analytics data",
            "工具": "效率 utility tool productivity",
            "文件": "文档 转换 file document convert",
            "AI": "助手 对话 ai assistant chatbot",
            "硬件": "设备 控制 hardware device iot",
            "农业": "智慧农业 种植 agriculture farming",
            "校园": "学校 学生 campus student",
            "健康": "医疗 医院 health medical hospital",
            "文创": "文化 IP cultural creative",
            "会员": "权益 订阅 membership loyalty subscription",
            "无障碍": "可访问性 accessibility a11y",
            "深色": "深色模式 dark mode",
            "浅色": "浅色模式 light mode",
            "加载": "loading 加载状态",
            "空状态": "empty state 空页面",
            "错误": "error 异常 错误恢复",
            "键盘": "keyboard 输入法 遮挡",
            "分享": "share 转发",
            "登录": "login 授权 auth",
            "路由": "route routing 页面栈",
            "动效": "动画 motion animation",
        }.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )
)

EN_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "what",
    "when",
    "where",
    "which",
    "why",
}
CJK_RE = re.compile(r"[㐀-䶿一-鿿]+")
WORD_RE = re.compile(r"[a-z0-9]+(?:[._/-][a-z0-9]+)*")
SEPARATORS_RE = re.compile(r"[^\w㐀-䶿一-鿿]+", re.UNICODE)

DOMAIN_HINTS: dict[str, tuple[str, ...]] = {
    "product": (
        "产品",
        "业务",
        "行业",
        "电商",
        "外卖",
        "生鲜",
        "旅游",
        "酒店",
        "教育",
        "音乐",
        "社区",
        "金融",
        "农业",
        "工具",
        "product",
        "industry",
    ),
    "style": (
        "风格",
        "美学",
        "气质",
        "极简",
        "东方",
        "复古",
        "未来",
        "高级感",
        "style",
        "aesthetic",
    ),
    "color": ("配色", "色板", "颜色", "主色", "对比度", "palette", "color", "hex"),
    "layout": ("布局", "页面结构", "首页", "列表页", "详情页", "layout", "structure"),
    "component": (
        "组件",
        "卡片",
        "按钮",
        "搜索框",
        "弹窗",
        "表单",
        "塔布",
        "component",
        "card",
        "button",
        "modal",
    ),
    "ux": (
        "体验",
        "交互",
        "可用性",
        "反馈",
        "错误",
        "空状态",
        "键盘",
        "ux",
        "usability",
        "interaction",
    ),
    "mini-program": (
        "小程序",
        "微信",
        "安全区域",
        "安全区",
        "导航栏",
        "路由",
        "页面栈",
        "tabbar",
        "wechat",
        "miniprogram",
        "mini program",
        "safe area",
    ),
    "anti-pattern": ("反模式", "常见错误", "避免", "问题", "anti-pattern", "anti pattern", "bad practice"),
    "typography": ("字体", "排版", "字号", "行高", "typography", "font"),
    "reasoning": ("推理", "为什么", "选择理由", "决策", "reasoning", "rationale"),
}


def configure_utf8_stdio() -> None:
    """Windows 控制台默认编码可能不是 UTF-8。"""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass


def utf8_subprocess_env() -> dict[str, str]:
    """强制 Python 子进程以 UTF-8 输出，避免继承 Windows 默认代码页。"""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _normalise(text: Any) -> str:
    value = unicodedata.normalize("NFKC", str(text or ""))
    value = value.casefold()
    value = value.replace("（", "(").replace("）", ")")
    return value


def _expand_synonyms(text: str) -> str:
    base = _normalise(text)
    extra: list[str] = []
    for phrase, expansion in PHRASE_SYNONYMS:
        if phrase.casefold() in base:
            extra.append(expansion)
    if extra:
        return base + " " + " ".join(extra)
    return base


def tokenize(text: Any) -> list[str]:
    """中英文混合 tokenizer。

    - 英文/数字按词切分，并保留 ecommerce、uni-app、rpx 等标识。
    - 中文连续文本同时加入完整短语（不超过 16 字）和相邻二字 bigram。
    - 同义词扩展在分词前完成，保证“底部安全区域”和“safe area”可互查。
    """
    if text is None:
        return []
    value = _expand_synonyms(str(text))
    value = SEPARATORS_RE.sub(" ", value)
    tokens: list[str] = []

    for cjk in CJK_RE.findall(value):
        if len(cjk) == 1:
            tokens.append(cjk)
            continue
        if len(cjk) <= 16:
            tokens.append(cjk)
        for index in range(len(cjk) - 1):
            tokens.append(cjk[index : index + 2])

    for word in WORD_RE.findall(value):
        word = word.strip("._/-")
        if not word:
            continue
        parts = [part for part in re.split(r"[._/-]+", word) if part]
        candidates = [word, *parts]
        for candidate in candidates:
            if candidate and candidate not in EN_STOPWORDS:
                tokens.append(candidate)
                if len(candidate) > 3 and candidate.endswith("s") and not candidate.endswith("ss"):
                    tokens.append(candidate[:-1])

    return tokens


def _flat(text: Any) -> str:
    value = _normalise(text)
    value = SEPARATORS_RE.sub("", value)
    return value


def _strip_product_suffix(text: str) -> str:
    value = _flat(text)
    for suffix in ("微信小程序", "小程序", "应用程序", "应用", "app"):
        if value.endswith(suffix) and len(value) > len(suffix):
            value = value[: -len(suffix)]
            break
    return value


class BM25Index:
    """轻量 BM25 索引，词频支持字段权重。"""

    def __init__(self, rows: list[dict[str, str]], search_fields: dict[str, float]):
        self.rows = rows
        self.search_fields = search_fields
        self.term_freqs: list[Counter[str]] = []
        self.lengths: list[int] = []
        self.vocabulary: set[str] = set()
        document_frequency: Counter[str] = Counter()

        for row in rows:
            frequencies: Counter[str] = Counter()
            length = 0
            for field, weight in search_fields.items():
                field_tokens = tokenize(row.get(field, ""))
                for token in field_tokens:
                    weighted = max(1, int(round(weight)))
                    frequencies[token] += weighted
                    length += weighted
            self.term_freqs.append(frequencies)
            self.lengths.append(max(length, 1))
            self.vocabulary.update(frequencies)
            document_frequency.update(frequencies.keys())

        self.document_count = len(rows)
        self.average_length = (
            sum(self.lengths) / len(self.lengths) if self.lengths else 1.0
        )
        self.idf: dict[str, float] = {
            term: math.log(
                1.0
                + (self.document_count - frequency + 0.5)
                / (frequency + 0.5)
            )
            for term, frequency in document_frequency.items()
        }
        self._field_token_sets: list[dict[str, set[str]]] = []
        for row in rows:
            field_sets = {
                field: set(tokenize(row.get(field, "")))
                for field in search_fields
            }
            self._field_token_sets.append(field_sets)

    def score(self, query_tokens: Iterable[str], row_index: int) -> float:
        frequencies = self.term_freqs[row_index]
        if not frequencies:
            return 0.0
        k1 = 1.5
        b = 0.75
        length = self.lengths[row_index]
        score = 0.0
        for token in set(query_tokens):
            tf = frequencies.get(token, 0)
            if not tf:
                continue
            idf = self.idf.get(token, 0.0)
            denominator = tf + k1 * (1.0 - b + b * length / self.average_length)
            score += idf * (tf * (k1 + 1.0)) / denominator
        return score

    def matched_fields(self, query_tokens: Iterable[str], row_index: int) -> list[dict[str, Any]]:
        query_set = set(query_tokens)
        matches: list[dict[str, Any]] = []
        for field, tokens in self._field_token_sets[row_index].items():
            common = sorted(query_set & tokens)
            if common:
                matches.append(
                    {
                        "field": field,
                        "terms": common[:10],
                        "count": len(common),
                    }
                )
        matches.sort(key=lambda item: (item["count"], self.rows[row_index].get(item["field"], "")), reverse=True)
        return matches[:8]


_ROW_CACHE: dict[Path, list[dict[str, str]]] = {}
_INDEX_CACHE: dict[tuple[Path, tuple[str, ...]], BM25Index] = {}


@lru_cache(maxsize=None)
def _read_csv_cached(file_path: str) -> tuple[dict[str, str], ...]:
    path = Path(file_path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return tuple(dict(row) for row in reader)


def read_csv(file_path: Path) -> list[dict[str, str]]:
    key = file_path.resolve()
    if key not in _ROW_CACHE:
        _ROW_CACHE[key] = [dict(row) for row in _read_csv_cached(str(key))]
    return _ROW_CACHE[key]


def load_domain(domain: str) -> list[dict[str, str]]:
    domain = resolve_domain(domain)
    if domain == "all":
        raise ValueError("load_domain() 不接受 all")
    config = DOMAIN_CONFIG[domain]
    return read_csv(DATA_DIR / config["file"])


def resolve_domain(domain: str | None) -> str:
    if not domain:
        return ""
    key = domain.strip().casefold()
    key = DOMAIN_ALIASES.get(key, key)
    if key == "all":
        return "all"
    if key not in DOMAIN_CONFIG:
        valid = ", ".join(DOMAIN_CONFIG)
        raise ValueError(f"未知分类 {domain!r}；可用分类：{valid}")
    return key


def _get_index(domain: str) -> BM25Index:
    config = DOMAIN_CONFIG[domain]
    path = (DATA_DIR / config["file"]).resolve()
    key = (path, tuple(config["search_fields"].keys()))
    if key not in _INDEX_CACHE:
        _INDEX_CACHE[key] = BM25Index(read_csv(path), config["search_fields"])
    return _INDEX_CACHE[key]


def detect_domain(query: str) -> tuple[str, str | None, dict[str, int]]:
    folded = _normalise(query)
    scores: dict[str, int] = {}
    for domain, hints in DOMAIN_HINTS.items():
        score = 0
        for hint in hints:
            if hint.casefold() in folded:
                score += 2 if len(hint) >= 2 else 1
        scores[domain] = score
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    if not ordered or ordered[0][1] == 0:
        return "all", None, scores
    runner_up = ordered[1][0] if len(ordered) > 1 and ordered[1][1] > 0 else None
    return ordered[0][0], runner_up, scores


def _record_name(domain: str, record: dict[str, str]) -> str:
    fields = DOMAIN_CONFIG[domain]["name_fields"]
    for field in fields:
        if record.get(field):
            return record[field]
    return record.get(DOMAIN_CONFIG[domain]["id"], "")


def _record_aliases(record: dict[str, str]) -> list[str]:
    values: list[str] = []
    for field in ("aliases", "keywords", "name_en", "scenario"):
        raw = record.get(field, "")
        if not raw:
            continue
        values.extend(part.strip() for part in raw.split("|") if part.strip())
    return values


def _exact_match_score(domain: str, record: dict[str, str], query: str) -> tuple[float, list[str]]:
    config = DOMAIN_CONFIG[domain]
    query_flat = _flat(query)
    query_flat_no_suffix = _strip_product_suffix(query)
    identities = [record.get(config["id"], ""), *_record_name_for_matching(domain, record), *_record_aliases(record)]
    identity_flats = {_flat(item) for item in identities if item}
    achieved = 0.0
    reasons: list[str] = []
    if query_flat and query_flat in identity_flats:
        achieved += 40.0
        reasons.append("名称/别名精确命中")
    elif query_flat_no_suffix and query_flat_no_suffix in identity_flats:
        achieved += 36.0
        reasons.append("名称/别名精确命中（忽略产品后缀）")
    for identity in identity_flats:
        if len(identity) >= 2 and identity != query_flat and (
            identity in query_flat or query_flat in identity
        ):
            achieved += 10.0
            reasons.append("名称/别名与查询存在包含关系")
            break
    return achieved, reasons


def _record_name_for_matching(domain: str, record: dict[str, str]) -> list[str]:
    result = []
    for field in DOMAIN_CONFIG[domain]["name_fields"]:
        if record.get(field):
            result.append(record[field])
    return result


def _product_preference_ids(product: dict[str, str] | None) -> dict[str, set[str]]:
    preferred: dict[str, set[str]] = {
        "style": set(),
        "color": set(),
        "layout": set(),
        "component": set(),
        "ux": set(),
        "anti-pattern": set(),
    }
    if not product:
        return preferred
    for domain, field in (
        ("style", "recommended_style_ids"),
        ("color", "recommended_color_ids"),
        ("layout", "primary_layout_ids"),
        ("component", "typical_component_ids"),
    ):
        preferred[domain].update(
            item.strip() for item in product.get(field, "").split(";") if item.strip()
        )
    reasoning_ids = [
        item.strip() for item in product.get("reasoning_ids", "").split(";") if item.strip()
    ]
    reasoning_rows = {row["reasoning_id"]: row for row in load_domain("reasoning")}
    for reasoning_id in reasoning_ids:
        row = reasoning_rows.get(reasoning_id)
        if not row:
            continue
        preferred["ux"].update(
            item.strip() for item in row.get("interaction_priority", "").split(";") if item.strip()
        )
        preferred["anti-pattern"].update(
            item.strip() for item in row.get("avoid", "").split(";") if item.strip()
        )
    return preferred


def is_strong_product_match(result: dict[str, Any]) -> bool:
    """产品解析必须命中身份字段，不能只靠 nav_pattern 等通用字段。"""
    if not isinstance(result, dict):
        return False
    score = result.get("score", 0)
    if not isinstance(score, (int, float)) or score < MIN_PRODUCT_MATCH_SCORE:
        return False
    matched_fields = {
        item.get("field")
        for item in result.get("matched_fields", [])
        if isinstance(item, dict)
    }
    return bool(matched_fields & PRODUCT_IDENTITY_FIELDS)


def resolve_product_reference(reference: str) -> dict[str, str] | None:
    if not reference:
        return None
    reference_flat = _strip_product_suffix(reference)
    for row in load_domain("product"):
        if _flat(row.get("product_id", "")) == _flat(reference):
            return row
        identities = [row.get("name", ""), *row.get("aliases", "").split("|")]
        if reference_flat and reference_flat in {_strip_product_suffix(item) for item in identities}:
            return row
    result = _search_single_domain(
        query=reference,
        domain="product",
        limit=5,
    )
    for item in result["results"]:
        if is_strong_product_match(item):
            return item["record"]
    return None


def search_knowledge(
    query: str,
    domain: str | None = None,
    limit: int = MAX_RESULTS,
    *,
    product: str | None = None,
    full: bool = False,
) -> dict[str, Any]:
    """搜索本地设计知识库。

    返回结构化结果；不访问网络。domain=None 时自动识别，all 时合并所有领域。
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("查询不能为空")
    limit = _normalise_limit(limit)
    product_record = resolve_product_reference(product) if product else None
    requested_domain = (domain or "").strip().casefold()
    domain_was_autodetected = False
    runner_up: str | None = None

    if not requested_domain:
        domain_was_autodetected = True
        detected, runner_up, _ = detect_domain(query)
        requested_domain = detected
    if requested_domain != "all":
        requested_domain = resolve_domain(requested_domain)

    if requested_domain == "all":
        merged_results: list[dict[str, Any]] = []
        for candidate in DOMAIN_CONFIG:
            result = _search_single_domain(
                query,
                candidate,
                limit=limit,
                product_record=product_record,
            )
            for item in result["results"]:
                item["domain"] = candidate
                item["source"] = result["source"]
                merged_results.append(item)
        merged_results.sort(key=lambda item: (-item["score"], item["domain"], item["id"]))
        merged_results = merged_results[:limit]
        return {
            "query": query,
            "domain": "all",
            "label": "全部知识库",
            "source": "data/*.csv",
            "count": len(merged_results),
            "results": merged_results,
            "suggestions": [],
            "notice": (
                "" if merged_results else "未找到匹配记录。请改用更具体的中文或英文关键词。"
            ),
            "auto_detected": domain_was_autodetected,
            "runner_up_domain": runner_up,
            "product_context": _product_context_summary(product_record),
        }

    result = _search_single_domain(
        query,
        requested_domain,
        limit=limit,
        product_record=product_record,
    )
    result["auto_detected"] = domain_was_autodetected
    result["runner_up_domain"] = runner_up
    result["product_context"] = _product_context_summary(product_record)
    return result


def _product_context_summary(product: dict[str, str] | None) -> dict[str, str] | None:
    if not product:
        return None
    return {
        "product_id": product.get("product_id", ""),
        "name": product.get("name", ""),
    }


def _normalise_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError) as exc:
        raise ValueError("结果数量必须是整数") from exc
    if value < 1 or value > 20:
        raise ValueError("结果数量必须在 1–20 之间")
    return value


def _search_single_domain(
    query: str,
    domain: str,
    limit: int,
    product_record: dict[str, str] | None = None,
) -> dict[str, Any]:
    config = DOMAIN_CONFIG[domain]
    rows = load_domain(domain)
    index = _get_index(domain)
    query_tokens = tokenize(query)
    if not query_tokens:
        return _empty_result(query, domain, config, [], "查询没有可检索的词。")

    preferred = _product_preference_ids(product_record)
    scored: list[tuple[float, int, list[str], list[dict[str, Any]]]] = []
    for row_index, row in enumerate(rows):
        if product_record and domain == "product":
            if row.get("product_id") != product_record.get("product_id"):
                continue
        base_score = index.score(query_tokens, row_index)
        exact_score, exact_reasons = _exact_match_score(domain, row, query)
        boost = 0.0
        row_id = row.get(config["id"], "")
        if row_id in preferred.get(domain, set()):
            boost += 2.5
        total = base_score + exact_score + boost
        if total <= 0:
            continue
        matched_fields = index.matched_fields(query_tokens, row_index)
        reasons = list(exact_reasons)
        if boost:
            reasons.append("与指定产品类型的推荐记录一致")
        scored.append((total, row_index, reasons, matched_fields))

    scored.sort(key=lambda item: (-item[0], rows[item[1]].get(config["id"], "")))
    selected = scored[:limit]
    results: list[dict[str, Any]] = []
    for score, row_index, reasons, matched_fields in selected:
        row = rows[row_index]
        matched_terms = sorted(
            {
                term
                for field_match in matched_fields
                for term in field_match["terms"]
            }
        )
        results.append(
            {
                "id": row.get(config["id"], ""),
                "name": _record_name(domain, row),
                "score": round(score, 3),
                "matched_terms": matched_terms[:12],
                "matched_fields": matched_fields,
                "reasons": reasons,
                "record": row,
                "source": str(Path("data") / config["file"]).replace("\\", "/"),
            }
        )

    suggestions: list[str] = []
    notice = ""
    if not results:
        suggestions = _suggest_terms(rows, config, query)
        notice = (
            "未找到匹配记录。这是真实的 0 结果，不是字段为空；"
            "请换用更具体的产品、风格、组件或问题描述。"
        )
    return {
        "query": query,
        "domain": domain,
        "label": config["label"],
        "source": results[0]["source"] if results else str(Path("data") / config["file"]).replace("\\", "/"),
        "count": len(results),
        "results": results,
        "suggestions": suggestions,
        "notice": notice,
    }


def _suggest_terms(rows: list[dict[str, str]], config: dict[str, Any], query: str) -> list[str]:
    query_flat = _flat(query)
    candidates: set[str] = set()
    for row in rows:
        candidates.add(row.get(config["id"], ""))
        for name_field in config["name_fields"]:
            value = row.get(name_field, "")
            if value:
                candidates.add(value)
        for alias in row.get("aliases", "").split("|"):
            if alias.strip():
                candidates.add(alias.strip())
    candidates.discard("")
    close = difflib.get_close_matches(query_flat, list(candidates), n=5, cutoff=0.35)
    if not close:
        close = sorted(candidates)[:5]
    return close


def _empty_result(
    query: str,
    domain: str,
    config: dict[str, Any],
    suggestions: list[str],
    notice: str,
) -> dict[str, Any]:
    return {
        "query": query,
        "domain": domain,
        "label": config["label"],
        "source": str(Path("data") / config["file"]).replace("\\", "/"),
        "count": 0,
        "results": [],
        "suggestions": suggestions,
        "notice": notice,
    }


def search_stack(query: str, stack: str, limit: int = MAX_RESULTS) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("查询不能为空")
    stack_key = (stack or "").strip().casefold()
    if stack_key not in STACK_CONFIG:
        raise ValueError(
            f"未知技术栈 {stack!r}；可用：{', '.join(STACK_CONFIG)}"
        )
    limit = _normalise_limit(limit)
    path = DATA_DIR / STACK_CONFIG[stack_key]["file"]
    rows = read_csv(path)
    index_key = (path.resolve(), tuple(STACK_SEARCH_FIELDS.keys()))
    if index_key not in _INDEX_CACHE:
        _INDEX_CACHE[index_key] = BM25Index(rows, STACK_SEARCH_FIELDS)
    index = _INDEX_CACHE[index_key]
    query_tokens = tokenize(query)
    scored: list[tuple[float, int, list[str], list[dict[str, Any]]]] = []
    for row_index, row in enumerate(rows):
        base_score = index.score(query_tokens, row_index)
        exact_score = 0.0
        reasons: list[str] = []
        if _flat(query) and _flat(query) == _flat(row.get("rule_id", "")):
            exact_score += 30.0
            reasons.append("规则 ID 精确命中")
        if _flat(row.get("guideline", "")) and _flat(row.get("guideline", "")) == _flat(query):
            exact_score += 20.0
            reasons.append("规则名称精确命中")
        total = base_score + exact_score
        if total <= 0:
            continue
        scored.append(
            (
                total,
                row_index,
                reasons,
                index.matched_fields(query_tokens, row_index),
            )
        )
    scored.sort(key=lambda item: (-item[0], rows[item[1]].get("rule_id", "")))
    results: list[dict[str, Any]] = []
    for score, row_index, reasons, matched_fields in scored[:limit]:
        row = rows[row_index]
        results.append(
            {
                "id": row.get("rule_id", ""),
                "name": row.get("guideline", ""),
                "score": round(score, 3),
                "matched_terms": sorted(
                    {
                        term
                        for field_match in matched_fields
                        for term in field_match["terms"]
                    }
                )[:12],
                "matched_fields": matched_fields,
                "reasons": reasons,
                "record": row,
                "source": str(Path("data") / STACK_CONFIG[stack_key]["file"]).replace("\\", "/"),
            }
        )
    suggestions = []
    notice = ""
    if not results:
        names = [row.get("guideline", "") for row in rows]
        suggestions = difflib.get_close_matches(query, names, n=5, cutoff=0.3)
        notice = "该技术栈没有匹配规则。请换用具体 API、组件、布局或平台问题。"
    return {
        "query": query,
        "stack": stack_key,
        "stack_label": STACK_CONFIG[stack_key]["label"],
        "source": str(Path("data") / STACK_CONFIG[stack_key]["file"]).replace("\\", "/"),
        "count": len(results),
        "results": results,
        "suggestions": suggestions,
        "notice": notice,
    }


def format_markdown(result: dict[str, Any], *, full: bool = False) -> str:
    if result.get("stack"):
        lines = [
            "## MPUX Pro · 技术栈规则检索",
            "",
            f"- **查询**：{result['query']}",
            f"- **技术栈**：{result['stack_label']} (`{result['stack']}`)",
            f"- **数据源**：`{result['source']}`",
            f"- **结果数**：{result['count']}",
            "",
        ]
    else:
        domain_label = result.get("label", result.get("domain", ""))
        auto_note = "（自动识别）" if result.get("auto_detected") else ""
        lines = [
            "## MPUX Pro · 设计知识检索",
            "",
            f"- **查询**：{result['query']}",
            f"- **分类**：{domain_label} (`{result.get('domain', '')}`){auto_note}",
            f"- **数据源**：`{result['source']}`",
            f"- **结果数**：{result['count']}",
            "",
        ]
        if result.get("product_context"):
            context = result["product_context"]
            lines.append(
                f"- **产品上下文**：{context['name']} (`{context['product_id']}`)"
            )
            lines.append("")

    if result["count"] == 0:
        lines.append(result.get("notice") or "未找到匹配记录。")
        if result.get("suggestions"):
            lines.append("")
            lines.append("**可能的相近词**：" + "、".join(f"`{item}`" for item in result["suggestions"]))
        return "\n".join(lines).rstrip()

    for index_number, item in enumerate(result["results"], start=1):
        record = item["record"]
        lines.append(f"### {index_number}. `{item['id']}` · {item['name']}")
        lines.append("")
        lines.append(f"- **匹配分**：{item['score']}")
        if item.get("matched_terms"):
            lines.append(
                "- **命中词**：" + "、".join(f"`{term}`" for term in item["matched_terms"])
            )
        if item.get("matched_fields"):
            field_text = "；".join(
                f"{match['field']}（{match['count']}）"
                for match in item["matched_fields"][:6]
            )
            lines.append(f"- **命中字段**：{field_text}")
        if item.get("reasons"):
            lines.append("- **加权原因**：" + "；".join(item["reasons"]))
        lines.append(f"- **记录来源**：`{item['source']}`")
        lines.append("")
        for field, value in record.items():
            if field == "id" or not value:
                continue
            rendered = str(value)
            if not full and field not in UNTRUNCATED_FIELDS and len(rendered) > 320:
                rendered = rendered[:320] + "…"
            lines.append(f"- **{field}**：{rendered}")
        lines.append("")
    return "\n".join(lines).rstrip()


def result_to_json(result: dict[str, Any]) -> str:
    import json

    return json.dumps(result, ensure_ascii=False, indent=2)


def design_system_search_prelude(query: str, product: str | None = None) -> dict[str, Any]:
    """供设计系统生成器使用的多领域检索结果摘要。"""
    product_record = resolve_product_reference(product or query)
    domain_queries = {
        "product": query,
        "style": query,
        "color": query,
        "layout": query,
        "component": query,
        "ux": query,
        "mini-program": query,
        "anti-pattern": query,
        "typography": query,
        "reasoning": query,
    }
    output = {}
    for domain_name, domain_query in domain_queries.items():
        output[domain_name] = _search_single_domain(
            domain_query,
            domain_name,
            limit=3,
            product_record=product_record,
        )
    return output


def available_products() -> list[dict[str, str]]:
    return load_domain("product")


def available_styles() -> list[dict[str, str]]:
    return load_domain("style")


def available_palettes() -> list[dict[str, str]]:
    return load_domain("color")


def get_record(domain: str, record_id: str) -> dict[str, str] | None:
    domain = resolve_domain(domain)
    id_field = DOMAIN_CONFIG[domain]["id"]
    for row in load_domain(domain):
        if row.get(id_field) == record_id:
            return row
    return None


def get_stack_record(stack: str, record_id: str) -> dict[str, str] | None:
    stack = stack.strip().casefold()
    if stack not in STACK_CONFIG:
        return None
    for row in read_csv(DATA_DIR / STACK_CONFIG[stack]["file"]):
        if row.get("rule_id") == record_id:
            return row
    return None