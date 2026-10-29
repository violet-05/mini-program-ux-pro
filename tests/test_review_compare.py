from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import FIXTURES, ROOT, load_json_output, run_script  # noqa: E402

from audit_mini_program import audit_project  # noqa: E402
from review_compare import compare_reports, format_markdown  # noqa: E402
from review_contract import ReportError, finding_fingerprint, load_report, validate_report  # noqa: E402


def make_finding(
    title: str = "WXML 使用浏览器 HTML 标签",
    *,
    file: str = "pages/home/index.wxml",
    line: int = 3,
    severity: str = "P0",
    check_id: str = "dom-browser-api",
    category: str = "平台兼容",
    rule_ids: tuple[str, ...] = ("wx-wxml-binding",),
) -> dict:
    finding = {
        "check_id": check_id,
        "severity": severity,
        "category": category,
        "title": title,
        "evidence": [{"file": file, "line": line, "excerpt": "<div>"}],
        "why": "why",
        "recommendation": "改成 view",
        "rule_ids": list(rule_ids),
        "verification": "automated",
        "confidence": "high",
    }
    finding["fingerprint"] = finding_fingerprint(finding)
    return finding


def make_report(
    findings: list[dict] | None = None,
    *,
    files: tuple[str, ...] = ("app.json", "pages/home/index.wxml"),
    checks: tuple[str, ...] = ("dom-browser-api", "ui-states", "design-tokens"),
    stack: str = "wechat-native",
    ruleset: str = "static-1",
    generated_at: str = "2026-10-29T10:00:00+00:00",
    name: str = "demo",
    path: str = "/tmp/demo",
    design_fingerprint: str = "a" * 64,
) -> dict:
    findings = list(findings or [])
    for index, finding in enumerate(findings, start=1):
        finding.setdefault("id", f"F-{index:03d}")
    summary = dict.fromkeys(("P0", "P1", "P2", "P3"), 0)
    for finding in findings:
        summary[finding["severity"]] += 1
    report = {
        "schema_version": "1.1.0",
        "report_type": "static-mini-program-review",
        "generator": {"name": "mini-program-ux-pro", "version": "1.0.0"},
        "project": {
            "name": name,
            "path": path,
            "stack": stack,
            "stack_label": stack,
            "stack_detection": "测试",
        },
        "generated_at": generated_at,
        "environment": {
            "mode": "static-code-review",
            "runtime": "not_run",
            "browser_preview": "not_run",
            "wechat_devtools": "not_run",
            "real_device": "not_run",
            "visual_model": "not_run",
        },
        "scope": {
            "files_scanned": len(files),
            "source_files": list(files),
            "pages_declared": 1,
            "pages_found": 1,
            "page_paths": ["pages/home/index"],
            "ruleset": ruleset,
            "scan_policy": {
                "max_file_bytes": 800000,
                "excluded_directories": ["node_modules"],
                "extensions": [".wxml", ".json"],
            },
            "design_system": None if design_fingerprint is None else {
                "path": "design-system/MASTER.json",
                "project": "demo",
                "version": "1.0.0",
                "schema_version": "1.0.0",
                "generated_at": "2026-10-29T09:00:00+00:00",
                "fingerprint": design_fingerprint,
            },
        },
        "executed_checks": [
            {"id": check, "finding_groups": sum(1 for f in findings if f["check_id"] == check), "mode": "static"}
            for check in checks
        ],
        "skipped_checks": [{"id": "runtime-render", "reason": "未运行微信开发者工具"}],
        "findings": findings,
        "summary": summary,
        "coverage": {
            "static_code": True,
            "automated_checks": True,
            "heuristic_checks": True,
            "runtime_checks": False,
            "visual_checks": False,
            "real_device_checks": False,
            "note": "未执行的检查不能视为通过。",
        },
        "next_steps": ["修复后重新运行审查。"],
    }
    validate_report(report)
    return report


