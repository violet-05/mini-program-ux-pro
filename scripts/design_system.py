#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MPUX Pro 设计系统生成器。

生成过程完全读取 data/ 中的原创知识库，并使用可解释的选择规则。
不调用远程 AI API，不伪造不存在的设计记录。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mpux_core import (
    DATA_DIR,
    DOMAIN_CONFIG,
    STACK_CONFIG,
    configure_utf8_stdio,
    get_stack_record,
    load_domain,
    read_csv,
    resolve_product_reference,
    search_knowledge,
    search_stack,
    tokenize,
)

VERSION = "1.0.0"

STYLE_TOKEN_PROFILES: dict[str, dict[str, Any]] = {
    "style-minimal": {
        "radius": [4, 8, 12, 999],
        "shadow": "none",
        "motion": "quick",
        "line_height": 1.65,
        "scale": [22, 26, 30, 34, 42, 52],
    },
    "style-swiss": {
        "radius": [0, 4, 8, 0],
        "shadow": "none",
        "motion": "quick",
        "line_height": 1.6,
        "scale": [22, 26, 30, 34, 40, 48],
    },
    "style-editorial": {
        "radius": [0, 6, 10, 0],
        "shadow": "none",
        "motion": "standard",
        "line_height": 1.78,
        "scale": [22, 26, 32, 38, 48, 64],
    },
    "style-oriental-modern": {
        "radius": [6, 12, 18, 999],
        "shadow": "subtle",
        "motion": "gentle",
        "line_height": 1.72,
        "scale": [22, 26, 30, 36, 44, 56],
    },
    "style-new-chinese": {
        "radius": [6, 12, 18, 999],
        "shadow": "subtle",
        "motion": "gentle",
        "line_height": 1.68,
        "scale": [22, 26, 30, 36, 42, 52],
    },
    "style-premium-commerce": {
        "radius": [2, 8, 12, 999],
        "shadow": "subtle",
        "motion": "standard",
        "line_height": 1.62,
        "scale": [22, 26, 30, 34, 40, 48],
    },
    "style-trend": {
        "radius": [0, 12, 20, 999],
        "shadow": "crisp",
        "motion": "expressive",
        "line_height": 1.55,
        "scale": [22, 26, 30, 38, 48, 64],
    },
    "style-playful": {
        "radius": [12, 20, 28, 999],
        "shadow": "soft",
        "motion": "expressive",
        "line_height": 1.7,
        "scale": [22, 26, 30, 36, 44, 54],
    },
    "style-soft-organic": {
        "radius": [12, 20, 28, 999],
        "shadow": "soft",
        "motion": "gentle",
        "line_height": 1.72,
        "scale": [22, 26, 30, 34, 42, 50],
    },
    "style-retro": {
        "radius": [0, 6, 8, 999],
        "shadow": "crisp",
        "motion": "standard",
        "line_height": 1.64,
        "scale": [22, 26, 30, 36, 44, 54],
    },
    "style-brutalist": {
        "radius": [0, 0, 0, 0],
        "shadow": "crisp",
        "motion": "quick",
        "line_height": 1.55,
        "scale": [22, 26, 30, 38, 48, 64],
    },
    "style-futuristic": {
        "radius": [8, 12, 16, 999],
        "shadow": "layer",
        "motion": "standard",
        "line_height": 1.6,
        "scale": [22, 26, 30, 34, 42, 54],
    },
    "style-soft-skeuomorphic": {
        "radius": [12, 16, 20, 999],
        "shadow": "soft",
        "motion": "standard",
        "line_height": 1.66,
        "scale": [22, 26, 30, 34, 42, 50],
    },
    "style-neomorphic": {
        "radius": [16, 24, 32, 999],
        "shadow": "emboss",
        "motion": "standard",
        "line_height": 1.68,
        "scale": [22, 26, 30, 34, 42, 48],
    },
    "style-glass": {
        "radius": [12, 16, 24, 999],
        "shadow": "layer",
        "motion": "gentle",
        "line_height": 1.66,
        "scale": [22, 26, 30, 34, 42, 50],
    },
    "style-illustration": {
        "radius": [12, 18, 24, 999],
        "shadow": "soft",
        "motion": "expressive",
        "line_height": 1.7,
        "scale": [22, 26, 30, 34, 42, 50],
    },
    "style-content-first": {
        "radius": [0, 6, 10, 999],
        "shadow": "none",
        "motion": "standard",
        "line_height": 1.82,
        "scale": [22, 28, 32, 36, 44, 52],
    },
    "style-data-dense": {
        "radius": [2, 6, 8, 4],
        "shadow": "none",
        "motion": "quick",
        "line_height": 1.5,
        "scale": [22, 24, 28, 32, 38, 46],
    },
    "style-gamified": {
        "radius": [12, 20, 28, 999],
        "shadow": "soft",
        "motion": "expressive",
        "line_height": 1.62,
        "scale": [22, 26, 30, 36, 44, 56],
    },
    "style-natural-eco": {
        "radius": [8, 16, 24, 999],
        "shadow": "subtle",
        "motion": "gentle",
        "line_height": 1.7,
        "scale": [22, 26, 30, 34, 42, 50],
    },
    "style-handcrafted": {
        "radius": [4, 10, 16, 999],
        "shadow": "subtle",
        "motion": "gentle",
        "line_height": 1.72,
        "scale": [22, 26, 30, 36, 44, 52],
    },
    "style-cultural-creative": {
        "radius": [6, 12, 16, 999],
        "shadow": "subtle",
        "motion": "standard",
        "line_height": 1.7,
        "scale": [22, 26, 30, 36, 44, 52],
    },
}

DEFAULT_STYLE_PROFILE = {
    "radius": [8, 12, 16, 999],
    "shadow": "subtle",
    "motion": "standard",
    "line_height": 1.65,
    "scale": [22, 26, 30, 34, 42, 50],
}

DENSITY_PROFILES: dict[str, dict[str, Any]] = {
    "low": {
        "label": "低",
        "page_gutter": 32,
        "section_gap": 64,
        "card_gap": 24,
        "scale": [8, 16, 24, 32, 48, 64, 96],
    },
    "medium": {
        "label": "中",
        "page_gutter": 32,
        "section_gap": 48,
        "card_gap": 24,
        "scale": [8, 16, 24, 32, 40, 56, 80],
    },
    "medium_high": {
        "label": "中高",
        "page_gutter": 32,
        "section_gap": 40,
        "card_gap": 20,
        "scale": [8, 16, 24, 32, 40, 48, 64],
    },
    "high": {
        "label": "高",
        "page_gutter": 24,
        "section_gap": 32,
        "card_gap": 16,
        "scale": [8, 12, 16, 24, 32, 48, 64],
    },
}

MOTION_PROFILES = {
    "quick": {"fast": 100, "normal": 150, "slow": 200},
    "standard": {"fast": 120, "normal": 180, "slow": 240},
    "gentle": {"fast": 160, "normal": 220, "slow": 280},
    "expressive": {"fast": 180, "normal": 260, "slow": 320},
}

FIXED_BOTTOM_LAYOUTS = {
    "layout-product-detail",
    "layout-cart",
    "layout-checkout",
    "layout-course-detail",
    "layout-event-detail",
    "layout-article-detail",
    "layout-booking",
    "layout-chat",
    "layout-music-player",
}

FORM_LAYOUTS = {
    "layout-form",
    "layout-checkout",
    "layout-booking",
    "layout-login",
    "layout-settings",
}

LIST_LAYOUTS = {
    "layout-home",
    "layout-category",
    "layout-search-results",
    "layout-product-list",
    "layout-order-list",
    "layout-messages",
    "layout-course-list",
}

ALWAYS_UX_IDS = [
    "ux-hierarchy",
    "ux-action-feedback",
    "ux-loading-states",
    "ux-error-states",
    "ux-touch-target",
    "ux-back-behavior",
]

ALWAYS_MINI_RULE_IDS = [
    "mp-native-nav",
    "mp-safe-area",
    "mp-touch-target",
    "mp-back",
    "mp-page-lifecycle",
    "mp-performance",
    "mp-devtools-vs-device",
]

STACK_BASE_RULE_IDS = {
    "wechat-native": [
        "wx-project-structure",
        "wx-wxml-binding",
        "wx-wxss-rpx",
        "wx-routing",
        "wx-safe-area",
        "wx-page-config",
        "wx-native-component",
    ],
    "uni-app": [
        "uni-project",
        "uni-pages-json",
        "uni-components",
        "uni-rpx",
        "uni-route",
        "uni-safe-area",
        "uni-lifecycle",
    ],
    "taro": [
        "taro-project",
        "taro-app-config",
        "taro-components",
        "taro-css-units",
        "taro-route",
        "taro-safe-area",
        "taro-lifecycle",
    ],
}

SHADOW_TEMPLATES = {
    "none": "none",
    "subtle": "0 4rpx 16rpx rgba(20, 20, 20, 0.06)",
    "soft": "0 8rpx 28rpx rgba(20, 20, 20, 0.08)",
    "crisp": "0 2rpx 0 rgba(20, 20, 20, 0.18)",
    "layer": "0 12rpx 32rpx rgba(10, 15, 25, 0.18)",
    "emboss": "8rpx 8rpx 20rpx rgba(30, 35, 40, 0.10), -8rpx -8rpx 20rpx rgba(255, 255, 255, 0.72)",
}


