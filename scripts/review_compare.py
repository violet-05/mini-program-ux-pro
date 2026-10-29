#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""比较两份静态审查报告，区分新增、已修复与遗留问题。

只读取两份已保存的 JSON 报告，不重新扫描项目，不修改被审查项目。
修复只有在本次确实执行了同一检查、且相关文件仍在扫描范围内时才确认；
否则标记为无法确认，避免把“没检查”误报成“已修复”。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mpux_core import configure_utf8_stdio
from review_contract import (
    COMPARISON_SCHEMA_PATH,
    PROJECT_CHECKS,
    ReportError,
    load_report,
    read_json,
    relative_path,
    validate_schema,
)

VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _brief(
    finding: dict[str, Any],
    side: str,
    *,
    recommendation: bool = False,
    reason: str | None = None,
    previous_severity: str | None = None,
) -> dict[str, Any]:
    entry = {
        "id": finding["id"],
        "fingerprint": finding["fingerprint"],
        "check_id": finding["check_id"],
        "side": side,
        "severity": finding["severity"],
        "category": finding["category"],
        "title": finding["title"],
        "evidence": [{"file": item["file"], "line": item["line"]} for item in finding["evidence"]],
    }
    if recommendation:
        entry["recommendation"] = finding["recommendation"]
    if reason:
        entry["reason"] = reason
    if previous_severity:
        entry["previous_severity"] = previous_severity
    return entry


def _sort_key(entry: dict[str, Any]) -> tuple:
    return (
        SEVERITY_ORDER.get(entry["severity"], 9),
        entry["title"],
        entry["evidence"][0]["file"] if entry["evidence"] else "",
    )


def _resolution_blockers(
    finding: dict[str, Any],
    after_checks: set[str],
    before_files: set[str],
    after_files: set[str],
) -> list[str]:
    reasons: list[str] = []
    check_id = finding["check_id"]
    if check_id not in after_checks:
        reasons.append(f"本次未执行检查 {check_id}")
    if check_id in PROJECT_CHECKS:
        if before_files - after_files:
            reasons.append(f"本次扫描比上次少 {len(before_files - after_files)} 个文件，无法确认全部源码已复查")
    else:
        missing = sorted(
            {relative_path(item["file"]) for item in finding["evidence"]} - after_files
        )
        if missing:
            reasons.append("证据文件 " + "、".join(missing[:3]) + " 不在本次扫描范围")
    return reasons


def _new_caveat(
    finding: dict[str, Any],
    before_checks: set[str],
    before_files: set[str],
    after_files: set[str],
) -> str | None:
    check_id = finding["check_id"]
    if check_id not in before_checks:
        return f"上次未执行检查 {check_id}"
    if check_id in PROJECT_CHECKS:
        if after_files - before_files:
            return f"本次扫描比上次多 {len(after_files - before_files)} 个文件，问题可能来自此前未覆盖的文件"
    else:
        missing = sorted(
            {relative_path(item["file"]) for item in finding["evidence"]} - before_files
        )
        if missing:
            return "证据文件 " + "、".join(missing[:3]) + " 不在上次扫描范围"
    return None


