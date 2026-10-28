from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT, load_json_output, run_script  # noqa: E402

from install_skill import SKILL_NAME, install  # noqa: E402
from validate_skill import REQUIRED_FILES, _read_frontmatter, validate  # noqa: E402


class SkillValidationTests(unittest.TestCase):
    def test_required_files_exist(self) -> None:
        missing = [relative for relative in REQUIRED_FILES if not (ROOT / relative).exists()]
        self.assertEqual(missing, [])

    def test_frontmatter(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter, _ = _read_frontmatter(text)
        self.assertEqual(frontmatter.get("name"), "mini-program-ux-pro")
        self.assertIn("微信小程序", frontmatter.get("description", ""))
        self.assertGreaterEqual(len(frontmatter.get("description", "")), 80)

    def test_current_skill_passes_validation(self) -> None:
        result = validate(ROOT)
        self.assertTrue(result["ok"], result["errors"])
        self.assertGreater(result["markdown_files_checked"], 30)
        self.assertGreater(result["documented_script_commands"], 0)

    def test_skill_json_matches(self) -> None:
        metadata = json.loads((ROOT / "skill.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["name"], "mini-program-ux-pro")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertEqual(metadata["license"], "MIT")
        self.assertFalse(metadata["requirements"]["network"])
        self.assertFalse(metadata["requirements"]["apiKey"])
        self.assertEqual(metadata["entry"], "SKILL.md")

    def test_all_referenced_cli_help(self) -> None:
        for script in (
            "search.py",
            "generate_design_system.py",
            "audit_mini_program.py",
            "validate_data.py",
            "validate_skill.py",
            "validate_project.py",
            "install_skill.py",
            "visual_review_adapter.py",
            "devtools_adapter.py",
        ):
            process = run_script(script, "--help")
            self.assertEqual(process.returncode, 0, f"{script}: {process.stderr}")

    def test_search_cli_from_docs(self) -> None:
        process = run_script(
            "search.py",
            "商品卡片",
            "--domain",
            "components",
            "--json",
            "-n",
            "1",
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        payload = load_json_output(process)
        self.assertEqual(payload["results"][0]["id"], "comp-product-card")

    def test_install_to_temp_with_smoke_test(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-install-") as temp:
            target_base = Path(temp) / "skills"
            result = install(target_base, force=True)
            self.assertEqual(result["status"], "installed")
            target = target_base / SKILL_NAME
            self.assertTrue((target / "SKILL.md").exists())
            self.assertTrue((target / "scripts" / "search.py").exists())
            self.assertTrue((target / "data" / "products.csv").exists())
            self.assertEqual(result["smoke_test"]["top_result"], "comp-product-card")
            self.assertFalse((target / "verification" / "devtools" / "node_modules").exists())
            self.assertFalse((target / ".github").exists())
            # 安装后的 Skill 可以独立执行检索
            process = run_script(
                "search.py",
                "底部安全区域",
                "--domain",
                "mini-program",
                "--json",
                "-n",
                "1",
                cwd=target,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            payload = load_json_output(process)
            self.assertEqual(payload["results"][0]["id"], "mp-safe-area")
            # 不覆盖已存在目标
            with self.assertRaises(Exception):
                install(target_base, force=False)

    def test_install_refuses_self_target(self) -> None:
        with self.assertRaises(Exception):
            install(ROOT, force=True)

    def test_no_network_imports_in_core(self) -> None:
        for name in ("mpux_core.py", "search.py", "design_system.py", "validate_data.py"):
            text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            for forbidden in ("import requests", "import httpx", "urllib.request"):
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()