class CompareCoreTests(unittest.TestCase):
    def test_identical_reports_are_all_remaining(self) -> None:
        report = make_report([make_finding()])
        result = compare_reports(report, report)
        self.assertEqual(result["summary"]["new"], 0)
        self.assertEqual(result["summary"]["resolved"], 0)
        self.assertEqual(result["summary"]["remaining"], 1)
        self.assertEqual(result["warnings"], [])

    def test_line_drift_does_not_change_identity(self) -> None:
        before = make_report([make_finding(line=3)])
        after = make_report([make_finding(line=44)])
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["remaining"], 1)
        self.assertEqual(result["summary"]["new"], 0)
        self.assertEqual(result["summary"]["resolved"], 0)

    def test_confirmed_resolution(self) -> None:
        before = make_report([make_finding()])
        after = make_report([])
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["resolved"], 1)
        self.assertEqual(result["unconfirmed"], [])
        self.assertEqual(result["resolved"][0]["side"], "before")

    def test_resolution_requires_the_check_to_run(self) -> None:
        before = make_report([make_finding()])
        after = make_report([], checks=("ui-states", "design-tokens"))
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["resolved"], 0)
        self.assertEqual(result["summary"]["unconfirmed"], 1)
        self.assertIn("dom-browser-api", result["unconfirmed"][0]["reason"])

    def test_resolution_requires_the_evidence_file_to_be_scanned(self) -> None:
        before = make_report([make_finding()])
        after = make_report([], files=("app.json",))
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["unconfirmed"], 1)
        self.assertIn("pages/home/index.wxml", result["unconfirmed"][0]["reason"])

    def test_global_check_requires_full_scan_coverage(self) -> None:
        before = make_report([make_finding(
            title="未发现加载状态线索", check_id="ui-states", category="交互状态", severity="P2",
            rule_ids=("ux-loading-states",),
        )])
        after = make_report([], files=("app.json",), checks=("ui-states",))
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["unconfirmed"], 1)
        self.assertIn("少 1 个文件", result["unconfirmed"][0]["reason"])

    def test_new_finding_is_confirmed_when_scope_is_unchanged(self) -> None:
        before = make_report([])
        after = make_report([make_finding()])
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["new"], 1)
        self.assertEqual(result["new_unverified"], [])
        self.assertEqual(result["new"][0]["recommendation"], "改成 view")

    def test_new_finding_in_unscanned_file_is_unverified(self) -> None:
        before = make_report([])
        after = make_report([make_finding(file="pages/new/index.wxml")])
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["new"], 0)
        self.assertEqual(result["summary"]["new_unverified"], 1)
        self.assertIn("不在上次扫描范围", result["new_unverified"][0]["reason"])

    def test_new_global_finding_after_scope_expansion_is_unverified(self) -> None:
        before = make_report([], checks=("ui-states",))
        after = make_report(
            [make_finding(title="未发现加载状态线索", check_id="ui-states", category="交互状态",
                          severity="P2", rule_ids=("ux-loading-states",))],
            files=("app.json", "pages/home/index.wxml", "pages/new/index.wxml"),
            checks=("ui-states",),
        )
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["new"], 0)
        self.assertEqual(result["summary"]["new_unverified"], 1)
        self.assertIn("多 1 个文件", result["new_unverified"][0]["reason"])

    def test_new_finding_for_unrun_check_is_unverified(self) -> None:
        before = make_report([], checks=("ui-states", "design-tokens"))
        after = make_report([make_finding()])
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["new_unverified"], 1)
        self.assertIn("上次未执行检查", result["new_unverified"][0]["reason"])

    def test_same_title_on_different_files_stays_separate(self) -> None:
        files = ("app.json", "pages/a/index.wxml", "pages/b/index.wxml")
        before = make_report([
            make_finding(file="pages/a/index.wxml"),
            make_finding(file="pages/b/index.wxml"),
        ], files=files)
        after = make_report([make_finding(file="pages/a/index.wxml")], files=files)
        result = compare_reports(before, after)
        self.assertEqual(result["summary"]["remaining"], 1)
        self.assertEqual(result["summary"]["resolved"], 1)

    def test_severity_change_is_reported_on_remaining(self) -> None:
        before = make_report([make_finding(severity="P1")])
        after = make_report([make_finding(severity="P3")])
        result = compare_reports(before, after)
        self.assertEqual(result["remaining"][0]["previous_severity"], "P1")
        self.assertEqual(result["remaining"][0]["severity"], "P3")

    def test_ruleset_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ReportError, "规则集不同"):
            compare_reports(make_report([]), make_report([], ruleset="static-2"))

    def test_stack_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(ReportError, "技术栈不同"):
            compare_reports(make_report([]), make_report([], stack="taro"))

    def test_warnings_cover_moved_project_and_order(self) -> None:
        before = make_report([], path="/tmp/demo", name="demo", generated_at="2026-10-29T10:00:00+00:00")
        after = make_report([], path="/tmp/moved", name="demo2", generated_at="2026-10-29T09:00:00+00:00",
                            design_fingerprint="b" * 64)
        result = compare_reports(before, after)
        text = "\n".join(result["warnings"])
        self.assertIn("项目名称不同", text)
        self.assertIn("项目路径不同", text)
        self.assertIn("早于", text)
        self.assertIn("设计系统", text)

    def test_comparison_markdown_sections(self) -> None:
        before = make_report([make_finding(), make_finding(file="pages/b/index.wxml")])
        after = make_report([make_finding(file="pages/b/index.wxml")], files=("app.json", "pages/b/index.wxml"))
        markdown = format_markdown(compare_reports(before, after))
        for text in ("静态审查结果对比", "变化摘要", "已确认修复", "遗留问题", "结论边界", "不能视为通过"):
            self.assertIn(text, markdown)