def compare_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    if before["scope"]["ruleset"] != after["scope"]["ruleset"]:
        raise ReportError(
            f"两份报告规则集不同（{before['scope']['ruleset']} / {after['scope']['ruleset']}），不能比较"
        )
    if before["project"]["stack"] != after["project"]["stack"]:
        raise ReportError(
            f"两份报告技术栈不同（{before['project']['stack']} / {after['project']['stack']}），不能比较"
        )
    warnings: list[str] = []
    if before["project"]["name"] != after["project"]["name"]:
        warnings.append(
            f"项目名称不同：{before['project']['name']} → {after['project']['name']}；确认是在比较同一个项目"
        )
    if before["project"]["path"] != after["project"]["path"]:
        warnings.append("项目路径不同；项目可能已移动，按相对路径匹配文件")
    if after["generated_at"] < before["generated_at"]:
        warnings.append("第二份报告生成时间早于第一份；确认前后顺序是否传反")
    before_design = before["scope"].get("design_system")
    after_design = after["scope"].get("design_system")
    if (before_design or {}).get("fingerprint") != (after_design or {}).get("fingerprint"):
        warnings.append("设计系统 token 与上次不同；与 token 相关的结果变化可能来自设计系统更新")

    before_files = {relative_path(path) for path in before["scope"]["source_files"]}
    after_files = {relative_path(path) for path in after["scope"]["source_files"]}
    after_checks = {item["id"] for item in after["executed_checks"]}
    before_checks = {item["id"] for item in before["executed_checks"]}
    before_findings = {item["fingerprint"]: item for item in before["findings"]}
    after_findings = {item["fingerprint"]: item for item in after["findings"]}

    new: list[dict[str, Any]] = []
    new_unverified: list[dict[str, Any]] = []
    resolved: list[dict[str, Any]] = []
    unconfirmed: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []

    for fingerprint, finding in after_findings.items():
        if fingerprint in before_findings:
            previous = before_findings[fingerprint]
            severity = previous["severity"] if previous["severity"] != finding["severity"] else None
            remaining.append(_brief(finding, "after", previous_severity=severity))
            continue
        caveat = _new_caveat(finding, before_checks, before_files, after_files)
        entry = _brief(finding, "after", recommendation=True)
        if caveat:
            entry["reason"] = caveat
            new_unverified.append(entry)
        else:
            new.append(entry)
    for fingerprint, finding in before_findings.items():
        if fingerprint in after_findings:
            continue
        reason = _resolution_blockers(finding, after_checks, before_files, after_files)
        entry = _brief(finding, "before")
        if reason:
            entry["reason"] = "；".join(reason)
            unconfirmed.append(entry)
        else:
            resolved.append(entry)

    for group in (new, new_unverified, resolved, unconfirmed, remaining):
        group.sort(key=_sort_key)

    new_by_severity = dict.fromkeys(("P0", "P1", "P2", "P3"), 0)
    for entry in new:
        new_by_severity[entry["severity"]] += 1

    result = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "static-review-comparison",
        "generator": {"name": "mini-program-ux-pro", "version": VERSION},
        "before": {
            "path": before["project"]["path"],
            "generated_at": before["generated_at"],
            "files_scanned": before["scope"]["files_scanned"],
            "findings": len(before["findings"]),
        },
        "after": {
            "path": after["project"]["path"],
            "generated_at": after["generated_at"],
            "files_scanned": after["scope"]["files_scanned"],
            "findings": len(after["findings"]),
        },
        "warnings": warnings,
        "scope": {
            "files_added": len(after_files - before_files),
            "files_removed": len(before_files - after_files),
        },
        "summary": {
            "new": len(new),
            "new_unverified": len(new_unverified),
            "resolved": len(resolved),
            "unconfirmed": len(unconfirmed),
            "remaining": len(remaining),
            "new_by_severity": new_by_severity,
        },
        "new": new,
        "new_unverified": new_unverified,
        "resolved": resolved,
        "unconfirmed": unconfirmed,
        "remaining": remaining,
        "note": "对比只反映两次静态规则结果的变化；未执行检查、范围变化和人工判断项不能视为通过，也不代表视觉、交互或真机验收。",
    }
    validate_comparison(result)
    return result


def validate_comparison(result: dict[str, Any]) -> None:
    validate_schema(result, read_json(COMPARISON_SCHEMA_PATH))


def _entry_line(entry: dict[str, Any]) -> str:
    location = f"`{entry['evidence'][0]['file']}:{entry['evidence'][0]['line']}`" if entry["evidence"] else "无证据"
    return f"- **[{entry['severity']}] {entry['title']}** · `{entry['check_id']}` · {location}"


