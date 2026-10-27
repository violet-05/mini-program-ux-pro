#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 MPUX Pro 原创知识库的结构、引用和颜色可访问性。"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")
HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]

DOMAIN_SPECS: dict[str, dict[str, Any]] = {
    "product": {
        "file": "products.csv",
        "id": "product_id",
        "prefix": "prod-",
        "min_rows": 30,
        "columns": [
            "product_id",
            "name",
            "aliases",
            "summary",
            "target_users",
            "scenarios",
            "core_tasks",
            "home_structure",
            "nav_pattern",
            "information_density",
            "typical_component_ids",
            "recommended_style_ids",
            "recommended_color_ids",
            "primary_layout_ids",
            "avoid",
            "design_reasoning",
            "reasoning_ids",
        ],
    },
    "style": {
        "file": "styles.csv",
        "id": "style_id",
        "prefix": "style-",
        "min_rows": 22,
        "columns": [
            "style_id",
            "name_zh",
            "name_en",
            "keywords",
            "visual_traits",
            "recommended_scenarios",
            "typography_rules",
            "color_tendency",
            "component_traits",
            "motion_strategy",
            "content_density",
            "avoid_scenarios",
            "common_errors",
            "combination_notes",
        ],
    },
    "color": {
        "file": "colors.csv",
        "id": "palette_id",
        "prefix": "palette-",
        "min_rows": 16,
        "color_fields": [
            "background",
            "surface",
            "text_primary",
            "text_secondary",
            "brand",
            "accent",
            "border",
            "success",
            "warning",
            "error",
        ],
        "columns": [
            "palette_id",
            "name",
            "business_fit",
            "style_ids",
            "background",
            "surface",
            "text_primary",
            "text_secondary",
            "brand",
            "accent",
            "border",
            "success",
            "warning",
            "error",
            "usage",
            "contrast_notes",
            "mode",
        ],
    },
    "layout": {
        "file": "layouts.csv",
        "id": "layout_id",
        "prefix": "layout-",
        "min_rows": 26,
        "columns": [
            "layout_id",
            "page_type",
            "goal",
            "hierarchy",
            "primary_regions",
            "secondary_regions",
            "navigation",
            "component_ids",
            "action_order",
            "information_density",
            "mobile_notes",
            "common_errors",
            "source",
        ],
    },
    "component": {
        "file": "components.csv",
        "id": "component_id",
        "prefix": "comp-",
        "min_rows": 33,
        "columns": [
            "component_id",
            "name",
            "use_cases",
            "visual_rules",
            "interaction_rules",
            "touch_target",
            "states",
            "accessibility",
            "native_implementation",
            "stacks",
            "common_errors",
        ],
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "id": "rule_id",
        "prefix": "ux-",
        "min_rows": 34,
        "columns": [
            "rule_id",
            "category",
            "name",
            "severity",
            "scenario",
            "problem",
            "recommendation",
            "bad_example",
            "how_to_check",
            "fix",
            "platforms",
        ],
    },
    "mini-program": {
        "file": "mini-program-rules.csv",
        "id": "rule_id",
        "prefix": "mp-",
        "min_rows": 30,
        "columns": [
            "rule_id",
            "category",
            "name",
            "severity",
            "scenario",
            "platform_behavior",
            "recommendation",
            "bad_example",
            "implementation",
            "how_to_verify",
            "stacks",
            "source_url",
            "verification_status",
            "verified_at",
        ],
    },
    "anti-pattern": {
        "file": "anti-patterns.csv",
        "id": "anti_pattern_id",
        "prefix": "anti-",
        "min_rows": 40,
        "columns": [
            "anti_pattern_id",
            "name",
            "manifestation",
            "root_cause",
            "scenario",
            "detection",
            "severity",
            "fix",
            "related_rule_ids",
        ],
    },
    "typography": {
        "file": "typography.csv",
        "id": "typography_id",
        "prefix": "type-",
        "min_rows": 8,
        "columns": [
            "typography_id",
            "name",
            "heading_stack",
            "body_stack",
            "numeric_stack",
            "scale_rationale",
            "moods",
            "style_ids",
            "best_for",
            "line_height_rules",
            "mini_program_notes",
        ],
    },
    "reasoning": {
        "file": "ui-reasoning.csv",
        "id": "reasoning_id",
        "prefix": "reason-",
        "min_rows": 10,
        "columns": [
            "reasoning_id",
            "scenario",
            "product_tags",
            "conditions",
            "style_priority",
            "color_priority",
            "layout_priority",
            "interaction_priority",
            "avoid",
            "explanation",
        ],
    },
}