class DesignSystemError(RuntimeError):
    """可向 CLI 用户直接展示的设计系统生成错误。"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or fallback


def _density_bucket(value: str) -> str:
    value = (value or "").strip()
    if "中高" in value:
        return "medium_high"
    if "中低" in value:
        return "low"
    if "高" in value:
        return "high"
    if "低" in value:
        return "low"
    return "medium"


def _density_rank(value: str) -> int:
    return {"low": 0, "medium": 1, "medium_high": 2, "high": 3}.get(
        _density_bucket(value), 1
    )


def _normalise_key(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").casefold())


def _resolve_product(description: str) -> tuple[dict[str, str], str, float]:
    if not description or not description.strip():
        raise DesignSystemError("--product 不能为空")
    reference = _normalise_key(description.replace("小程序", "").replace("应用", ""))
    for row in load_domain("product"):
        identities = [row.get("product_id", ""), row.get("name", "")]
        identities.extend(row.get("aliases", "").split("|"))
        for identity in identities:
            if reference and _normalise_key(identity) == reference:
                return row, "exact", 1.0
    result = search_knowledge(description, domain="product", limit=3)
    if not result["results"]:
        suggestions = "、".join(result.get("suggestions", [])[:4])
        hint = f" 可尝试：{suggestions}。" if suggestions else ""
        raise DesignSystemError(
            f"知识库没有匹配的产品类型“{description}”。请使用更具体的产品名称或先运行 search.py --domain product 检索。{hint}"
        )
    top = result["results"][0]
    if top["score"] < 10.0:
        suggestions = "、".join(result.get("suggestions", [])[:4])
        hint = f" 可尝试：{suggestions}。" if suggestions else ""
        raise DesignSystemError(
            f"产品描述“{description}”与知识库的匹配过弱，不能安全地生成设计系统。"
            f"请使用更明确的产品类型或先运行 search.py --domain product 检索。{hint}"
        )
    confidence = min(0.95, max(0.55, top["score"] / 100.0))
    return top["record"], "search", round(confidence, 2)


def _style_lookup() -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in load_domain("style"):
        keys = [row.get("style_id", ""), row.get("name_zh", ""), row.get("name_en", "")]
        keys.extend(row.get("keywords", "").split("|"))
        keys.extend(row.get("name_zh", "").removesuffix("风格").split("、"))
        for key in keys:
            if key.strip():
                lookup.setdefault(_normalise_key(key), row)
    return lookup


def _resolve_style(style_reference: str | None) -> tuple[dict[str, str], str]:
    if not style_reference:
        return {}, ""
    lookup = _style_lookup()
    direct = lookup.get(_normalise_key(style_reference))
    if direct:
        return direct, "explicit"
    result = search_knowledge(style_reference, domain="style", limit=3)
    if result["results"] and result["results"][0]["score"] >= 10.0:
        return result["results"][0]["record"], "explicit-search"
    available = "、".join(
        f"{row['name_zh']} ({row['style_id']})" for row in load_domain("style")
    )
    raise DesignSystemError(
        f"没有找到设计风格“{style_reference}”。可用风格：{available}"
    )


def _select_style(
    product: dict[str, str], style_reference: str | None
) -> tuple[dict[str, str], str, list[dict[str, str]]]:
    reasoning_rows = _product_reasoning(product)
    if style_reference:
        style, basis = _resolve_style(style_reference)
        return style, basis, reasoning_rows
    candidates = [
        item.strip() for item in product.get("recommended_style_ids", "").split(";") if item.strip()
    ]
    style_id = candidates[0] if candidates else "style-minimal"
    style = next(
        (row for row in load_domain("style") if row.get("style_id") == style_id),
        {},
    )
    if not style:
        style = next(
            (row for row in load_domain("style") if row.get("style_id") == "style-minimal"),
            {},
        )
        style_id = "style-minimal"
    return style, "recommended", reasoning_rows


def _product_reasoning(product: dict[str, str]) -> list[dict[str, str]]:
    wanted = [
        item.strip()
        for item in product.get("reasoning_ids", "").split(";")
        if item.strip()
    ]
    rows = {row["reasoning_id"]: row for row in load_domain("reasoning")}
    return [rows[item] for item in wanted if item in rows]


def _select_palette(
    product: dict[str, str], style: dict[str, str]
) -> tuple[dict[str, str], list[str]]:
    product_palette_ids = [
        item.strip()
        for item in product.get("recommended_color_ids", "").split(";")
        if item.strip()
    ]
    palettes = {row["palette_id"]: row for row in load_domain("color")}
    candidates = [palettes[item] for item in product_palette_ids if item in palettes]
    notes: list[str] = []
    if not candidates:
        candidates = list(palettes.values())
        notes.append("产品没有可用的配色引用，已回退到完整配色库排序。")
    style_id = style.get("style_id", "")
    compatible = [
        row for row in candidates if style_id in row.get("style_ids", "").split(";")
    ]
    if compatible:
        return compatible[0], notes
    if style_id:
        notes.append(
            f"推荐配色与风格 {style_id} 没有直接兼容标记；保留产品首选配色，避免伪造新色板。"
        )
    return candidates[0], notes


def _select_typography(
    product: dict[str, str], style: dict[str, str]
) -> tuple[dict[str, str], list[str]]:
    style_id = style.get("style_id", "")
    notes: list[str] = []
    best: dict[str, str] = {}
    best_score = -1.0
    product_tokens = set(tokenize(product.get("name", "") + " " + product.get("summary", "")))
    for row in load_domain("typography"):
        score = 0.0
        if style_id in row.get("style_ids", "").split(";"):
            score += 10.0
        row_tokens = set(tokenize(row.get("best_for", "") + " " + row.get("moods", "")))
        overlap = len(product_tokens & row_tokens)
        score += overlap * 0.15
        if row.get("typography_id") == "type-accessible-large" and any(
            token in product.get("name", "") for token in ("健康", "农业", "校园")
        ):
            score += 1.0
        if score > best_score:
            best_score = score
            best = row
    if not best:
        best = {
            "typography_id": "type-modern-sans",
            "name": "现代系统无衬线",
            "heading_stack": "-apple-system,BlinkMacSystemFont,PingFang SC,Microsoft YaHei,sans-serif",
            "body_stack": "-apple-system,BlinkMacSystemFont,PingFang SC,Microsoft YaHei,sans-serif",
            "numeric_stack": "SF Pro Display,Helvetica,Arial,sans-serif",
            "line_height_rules": "正文 1.6–1.75；标题 1.3–1.5",
            "mini_program_notes": "使用系统字体，避免远程字体闪烁。",
        }
        notes.append("字体库没有可用记录，使用系统无衬线回退。")
    return best, notes


def _layout_map() -> dict[str, dict[str, str]]:
    return {row["layout_id"]: row for row in load_domain("layout")}


def _component_map() -> dict[str, dict[str, str]]:
    return {row["component_id"]: row for row in load_domain("component")}


def _select_layouts(product: dict[str, str]) -> tuple[list[dict[str, str]], list[str]]:
    layout_map = _layout_map()
    ids = [
        item.strip()
        for item in product.get("primary_layout_ids", "").split(";")
        if item.strip()
    ]
    missing: list[str] = []
    layouts = []
    for layout_id in ids:
        if layout_id in layout_map:
            layouts.append(layout_map[layout_id])
        else:
            missing.append(layout_id)
    if not layouts and "layout-home" in layout_map:
        layouts.append(layout_map["layout-home"])
        missing.append("primary_layout_ids 为空，使用 layout-home 回退")
    return layouts[:8], missing


def _select_components(
    product: dict[str, str], layouts: list[dict[str, str]], limit: int = 12
) -> list[dict[str, str]]:
    component_map = _component_map()
    ordered: list[str] = []
    for value in (product.get("typical_component_ids", ""),):
        ordered.extend(item.strip() for item in value.split(";") if item.strip())
    for layout in layouts:
        ordered.extend(
            item.strip()
            for item in layout.get("component_ids", "").split(";")
            if item.strip()
        )
    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for component_id in ordered:
        if component_id in seen:
            continue
        seen.add(component_id)
        row = component_map.get(component_id)
        if row:
            selected.append(row)
        if len(selected) >= limit:
            break
    return selected


def _rows_by_id(domain: str, id_field: str) -> dict[str, dict[str, str]]:
    return {row[id_field]: row for row in load_domain(domain)}


def _search_rule_ids(
    query: str,
    domain: str,
    limit: int,
    product_record: dict[str, str] | None = None,
) -> list[str]:
    result = search_knowledge(
        query,
        domain=domain,
        limit=limit,
        product=product_record.get("product_id") if product_record else None,
    )
    return [item["id"] for item in result["results"]]


def _select_ux_rules(
    product: dict[str, str],
    style: dict[str, str],
    palette: dict[str, str],
    layouts: list[dict[str, str]],
    components: list[dict[str, str]],
    reasoning_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    ux_map = _rows_by_id("ux", "rule_id")
    wanted: list[str] = list(ALWAYS_UX_IDS)
    for row in reasoning_rows:
        wanted.extend(
            item.strip()
            for item in row.get("interaction_priority", "").split(";")
            if item.strip()
        )
    layout_ids = {row["layout_id"] for row in layouts}
    component_ids = {row["component_id"] for row in components}
    if "comp-bottom-action" in component_ids or layout_ids & FIXED_BOTTOM_LAYOUTS:
        wanted.append("ux-bottom-bar")
    if layout_ids & FORM_LAYOUTS:
        wanted.append("ux-form-validation")
        wanted.append("ux-duplicate-submit")
    if "layout-chat" in layout_ids or "comp-input" in component_ids:
        wanted.append("ux-keyboard")
    if layout_ids & LIST_LAYOUTS:
        wanted.append("ux-empty-states")
        wanted.append("ux-long-text")
    if "comp-image-preview" in component_ids:
        wanted.append("ux-image-fallback")
    if palette.get("mode") == "dark":
        wanted.append("ux-dark-theme")
    if style.get("style_id") in {"style-gamified", "style-trend", "style-futuristic", "style-glass"}:
        wanted.append("ux-motion-preference")

    query = " ".join(
        [
            product.get("name", ""),
            product.get("core_tasks", ""),
            style.get("name_zh", ""),
            "反馈 加载 错误 表单 键盘 无障碍",
        ]
    )
    wanted.extend(_search_rule_ids(query, "ux", 8, product))

    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for rule_id in wanted:
        if rule_id in seen or rule_id not in ux_map:
            continue
        seen.add(rule_id)
        selected.append(ux_map[rule_id])
        if len(selected) >= 12:
            break
    return selected


def _select_mini_rules(
    product: dict[str, str],
    layouts: list[dict[str, str]],
    components: list[dict[str, str]],
    palette: dict[str, str],
) -> list[dict[str, str]]:
    rule_map = _rows_by_id("mini-program", "rule_id")
    wanted = list(ALWAYS_MINI_RULE_IDS)
    nav_pattern = product.get("nav_pattern", "")
    layout_ids = {row["layout_id"] for row in layouts}
    component_ids = {row["component_id"] for row in components}
    if "TabBar" in nav_pattern:
        wanted.extend(["mp-tabbar", "mp-tabbar-icon"])
    if layout_ids & FIXED_BOTTOM_LAYOUTS or "comp-bottom-action" in component_ids:
        wanted.append("mp-fixed-bottom")
    if layout_ids & FORM_LAYOUTS or "layout-chat" in layout_ids:
        wanted.append("mp-keyboard")
    if layout_ids & LIST_LAYOUTS:
        wanted.append("mp-scroll")
    if "custom" in nav_pattern.casefold() or "自定义导航" in nav_pattern:
        wanted.append("mp-custom-nav")
    if "comp-share" in component_ids:
        wanted.append("mp-share")
    if palette.get("mode") == "dark":
        wanted.append("mp-dark-mode")

    query = " ".join(
        [
            product.get("name", ""),
            product.get("core_tasks", ""),
            "微信小程序 安全区域 导航 键盘 真机",
        ]
    )
    wanted.extend(_search_rule_ids(query, "mini-program", 6, product))
    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for rule_id in wanted:
        if rule_id in seen or rule_id not in rule_map:
            continue
        seen.add(rule_id)
        selected.append(rule_map[rule_id])
        if len(selected) >= 11:
            break
    return selected


def _select_anti_patterns(
    product: dict[str, str], style: dict[str, str], reasoning_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    anti_map = {
        row["anti_pattern_id"]: row for row in load_domain("anti-pattern")
    }
    wanted: list[str] = []
    for row in reasoning_rows:
        wanted.extend(
            item.strip() for item in row.get("avoid", "").split(";") if item.strip()
        )
    query = " ".join(
        [
            product.get("avoid", ""),
            style.get("avoid_scenarios", ""),
            style.get("common_errors", ""),
            product.get("name", ""),
        ]
    )
    wanted.extend(_search_rule_ids(query, "anti-pattern", 7, product))
    wanted.append("anti-token-mismatch")

    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for anti_id in wanted:
        if anti_id in seen or anti_id not in anti_map:
            continue
        seen.add(anti_id)
        selected.append(anti_map[anti_id])
        if len(selected) >= 10:
            break
    return selected


def _select_stack_rules(
    stack: str,
    product: dict[str, str],
    layouts: list[dict[str, str]],
    components: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows = read_csv(DATA_DIR / STACK_CONFIG[stack]["file"])
    rule_map = {row["rule_id"]: row for row in rows}
    wanted = list(STACK_BASE_RULE_IDS.get(stack, []))
    layout_ids = {row["layout_id"] for row in layouts}
    component_ids = {row["component_id"] for row in components}
    if stack == "wechat-native":
        if "TabBar" in product.get("nav_pattern", ""):
            wanted.append("wx-app-tabbar")
        if layout_ids & FORM_LAYOUTS:
            wanted.append("wx-form-components")
        if "comp-bottom-action" in component_ids:
            wanted.append("wx-fixed-bottom")
        if "layout-chat" in layout_ids:
            wanted.append("wx-keyboard")
        if "comp-share" in component_ids:
            wanted.append("wx-share")
    elif stack == "uni-app":
        if "TabBar" in product.get("nav_pattern", ""):
            wanted.append("uni-tabbar")
        if layout_ids & FORM_LAYOUTS:
            wanted.append("uni-form-picker")
        if "comp-share" in component_ids:
            wanted.append("uni-share")
        if layout_ids & FIXED_BOTTOM_LAYOUTS:
            wanted.append("uni-keyboard")
    elif stack == "taro":
        if "TabBar" in product.get("nav_pattern", ""):
            wanted.append("taro-tabbar")
        if layout_ids & FORM_LAYOUTS:
            wanted.append("taro-form")
        if "comp-share" in component_ids:
            wanted.append("taro-share")
        if layout_ids & FIXED_BOTTOM_LAYOUTS:
            wanted.append("taro-safe-area")

    result = search_stack(
        f"{product.get('name', '')} {product.get('core_tasks', '')}",
        stack,
        limit=6,
    )
    wanted.extend(item["id"] for item in result["results"])

    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for rule_id in wanted:
        if rule_id in seen or rule_id not in rule_map:
            continue
        seen.add(rule_id)
        selected.append(rule_map[rule_id])
        if len(selected) >= 11:
            break
    return selected


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    if len(value) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        raise DesignSystemError(f"无效颜色值：{color!r}")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _relative_luminance(color: str) -> float:
    channels = []
    for channel in _hex_to_rgb(color):
        value = channel / 255.0
        channels.append(
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        )
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: str, second: str) -> float:
    lamp_a = _relative_luminance(first)
    lamp_b = _relative_luminance(second)
    lighter, darker = max(lamp_a, lamp_b), min(lamp_a, lamp_b)
    return (lighter + 0.05) / (darker + 0.05)


def _best_text_on(background: str) -> str:
    dark = "#111111"
    light = "#FFFFFF"
    return dark if contrast_ratio(dark, background) >= contrast_ratio(light, background) else light


def _blend(foreground: str, background: str, alpha: float) -> str:
    fg = _hex_to_rgb(foreground)
    bg = _hex_to_rgb(background)
    mixed = tuple(round(fg[index] * alpha + bg[index] * (1 - alpha)) for index in range(3))
    return "#" + "".join(f"{channel:02X}" for channel in mixed)


def _build_colors(palette: dict[str, str]) -> tuple[dict[str, str], list[dict[str, Any]]]:
    background = palette["background"]
    surface = palette["surface"]
    brand = palette["brand"]
    link = palette["brand"] if contrast_ratio(palette["brand"], background) >= 4.5 else palette["text_primary"]
    colors = {
        "background": background,
        "surface": surface,
        "surface_alt": _blend(brand, background, 0.045),
        "text_primary": palette["text_primary"],
        "text_secondary": palette["text_secondary"],
        "brand": brand,
        "on_brand": _best_text_on(brand),
        "brand_soft": _blend(brand, background, 0.12),
        "accent": palette["accent"],
        "on_accent": _best_text_on(palette["accent"]),
        "border": palette["border"],
        "divider": _blend(palette["border"], background, 0.75),
        "success": palette["success"],
        "warning": palette["warning"],
        "error": palette["error"],
        "on_error": _best_text_on(palette["error"]),
        "link": link,
        "disabled": _blend(palette["text_secondary"], background, 0.38),
        "overlay": "rgba(12, 14, 18, 0.48)",
    }
    checks = []
    for foreground, background_key, label in (
        ("text_primary", "background", "主文字/背景"),
        ("text_primary", "surface", "主文字/表面"),
        ("text_secondary", "background", "次级文字/背景"),
        ("text_secondary", "surface", "次级文字/表面"),
        ("link", "background", "链接/背景"),
        ("on_brand", "brand", "品牌按钮文字/品牌色"),
        ("on_error", "error", "错误按钮文字/错误色"),
    ):
        ratio = contrast_ratio(colors[foreground], colors[background_key])
        checks.append(
            {
                "fg": colors[foreground],
                "bg": colors[background_key],
                "label": label,
                "ratio": round(ratio, 2),
                "threshold": 4.5,
                "passes": ratio >= 4.5,
            }
        )
    return colors, checks


def _shadow(profile_name: str, mode: str) -> str:
    template = SHADOW_TEMPLATES.get(profile_name, SHADOW_TEMPLATES["subtle"])
    if template == "none":
        return "none"
    if mode == "dark":
        if profile_name == "emboss":
            return "8rpx 8rpx 20rpx rgba(0, 0, 0, 0.38), -8rpx -8rpx 20rpx rgba(255, 255, 255, 0.03)"
        return template.replace("rgba(20, 20, 20, 0.06)", "rgba(0, 0, 0, 0.34)").replace(
            "rgba(20, 20, 20, 0.08)", "rgba(0, 0, 0, 0.40)"
        ).replace("rgba(20, 20, 20, 0.18)", "rgba(0, 0, 0, 0.45)").replace(
            "rgba(10, 15, 25, 0.18)", "rgba(0, 0, 0, 0.45)"
        )
    return template


def _build_tokens(
    product: dict[str, str],
    style: dict[str, str],
    palette: dict[str, str],
    colors: dict[str, str],
    typography: dict[str, str],
) -> dict[str, Any]:
    style_id = style.get("style_id", "")
    profile = STYLE_TOKEN_PROFILES.get(style_id, DEFAULT_STYLE_PROFILE)
    density = DENSITY_PROFILES[_density_bucket(product.get("information_density", ""))]
    scale = list(profile["scale"])
    if typography.get("typography_id") == "type-accessible-large":
        scale = [max(value, minimum) for value, minimum in zip(scale, [24, 28, 32, 36, 44, 52])]
    elif "data-dense" in style_id:
        scale = [22, 24, 28, 32, 38, 46]
        scale[2] = max(scale[2], 28)
    scale = [max(28, scale[2]) if index == 2 else value for index, value in enumerate(scale)]
    scale[0] = max(scale[0], 24)
    scale[1] = max(scale[1], 26)

    radius_names = ["sm", "md", "lg", "pill"]
    radii = {
        f"radius_{name}": f"{value}rpx" if value < 900 else "999rpx"
        for name, value in zip(radius_names, profile["radius"])
    }
    motion = MOTION_PROFILES[profile["motion"]]
    spacing_names = ["1", "2", "3", "4", "5", "6", "7"]
    spacing = {
        f"space_{name}": f"{value}rpx"
        for name, value in zip(spacing_names, density["scale"])
    }
    return {
        "colors": colors,
        "typography": {
            "font_family_heading": typography.get("heading_stack", ""),
            "font_family_body": typography.get("body_stack", ""),
            "font_family_numeric": typography.get("numeric_stack", ""),
            "font_weight_regular": 400,
            "font_weight_medium": 500,
            "font_weight_semibold": 600,
            "font_weight_bold": 700,
            "scale": {
                "caption": f"{scale[0]}rpx",
                "meta": f"{scale[1]}rpx",
                "body": f"{scale[2]}rpx",
                "body_lg": f"{scale[3]}rpx",
                "title": f"{scale[4]}rpx",
                "display": f"{scale[5]}rpx",
            },
            "line_height": {
                "body": profile["line_height"],
                "title": round(max(1.25, profile["line_height"] - 0.35), 2),
                "numeric": 1.15,
            },
            "line_height_note": typography.get("line_height_rules", ""),
            "mini_program_note": typography.get("mini_program_notes", ""),
        },
        "spacing": {
            "scale": spacing,
            "page_gutter": f"{density['page_gutter']}rpx",
            "section_gap": f"{density['section_gap']}rpx",
            "card_gap": f"{density['card_gap']}rpx",
            "density": density["label"],
            "content_max_width": "1120rpx",
        },
        "radius": radii,
        "shadows": {
            "none": "none",
            "card": _shadow(profile["shadow"], palette.get("mode", "light")),
            "raised": _shadow(
                "layer" if profile["shadow"] in {"none", "subtle"} else profile["shadow"],
                palette.get("mode", "light"),
            ),
        },
        "motion": {
            "fast": f"{motion['fast']}ms",
            "normal": f"{motion['normal']}ms",
            "slow": f"{motion['slow']}ms",
            "easing": "cubic-bezier(0.2, 0.8, 0.2, 1)",
            "policy": "动效只表达状态和空间关系；避免无限循环动画；低端设备与系统减少动效时降级。",
        },
        "sizes": {
            "touch_target": "88rpx",
            "button_height": "88rpx",
            "input_height": "88rpx",
            "list_row_min_height": "104rpx" if density["label"] != "高" else "96rpx",
            "icon": "40rpx",
            "tabbar_height": "100rpx" if density["label"] != "高" else "96rpx",
            "navigation_content_height": "88rpx",
        },
        "safe_area": {
            "bottom_css": "env(safe-area-inset-bottom)",
            "bottom_padding_formula": "calc(24rpx + env(safe-area-inset-bottom))",
            "note": "固定底栏必须为内容设置等高占位；具体支持需在目标基础库和真机验证。",
        },
        "provenance": {
            "colors": palette.get("palette_id", ""),
            "style_profile": style_id,
            "density": _density_bucket(product.get("information_density", "")),
            "typography": typography.get("typography_id", ""),
            "note": "颜色、字号和布局引用知识库；圆角、阴影、动效与控件尺寸由版本化的设计引擎规则派生。",
        },
    }


def _build_conflicts(
    product: dict[str, str],
    style: dict[str, str],
    palette: dict[str, str],
    palette_notes: list[str],
    contrast_checks: list[dict[str, Any]],
    explicit_style: bool,
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    recommended_styles = {
        item.strip() for item in product.get("recommended_style_ids", "").split(";") if item.strip()
    }
    style_id = style.get("style_id", "")
    if explicit_style and style_id not in recommended_styles:
        conflicts.append(
            {
                "id": "conflict-style-vs-product",
                "severity": "P3",
                "title": "指定风格不是该产品的首选推荐",
                "detail": f"产品首选风格为 {', '.join(sorted(recommended_styles))}，当前使用 {style_id}。",
                "resolution": "尊重用户明确指定的风格；在实现后重点验证信息层级和可读性。",
                "source_ids": [product.get("product_id", ""), style_id],
            }
        )
    product_density = _density_bucket(product.get("information_density", ""))
    style_density = _density_bucket(style.get("content_density", ""))
    if product_density in {"high", "medium_high"} and style_density == "low":
        conflicts.append(
            {
                "id": "conflict-density",
                "severity": "P2",
                "title": "产品信息密度高于风格建议",
                "detail": f"产品密度为“{DENSITY_PROFILES[product_density]['label']}”，风格建议内容密度为“{style.get('content_density', '')}”。",
                "resolution": "保留风格语气，但优先压缩间距、使用分组和列表，避免为了留白牺牲关键信息。",
                "source_ids": [product.get("product_id", ""), style_id],
            }
        )
    if product_density == "low" and style_id in {"style-data-dense", "style-brutalist"}:
        conflicts.append(
            {
                "id": "conflict-density-high",
                "severity": "P2",
                "title": "风格本身信息密度偏高",
                "detail": f"产品密度为“{DENSITY_PROFILES[product_density]['label']}”，风格为高密度表达。",
                "resolution": "减少页面模块数量，仅在高频数据区使用高密度；其余区域恢复留白。",
                "source_ids": [product.get("product_id", ""), style_id],
            }
        )
    if style_id in {"style-neomorphic", "style-glass"} and product_density in {"high", "medium_high"}:
        conflicts.append(
            {
                "id": "conflict-performance",
                "severity": "P2",
                "title": "高成本视觉效果与高信息密度冲突",
                "detail": f"{style_id} 的模糊/双向阴影在低端设备上可能影响滚动和数据辨认。",
                "resolution": "只将效果用于局部容器；提供无模糊/无阴影回退；先验证低端 Android。",
                "source_ids": [style_id, product.get("product_id", "")],
            }
        )
    avoided = style.get("avoid_scenarios", "")
    product_identity = product.get("name", "") + " " + product.get("aliases", "")
    common_tokens = {
        token
        for token in set(tokenize(avoided)) & set(tokenize(product_identity))
        if len(token) >= 2 and token not in {"页面", "内容", "场景", "用户", "设计", "产品"}
    }
    if common_tokens:
        conflicts.append(
            {
                "id": "conflict-style-avoid",
                "severity": "P2",
                "title": "风格数据明确提示不适合该场景",
                "detail": "风格避免场景与产品关键词重叠：" + "、".join(sorted(common_tokens)[:5]),
                "resolution": "重新评估风格；如坚持使用，必须通过页面级验证并记录例外理由。",
                "source_ids": [style_id, product.get("product_id", "")],
            }
        )
    for check in contrast_checks:
        if not check["passes"]:
            conflicts.append(
                {
                    "id": "conflict-contrast",
                    "severity": "P1",
                    "title": "颜色对比不足",
                    "detail": f"{check['label']} 对比度为 {check['ratio']}:1，低于 4.5:1。",
                    "resolution": "调整 token 或使用更深的文字/更浅的表面；不要靠提高字重掩盖对比不足。",
                    "source_ids": [palette.get("palette_id", "")],
                }
            )
    for note in palette_notes:
        if "没有直接兼容" in note:
            conflicts.append(
                {
                    "id": "conflict-palette-style",
                    "severity": "P3",
                    "title": "配色与指定风格缺少兼容标记",
                    "detail": note,
                    "resolution": "保留已有产品配色并在实现后验证；不要凭空编造新色板。",
                    "source_ids": [palette.get("palette_id", ""), style_id],
                }
            )
    return conflicts


def _select_default_pages(layouts: list[dict[str, str]]) -> list[dict[str, str]]:
    if not layouts:
        return []
    selected: list[dict[str, str]] = []
    home = next((row for row in layouts if row["layout_id"] == "layout-home"), layouts[0])
    selected.append(home)
    detail_preferences = ("详情", "播放器", "聊天", "看板", "视频流", "表单")
    detail = next(
        (
            row
            for row in layouts
            if row is not home
            and any(keyword in row.get("page_type", "") for keyword in detail_preferences)
        ),
        None,
    )
    if detail is None:
        detail = next((row for row in layouts if row is not home), None)
    if detail is not None:
        selected.append(detail)
    profile = next((row for row in layouts if row["layout_id"] == "layout-profile"), None)
    if profile is not None and profile not in selected:
        selected.append(profile)
    for row in layouts:
        if len(selected) >= 3:
            break
        if row not in selected:
            selected.append(row)
    return selected[:3]


def _resolve_page_references(
    references: list[str] | None, layouts: list[dict[str, str]]
) -> list[dict[str, str]]:
    if not references:
        return _select_default_pages(layouts)
    if len(references) == 1 and references[0].strip().casefold() == "all":
        return layouts
    lookup: dict[str, dict[str, str]] = {}
    for row in load_domain("layout"):
        for key in (
            row.get("layout_id", ""),
            row.get("layout_id", "").removeprefix("layout-"),
            row.get("page_type", ""),
        ):
            if key:
                lookup[_normalise_key(key)] = row
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for reference in references:
        row = lookup.get(_normalise_key(reference))
        if row is None:
            result = search_knowledge(reference, domain="layout", limit=1)
            if result["results"]:
                row = result["results"][0]["record"]
        if row is None:
            raise DesignSystemError(f"无法识别页面“{reference}”；可传 layout ID 或页面类型。")
        if row["layout_id"] not in seen:
            seen.add(row["layout_id"])
            selected.append(row)
    return selected


def _flatten_record(row: dict[str, str], fields: list[str]) -> dict[str, str]:
    return {field: row.get(field, "") for field in fields}


def _build_sources(
    product: dict[str, str],
    style: dict[str, str],
    palette: dict[str, str],
    typography: dict[str, str],
    layouts: list[dict[str, str]],
    components: list[dict[str, str]],
    ux_rules: list[dict[str, str]],
    mini_rules: list[dict[str, str]],
    anti_patterns: list[dict[str, str]],
    stack_rules: list[dict[str, str]],
    reasoning_rows: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "product": [product.get("product_id", "")],
        "style": [style.get("style_id", "")],
        "palette": [palette.get("palette_id", "")],
        "typography": [typography.get("typography_id", "")],
        "layouts": [row["layout_id"] for row in layouts],
        "components": [row["component_id"] for row in components],
        "ux_rules": [row["rule_id"] for row in ux_rules],
        "mini_program_rules": [row["rule_id"] for row in mini_rules],
        "anti_patterns": [row["anti_pattern_id"] for row in anti_patterns],
        "stack_rules": [row["rule_id"] for row in stack_rules],
        "reasoning": [row["reasoning_id"] for row in reasoning_rows],
    }


def _build_design_system(
    product: dict[str, str],
    style: dict[str, str],
    palette: dict[str, str],
    typography: dict[str, str],
    stack: str,
    project_name: str,
    page_layouts: list[dict[str, str]],
    style_basis: str,
    product_match: str,
    product_confidence: float,
    layouts: list[dict[str, str]],
    components: list[dict[str, str]],
    ux_rules: list[dict[str, str]],
    mini_rules: list[dict[str, str]],
    anti_patterns: list[dict[str, str]],
    stack_rules: list[dict[str, str]],
    reasoning_rows: list[dict[str, str]],
    palette_notes: list[str],
) -> dict[str, Any]:
    colors, contrast_checks = _build_colors(palette)
    tokens = _build_tokens(product, style, palette, colors, typography)
    conflicts = _build_conflicts(
        product,
        style,
        palette,
        palette_notes,
        contrast_checks,
        explicit_style=style_basis.startswith("explicit"),
    )
    sources = _build_sources(
        product,
        style,
        palette,
        typography,
        layouts,
        components,
        ux_rules,
        mini_rules,
        anti_patterns,
        stack_rules,
        reasoning_rows,
    )
    why_style = (
        "由产品类型的推荐风格与设计推理规则推导。"
        if style_basis == "recommended"
        else "由用户在生成命令中指定，系统保留该方向并检查冲突。"
    )
    rationale = [
        {
            "step": "产品类型",
            "choice": f"{product.get('name', '')} ({product.get('product_id', '')})",
            "reason": product.get("design_reasoning", "") or product.get("summary", ""),
            "sources": [product.get("product_id", "")],
        },
        {
            "step": "设计风格",
            "choice": f"{style.get('name_zh', '')} ({style.get('style_id', '')})",
            "reason": why_style + " " + style.get("visual_traits", ""),
            "sources": [style.get("style_id", "")],
        },
        {
            "step": "配色",
            "choice": f"{palette.get('name', '')} ({palette.get('palette_id', '')})",
            "reason": palette.get("usage", "") + " " + palette.get("contrast_notes", ""),
            "sources": [palette.get("palette_id", "")],
        },
        {
            "step": "排版",
            "choice": f"{typography.get('name', '')} ({typography.get('typography_id', '')})",
            "reason": typography.get("scale_rationale", "")
            + " "
            + typography.get("mini_program_notes", ""),
            "sources": [typography.get("typography_id", "")],
        },
        {
            "step": "页面结构",
            "choice": "、".join(row["page_type"] for row in layouts),
            "reason": "按产品核心任务排序，页面级覆盖默认继承 Master。",
            "sources": [row["layout_id"] for row in layouts],
        },
        {
            "step": "技术栈",
            "choice": f"{STACK_CONFIG[stack]['label']} ({stack})",
            "reason": "加载对应框架规则并区分静态审查、开发者工具与真机验证。",
            "sources": [row["rule_id"] for row in stack_rules],
        },
    ]
    for row in reasoning_rows:
        rationale.append(
            {
                "step": "产品推理",
                "choice": row.get("scenario", ""),
                "reason": row.get("explanation", ""),
                "sources": [row.get("reasoning_id", "")],
            }
        )

    acceptance = [
        "首屏主任务清晰可见，且只保留一个主操作或主信息焦点。",
        f"核心任务路径覆盖：{product.get('core_tasks', '')}",
        f"所有可点击热区不小于 {tokens['sizes']['touch_target']}，相邻操作保持足够间距。",
        "固定底部操作栏包含安全区处理，并为页面内容设置等高占位。",
        "列表、表单、支付或长任务包含加载、空、错误与恢复状态，不以静态稿替代。",
        "正文与背景、次级文字与背景的对比度不低于 4.5:1（以自动化检查结果为准）。",
        "页面级规范只覆盖必要规则，不引入 Master 之外的新配色、字体或圆角语言。",
        "设计 token 与组件样式一致，不允许新增未登记颜色或魔法间距。",
        "静态检查、微信开发者工具和至少一台 iOS/一台 Android 真机的执行状态分别记录。",
        "未执行的真机、键盘、安全区、分享与性能检查不得标记为通过。",
    ]
    limitations = [
        "本设计系统由本地知识库和可解释规则生成，不包含运行截图、视觉模型判断或真机结果。",
        "CSS 自定义属性、安全区、原生组件和渲染引擎能力必须在目标基础库与真机验证。",
        "平台规则带有核验状态；标记为“需按目标基础库验证”的规则不能当作已验证事实。",
        "设计系统生成不等于页面实现；可选 DevTools 模拟器验收需要用户开启服务端口，且模拟器不等于真机。",
        "设计系统不能替代对现有业务逻辑、权限和数据安全的审查。",
    ]
    token_implementation = _token_implementation(stack, tokens)
    generated_at = _now_iso()
    return {
        "schema_version": "1.0.0",
        "generator": {"name": "mini-program-ux-pro", "version": VERSION},
        "generated_at": generated_at,
        "project": {
            "name": project_name,
            "slug": _slugify(project_name, product.get("product_id", "mini-program")),
        },
        "stack": {
            "id": stack,
            "label": STACK_CONFIG[stack]["label"],
            "verification_limit": "框架差异与平台能力需按项目依赖、基础库和真机复核。",
        },
        "product": {
            "id": product.get("product_id", ""),
            "name": product.get("name", ""),
            "match": product_match,
            "confidence": product_confidence,
            "summary": product.get("summary", ""),
            "target_users": product.get("target_users", ""),
            "scenarios": product.get("scenarios", ""),
            "core_tasks": product.get("core_tasks", ""),
            "home_structure": product.get("home_structure", ""),
            "nav_pattern": product.get("nav_pattern", ""),
            "information_density": product.get("information_density", ""),
            "avoid": product.get("avoid", ""),
            "reasoning_ids": product.get("reasoning_ids", "").split(";"),
        },
        "style": {
            "id": style.get("style_id", ""),
            "name": style.get("name_zh", ""),
            "name_en": style.get("name_en", ""),
            "selection": style_basis,
            "why": why_style,
            "keywords": style.get("keywords", ""),
            "visual_traits": style.get("visual_traits", ""),
            "typography_rules": style.get("typography_rules", ""),
            "component_traits": style.get("component_traits", ""),
            "motion_strategy": style.get("motion_strategy", ""),
            "avoid_scenarios": style.get("avoid_scenarios", ""),
            "common_errors": style.get("common_errors", ""),
            "combination_notes": style.get("combination_notes", ""),
        },
        "palette": {
            "id": palette.get("palette_id", ""),
            "name": palette.get("name", ""),
            "mode": palette.get("mode", ""),
            "usage": palette.get("usage", ""),
            "contrast_notes": palette.get("contrast_notes", ""),
            "colors": colors,
            "contrast_checks": contrast_checks,
        },
        "typography": {
            "id": typography.get("typography_id", ""),
            "name": typography.get("name", ""),
            "heading_stack": typography.get("heading_stack", ""),
            "body_stack": typography.get("body_stack", ""),
            "numeric_stack": typography.get("numeric_stack", ""),
            "scale_rationale": typography.get("scale_rationale", ""),
            "line_height_rules": typography.get("line_height_rules", ""),
            "mini_program_notes": typography.get("mini_program_notes", ""),
        },
        "tokens": tokens,
        "token_implementation": token_implementation,
        "layouts": [
            {
                "id": row["layout_id"],
                "page_type": row["page_type"],
                "goal": row["goal"],
                "hierarchy": row["hierarchy"],
                "primary_regions": row["primary_regions"],
                "secondary_regions": row["secondary_regions"],
                "navigation": row["navigation"],
                "components": row["component_ids"].split(";"),
                "action_order": row["action_order"],
                "information_density": row["information_density"],
                "mobile_notes": row["mobile_notes"],
                "common_errors": row["common_errors"],
                "override_file": f"pages/{row['layout_id'].removeprefix('layout-')}.md",
            }
            for row in layouts
        ],
        "pages": [
            {
                "layout_id": row["layout_id"],
                "page_type": row["page_type"],
                "file": f"pages/{row['layout_id'].removeprefix('layout-')}.md",
            }
            for row in page_layouts
        ],
        "components": [
            {
                "id": row["component_id"],
                "name": row["name"],
                "use_cases": row["use_cases"],
                "visual_rules": row["visual_rules"],
                "interaction_rules": row["interaction_rules"],
                "touch_target": row["touch_target"],
                "states": row["states"],
                "accessibility": row["accessibility"],
                "native_implementation": row["native_implementation"],
                "common_errors": row["common_errors"],
            }
            for row in components
        ],
        "ux_rules": [
            {
                "id": row["rule_id"],
                "severity": row["severity"],
                "category": row["category"],
                "name": row["name"],
                "recommendation": row["recommendation"],
                "how_to_check": row["how_to_check"],
                "fix": row["fix"],
            }
            for row in ux_rules
        ],
        "mini_program_rules": [
            {
                "id": row["rule_id"],
                "severity": row["severity"],
                "category": row["category"],
                "name": row["name"],
                "recommendation": row["recommendation"],
                "implementation": row["implementation"],
                "how_to_verify": row["how_to_verify"],
                "verification_status": row["verification_status"],
                "source_url": row["source_url"],
            }
            for row in mini_rules
        ],
        "anti_patterns": [
            {
                "id": row["anti_pattern_id"],
                "severity": row["severity"],
                "name": row["name"],
                "manifestation": row["manifestation"],
                "detection": row["detection"],
                "fix": row["fix"],
            }
            for row in anti_patterns
        ],
        "stack_rules": [
            {
                "id": row["rule_id"],
                "severity": row["severity"],
                "guideline": row["guideline"],
                "do": row["do"],
                "don_t": row["don_t"],
                "verification_status": row["verification_status"],
                "source_url": row["source_url"],
            }
            for row in stack_rules
        ],
        "conflicts": conflicts,
        "design_rationale": rationale,
        "acceptance_criteria": acceptance,
        "sources": sources,
        "limitations": limitations,
    }


def _token_implementation(stack: str, tokens: dict[str, Any]) -> dict[str, Any]:
    if stack == "wechat-native":
        return {
            "file": "tokens.wxss",
            "language": "wxss",
            "note": "WXSS 自定义属性支持取决于目标基础库；若旧版本不支持，使用 MASTER.json 中的字面值或编译期样式，不要假设所有小程序环境都有 CSS 变量。",
            "primary": "为组件提供字面值 token；tokens.wxss 仅作为可验证的变量层。",
        }
    return {
        "file": "tokens.scss",
        "language": "scss",
        "note": "SCSS 变量在构建时可用；运行期 CSS 变量仍受微信基础库与渲染引擎限制，需按项目编译配置验证。",
        "primary": "优先消耗 SCSS 变量，必要时再输出 CSS 自定义属性。",
    }


def _css_tokens(stack: str, tokens: dict[str, Any]) -> str:
    lines = [
        "/* MPUX Pro design tokens - generated from local knowledge base. */",
        "/* Do not treat CSS custom properties as universally supported; verify the target base library. */",
        "",
    ]
    colors = tokens["colors"]
    typography = tokens["typography"]
    spacing = tokens["spacing"]
    radius = tokens["radius"]
    shadows = tokens["shadows"]
    motion = tokens["motion"]
    sizes = tokens["sizes"]
    safe_area = tokens["safe_area"]
    variable_lines: list[tuple[str, str]] = []
    for name, value in colors.items():
        variable_lines.append((f"--mpux-color-{name.replace('_', '-')}", value))
    for name, value in typography["scale"].items():
        variable_lines.append((f"--mpux-font-{name.replace('_', '-')}", value))
    variable_lines.extend(
        [
            ("--mpux-font-family-heading", typography["font_family_heading"]),
            ("--mpux-font-family-body", typography["font_family_body"]),
            ("--mpux-font-family-numeric", typography["font_family_numeric"]),
        ]
    )
    for name, value in spacing["scale"].items():
        display_name = name.removeprefix("space_")
        variable_lines.append((f"--mpux-space-{display_name}", value))
    variable_lines.extend(
        [
            ("--mpux-space-page-gutter", spacing["page_gutter"]),
            ("--mpux-space-section-gap", spacing["section_gap"]),
            ("--mpux-space-card-gap", spacing["card_gap"]),
            ("--mpux-space-content-max-width", spacing["content_max_width"]),
        ]
    )
    for name, value in radius.items():
        variable_lines.append((f"--mpux-{name.replace('_', '-')}", value))
    variable_lines.extend(
        [
            ("--mpux-shadow-card", shadows["card"]),
            ("--mpux-shadow-raised", shadows["raised"]),
            ("--mpux-motion-fast", motion["fast"]),
            ("--mpux-motion-normal", motion["normal"]),
            ("--mpux-motion-slow", motion["slow"]),
            ("--mpux-easing-standard", motion["easing"]),
            ("--mpux-touch-target", sizes["touch_target"]),
            ("--mpux-button-height", sizes["button_height"]),
            ("--mpux-input-height", sizes["input_height"]),
            ("--mpux-tabbar-height", sizes["tabbar_height"]),
            ("--mpux-nav-content-height", sizes["navigation_content_height"]),
            ("--mpux-safe-bottom", safe_area["bottom_css"]),
        ]
    )
    if stack == "wechat-native":
        lines.append("page {")
        for name, value in variable_lines:
            lines.append(f"  {name}: {value};")
        lines.extend(
            [
                "}",
                "",
                "/* Content wrapper example: */",
                "/* .mpux-page { padding-bottom: calc(var(--mpux-bottom-bar-height, 112rpx) + env(safe-area-inset-bottom)); } */",
                "",
            ]
        )
    else:
        lines.append("// Build-time SCSS variables (recommended primary path).")
        for name, value in variable_lines:
            scss_name = name.removeprefix("--mpux-")
            lines.append(f"$mpux-{scss_name}: {value};")
        lines.extend(
            [
                "",
                "// Runtime CSS variables: verify the compiled target supports them.",
                "page {",
            ]
        )
        for name, value in variable_lines:
            lines.append(f"  {name}: {value};")
        lines.extend(["}", ""])
    return "\n".join(lines)


def _md_cell(value: Any, limit: int | None = None) -> str:
    text = str(value or "").replace("|", "\\|").replace("\n", " ")
    if limit and len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


def _markdown(ds: dict[str, Any]) -> str:
    product = ds["product"]
    style = ds["style"]
    palette = ds["palette"]
    typography = ds["typography"]
    tokens = ds["tokens"]
    project = ds["project"]
    lines: list[str] = []
    add = lines.append

    add(f"# {project['name']} · 小程序设计系统")
    add("")
    add("> 本文件是项目级唯一设计事实源（Master）。页面规范默认继承本文件。")
    add(f"> 设计系统版本：1.0.0 · 生成器：MPUX Pro {ds['generator']['version']} · 生成时间：{ds['generated_at']} · 技术栈：{ds['stack']['label']}")
    add("> 数据引用与未执行检查见第 16 节。任何未在真机执行的结论都不得标记为已验证。")
    add("")
    add("## 使用约束")
    add("")
    add("1. 先读本文件，再读 `pages/<page>.md`；页面覆盖只允许修改页面级顺序、局部间距与状态，不得另起配色或字体系统。")
    add("2. Token 以第 8 节和 `MASTER.json` 为准；组件不得硬编码未登记的颜色、圆角或间距。")
    add("3. 本节由静态知识库生成，不代表已完成视觉、键盘、安全区或真机验证。")
    add("")
    add("## 1. 产品定位")
    add("")
    add(f"- **项目名称**：{project['name']}")
    add(f"- **产品类型**：{product['name']} (`{product['id']}`)")
    match_label = {"exact": "精确匹配", "search": "检索匹配"}.get(product["match"], product["match"])
    add(f"- **匹配方式**：{match_label}；置信度：{product['confidence']}")
    add(f"- **产品摘要**：{product['summary']}")
    add(f"- **信息密度**：{product['information_density']}")
    add(f"- **首页结构**：{product['home_structure']}")
    add(f"- **导航模式**：{product['nav_pattern']}")
    add("")
    add("## 2. 目标用户与场景")
    add("")
    add(f"- **目标用户**：{product['target_users']}")
    add(f"- **主要场景**：{product['scenarios']}")
    add("")
    add("## 3. 核心任务与成功标准")
    add("")
    add(f"- **核心任务**：{product['core_tasks']}")
    add("- **成功的界面**：用户能识别当前状态、完成下一动作，并在错误或中断后恢复；不是“所有卡片看起来一致”。")
    add("")
    add("## 4. 设计风格")
    add("")
    add(f"### {style['name']} / {style['name_en']}")
    add("")
    add(f"- **风格 ID**：`{style['id']}`")
    selection_label = {
        "recommended": "产品推荐",
        "explicit": "用户指定",
        "explicit-search": "用户指定（风格检索命中）",
    }.get(style["selection"], style["selection"])
    add(f"- **选择方式**：{selection_label}")
    add(f"- **关键词**：{style['keywords']}")
    add(f"- **视觉特点**：{style['visual_traits']}")
    add(f"- **排版规则**：{style['typography_rules']}")
    add(f"- **组件语言**：{style['component_traits']}")
    add(f"- **动效策略**：{style['motion_strategy']}")
    add(f"- **不适合场景**：{style['avoid_scenarios']}")
    add(f"- **组合注意**：{style['combination_notes']}")
    add("")
    add("## 5. 设计选择理由与冲突")
    add("")
    for item in ds["design_rationale"]:
        add(f"### {item['step']}：{item['choice']}")
        add("")
        add(item["reason"])
        add("")
        add(f"数据来源：{'、'.join(f'`{source}`' for source in item['sources'])}")
        add("")
    if ds["conflicts"]:
        add("### 冲突检查")
        add("")
        for conflict in ds["conflicts"]:
            add(f"- **[{conflict['severity']}] {conflict['title']}**：{conflict['detail']} 处理：{conflict['resolution']}")
        add("")
    else:
        add("未发现数据层面需阻断的冲突。仍需在实现后进行视觉、交互和真机检查。")
        add("")
    add("## 6. 配色系统")
    add("")
    add(f"配色方案：**{palette['name']}** (`{palette['id']}`) · 模式：{palette['mode']}")
    add("")
    add(palette["usage"])
    add("")
    add("| Token | 值 | 用途 |")
    add("| --- | --- | --- |")
    roles = {
        "background": "页面背景",
        "surface": "卡片/表面",
        "surface_alt": "弱分区表面",
        "text_primary": "主文字",
        "text_secondary": "次级文字",
        "brand": "品牌主色/主操作",
        "on_brand": "品牌色上的文字",
        "brand_soft": "品牌弱底",
        "accent": "辅助强调",
        "on_accent": "辅助色上的文字",
        "border": "边框",
        "divider": "分隔线",
        "success": "成功",
        "warning": "警告",
        "error": "错误",
        "on_error": "错误色上的文字",
        "link": "链接",
        "disabled": "禁用",
        "overlay": "遮罩",
    }
    for key, value in tokens["colors"].items():
        add(f"| `{key}` | `{value}` | {roles.get(key, '')} |")
    add("")
    add("### 对比度检查")
    add("")
    add("| 组合 | 对比度 | 阈值 | 结果 |")
    add("| --- | ---: | ---: | --- |")
    for check in palette["contrast_checks"]:
        result = "通过" if check["passes"] else "未通过"
        add(f"| {check['label']} | {check['ratio']}:1 | {check['threshold']}:1 | {result} |")
    add("")
    add(f"{palette['contrast_notes']}")
    add("")
    add("## 7. 字体与排版")
    add("")
    add(f"字体方案：**{typography['name']}** (`{typography['id']}`)")
    add("")
    add(f"- **标题字体**：`{typography['heading_stack']}`")
    add(f"- **正文字体**：`{typography['body_stack']}`")
    add(f"- **数字字体**：`{typography['numeric_stack']}`")
    add(f"- **比例依据**：{typography['scale_rationale']}")
    add(f"- **行高规则**：{typography['line_height_rules']}")
    add(f"- **小程序注意**：{typography['mini_program_notes']}")
    add("")
    add("| 层级 | 字号 | 行高 |")
    add("| --- | ---: | ---: |")
    for name in ("caption", "meta", "body", "body_lg", "title", "display"):
        if name in {"body", "body_lg"}:
            line_height = tokens["typography"]["line_height"]["body"]
        elif name in {"title", "display"}:
            line_height = tokens["typography"]["line_height"]["title"]
        else:
            line_height = 1.4
        add(f"| `{name}` | {tokens['typography']['scale'][name]} | {line_height} |")
    add("")
    add("## 8. 间距、圆角、阴影、动效与尺寸")
    add("")
    add(f"密度：**{tokens['spacing']['density']}** · 页面边距：{tokens['spacing']['page_gutter']} · 区块间距：{tokens['spacing']['section_gap']} · 卡片间距：{tokens['spacing']['card_gap']}")
    add("")
    add("| Token | 值 |")
    add("| --- | --- |")
    for name, value in tokens["spacing"]["scale"].items():
        display_name = name.removeprefix("space_")
        add(f"| `space-{display_name}` | {value} |")
    for name, value in tokens["radius"].items():
        add(f"| `{name}` | {value} |")
    add(f"| `shadow-card` | {tokens['shadows']['card']} |")
    add(f"| `shadow-raised` | {tokens['shadows']['raised']} |")
    add(f"| `motion-fast` | {tokens['motion']['fast']} |")
    add(f"| `motion-normal` | {tokens['motion']['normal']} |")
    add(f"| `motion-slow` | {tokens['motion']['slow']} |")
    add(f"| `touch-target` | {tokens['sizes']['touch_target']} |")
    add(f"| `button-height` | {tokens['sizes']['button_height']} |")
    add(f"| `input-height` | {tokens['sizes']['input_height']} |")
    add(f"| `tabbar-height` | {tokens['sizes']['tabbar_height']} |")
    add("")
    add(f"动效策略：{tokens['motion']['policy']}")
    add("")
    add(f"安全区域：`{tokens['safe_area']['bottom_padding_formula']}`。{tokens['safe_area']['note']}")
    add("")
    add("### 技术栈 Token 落地")
    add("")
    add(f"- 文件：`{ds['token_implementation']['file']}`")
    add(f"- 说明：{ds['token_implementation']['note']}")
    add(f"- 主路径：{ds['token_implementation']['primary']}")
    add("")
    add("```" + ds["token_implementation"]["language"])
    add(_css_tokens(ds["stack"]["id"], tokens).rstrip())
    add("```")
    add("")
    add("## 9. 页面布局")
    add("")
    add("默认页面覆盖文件：" + "、".join(f"`{page['file']}`" for page in ds["pages"]) if ds["pages"] else "未生成页面覆盖。")
    add("")
    add("| 页面 | 目标 | 主要内容 | 主操作顺序 |")
    add("| --- | --- | --- | --- |")
    for layout in ds["layouts"]:
        add(
            f"| {layout['page_type']} (`{layout['id']}`) | {_md_cell(layout['goal'], 90)} | {_md_cell(layout['primary_regions'], 100)} | {_md_cell(layout['action_order'], 100)} |"
        )
    add("")
    add("页面级覆盖默认继承本文件。不得为每个页面建立独立配色或字体；如页面任务确实需要例外，在页面文件记录理由。")
    add("")
    add("## 10. 组件规范")
    add("")
    add("| 组件 | 使用场景 | 触摸/状态 | 常见错误 |")
    add("| --- | --- | --- | --- |")
    for component in ds["components"]:
        add(
            f"| {component['name']} (`{component['id']}`) | {_md_cell(component['use_cases'], 80)} | {_md_cell(component['touch_target'], 70)}；{_md_cell(component['states'], 70)} | {_md_cell(component['common_errors'], 90)} |"
        )
    add("")
    add("### 关键实现边界")
    add("")
    for component in ds["components"][:6]:
        add(f"- **{component['name']}**：{component['interaction_rules']}")
        add(f"  - 无障碍：{component['accessibility']}")
        add(f"  - 原生实现：{component['native_implementation']}")
    add("")
    add("## 11. 交互与反馈规范")
    add("")
    add("| 优先级 | 规则 | 检查方法 | 修复方向 |")
    add("| --- | --- | --- | --- |")
    for rule in ds["ux_rules"]:
        add(
            f"| {rule['severity']} | {rule['name']} | {_md_cell(rule['how_to_check'], 110)} | {_md_cell(rule['fix'], 100)} |"
        )
    add("")
    add("## 12. 微信平台注意事项")
    add("")
    add("> 下列规则的核验状态来自知识库。标记为需验证的项目在真实基础库/真机上通过前，不能算已完成。")
    add("")
    add("| 严重度 | 规则 | 推荐做法 | 核验状态 |")
    add("| --- | --- | --- | --- |")
    for rule in ds["mini_program_rules"]:
        add(
            f"| {rule['severity']} | {rule['name']} | {_md_cell(rule['recommendation'], 100)} | {rule['verification_status']} |"
        )
    add("")
    add("### 本轮明确未执行的验证")
    add("")
    add("- 未运行页面截图或视觉模型评审。")
    add("- 未导入微信开发者工具执行编译、交互与真机截图。")
    add("- 未在真实 iOS/Android 设备验证键盘、安全区、分享、性能与原生组件。")
    add("- 未验证项目实际基础库、渲染引擎和第三方组件兼容性。")
    add("")
    add("## 13. 技术栈约束")
    add("")
    add(f"目标技术栈：**{ds['stack']['label']}** (`{ds['stack']['id']}`)")
    add("")
    add("| 规则 | 应该做 | 不要做 | 核验状态 |")
    add("| --- | --- | --- | --- |")
    for rule in ds["stack_rules"]:
        add(
            f"| {rule['guideline']} | {_md_cell(rule['do'], 100)} | {_md_cell(rule['don_t'], 100)} | {rule['verification_status']} |"
        )
    add("")
    add(f"⚠️ {ds['stack']['verification_limit']}")
    add("")
    add("## 14. 需要主动避免的反模式")
    add("")
    add("| 严重度 | 反模式 | 表现 | 检查方法 | 修复 |")
    add("| --- | --- | --- | --- | --- |")
    for anti in ds["anti_patterns"]:
        add(
            f"| {anti['severity']} | {anti['name']} | {_md_cell(anti['manifestation'], 90)} | {_md_cell(anti['detection'], 100)} | {_md_cell(anti['fix'], 90)} |"
        )
    add("")
    add("## 15. 验收标准")
    add("")
    for criterion in ds["acceptance_criteria"]:
        add(f"- [ ] {criterion}")
    add("")
    add("## 16. 数据来源、未完成项与限制")
    add("")
    add("### 引用的数据记录 ID")
    add("")
    for source_type, ids in ds["sources"].items():
        if ids:
            add(f"- **{source_type}**：{'、'.join(f'`{item}`' for item in ids)}")
    add("")
    add("### 生成限制")
    add("")
    for limitation in ds["limitations"]:
        add(f"- {limitation}")
    add("")
    add("### 维护方式")
    add("")
    add("修改设计前先更新本文件或页面覆盖，再改组件；如果数据本身需要扩展，运行 `python scripts/validate_data.py` 并补充相应记录。")
    add("")
    return "\n".join(lines).rstrip() + "\n"


def _page_override_markdown(ds: dict[str, Any], page: dict[str, str]) -> str:
    components = {row["id"]: row for row in ds["components"]}
    component_names = []
    for component_id in page.get("component_ids", "").split(";"):
        if not component_id:
            continue
        component_names.append(
            f"`{component_id}`" + (f"（{components[component_id]['name']}）" if component_id in components else "")
        )
    lines = [
        f"# 页面覆盖：{page['page_type']}",
        "",
        f"> 继承 `MASTER.md`。本文件只记录页面级必要差异；未提及的 token、颜色、字体、圆角与交互规则全部继承 Master。",
        f"> Master 版本：MPUX Pro {ds['generator']['version']} · 生成时间：{ds['generated_at']}",
        "",
        "## 页面标识",
        "",
        f"- 页面类型：{page['page_type']}",
        f"- Layout ID：`{page['layout_id']}`",
        f"- 目标：{page['goal']}",
        f"- 信息密度：{page['information_density']}",
        "",
        "## 内容顺序与区域",
        "",
        f"1. **视觉层级**：{page['hierarchy']}",
        f"2. **主要区域**：{page['primary_regions']}",
        f"3. **次要区域**：{page['secondary_regions']}",
        f"4. **操作顺序**：{page['action_order']}",
        f"5. **导航**：{page['navigation']}",
        "",
        "## 组件",
        "",
        "、".join(component_names) if component_names else "按 Master 组件规范实现。",
        "",
        "## 页面级允许覆盖",
        "",
        "- 根据实际任务调整区域顺序，但不得移除本页的关键状态与导航出口。",
        "- 可在 Master 间距 token 范围内选择更紧凑的局部间距；不得发明新间距。",
        "- 可增加本页特有的空、错误或加载文案，但必须符合 Master 的反馈规则。",
        "- 可隐藏非必要次要区域，并记录原因。",
        "",
        "## 禁止覆盖",
        "",
        "- 不得新增 Master 之外的品牌色、字体、圆角或阴影语言。",
        "- 所有触摸目标遵循 Master 的 88rpx 基线，不得缩小或删除返回/关闭/撤销路径。",
        "- 不得用页面级规范推翻全局安全区、隐私、加载、错误恢复和防重复提交规则。",
        "- 不得把本页做成一套独立设计系统。",
        "",
        "## 移动端风险",
        "",
        page["mobile_notes"],
        "",
        "## 常见错误",
        "",
        page["common_errors"],
        "",
        "## 验证要求",
        "",
        "- 静态检查本页 WXML/WXSS 或对应框架页面结构与 Master token 一致。",
        f"- 在目标技术栈（{ds['stack']['label']}）的开发者工具中打开本页。",
        "- 在至少一台 iOS 和一台 Android 真机检查键盘、安全区、滚动和返回。",
        "- 未执行的检查必须记录在审查报告中，不能算作通过。",
        "",
    ]
    return "\n".join(lines)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_design_system(
    ds: dict[str, Any],
    markdown: str,
    output_dir: Path,
    *,
    output_format: str = "both",
    page_layouts: list[dict[str, str]] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    output_dir = output_dir.expanduser()
    master_md = output_dir / "MASTER.md"
    master_json = output_dir / "MASTER.json"
    tokens_file = output_dir / ds["token_implementation"]["file"]
    page_files = {
        output_dir / "pages" / f"{page['layout_id'].removeprefix('layout-')}.md": page
        for page in (page_layouts or [])
    }
    requested: list[Path] = []
    if output_format in {"md", "both"}:
        requested.append(master_md)
    if output_format in {"json", "both"}:
        requested.append(master_json)
    requested.append(tokens_file)
    requested.extend(page_files)

    if master_md.exists() and not force:
        return {
            "status": "skipped_exists",
            "output_dir": str(output_dir),
            "created_files": [],
            "skipped_files": [str(path) for path in requested if path.exists()],
            "message": "MASTER.md 已存在；为保护已有设计决策，未覆盖任何文件。检查后如需重新生成，请显式传入 --force。",
        }

    created: list[str] = []
    skipped: list[str] = []
    for path in requested:
        if path.exists() and not force:
            skipped.append(str(path))
            continue
        if path == master_md:
            content = markdown
        elif path == master_json:
            content = json.dumps(ds, ensure_ascii=False, indent=2) + "\n"
        elif path == tokens_file:
            content = _css_tokens(ds["stack"]["id"], ds["tokens"])
        else:
            page = page_files.get(path)
            if page is None:
                continue
            content = _page_override_markdown(ds, page)
        _write_text(path, content)
        created.append(str(path))
    status = "partial" if skipped else "success"
    return {
        "status": status,
        "output_dir": str(output_dir),
        "created_files": created,
        "skipped_files": skipped,
        "message": (
            "设计系统已写入。"
            if status == "success"
            else "部分页面文件已存在，已保留原文件；其余文件已写入。"
        ),
    }


def generate_design_system(
    product: str,
    *,
    style: str | None = None,
    stack: str = "wechat-native",
    project_name: str | None = None,
    pages: list[str] | None = None,
    no_pages: bool = False,
    output_dir: str | Path | None = None,
    output_format: str = "both",
    force: bool = False,
) -> dict[str, Any]:
    if stack not in STACK_CONFIG:
        raise DesignSystemError(f"未知技术栈：{stack}；可用：{', '.join(STACK_CONFIG)}")
    if output_format not in {"md", "json", "both"}:
        raise DesignSystemError("output_format 必须是 md、json 或 both")
    product_row, product_match, product_confidence = _resolve_product(product)
    style_row, style_basis, reasoning_rows = _select_style(product_row, style)
    palette_row, palette_notes = _select_palette(product_row, style_row)
    typography_row, typography_notes = _select_typography(product_row, style_row)
    layouts, layout_notes = _select_layouts(product_row)
    components = _select_components(product_row, layouts)
    ux_rules = _select_ux_rules(
        product_row, style_row, palette_row, layouts, components, reasoning_rows
    )
    mini_rules = _select_mini_rules(product_row, layouts, components, palette_row)
    anti_patterns = _select_anti_patterns(product_row, style_row, reasoning_rows)
    stack_rules = _select_stack_rules(stack, product_row, layouts, components)
    page_layouts = [] if no_pages else _resolve_page_references(pages, layouts)
    display_name = project_name.strip() if project_name and project_name.strip() else product_row["name"]
    ds = _build_design_system(
        product_row,
        style_row,
        palette_row,
        typography_row,
        stack,
        display_name,
        page_layouts,
        style_basis,
        product_match,
        product_confidence,
        layouts,
        components,
        ux_rules,
        mini_rules,
        anti_patterns,
        stack_rules,
        reasoning_rows,
        palette_notes,
    )
    notes = [*palette_notes, *typography_notes]
    if layout_notes:
        notes.extend(layout_notes)
    if notes:
        ds["limitations"].extend(notes)
    markdown = _markdown(ds)
    persistence: dict[str, Any] = {
        "status": "not_written",
        "output_dir": None,
        "created_files": [],
        "skipped_files": [],
        "message": "未指定 --output，结果只输出到标准输出。",
    }
    if output_dir:
        persistence = write_design_system(
            ds,
            markdown,
            Path(output_dir),
            output_format=output_format,
            page_layouts=page_layouts,
            force=force,
        )
    return {
        "design_system": ds,
        "markdown": markdown,
        "persistence": persistence,
    }


def _parse_pages(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    pages: list[str] = []
    for value in values:
        pages.extend(part.strip() for part in value.split(",") if part.strip())
    return pages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="生成微信小程序设计系统（Master + 页面覆盖）。数据完全来自本地知识库。",
    )
    parser.add_argument("--product", "-p", required=True, help="产品名称、别名或产品 ID，如“音乐播放器小程序”")
    parser.add_argument("--style", "-s", default=None, help="指定设计风格，如“现代极简”“现代东方美学”")
    parser.add_argument(
        "--stack",
        choices=sorted(STACK_CONFIG),
        default="wechat-native",
        help="目标技术栈，默认 wechat-native",
    )
    parser.add_argument("--project-name", default=None, help="项目名称；默认使用产品类型名称")
    parser.add_argument(
        "--pages",
        action="append",
        default=None,
        help="要生成的页面覆盖，逗号分隔或重复传入；all 表示全部。默认生成 3 个推荐页面。",
    )
    parser.add_argument("--no-pages", action="store_true", help="不生成页面覆盖文件")
    parser.add_argument("--output", "-o", default=None, help="输出目录，如 ./design-system")
    parser.add_argument(
        "--format",
        choices=["both", "md", "json"],
        default="both",
        help="输出格式，默认 both（MASTER.md + MASTER.json）",
    )
    parser.add_argument("--json", action="store_true", help="等价于 --format json；未指定输出时打印 JSON")
    parser.add_argument("--force", action="store_true", help="明确覆盖已有 MASTER 和页面文件")
    parser.add_argument("--quiet", action="store_true", help="指定 --output 时不打印摘要")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.json:
        args.format = "json"
    try:
        result = generate_design_system(
            args.product,
            style=args.style,
            stack=args.stack,
            project_name=args.project_name,
            pages=_parse_pages(args.pages),
            no_pages=args.no_pages,
            output_dir=args.output,
            output_format=args.format,
            force=args.force,
        )
    except DesignSystemError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    if args.output:
        persistence = result["persistence"]
        if not args.quiet:
            print(persistence["message"])
            if persistence["output_dir"]:
                print(f"输出目录：{persistence['output_dir']}")
            for path in persistence["created_files"]:
                print(f"已写入：{path}")
            for path in persistence["skipped_files"]:
                print(f"未覆盖：{path}")
        return 0 if persistence["status"] != "skipped_exists" else 0

    if args.format == "json":
        print(json.dumps(result["design_system"], ensure_ascii=False, indent=2))
    else:
        print(result["markdown"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())