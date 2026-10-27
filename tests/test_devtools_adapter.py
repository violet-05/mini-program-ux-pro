from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT  # noqa: E402

from devtools_adapter import (  # noqa: E402
    DevToolsUnavailable,
    check_node_dependency,
    classify_status,
    find_cli,
    probe,
    run_suite,
)


class DevToolsAdapterTests(unittest.TestCase):
    def test_classify_service_port_disabled(self) -> None:
        status, message = classify_status(
            "[error] IDE service port disabled. To use CLI Call, please enter y",
            0,
        )
        self.assertEqual(status, "service_port_disabled")
        self.assertIn("服务端口", message)

    def test_classify_chinese_service_port_disabled(self) -> None:
        status, _ = classify_status("工具的服务端口已关闭。要使用命令行调用工具", 0)
        self.assertEqual(status, "service_port_disabled")

    def test_classify_ready(self) -> None:
        status, _ = classify_status('{"login":true}\n✔ islogin', 0)
        self.assertEqual(status, "ready")

    def test_classify_login_required(self) -> None:
        status, _ = classify_status("not login", 0)
        self.assertEqual(status, "login_required")

    def test_find_cli_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-cli-") as temp:
            path = Path(temp) / "cli.bat"
            path.write_text("@echo off\n", encoding="utf-8")
            found = find_cli(str(path))
            self.assertIsNotNone(found)
            self.assertEqual(found.resolve(), path.resolve())
        self.assertIsNone(find_cli(str(Path(temp) / "missing.bat")))

    def test_probe_uses_cli_output(self) -> None:
        fake = subprocess.CompletedProcess(
            args=["cli"],
            returncode=0,
            stdout="",
            stderr="IDE service port disabled",
        )
        with patch("devtools_adapter._run", return_value=fake):
            result = probe(Path("C:/fake/cli.bat"))
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "service_port_disabled")
        self.assertTrue(result["remediation"])

    def test_run_suite_stops_when_service_unavailable(self) -> None:
        with patch(
            "devtools_adapter.probe",
            return_value={"ok": False, "status": "service_port_disabled", "message": "off"},
        ):
            with self.assertRaises(DevToolsUnavailable):
                run_suite(Path("C:/fake/cli.bat"))

    def test_node_dependency_report(self) -> None:
        dependency = check_node_dependency()
        self.assertIn("node", dependency)
        self.assertIn("npm", dependency)
        self.assertIn("automator_installed", dependency)

    def test_verify_script_syntax(self) -> None:
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js not installed")
        result = subprocess.run(
            [node, "--check", str(ROOT / "verification" / "devtools" / "verify.cjs")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (ROOT / "verification" / "devtools" / "verify.cjs").read_text(encoding="utf-8")
        self.assertIn("automator.connect", text)
        self.assertIn("miniProgram.screenshot", text)
        self.assertIn("--trust-project", text)

    def test_runtime_evidence_exists_and_matches_screenshots(self) -> None:
        results_path = ROOT / "verification" / "artifacts" / "results.json"
        if not results_path.exists():
            self.skipTest("Runtime evidence not generated yet")
        report = json.loads(results_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "passed")
        self.assertGreaterEqual(len(report["checks"]), 20)
        self.assertTrue(report["screenshots"])
        self.assertFalse(report.get("console_error_count"))
        self.assertFalse(report.get("exceptions"))
        for screenshot in report["screenshots"]:
            self.assertTrue((ROOT / screenshot["path"]).exists(), screenshot["path"])


if __name__ == "__main__":
    unittest.main()