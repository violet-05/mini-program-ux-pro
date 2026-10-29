from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT, load_json_output, run_cli, run_script  # noqa: E402

import install_skill as installer  # noqa: E402
from install_skill import IGNORE, SKILL_NAME, InstallError, install  # noqa: E402
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
            target_base = Path(temp) / "skills with spaces"
            result = install(target_base)
            self.assertEqual(result["status"], "installed")
            target = target_base / SKILL_NAME
            self.assertTrue((target / "mpux.py").is_file())
            self.assertEqual([name for name in REQUIRED_FILES if not (target / name).is_file()], [])
            self.assertEqual(result["smoke_test"]["top_result"], "comp-product-card")
            for relative in ("promo-video", ".github", ".qoder", ".cursor", "verification/devtools/node_modules"):
                self.assertFalse((target / relative).exists(), relative)
            process = run_cli(
                "-B",
                str(target / "scripts" / "search.py"),
                "底部安全区域",
                "--domain",
                "mini-program",
                "--json",
                "-n",
                "1",
                cwd=Path(temp),
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            payload = load_json_output(process)
            self.assertEqual(payload["results"][0]["id"], "mp-safe-area")
            process = run_cli(
                "-B", str(target / "scripts" / "validate_skill.py"), "--json", cwd=Path(temp),
            )
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertTrue(load_json_output(process)["ok"])
            process = run_cli(
                "-B", str(target / "scripts" / "install_skill.py"),
                "--target", str(Path(temp) / "second skills"), "--json", cwd=Path(temp),
            )
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            second = load_json_output(process)
            self.assertEqual(Path(second["source"]), target)
            self.assertEqual(second["smoke_test"]["top_result"], "comp-product-card")
            quoted_entry = installer._quoted(str(target / "mpux.py"))
            self.assertIn(quoted_entry + " doctor", result["commands"]["doctor"])
            self.assertIn(quoted_entry + " search ", result["commands"]["search"])
            with self.assertRaises(InstallError):
                install(target_base)

    def test_install_refuses_source_directory(self) -> None:
        with self.assertRaisesRegex(InstallError, "源目录内"):
            install(ROOT, force=True)

    def test_no_network_imports_in_core(self) -> None:
        for name in ("mpux_core.py", "search.py", "design_system.py", "validate_data.py"):
            text = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            for forbidden in ("import requests", "import httpx", "urllib.request"):
                self.assertNotIn(forbidden, text)


class InstallSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="mpux-install-safety-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.source = self.directory / "source"
        self.target_base = self.directory / "skills"
        self.target = self.target_base / SKILL_NAME
        files = {
            "SKILL.md": "---\nname: mini-program-ux-pro\n---\n",
            "skill.json": json.dumps({"name": SKILL_NAME}),
            "mpux.py": "raise SystemExit(0)\n",
            "scripts/search.py": "",
            "data/products.csv": "product_id,name\nproduct-test,Test\n",
        }
        for relative, content in files.items():
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.valid_payload = {"count": 1, "results": [{"id": "comp-product-card"}]}
        self.set_smoke_output(json.dumps(self.valid_payload))
        patcher = mock.patch.object(installer, "ROOT", self.source)
        patcher.start()
        self.addCleanup(patcher.stop)

    def set_smoke_output(self, output: str, exit_code: int = 0) -> None:
        (self.source / "scripts" / "search.py").write_text(
            f"print({output!r})\nraise SystemExit({exit_code})\n", encoding="utf-8",
        )

    def snapshot(self, root: Path) -> dict:
        return {
            str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
            for path in root.rglob("*")
        }

    def existing_install(self) -> dict:
        install(self.target_base)
        (self.target / "old-only.txt").write_bytes(b"keep the previous installation\x00")
        return self.snapshot(self.target)

    def assert_old_unchanged(self, before: dict) -> None:
        self.assertEqual(self.snapshot(self.target), before)
        self.assertEqual(list(self.target_base.iterdir()), [self.target])

    def test_ignores_promo_and_tool_caches_but_keeps_validation_dependencies(self) -> None:
        excluded = (
            "promo-video", ".github", ".git", ".claude", ".qoder", ".cursor", ".codex",
            ".idea", ".vscode", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
            ".cache", ".venv", "node_modules", "verification/devtools/node_modules",
        )
        for relative in excluded:
            path = self.source / relative / "out" / "asset.bin"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"not distributable")
        private_files = (".env", ".env.local", "verification/project.private.config.json")
        for relative in private_files:
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("local-only", encoding="utf-8")
        retained = (
            "verification/devtools/verify.cjs", "verification/artifacts/runtime-run.log",
            "schemas/review-report.schema.json", "tests/test_search.py", "docs/usage.md",
        )
        for relative in retained:
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("keep", encoding="utf-8")
        install(self.target_base)
        for relative in (*excluded, *private_files):
            self.assertFalse((self.target / relative).exists(), relative)
        for relative in retained:
            self.assertEqual((self.target / relative).read_text(encoding="utf-8"), "keep")
        self.assertIn("promo-video", IGNORE(str(self.source), ["promo-video"]))

    def test_normalizes_relative_target(self) -> None:
        previous = Path.cwd()
        os.chdir(self.directory)
        try:
            result = install(Path("unused") / ".." / "skills")
        finally:
            os.chdir(previous)
        self.assertEqual(Path(result["target"]), self.target)
        self.assertTrue(self.target.is_dir())

    def test_refuses_relative_source_target_without_writes(self) -> None:
        before = self.snapshot(self.source)
        previous = Path.cwd()
        os.chdir(self.source)
        try:
            for relative in (Path("."), Path("nested"), Path("unused/../nested")):
                with self.subTest(relative=relative), self.assertRaises(InstallError):
                    install(relative, force=True)
        finally:
            os.chdir(previous)
        self.assertEqual(self.snapshot(self.source), before)

    def test_refuses_exact_self_target(self) -> None:
        source = self.directory / SKILL_NAME
        self.source.rename(source)
        before = self.snapshot(source)
        with mock.patch.object(installer, "ROOT", source):
            with self.assertRaisesRegex(InstallError, "自身"):
                install(self.directory, force=True)
        self.assertEqual(self.snapshot(source), before)

    def test_refuses_target_containing_source(self) -> None:
        ancestor = self.directory / SKILL_NAME
        ancestor.mkdir()
        source = ancestor / "source"
        self.source.rename(source)
        before = self.snapshot(ancestor)
        with mock.patch.object(installer, "ROOT", source):
            with self.assertRaisesRegex(InstallError, "包含源目录"):
                install(self.directory, force=True)
        self.assertEqual(self.snapshot(ancestor), before)

    def test_force_refuses_unrelated_directories(self) -> None:
        self.target.mkdir(parents=True)
        (self.target / "important.txt").write_bytes(b"unrelated data")
        variants = (
            (False, None), (True, None), (False, json.dumps({"name": SKILL_NAME})),
            (True, "not JSON"), (True, "null"), (True, "[]"),
            (True, json.dumps({"name": "another-skill"})),
        )
        for skill_marker, metadata in variants:
            with self.subTest(skill_marker=skill_marker, metadata=metadata):
                for name in ("SKILL.md", "skill.json"):
                    (self.target / name).unlink(missing_ok=True)
                if skill_marker:
                    (self.target / "SKILL.md").write_text("skill", encoding="utf-8")
                if metadata is not None:
                    (self.target / "skill.json").write_text(metadata, encoding="utf-8")
                before = self.snapshot(self.target)
                with self.assertRaises(InstallError):
                    install(self.target_base, force=True)
                with self.assertRaises(InstallError):
                    install(self.target_base, force=True, check_only=True)
                self.assert_old_unchanged(before)

    def test_refuses_non_directory_base_and_target(self) -> None:
        blocked = self.directory / "file"
        blocked.write_bytes(b"keep")
        for base in (blocked, blocked / "child"):
            with self.subTest(base=base), self.assertRaises((InstallError, OSError)):
                install(base, force=True)
        self.target_base.mkdir()
        self.target.write_bytes(b"keep target")
        with self.assertRaisesRegex(InstallError, "不是目录"):
            install(self.target_base, force=True)
        self.assertEqual(blocked.read_bytes(), b"keep")
        self.assertEqual(self.target.read_bytes(), b"keep target")

    def test_refuses_symlink_target_base_and_ancestor(self) -> None:
        real = self.directory / "real"
        real.mkdir()
        link = self.directory / "linked"
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"当前环境无法创建符号链接：{exc}")
        for base in (link, link / "child"):
            with self.subTest(base=base), self.assertRaisesRegex(InstallError, "符号链接"):
                install(base, force=True)
        self.target_base.mkdir()
        for destination in (real, self.directory / "missing"):
            with self.subTest(destination=destination):
                self.target.symlink_to(destination, target_is_directory=True)
                with self.assertRaisesRegex(InstallError, "符号链接"):
                    install(self.target_base, force=True)
                self.assertTrue(self.target.is_symlink())
                self.target.unlink()
        self.assertEqual(list(real.iterdir()), [])

    def test_symlink_guard_before_normalization_without_platform_privileges(self) -> None:
        before = self.snapshot(self.directory)
        for linked in (self.target, self.target_base, self.directory):
            with self.subTest(linked=linked):
                with mock.patch.object(Path, "is_symlink", autospec=True, side_effect=lambda path: path == linked):
                    with self.assertRaisesRegex(InstallError, "符号链接"):
                        install(self.target_base, force=True)
        self.assertEqual(self.snapshot(self.directory), before)

    def test_replacement_removes_obsolete_files_only_after_smoke(self) -> None:
        before = self.existing_install()
        (self.source / "new-only.txt").write_text("new", encoding="utf-8")
        real_run = subprocess.run

        def inspect_staging(command, **kwargs):
            script = Path(command[2])
            self.assertTrue(script.is_absolute())
            self.assertEqual(script, Path(kwargs["cwd"]) / "scripts" / "search.py")
            self.assertEqual(script.parents[3], self.target_base)
            self.assertNotEqual(script, self.source / "scripts" / "search.py")
            self.assertNotEqual(script, self.target / "scripts" / "search.py")
            self.assertEqual(self.snapshot(self.target), before)
            self.assertNotIn("PYTHONPATH", kwargs["env"])
            return real_run(command, **kwargs)

        with mock.patch.object(installer.subprocess, "run", side_effect=inspect_staging):
            result = install(self.target_base, force=True)
        self.assertEqual(result["status"], "installed")
        self.assertFalse((self.target / "old-only.txt").exists())
        self.assertEqual((self.target / "new-only.txt").read_text(encoding="utf-8"), "new")
        self.assertEqual(list(self.target_base.iterdir()), [self.target])

    def test_no_force_refuses_existing_install_without_changes(self) -> None:
        before = self.existing_install()
        for check_only in (False, True):
            with self.subTest(check_only=check_only), self.assertRaisesRegex(InstallError, "--force"):
                install(self.target_base, check_only=check_only)
        self.assert_old_unchanged(before)

    def test_bad_smoke_outputs_preserve_previous_install(self) -> None:
        before = self.existing_install()
        invalid = (
            "not JSON", "[]", "null", "1", "{}",
            json.dumps({"count": True, "results": self.valid_payload["results"]}),
            json.dumps({"count": "1", "results": self.valid_payload["results"]}),
            json.dumps({"count": 2, "results": self.valid_payload["results"]}),
            json.dumps({"count": 1, "results": []}),
            json.dumps({"count": 1, "results": {"id": "comp-product-card"}}),
            json.dumps({"count": 1, "results": [None]}),
            json.dumps({"count": 1, "results": [{}]}),
            json.dumps({"count": 1, "results": [{"id": "wrong-result"}]}),
        )
        for output in invalid:
            with self.subTest(output=output):
                self.set_smoke_output(output)
                with self.assertRaises(InstallError):
                    install(self.target_base, force=True)
                self.assert_old_unchanged(before)

    def test_smoke_process_failure_preserves_previous_install(self) -> None:
        before = self.existing_install()
        self.set_smoke_output(json.dumps(self.valid_payload), exit_code=7)
        with self.assertRaisesRegex(InstallError, "退出码 7"):
            install(self.target_base, force=True)
        self.assert_old_unchanged(before)
        with mock.patch.object(installer.subprocess, "run", side_effect=subprocess.TimeoutExpired("search", 30)):
            with self.assertRaises(subprocess.TimeoutExpired):
                install(self.target_base, force=True)
        self.assert_old_unchanged(before)

    def test_copy_failure_preserves_previous_install(self) -> None:
        before = self.existing_install()
        with mock.patch.object(installer.shutil, "copytree", side_effect=OSError("copy failed")):
            with self.assertRaisesRegex(OSError, "copy failed"):
                install(self.target_base, force=True)
        self.assert_old_unchanged(before)

    def test_missing_copied_entry_preserves_previous_install(self) -> None:
        before = self.existing_install()
        real_copy = shutil.copytree

        def incomplete_copy(source, target, *args, **kwargs):
            result = real_copy(source, target, *args, **kwargs)
            if Path(source) == self.source:
                (Path(target) / "mpux.py").unlink()
            return result

        with mock.patch.object(installer.shutil, "copytree", side_effect=incomplete_copy):
            with self.assertRaisesRegex(InstallError, "mpux.py"):
                install(self.target_base, force=True)
        self.assert_old_unchanged(before)

    def test_missing_source_entry_fails_even_check(self) -> None:
        (self.source / "mpux.py").unlink()
        for check_only in (False, True):
            with self.subTest(check_only=check_only), self.assertRaisesRegex(InstallError, "mpux.py"):
                install(self.target_base, check_only=check_only)
        self.assertFalse(self.target_base.exists())

    def test_rename_failure_rolls_back_previous_install(self) -> None:
        before = self.existing_install()
        real_rename = Path.rename
        for failed_name in (SKILL_NAME, "staged"):
            def fail_rename(path, destination):
                if path.name == failed_name:
                    raise OSError("rename failed")
                return real_rename(path, destination)

            with self.subTest(failed_name=failed_name):
                with mock.patch.object(Path, "rename", autospec=True, side_effect=fail_rename):
                    with self.assertRaisesRegex(OSError, "rename failed"):
                        install(self.target_base, force=True)
                self.assert_old_unchanged(before)

    def test_rollback_failure_keeps_backup_for_recovery(self) -> None:
        before = self.existing_install()
        real_rename = Path.rename

        def fail_publish_and_rollback(path, destination):
            if path.name in ("staged", "previous"):
                raise OSError("rename failed")
            return real_rename(path, destination)

        with mock.patch.object(Path, "rename", autospec=True, side_effect=fail_publish_and_rollback):
            with self.assertRaisesRegex(InstallError, "旧安装完整保留在") as raised:
                install(self.target_base, force=True)
        backups = list(self.target_base.glob(f".{SKILL_NAME}-*/previous"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(self.snapshot(backups[0]), before)
        self.assertIn(str(backups[0]), str(raised.exception))

    def test_failed_fresh_install_never_publishes_target(self) -> None:
        self.set_smoke_output("not JSON")
        with self.assertRaises(InstallError):
            install(self.target_base)
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.target_base.iterdir()), [])

    def test_check_does_not_write_or_run_smoke(self) -> None:
        before = self.snapshot(self.directory)
        with mock.patch.object(installer.tempfile, "mkdtemp") as staging:
            with mock.patch.object(installer.subprocess, "run") as smoke:
                result = install(self.target_base, check_only=True)
        self.assertEqual(result["status"], "ready")
        staging.assert_not_called()
        smoke.assert_not_called()
        self.assertEqual(self.snapshot(self.directory), before)
        before = self.existing_install()
        install(self.target_base, force=True, check_only=True)
        self.assert_old_unchanged(before)


class InstallCliTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="mpux-install-cli-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()

    def run_installer(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return run_cli(
            "-B", str(ROOT / "scripts" / "install_skill.py"), *args,
            cwd=cwd or self.directory,
        )

    def test_project_path_and_default_current_directory(self) -> None:
        for arguments, project in (
            (("--project",), self.directory),
            (("--project", "app with spaces"), self.directory / "app with spaces"),
            (("--project", str(self.directory / "absolute app")), self.directory / "absolute app"),
        ):
            with self.subTest(arguments=arguments):
                process = self.run_installer(*arguments, "--check", "--json")
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
                payload = load_json_output(process)
                self.assertEqual(payload["status"], "ready")
                self.assertEqual(Path(payload["target"]), project / ".claude" / "skills" / SKILL_NAME)
                self.assertEqual(process.stderr, "")
                self.assertEqual(list(self.directory.iterdir()), [])

    def test_explicit_project_installs_and_json_overwrite_error(self) -> None:
        project = self.directory / "my app"
        process = self.run_installer("--project", str(project), "--json")
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        payload = load_json_output(process)
        target = project / ".claude" / "skills" / SKILL_NAME
        self.assertEqual(Path(payload["target"]), target)
        self.assertEqual(payload["status"], "installed")
        self.assertEqual(payload["smoke_test"]["top_result"], "comp-product-card")
        self.assertTrue((target / "mpux.py").is_file())
        self.assertEqual(process.stderr, "")
        process = self.run_installer("--project", str(project), "--json")
        self.assertEqual(process.returncode, 2)
        self.assertFalse(load_json_output(process)["ok"])
        self.assertIn("--force", load_json_output(process)["error"])
        self.assertEqual(process.stderr, "")
        process = self.run_installer("--project", str(project), "--force")
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        entry = installer._quoted(str(target / "mpux.py"))
        self.assertIn(entry + " doctor", process.stdout)
        self.assertIn(entry + " search ", process.stdout)
        self.assertIn(installer._quoted(sys.executable), process.stdout)

    def test_mutually_exclusive_options_and_parse_errors_are_json(self) -> None:
        for arguments in (
            ("--target", str(self.directory), "--project", str(self.directory)),
            ("--project", "--target", str(self.directory)),
            ("--target",),
            ("--unknown",),
        ):
            with self.subTest(arguments=arguments):
                process = self.run_installer(*arguments, "--json")
                self.assertEqual(process.returncode, 2)
                payload = load_json_output(process)
                self.assertEqual(payload["status"], "error")
                self.assertTrue(payload["error"])
                self.assertEqual(process.stderr, "")
                self.assertEqual(list(self.directory.iterdir()), [])

    def test_source_project_error_has_correct_usage(self) -> None:
        process = self.run_installer("--project", "--check", "--json", cwd=ROOT)
        self.assertEqual(process.returncode, 2)
        error = load_json_output(process)["error"]
        self.assertIn("源目录内", error)
        self.assertIn("python mpux.py install --project /path/to/app", error)
        process = self.run_installer("--project", str(ROOT), "--check")
        self.assertEqual(process.returncode, 2)
        self.assertIn("--target /path/to/skills", process.stderr)
        self.assertEqual(process.stdout, "")

    def test_relative_target_check_is_normalized_and_read_only(self) -> None:
        process = self.run_installer("--target", "unused/../skills", "--check", "--json")
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(Path(load_json_output(process)["target"]), self.directory / "skills" / SKILL_NAME)
        self.assertEqual(list(self.directory.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
