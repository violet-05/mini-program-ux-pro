"""静态审查报告的离线契约与问题组标识。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

SCHEMA_VERSION = "1.1.0"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "review-report.schema.json"
COMPARISON_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "review-comparison.schema.json"
PROJECT_CHECKS = {"custom-navigation", "ui-states", "privacy", "design-tokens", "misc-css", "environment"}
SCHEMA_KEYWORDS = {
    "$schema", "$id", "$defs", "$ref", "title", "description", "type", "const", "enum",
    "properties", "required", "additionalProperties", "items", "minItems", "uniqueItems",
    "minimum", "minLength", "pattern", "anyOf",
}


class ReportError(ValueError):
    pass


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReportError(f"JSON 包含重复字段：{key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ReportError(f"JSON 不允许 {value}")


def read_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8-sig"),
            object_pairs_hook=_json_object,
            parse_constant=_invalid_constant,
        )
    except (OSError, ValueError, RecursionError) as exc:
        raise ReportError(f"无法读取 JSON：{path}；{exc}") from exc


def validate_schema(value: Any, schema: dict[str, Any], *, root: dict | None = None, path: str = "$") -> None:
    # 只支持本项目契约使用的关键字；未知关键字拒绝而不是静默忽略。
    root = schema if root is None else root
    unknown = set(schema) - SCHEMA_KEYWORDS
    if unknown:
        raise ReportError(f"{path}：不支持的 Schema 关键字 {sorted(unknown)}")
    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/$defs/") or reference[8:] not in root.get("$defs", {}):
            raise ReportError(f"{path}：只允许本地 Schema 定义引用")
        validate_schema(value, root["$defs"][reference[8:]], root=root, path=path)
    if "anyOf" in schema:
        for alternative in schema["anyOf"]:
            try:
                validate_schema(value, alternative, root=root, path=path)
                break
            except ReportError:
                continue
        else:
            raise ReportError(f"{path}：不符合任何允许的类型或结构")
    expected = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    if expected is not None and (expected not in types or type(value) is not types[expected]):
        raise ReportError(f"{path}：必须是 {expected}")
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        raise ReportError(f"{path}：必须为 {schema['const']!r}")
    if "enum" in schema and not any(type(value) is type(item) and value == item for item in schema["enum"]):
        raise ReportError(f"{path}：不在允许值范围内")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise ReportError(f"{path}：缺少字段 {', '.join(sorted(missing))}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], root=root, path=f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ReportError(f"{path}：未知字段 {key}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ReportError(f"{path}：列表项不足")
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise ReportError(f"{path}：列表项不能重复")
        for index, item in enumerate(value):
            if "items" in schema:
                validate_schema(item, schema["items"], root=root, path=f"{path}[{index}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0) or ("pattern" in schema and not re.search(schema["pattern"], value)):
            raise ReportError(f"{path}：字符串格式不正确")
    if type(value) is int and "minimum" in schema and value < schema["minimum"]:
        raise ReportError(f"{path}：不能小于 {schema['minimum']}")


def relative_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if "\x00" in value or ":" in value or path.is_absolute() or PureWindowsPath(value).anchor or ".." in path.parts:
        raise ReportError(f"证据/扫描路径必须在项目内：{value}")
    return path.as_posix()


def finding_fingerprint(finding: dict[str, Any]) -> str:
    files = [] if finding["check_id"] in PROJECT_CHECKS else sorted({relative_path(item["file"]) for item in finding["evidence"]})
    identity = [finding["check_id"], finding["category"], finding["title"], sorted(finding["rule_ids"]), files]
    return hashlib.sha256(json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_report(report: Any) -> None:
    if isinstance(report, dict) and report.get("schema_version") != SCHEMA_VERSION:
        raise ReportError(f"仅支持审查报告 {SCHEMA_VERSION}；请用当前版本重新运行 audit 生成两份报告")
    validate_schema(report, read_json(SCHEMA_PATH))
    ids: set[str] = set()
    fingerprints: set[str] = set()
    checks = [item["id"] for item in report["executed_checks"]]
    skipped = [item["id"] for item in report["skipped_checks"]]
    if len(set(checks)) != len(checks) or len(set(skipped)) != len(skipped) or set(checks) & set(skipped):
        raise ReportError("检查 ID 重复或同时标为已执行与未执行")
    sources = [relative_path(item) for item in report["scope"]["source_files"]]
    if len(set(sources)) != len(sources) or "." in sources or len(sources) != report["scope"]["files_scanned"]:
        raise ReportError("scope.source_files 与扫描数量不一致或存在重复路径")
    pages = report["scope"]["page_paths"]
    if len(pages) != report["scope"]["pages_declared"]:
        raise ReportError("scope.page_paths 与声明页面数量不一致")
    for page in pages:
        relative_path(page)
    summary = dict.fromkeys(("P0", "P1", "P2", "P3"), 0)
    for finding in report["findings"]:
        if finding["id"] in ids or finding["fingerprint"] in fingerprints:
            raise ReportError("问题 ID 或 fingerprint 重复")
        if finding["check_id"] not in checks:
            raise ReportError(f"问题 {finding['id']} 引用了未执行的检查")
        for evidence in finding["evidence"]:
            relative_path(evidence["file"])
        if finding["fingerprint"] != finding_fingerprint(finding):
            raise ReportError(f"问题 {finding['id']} 的 fingerprint 与内容不一致")
        ids.add(finding["id"])
        fingerprints.add(finding["fingerprint"])
        summary[finding["severity"]] += 1
    if report["summary"] != summary:
        raise ReportError("summary 与实际问题数量不一致")


def load_report(path: Path) -> dict[str, Any]:
    report = read_json(path)
    try:
        validate_report(report)
    except ReportError as exc:
        raise ReportError(f"无效审查报告：{path}；{exc}") from exc
    return report
