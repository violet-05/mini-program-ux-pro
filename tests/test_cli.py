from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import FIXTURES, ROOT, load_json_output, run_cli
from doctor import diagnose
from validate_skill import _check_text_files

CLI = str(ROOT / "mpux.py")


class UnifiedCliTests(unittest.TestCase):
    def test_help_and_subcommand_help(self) -> None:
        for args in ([], ["--help"], *([command, "--help"] for command in (
            "doctor", "search", "design", "audit", "compare", "install", "validate", "verify", "visual",
        ))):
            with self.subTest(args=args):
                process = run_cli(CLI, *args)
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertIn("usage:", process.stdout)

    def test_version_from_metadata(self) -> None:
        version = json.loads((ROOT / "skill.json").read_text(encoding="utf-8"))["version"]
        self.assertEqual(run_cli(CLI, "--version").stdout.strip(), f"MPUX Pro {version}")

    def test_invalid_command_and_arguments(self) -> None:
        for args in (["unknown"], ["search", "--not-an-option"], ["doctor", "--path", "."], ["--version", "search"]):
            with self.subTest(args=args):
                process = run_cli(CLI, *args)
                self.assertEqual(process.returncode, 2)
                self.assertNotIn("Traceback", process.stderr)

    def test_search_from_unrelated_working_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-cli-") as temp:
            process = run_cli(CLI, "search", "商品卡片", "--domain", "components", "--json", "-n", "1", cwd=Path(temp))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(load_json_output(process)["results"][0]["id"], "comp-product-card")

    def test_design_three_stacks_and_preserve_existing_master(self) -> None:
        for stack in ("wechat-native", "uni-app", "taro"):
            with self.subTest(stack=stack), tempfile.TemporaryDirectory(prefix="mpux-design-") as temp:
                output = Path(temp) / "我的设计"
                args = ("design", "--product", "音乐播放器小程序", "--stack", stack,
                        "--output", str(output), "--format", "both")
                result = run_cli(CLI, *args, cwd=Path(temp))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((output / "MASTER.json").is_file())
                self.assertTrue((output / ("tokens.wxss" if stack == "wechat-native" else "tokens.scss")).is_file())
                master = output / "MASTER.md"
                master.write_text("用户保留内容", encoding="utf-8")
                again = run_cli(CLI, *args, cwd=Path(temp))
                self.assertEqual(again.returncode, 0, again.stderr)
                self.assertEqual(master.read_text(encoding="utf-8"), "用户保留内容")

    def test_audit_preserves_gate_exit_code(self) -> None:
        result = run_cli(CLI, "audit", "--path", str(FIXTURES / "wechat-native"), "--format", "json", "--fail-on", "P1")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertGreater(load_json_output(result)["summary"]["P0"], 0)

    def test_doctor_json_and_scope(self) -> None:
        result = run_cli(CLI, "doctor", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = load_json_output(result)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["scope"], "local-installation")
        self.assertIn("iOS/Android 真机", payload["not_checked"])
        self.assertTrue(payload["warnings"])

    def test_installed_cli_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-product-") as temp:
            project = Path(temp) / "我的小程序"
            shutil.copytree(FIXTURES / "uni-app", project)
            installed = run_cli(CLI, "install", "--project", str(project), "--json")
            self.assertEqual(installed.returncode, 0, installed.stderr)
            target = Path(load_json_output(installed)["target"])
            entry = str(target / "mpux.py")
            for command in (["doctor", "--json"], ["search", "商品卡片", "--domain", "components", "--json"]):
                process = run_cli("-I", entry, *command, cwd=project)
                self.assertEqual(process.returncode, 0, process.stderr)
                payload = load_json_output(process)
                if command[0] == "doctor":
                    self.assertEqual(Path(payload["root"]), target)
                    self.assertTrue(payload["ok"])
                else:
                    self.assertEqual(payload["results"][0]["id"], "comp-product-card")
            generated = run_cli("-I", entry, "design", "--product", "音乐播放器小程序", "--stack", "uni-app",
                                "--output", "design-system", "--format", "both", cwd=project)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertTrue((project / "design-system" / "tokens.scss").is_file())
            audited = run_cli("-I", entry, "audit", "--path", ".", "--format", "json", cwd=project)
            self.assertEqual(audited.returncode, 0, audited.stderr)
            report = load_json_output(audited)
            self.assertEqual(report["project"]["stack"], "uni-app")
            self.assertTrue(report["scope"]["design_system"])
            self.assertTrue(all(
                not evidence["file"].replace("\\", "/").startswith(".claude/")
                for finding in report["findings"] for evidence in finding["evidence"]
            ))
            self.assertFalse((target / "promo-video").exists())

    def test_validate_rejects_user_project_with_guidance(self) -> None:
        result = run_cli(CLI, "validate", "--path", str(FIXTURES / "wechat-native"), "--json")
        self.assertEqual(result.returncode, 2)
        payload = load_json_output(result)
        self.assertFalse(payload["ok"])
        self.assertIn("audit", payload["error"])
        self.assertNotIn("Traceback", result.stderr)

    def test_gbk_entrypoint_and_doctor(self) -> None:
        env = {**os.environ, "PYTHONIOENCODING": "gbk"}
        env.pop("PYTHONUTF8", None)
        for args in (["--help"], ["doctor", "--json"], ["search", "商品卡片", "--json"]):
            with self.subTest(args=args):
                result = subprocess.run([sys.executable, CLI, *args], capture_output=True, env=env, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                text = result.stdout.decode("utf-8")
                self.assertNotIn("\ufffd", text)


class DoctorTests(unittest.TestCase):
    def test_document_validation_excludes_independent_projects(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-docs-") as temp:
            root = Path(temp)
            (root / "README.md").write_text("Valid documentation", encoding="utf-8")
            for directory in ("promo-video", "node_modules", ".qoder", ".claude", ".cursor"):
                path = root / directory
                path.mkdir()
                (path / "README.md").write_text("[missing](absent.md)", encoding="utf-8")
            errors, warnings = [], []
            self.assertEqual(_check_text_files(root, errors, warnings), 1)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_installation_does_not_start_subprocess(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-doctor-") as temp, patch("doctor.subprocess.run") as run:
            result = diagnose(Path(temp))
        self.assertFalse(result["ok"])
        self.assertTrue(all(check["remedy"] for check in result["checks"] if not check["passed"]))
        run.assert_not_called()

    def test_corrupt_metadata(self) -> None:
        for metadata in ([], None, {"name": "other", "version": "1.0.0"}, {"name": "mini-program-ux-pro", "version": []}):
            with self.subTest(metadata=metadata), tempfile.TemporaryDirectory(prefix="mpux-doctor-") as temp:
                root = Path(temp)
                (root / "skill.json").write_text(json.dumps(metadata), encoding="utf-8")
                shutil.copy2(ROOT / "package.json", root / "package.json")
                result = diagnose(root)
                self.assertFalse(result["ok"])
                self.assertFalse(next(item for item in result["checks"] if item["name"] == "版本信息")["passed"])

    def test_failed_smoke_is_reported(self) -> None:
        cases = (
            subprocess.CompletedProcess([], 1, "", "检索失败"),
            subprocess.CompletedProcess([], 0, "null", ""),
            subprocess.CompletedProcess([], 0, '{"results": [null]}', ""),
            subprocess.CompletedProcess([], 0, '{"results": [{"id": "wrong"}]}', ""),
        )
        for process in cases:
            with self.subTest(stdout=process.stdout), patch("doctor.subprocess.run", return_value=process):
                result = diagnose(ROOT)
            self.assertFalse(result["ok"])
            self.assertTrue(result["checks"][-1]["remedy"])
        with patch("doctor.subprocess.run", side_effect=subprocess.TimeoutExpired("search", 30)):
            self.assertFalse(diagnose(ROOT)["ok"])

    def test_invalid_data_encoding_is_reported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-doctor-") as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "products.csv").write_bytes(b"\xff\xfe")
            result = diagnose(root)
        self.assertFalse(result["ok"])
        self.assertFalse(next(item for item in result["checks"] if item["name"] == "知识库")["passed"])


if __name__ == "__main__":
    unittest.main()