def format_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines: list[str] = []
    add = lines.append
    add("# 静态审查结果对比")
    add("")
    add(f"> 生成器：MPUX Pro {result['generator']['version']}。只比较已保存的静态报告，没有重新扫描或执行项目。")
    add("")
    add("## 输入")
    add("")
    add(f"- **前**：`{result['before']['path']}` · {result['before']['generated_at']} · {result['before']['files_scanned']} 个文件 · {result['before']['findings']} 个问题组")
    add(f"- **后**：`{result['after']['path']}` · {result['after']['generated_at']} · {result['after']['files_scanned']} 个文件 · {result['after']['findings']} 个问题组")
    add(f"- **扫描文件变化**：新增 {result['scope']['files_added']}，减少 {result['scope']['files_removed']}")
    add("")
    if result["warnings"]:
        add("## 注意")
        add("")
        for warning in result["warnings"]:
            add(f"- {warning}")
        add("")
    add("## 变化摘要")
    add("")
    add("| 新增 | 新增待确认 | 已确认修复 | 无法确认 | 遗留 |")
    add("| ---: | ---: | ---: | ---: | ---: |")
    add(f"| {summary['new']} | {summary['new_unverified']} | {summary['resolved']} | {summary['unconfirmed']} | {summary['remaining']} |")
    add("")
    if summary["new"]:
        add("新增问题按严重度：" + "，".join(f"{level} {count}" for level, count in summary["new_by_severity"].items()))
        add("")
    sections = (
        ("新增问题", "new", True),
        ("新增但无法归因（可能来自扫描范围变化）", "new_unverified", False),
        ("已确认修复", "resolved", False),
        ("无法确认是否修复", "unconfirmed", False),
        ("遗留问题", "remaining", False),
    )
    for title, key, with_recommendation in sections:
        entries = result[key]
        if not entries and key != "remaining":
            continue
        add(f"## {title}（{len(entries)}）")
        add("")
        if not entries:
            add("无。")
            add("")
            continue
        for entry in entries:
            line = _entry_line(entry)
            if entry.get("previous_severity"):
                line = line.replace(f"[{entry['severity']}]", f"[{entry['severity']}，原 {entry['previous_severity']}]")
            add(line)
            if entry.get("reason"):
                add(f"  - 原因：{entry['reason']}")
            if with_recommendation and entry.get("recommendation"):
                add(f"  - 建议：{entry['recommendation']}")
        add("")
    add("## 结论边界")
    add("")
    add(result["note"])
    add("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="比较两份 audit_mini_program.py 生成的静态审查 JSON 报告。",
        epilog="示例：python mpux.py compare review-before.json review-after.json --fail-on-new P1",
    )
    parser.add_argument("before", help="较早的审查 JSON 报告")
    parser.add_argument("after", help="较新的审查 JSON 报告")
    parser.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown", help="输出格式")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--output", "-o", default=None, help="同时写入文件；不能覆盖输入报告")
    parser.add_argument(
        "--fail-on-new",
        choices=["none", "P0", "P1", "P2", "P3"],
        default="none",
        help="出现达到阈值的新增问题时返回退出码 1；默认不因问题失败",
    )
    return parser


def _exit_code(result: dict[str, Any], fail_on_new: str) -> int:
    if fail_on_new == "none":
        return 0
    threshold = SEVERITY_ORDER[fail_on_new]
    return 1 if any(SEVERITY_ORDER[item["severity"]] <= threshold for item in result["new"]) else 0


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        before = load_report(Path(args.before))
        after = load_report(Path(args.after))
        result = compare_reports(before, after)
    except ReportError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    markdown = format_markdown(result)
    if args.output:
        output = Path(args.output)
        if output.resolve() in {Path(args.before).resolve(), Path(args.after).resolve()}:
            print("错误：--output 不能覆盖输入报告；请改用其他文件名。", file=sys.stderr)
            return 2
        content = (
            json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            if args.json or args.format == "json"
            else markdown
        )
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
        except (OSError, ValueError) as exc:
            print(f"错误：无法写入对比结果：{output}；{exc}", file=sys.stderr)
            return 2
    if args.json or args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(markdown)
    return _exit_code(result, args.fail_on_new)


if __name__ == "__main__":
    raise SystemExit(main())
