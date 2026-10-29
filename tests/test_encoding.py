from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CLI_SCRIPTS = (
    "doctor.py",
    "search.py",
    "generate_design_system.py",
    "audit_mini_program.py",
    "validate_data.py",
    "validate_skill.py",
    "validate_project.py",
    "install_skill.py",
    "visual_review_adapter.py",
    "devtools_adapter.py",
)


def run_with_gbk_stdio(script: str, *args: str) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "gbk"
    env.pop("PYTHONUTF8", None)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=ROOT,
        capture_output=True,
        env=env,
        timeout=120,
    )


class EncodingRegressionTests(unittest.TestCase):
    def assert_utf8_stdout(self, process: subprocess.CompletedProcess[bytes]) -> str:
        stderr = process.stderr.decode("utf-8", errors="replace")
        self.assertEqual(process.returncode, 0, stderr)
        try:
            text = process.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            self.fail(f"stdout 不是合法 UTF-8：{exc}")
        self.assertNotIn("\ufffd", text)
        return text

    def test_data_validator_emits_utf8(self) -> None:
        text = self.assert_utf8_stdout(run_with_gbk_stdio("validate_data.py", "--json"))
        self.assertTrue(json.loads(text)["ok"])

    def test_skill_validator_emits_utf8(self) -> None:
        text = self.assert_utf8_stdout(run_with_gbk_stdio("validate_skill.py", "--json"))
        self.assertTrue(json.loads(text)["ok"])

    def test_visual_review_response_emits_utf8(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-encoding-") as temp:
            response = Path(temp) / "response.json"
            response.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "issues": [],
                        "limitations": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            text = self.assert_utf8_stdout(
                run_with_gbk_stdio(
                    "visual_review_adapter.py",
                    "validate-response",
                    "--response",
                    str(response),
                )
            )
        self.assertIn("契约通过", text)

    def test_all_cli_help_emits_utf8(self) -> None:
        for script in CLI_SCRIPTS:
            with self.subTest(script=script):
                self.assert_utf8_stdout(run_with_gbk_stdio(script, "--help"))

    def test_project_validator_emits_utf8(self) -> None:
        text = self.assert_utf8_stdout(
            run_with_gbk_stdio("validate_project.py", "--path", ".", "--json")
        )
        payload = json.loads(text)
        self.assertTrue(payload["ok"], payload)


if __name__ == "__main__":
    unittest.main()