class ReportContractTests(unittest.TestCase):
    def _load(self, payload: object) -> dict:
        with tempfile.TemporaryDirectory(prefix="mpux-contract-") as temp:
            path = Path(temp) / "review.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return load_report(path)

    def test_valid_report_loads(self) -> None:
        self.assertTrue(self._load(make_report([make_finding()]))["findings"])

    def test_old_schema_version_rejected(self) -> None:
        report = make_report([])
        report["schema_version"] = "1.0.0"
        with self.assertRaisesRegex(ReportError, "1.1.0"):
            self._load(report)

    def test_tampered_fingerprint_rejected(self) -> None:
        report = make_report([make_finding()])
        report["findings"][0]["fingerprint"] = "0" * 64
        with self.assertRaisesRegex(ReportError, "fingerprint"):
            self._load(report)

    def test_wrong_summary_rejected(self) -> None:
        report = make_report([make_finding()])
        report["summary"]["P0"] = 0
        with self.assertRaisesRegex(ReportError, "summary"):
            self._load(report)

    def test_evidence_escaping_project_rejected(self) -> None:
        report = make_report([make_finding()])
        report["findings"][0]["evidence"] = [{"file": "../outside.wxml", "line": 1}]
        with self.assertRaisesRegex(ReportError, "项目内"):
            self._load(report)

    def test_duplicate_json_keys_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-contract-") as temp:
            path = Path(temp) / "review.json"
            path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
            with self.assertRaisesRegex(ReportError, "重复字段"):
                load_report(path)

    def test_nan_and_missing_files_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-contract-") as temp:
            path = Path(temp) / "review.json"
            path.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaises(ReportError):
                load_report(path)
            with self.assertRaisesRegex(ReportError, "无法读取"):
                load_report(Path(temp) / "missing.json")

    def test_unknown_check_reference_rejected(self) -> None:
        report = make_report([make_finding()])
        report["executed_checks"] = [item for item in report["executed_checks"] if item["id"] != "dom-browser-api"]
        with self.assertRaisesRegex(ReportError, "未执行"):
            self._load(report)


