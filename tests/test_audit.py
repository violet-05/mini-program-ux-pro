from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import FIXTURES, ROOT, load_json_output, run_script  # noqa: E402

from audit_mini_program import (  # noqa: E402
    AuditError,
    _detect_stack,
    _find_files,
    _strip_json_comments,
    audit_project,
    format_markdown,
)


class AuditTests(unittest.TestCase):
    def test_native_fixture_detects_issues(self) -> None:
        report = audit_project(FIXTURES / "wechat-native")
        self.assertEqual(report["project"]["stack"], "wechat-native")
        self.assertEqual(report["scope"]["pages_declared"], 2)
        self.assertEqual(report["scope"]["pages_found"], 1)
        self.assertGreaterEqual(report["summary"]["P0"], 1)
        self.assertGreaterEqual(report["summary"]["P1"], 1)
        titles = {finding["title"] for finding in report["findings"]}
        self.assertIn("声明的页面缺少模板文件：pages/detail/index", titles)
        self.assertIn("WXML 使用浏览器 HTML 标签", titles)
        self.assertIn("WXML 使用浏览器/Vue 事件语法", titles)
        self.assertIn("固定底部元素未发现安全区处理", titles)
        self.assertIn("检测到浏览器 DOM/BOM API", titles)
        self.assertIn("启用 customTabBar 但未找到 custom-tab-bar 组件", titles)
        self.assertIn("未发现加载状态线索", titles)
        self.assertIn("未发现空状态线索", titles)
        self.assertIn("未发现错误/重试状态线索", titles)
        self.assertIn("存在过小字号", titles)
        self.assertIn("样式中存在设计系统未登记的硬编码颜色", titles)

    def test_fingerprints_are_stable_between_runs(self) -> None:
        first = audit_project(FIXTURES / "wechat-native")
        second = audit_project(FIXTURES / "wechat-native")
        self.assertEqual(
            {finding["fingerprint"] for finding in first["findings"]},
            {finding["fingerprint"] for finding in second["findings"]},
        )
        self.assertEqual(len({finding["fingerprint"] for finding in first["findings"]}), len(first["findings"]))

    def test_check_ids_match_executed_checks(self) -> None:
        report = audit_project(FIXTURES / "wechat-native")
        executed = {item["id"] for item in report["executed_checks"]}
        for finding in report["findings"]:
            self.assertIn(finding["check_id"], executed)
        self.assertEqual(report["schema_version"], "1.1.0")
        self.assertTrue(report["scope"]["source_files"])
        self.assertEqual(report["scope"]["files_scanned"], len(report["scope"]["source_files"]))

    def test_report_environment_and_coverage(self) -> None:
        report = audit_project(FIXTURES / "wechat-native")
        self.assertEqual(report["environment"]["mode"], "static-code-review")
        self.assertEqual(report["environment"]["runtime"], "not_run")
        self.assertEqual(report["environment"]["real_device"], "not_run")
        self.assertFalse(report["coverage"]["runtime_checks"])
        self.assertFalse(report["coverage"]["visual_checks"])
        self.assertTrue(report["coverage"]["static_code"])
        self.assertTrue(report["skipped_checks"])
        self.assertTrue(any(item["id"] == "runtime-render" for item in report["skipped_checks"]))

    def test_findings_have_evidence_and_taxonomy(self) -> None:
        report = audit_project(FIXTURES / "wechat-native")
        self.assertTrue(report["findings"])
        for finding in report["findings"]:
            self.assertRegex(finding["id"], r"^F-\d{3}$")
            self.assertIn(finding["severity"], {"P0", "P1", "P2", "P3"})
            self.assertIn(finding["verification"], {"automated", "rule-assisted", "needs-manual"})
            self.assertIn(finding["confidence"], {"high", "medium", "low"})
            self.assertTrue(finding["evidence"])
            self.assertTrue(finding["rule_ids"])
            self.assertTrue(finding["recommendation"])
        severities = [finding["severity"] for finding in report["findings"]]
        self.assertEqual(severities, sorted(severities, key=lambda value: int(value[1])))

    def test_other_stacks_detected(self) -> None:
        cases = {
            "uni-app": "uni-app",
            "taro": "taro",
            "browser-prototype": "browser-prototype",
        }
        for directory, stack in cases.items():
            report = audit_project(FIXTURES / directory)
            self.assertEqual(report["project"]["stack"], stack)
            if stack in {"uni-app", "taro"}:
                self.assertEqual(report["summary"]["P0"], 0)
        browser = audit_project(FIXTURES / "browser-prototype")
        self.assertTrue(any("浏览器原型" in item["title"] for item in browser["findings"]))

    def test_markdown_report(self) -> None:
        report = audit_project(FIXTURES / "wechat-native")
        markdown = format_markdown(report)
        self.assertIn("小程序静态审查报告", markdown)
        self.assertIn("未执行", markdown)
        self.assertIn("F-001", markdown)
        self.assertIn("不能证明", markdown)
        self.assertIn("P0", markdown)

    def test_jsonc_trailing_commas_preserve_strings(self) -> None:
        cleaned = _strip_json_comments('{"a": "x,}", "b": [1, 2,],}')
        self.assertEqual(json.loads(cleaned), {"a": "x,}", "b": [1, 2]})
        cleaned = _strip_json_comments('{\n // comment\n "a": "http://x,]",\n}')
        self.assertEqual(json.loads(cleaned), {"a": "http://x,]"})

    def test_design_system_found_in_parent(self) -> None:
        report = audit_project(ROOT / "verification" / "mini-program")
        self.assertIsNotNone(report["scope"].get("design_system"))
        self.assertFalse(
            any("未检测到设计系统" in finding["title"] for finding in report["findings"])
        )

    def test_explicit_design_system(self) -> None:
        report = audit_project(
            ROOT / "verification" / "mini-program",
            ROOT / "verification" / "design-system",
        )
        self.assertIsNotNone(report["scope"].get("design_system"))

    def test_invalid_explicit_design_system(self) -> None:
        with self.assertRaises(AuditError):
            audit_project(
                ROOT / "verification" / "mini-program",
                ROOT / "definitely-not-there",
            )

    def test_malformed_design_system_is_rejected(self) -> None:
        valid = {"project": {"name": "Test"}, "tokens": {"colors": {"brand": "#FFFFFF"}}}
        invalid = [None, [], {}, {**valid, "project": []},
                   {**valid, "project": {"name": 1}}, {**valid, "tokens": None},
                   {**valid, "tokens": {"colors": []}}, {**valid, "tokens": {"colors": {"brand": 1}}},
                   {**valid, "generator": "bad"}, {**valid, "generator": {"version": []}},
                   {**valid, "schema_version": []}, {**valid, "generated_at": {}}]
        for payload in invalid:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory(prefix="mpux-master-") as temp:
                master = Path(temp) / "MASTER.json"
                master.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(AuditError):
                    audit_project(FIXTURES / "wechat-native", master)

    def test_invalid_utf8_design_system_reports_error(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-master-") as temp:
            master = Path(temp) / "MASTER.json"
            master.write_bytes(b"\xff\xfe")
            process = run_script("audit_mini_program.py", "--path", str(FIXTURES / "wechat-native"),
                                 "--design-system", str(master), "--format", "json")
        self.assertEqual(process.returncode, 2)
        self.assertIn("设计系统无法读取", process.stderr)
        self.assertNotIn("Traceback", process.stderr)

    def test_automatic_discovery_does_not_hide_invalid_master(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-master-") as temp:
            root = Path(temp)
            (root / "design-system").mkdir()
            (root / "design-system" / "MASTER.json").write_text("[]", encoding="utf-8")
            with self.assertRaises(AuditError):
                audit_project(root)

    def test_cli_design_system_option(self) -> None:
        process = run_script(
            "audit_mini_program.py",
            "--path",
            str(ROOT / "verification" / "mini-program"),
            "--design-system",
            str(ROOT / "verification" / "design-system"),
            "--format",
            "json",
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        payload = load_json_output(process)
        self.assertTrue(payload["scope"]["design_system"])

    def test_cli_json_and_gate(self) -> None:
        process = run_script(
            "audit_mini_program.py",
            "--path",
            str(FIXTURES / "wechat-native"),
            "--format",
            "json",
            "--fail-on",
            "P1",
        )
        self.assertEqual(process.returncode, 1, process.stderr)
        payload = load_json_output(process)
        self.assertEqual(payload["project"]["stack"], "wechat-native")
        self.assertGreater(payload["summary"]["P1"], 0)
        clean = run_script(
            "audit_mini_program.py",
            "--path",
            str(FIXTURES / "uni-app"),
            "--format",
            "json",
            "--fail-on",
            "P1",
        )
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertEqual(load_json_output(clean)["summary"], {"P0": 0, "P1": 0, "P2": 0, "P3": 0})

    def test_cli_output_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-audit-") as temp:
            output = Path(temp) / "review.json"
            process = run_script(
                "audit_mini_program.py",
                "--path",
                str(FIXTURES / "wechat-native"),
                "--format",
                "json",
                "--output",
                str(output),
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_type"], "static-mini-program-review")

    def test_tool_and_dependency_directories_do_not_pollute_audit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-scan-") as temp:
            root = Path(temp)
            for name in (".claude", ".qoder", ".cursor", ".codex", "node_modules", "dist"):
                directory = root / name / "nested"
                directory.mkdir(parents=True)
                (directory / "index.html").write_text("<div>sample</div>", encoding="utf-8")
                (directory / "index.js").write_text("document.querySelector('div')", encoding="utf-8")
            self.assertEqual(_find_files(root), [])
            self.assertEqual(_detect_stack(root)[0], "unknown")
            source = root / "index.js"
            source.write_text("Page({})", encoding="utf-8")
            self.assertEqual(_find_files(root), [source])

    def test_scan_limit_never_returns_a_partial_success(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-scan-") as temp:
            root = Path(temp)
            source = root / "index.js"
            source.write_text("Page({})", encoding="utf-8")
            with patch("audit_mini_program._walk_project_files", return_value=iter([source] * 4001)):
                with self.assertRaisesRegex(AuditError, "4000"):
                    _find_files(root)

    def test_nonexistent_path(self) -> None:
        process = run_script(
            "audit_mini_program.py",
            "--path",
            str(ROOT / "definitely-not-there"),
            "--format",
            "json",
        )
        self.assertEqual(process.returncode, 2)
        self.assertIn("不存在", process.stderr)

    def test_project_with_miniprogram_root_detected(self) -> None:
        report = audit_project(ROOT / "verification")
        self.assertEqual(report["project"]["stack"], "wechat-native")
        self.assertGreaterEqual(report["scope"]["pages_declared"], 3)
        self.assertTrue(report["scope"]["design_system"])
        self.assertEqual(report["summary"], {"P0": 0, "P1": 0, "P2": 0, "P3": 0})

    def test_no_finding_from_valid_canvas_tag(self) -> None:
        # <canvas> 是小程序原生组件，不应被浏览器 HTML 标签规则误伤。
        with tempfile.TemporaryDirectory(prefix="mpux-canvas-") as temp:
            project = Path(temp) / "project"
            page = project / "pages" / "home"
            page.mkdir(parents=True)
            (project / "project.config.json").write_text('{"miniprogramRoot":"./"}', encoding="utf-8")
            (project / "app.json").write_text(
                '{"pages":["pages/home/index"],"window":{"navigationStyle":"default"}}',
                encoding="utf-8",
            )
            (page / "index.wxml").write_text(
                '<view><canvas canvas-id="chart"></canvas><view>加载中 暂无内容 加载失败 重试</view></view>',
                encoding="utf-8",
            )
            (page / "index.js").write_text("Page({})", encoding="utf-8")
            (page / "index.json").write_text("{}", encoding="utf-8")
            (page / "index.wxss").write_text(".chart { width: 300rpx; height: 200rpx; }", encoding="utf-8")
            report = audit_project(project)
            html_findings = [
                item for item in report["findings"] if "浏览器 HTML 标签" in item["title"]
            ]
            self.assertEqual(html_findings, [])


if __name__ == "__main__":
    unittest.main()