STACK_SPECS = {
    "wechat-native": {"file": "stacks/wechat-native.csv", "prefix": "wx-", "min_rows": 18},
    "uni-app": {"file": "stacks/uni-app.csv", "prefix": "uni-", "min_rows": 18},
    "taro": {"file": "stacks/taro.csv", "prefix": "taro-", "min_rows": 18},
}
STACK_COLUMNS = [
    "rule_id",
    "category",
    "guideline",
    "description",
    "do",
    "don_t",
    "code_good",
    "code_bad",
    "severity",
    "platform",
    "verification_status",
    "source_url",
    "verified_at",
]

ALLOWED_DENSITIES = {"低", "中低", "中", "中高", "高"}
ALLOWED_SEVERITIES = {"P0", "P1", "P2", "P3"}


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    return headers, rows


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _luminance(color: str) -> float:
    result = []
    for channel in _hex_to_rgb(color):
        value = channel / 255
        result.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = result
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(a: str, b: str) -> float:
    first, second = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def _split_ids(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1 and value)


def validate(data_dir: Path = DATA_DIR) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    datasets: dict[str, list[dict[str, str]]] = {}
    id_sets: dict[str, set[str]] = {}
    all_ids: dict[str, str] = {}
    counts: dict[str, int] = {}

    for domain, spec in DOMAIN_SPECS.items():
        path = data_dir / spec["file"]
        if not path.exists():
            errors.append(f"缺少数据文件：{path}")
            continue
        try:
            headers, rows = _read_csv(path)
        except (OSError, csv.Error) as exc:
            errors.append(f"{spec['file']} 无法解析：{exc}")
            continue
        datasets[domain] = rows
        counts[domain] = len(rows)
        missing_columns = [column for column in spec["columns"] if column not in headers]
        if missing_columns:
            errors.append(f"{spec['file']} 缺少列：{', '.join(missing_columns)}")
        if len(rows) < spec["min_rows"]:
            errors.append(
                f"{spec['file']} 至少需要 {spec['min_rows']} 条记录，当前 {len(rows)} 条"
            )
        ids = [row.get(spec["id"], "").strip() for row in rows]
        duplicates = _duplicates([item for item in ids if item])
        if duplicates:
            errors.append(f"{spec['file']} 存在重复 ID：{', '.join(duplicates)}")
        empty_ids = sum(1 for item in ids if not item)
        if empty_ids:
            errors.append(f"{spec['file']} 有 {empty_ids} 条记录缺少 {spec['id']}")
        for row_index, row in enumerate(rows, start=2):
            record_id = row.get(spec["id"], "").strip()
            if record_id and not ID_PATTERN.match(record_id):
                errors.append(f"{spec['file']}:{row_index} ID 格式不合法：{record_id!r}")
            if record_id and not record_id.startswith(spec["prefix"]):
                errors.append(
                    f"{spec['file']}:{row_index} ID {record_id!r} 应以 {spec['prefix']} 开头"
                )
            for column in spec["columns"]:
                if not str(row.get(column, "")).strip():
                    errors.append(f"{spec['file']}:{row_index} 字段 {column} 为空")
            if record_id:
                if record_id in all_ids:
                    errors.append(
                        f"跨领域 ID 冲突：{record_id} 同时出现在 {all_ids[record_id]} 和 {domain}"
                    )
                else:
                    all_ids[record_id] = domain
        id_sets[domain] = set(item for item in ids if item)

    # 具体领域检查
    for domain in ("product", "layout", "style"):
        rows = datasets.get(domain, [])
        names = [row.get("name" if domain != "layout" else "page_type", "") for row in rows]
        duplicates = _duplicates([name for name in names if name])
        if duplicates:
            warnings.append(f"{domain} 存在重复显示名称：{', '.join(duplicates)}")

    for row in datasets.get("product", []):
        pid = row.get("product_id")
        if row.get("information_density") not in ALLOWED_DENSITIES:
            errors.append(f"{pid} information_density 不合法：{row.get('information_density')}")
        for field, target in (
            ("typical_component_ids", "component"),
            ("recommended_style_ids", "style"),
            ("recommended_color_ids", "color"),
            ("primary_layout_ids", "layout"),
            ("reasoning_ids", "reasoning"),
        ):
            values = _split_ids(row.get(field, ""))
            if not values:
                errors.append(f"{pid} 的 {field} 为空")
            for value in values:
                if value not in id_sets.get(target, set()):
                    errors.append(f"{pid} 的 {field} 引用了不存在的 {target}：{value}")
        if not _split_ids(row.get("reasoning_ids", "")):
            errors.append(f"{pid} 缺少设计推理引用")

    for row in datasets.get("style", []):
        if row.get("content_density") not in ALLOWED_DENSITIES:
            errors.append(f"{row.get('style_id')} content_density 不合法：{row.get('content_density')}")

    # 明显矛盾：产品推荐了一个明确声明“不适用该产品名/别名”的风格。
    style_by_id = {row.get("style_id"): row for row in datasets.get("style", [])}
    for row in datasets.get("product", []):
        identities = [row.get("name", "")]
        identities.extend(part.strip() for part in row.get("aliases", "").split("|"))
        for style_id in _split_ids(row.get("recommended_style_ids", "")):
            style = style_by_id.get(style_id)
            if not style:
                continue
            avoided = style.get("avoid_scenarios", "")
            for identity in identities:
                if len(identity) >= 2 and identity in avoided:
                    errors.append(
                        f"{row.get('product_id')} 推荐了 {style_id}，但该风格明确避免“{identity}”"
                    )

    for row in datasets.get("layout", []):
        lid = row.get("layout_id")
        if row.get("information_density") not in ALLOWED_DENSITIES:
            errors.append(f"{lid} information_density 不合法：{row.get('information_density')}")
        for value in _split_ids(row.get("component_ids", "")):
            if value not in id_sets.get("component", set()):
                errors.append(f"{lid} 引用了不存在的组件：{value}")

    for row in datasets.get("color", []):
        pid = row.get("palette_id")
        if row.get("mode") not in {"light", "dark"}:
            errors.append(f"{pid} mode 不合法：{row.get('mode')}")
        for field in DOMAIN_SPECS["color"]["color_fields"]:
            value = row.get(field, "")
            if not HEX_PATTERN.match(value):
                errors.append(f"{pid} 的 {field} 不是合法 HEX：{value}")
        for value in _split_ids(row.get("style_ids", "")):
            if value not in id_sets.get("style", set()):
                errors.append(f"{pid} 引用了不存在的风格：{value}")
        if all(HEX_PATTERN.match(row.get(field, "")) for field in ("background", "surface", "text_primary", "text_secondary")):
            for background in ("background", "surface"):
                for foreground in ("text_primary", "text_secondary"):
                    ratio = _contrast(row[foreground], row[background])
                    if ratio < 4.5:
                        errors.append(
                            f"{pid} 对比度不足：{foreground} 对 {background} 为 {ratio:.2f}:1（最低 4.5:1）"
                        )

    for row in datasets.get("typography", []):
        tid = row.get("typography_id")
        for value in _split_ids(row.get("style_ids", "")):
            if value not in id_sets.get("style", set()):
                errors.append(f"{tid} 引用了不存在的风格：{value}")

    for row in datasets.get("reasoning", []):
        rid = row.get("reasoning_id")
        for field, target in (
            ("style_priority", "style"),
            ("color_priority", "color"),
            ("layout_priority", "layout"),
            ("interaction_priority", "ux"),
            ("avoid", "anti-pattern"),
        ):
            values = _split_ids(row.get(field, ""))
            if not values:
                errors.append(f"{rid} 的 {field} 为空")
            for value in values:
                if value not in id_sets.get(target, set()):
                    errors.append(f"{rid} 的 {field} 引用了不存在的 {target}：{value}")

    valid_any = set(all_ids)
    for row in datasets.get("anti-pattern", []):
        aid = row.get("anti_pattern_id")
        for value in _split_ids(row.get("related_rule_ids", "")):
            if value not in valid_any:
                errors.append(f"{aid} 的 related_rule_ids 引用不存在：{value}")

    for domain in ("ux", "mini-program", "anti-pattern"):
        for row in datasets.get(domain, []):
            if row.get("severity") not in ALLOWED_SEVERITIES:
                errors.append(f"{row.get(DOMAIN_SPECS[domain]['id'])} severity 不合法：{row.get('severity')}")

    for row in datasets.get("mini-program", []):
        rid = row.get("rule_id")
        source_url = row.get("source_url", "")
        if not source_url.startswith("https://"):
            errors.append(f"{rid} source_url 不是 HTTPS 地址")
        verified_at = row.get("verified_at", "")
        if not DATE_PATTERN.match(verified_at):
            errors.append(f"{rid} verified_at 不是 YYYY-MM-DD：{verified_at}")
        status = row.get("verification_status", "")
        if not status.startswith(("已核对", "需按", "需根据", "项目原则", "未核对")):
            warnings.append(f"{rid} verification_status 前缀无法识别：{status}")

    # 技术栈数据
    for stack, spec in STACK_SPECS.items():
        path = data_dir / spec["file"]
        if not path.exists():
            errors.append(f"缺少技术栈数据文件：{path}")
            continue
        try:
            headers, rows = _read_csv(path)
        except (OSError, csv.Error) as exc:
            errors.append(f"{spec['file']} 无法解析：{exc}")
            continue
        datasets[f"stack:{stack}"] = rows
        counts[f"stack:{stack}"] = len(rows)
        missing_columns = [column for column in STACK_COLUMNS if column not in headers]
        if missing_columns:
            errors.append(f"{spec['file']} 缺少列：{', '.join(missing_columns)}")
        if len(rows) < spec["min_rows"]:
            errors.append(f"{spec['file']} 至少需要 {spec['min_rows']} 条，当前 {len(rows)} 条")
        ids = [row.get("rule_id", "").strip() for row in rows]
        duplicates = _duplicates([item for item in ids if item])
        if duplicates:
            errors.append(f"{spec['file']} 存在重复 ID：{', '.join(duplicates)}")
        for row_index, row in enumerate(rows, start=2):
            rule_id = row.get("rule_id", "").strip()
            if not ID_PATTERN.match(rule_id):
                errors.append(f"{spec['file']}:{row_index} rule_id 格式不合法：{rule_id!r}")
            if not rule_id.startswith(spec["prefix"]):
                errors.append(f"{spec['file']}:{row_index} rule_id {rule_id!r} 应以 {spec['prefix']} 开头")
            for column in STACK_COLUMNS:
                if not str(row.get(column, "")).strip():
                    errors.append(f"{spec['file']}:{row_index} 字段 {column} 为空")
            if row.get("platform") != stack:
                errors.append(f"{rule_id} platform 应为 {stack}，实际 {row.get('platform')}")
            if row.get("severity") not in ALLOWED_SEVERITIES:
                errors.append(f"{rule_id} severity 不合法：{row.get('severity')}")
            if not str(row.get("source_url", "")).startswith("https://"):
                errors.append(f"{rule_id} source_url 不是 HTTPS 地址")
            if not DATE_PATTERN.match(row.get("verified_at", "")):
                errors.append(f"{rule_id} verified_at 不是 YYYY-MM-DD")
            if rule_id in all_ids:
                errors.append(f"跨领域 ID 冲突：{rule_id} 与 {all_ids[rule_id]}")
            else:
                all_ids[rule_id] = f"stack:{stack}"

    # 重复整行和敏感信息
    for domain, rows in datasets.items():
        signatures = [
            tuple(row.get(column, "") for column in sorted(row.keys()))
            for row in rows
        ]
        duplicate_count = sum(count - 1 for count in Counter(signatures).values() if count > 1)
        if duplicate_count:
            warnings.append(f"{domain} 存在 {duplicate_count} 条完全重复记录")
    for path in data_dir.rglob("*.csv"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.name} 可能包含密钥或令牌")
                break
    unverified = sum(
        1
        for row in datasets.get("mini-program", [])
        if "需" in row.get("verification_status", "")
    ) + sum(
        1
        for rows in (datasets.get("stack:wechat-native", []), datasets.get("stack:uni-app", []), datasets.get("stack:taro", []))
        for row in rows
        if "需" in row.get("verification_status", "")
    )
    if unverified:
        warnings.append(
            f"有 {unverified} 条平台/技术栈规则需要按目标基础库或真机复核，输出时必须保留核验状态"
        )

    return {
        "ok": not errors,
        "data_dir": str(data_dir),
        "checked_at": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "counts": counts,
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="验证 MPUX Pro 设计知识库")
    parser.add_argument("--data-dir", default=str(DATA_DIR), help="数据目录，默认 data/")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)
    result = validate(Path(args.data_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("MPUX Pro 数据验证")
        print("=" * 60)
        for name, count in result["counts"].items():
            print(f"{name:28} {count:4} 条")
        print("=" * 60)
        print(f"错误：{len(result['errors'])}  警告：{len(result['warnings'])}")
        for error in result["errors"]:
            print(f"[ERROR] {error}")
        for warning in result["warnings"]:
            print(f"[WARN]  {warning}")
        print("结果：" + ("通过" if result["ok"] else "未通过"))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())