class CompareCliTests(unittest.TestCase):
    def _write(self, directory: Path, name: str, report: dict) -> Path:
        path = directory / name
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_cli_roundtrip_json_and_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-compare-") as temp:
            directory = Path(temp) / "审查 报告"
            directory.mkdir()
            before = self._write(directory, "before.json", make_report([]))
            after = self._write(directory, "after.json", make_report([make_finding(severity="P1")]))
            process = run_script("review_compare.py", str(before), str(after), "--json", "--fail-on-new", "P1")
            self.assertEqual(process.returncode, 1, process.stderr)
            payload = load_json_output(process)
            self.assertEqual(payload["summary"]["new"], 1)
            self.assertEqual(payload["new"][0]["severity"], "P1")

    def test_cli_gate_none_and_threshold(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-compare-") as temp:
            directory = Path(temp)
            before = self._write(directory, "before.json", make_report([]))
            after = self._write(directory, "after.json", make_report([make_finding(severity="P2")]))
            self.assertEqual(run_script("review_compare.py", str(before), str(after)).returncode, 0)
            process = run_script("review_compare.py", str(before), str(after), "--fail-on-new", "P0")
            self.assertEqual(process.returncode, 0, process.stderr)

    def test_cli_output_cannot_overwrite_input(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-compare-") as temp:
            directory = Path(temp)
            before = self._write(directory, "before.json", make_report([]))
            after = self._write(directory, "after.json", make_report([]))
            original = before.read_text(encoding="utf-8")
            process = run_script("review_compare.py", str(before), str(after), "--json", "--output", str(before))
            self.assertEqual(process.returncode, 2)
            self.assertIn("不能覆盖输入报告", process.stderr)
            self.assertEqual(before.read_text(encoding="utf-8"), original)

    def test_cli_output_write_failure_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-compare-") as temp:
            directory = Path(temp)
            before = self._write(directory, "before.json", make_report([]))
            after = self._write(directory, "after.json", make_report([]))
            output_dir = directory / "out"
            output_dir.mkdir()
            process = run_script("review_compare.py", str(before), str(after), "--json", "--output", str(output_dir))
            self.assertEqual(process.returncode, 2)
            self.assertIn("无法写入", process.stderr)
            self.assertNotIn("Traceback", process.stderr)

    def test_cli_invalid_report_has_no_traceback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-compare-") as temp:
            directory = Path(temp)
            before = self._write(directory, "before.json", make_report([]))
            broken = directory / "broken.json"
            broken.write_text("[]", encoding="utf-8")
            process = run_script("review_compare.py", str(before), str(broken), "--json")
            self.assertEqual(process.returncode, 2)
            self.assertIn("无效审查报告", process.stderr)
            self.assertNotIn("Traceback", process.stderr)

    def test_real_fix_and_new_regression_are_classified(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-compare-fix-") as temp:
            project = Path(temp) / "app"
            shutil.copytree(FIXTURES / "wechat-native", project)
            before = audit_project(project)
            detail = project / "pages" / "detail"
            (detail / "index.wxml").write_text("<view>详情</view>", encoding="utf-8")
            after = audit_project(project)
            result = compare_reports(before, after)
        resolved = [entry["title"] for entry in result["resolved"]]
        self.assertIn("声明的页面缺少模板文件：pages/detail/index", resolved)
        new_titles = [entry["title"] for entry in result["new"]]
        self.assertIn("页面缺少逻辑文件：pages/detail/index", new_titles)
        self.assertFalse(any("缺少模板文件" in title for title in new_titles))

    def test_real_audit_reports_compare_cleanly(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-compare-") as temp:
            directory = Path(temp)
            generated = []
            for name in ("before.json", "after.json"):
                process = run_script(
                    "audit_mini_program.py",
                    "--path", str(FIXTURES / "wechat-native"),
                    "--format", "json",
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                generated.append(self._write(directory, name, load_json_output(process)))
            process = run_script("review_compare.py", str(generated[0]), str(generated[1]), "--json", "--fail-on-new", "P0")
            self.assertEqual(process.returncode, 0, process.stderr)
            payload = load_json_output(process)
            self.assertEqual(payload["summary"]["new"], 0)
            self.assertEqual(payload["summary"]["resolved"], 0)
            self.assertGreater(payload["summary"]["remaining"], 0)


if __name__ == "__main__":
    unittest.main()
