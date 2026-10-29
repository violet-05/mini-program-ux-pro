from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import run_script  # noqa: E402

import audit_mini_program as audit  # noqa: E402


class AuditInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="mpux-inputs-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "project"
        self.root.mkdir()

    def write_json(self, name: str, payload: object) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def project(self, config: object, stack: str = "wechat-native") -> dict:
        return {
            "root": self.root,
            "app_root": self.root,
            "stack": stack,
            "app_config": config,
            "app_config_path": self.root / ("pages.json" if stack == "uni-app" else "app.json"),
        }

    def assert_cli_error(self, filename: str) -> None:
        output = Path(self.temp.name) / "review.json"
        result = run_script(
            "audit_mini_program.py", "--path", str(self.root),
            "--format", "json", "--output", str(output), cwd=self.root,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("错误：", result.stderr)
        self.assertIn(filename, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(output.exists())

    def assert_main_error(self, filename: str, path: Path | None = None) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(audit, "configure_utf8_stdio"), redirect_stdout(stdout), redirect_stderr(stderr):
            code = audit.main(["--path", str(path or self.root), "--format", "json"])
        self.assertEqual(code, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("错误：", stderr.getvalue())
        self.assertIn(filename, stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_read_text_preserves_empty_and_bom_utf8(self) -> None:
        path = self.root / "index.js"
        path.write_text("", encoding="utf-8")
        self.assertEqual(audit._read_text(path), "")
        path.write_text("页面内容", encoding="utf-8-sig")
        self.assertEqual(audit._read_text(path), "页面内容")

    def test_read_text_rejects_invalid_utf8_with_path(self) -> None:
        path = self.root / "index.js"
        path.write_bytes(b"Page({ title: '\xff' })")
        with self.assertRaises(audit.AuditError) as context:
            audit._read_text(path)
        self.assertIn(str(path), str(context.exception))
        self.assertIsInstance(context.exception.__cause__, UnicodeDecodeError)

    def test_read_text_wraps_io_and_value_errors(self) -> None:
        path = self.root / "index.js"
        for error in (PermissionError("denied"), FileNotFoundError("gone"), ValueError("bad path")):
            with self.subTest(error=error), patch.object(Path, "read_text", side_effect=error):
                with self.assertRaises(audit.AuditError) as context:
                    audit._read_text(path)
                self.assertIn(str(path), str(context.exception))
                self.assertIs(context.exception.__cause__, error)

    def test_walk_onerror_rejects_partial_scan(self) -> None:
        unreadable = self.root / "private"
        error = PermissionError(13, "denied", str(unreadable))

        def broken_walk(root, *, onerror):
            yield str(root), [], ["index.js"]
            onerror(error)

        (self.root / "index.js").write_text("Page({})", encoding="utf-8")
        with patch.object(audit.os, "walk", side_effect=broken_walk):
            with self.assertRaises(audit.AuditError) as context:
                audit._find_files(self.root)
        self.assertIn(str(unreadable), str(context.exception))

    def test_walk_wraps_file_metadata_failure(self) -> None:
        source = self.root / "index.js"
        with patch.object(audit.os, "walk", return_value=iter([(str(self.root), [], [source.name])])):
            with patch.object(Path, "lstat", side_effect=PermissionError("denied")):
                with self.assertRaises(audit.AuditError) as context:
                    list(audit._walk_project_files(self.root))
        self.assertIn(str(source), str(context.exception))

    def test_find_files_stat_failure_is_not_skipped(self) -> None:
        source = self.root / "index.js"
        for error in (PermissionError("denied"), FileNotFoundError("gone"), ValueError("bad path")):
            with self.subTest(error=error):
                with patch.object(audit, "_walk_project_files", return_value=iter([source])):
                    with patch.object(Path, "stat", side_effect=error):
                        with self.assertRaises(audit.AuditError) as context:
                            audit._find_files(self.root)
                self.assertIn(str(source), str(context.exception))

    def test_file_size_limit_and_skip_directories_unchanged(self) -> None:
        included = self.root / "exact.js"
        included.write_bytes(b" " * 800_000)
        (self.root / "large.js").write_bytes(b"\xff" * 800_001)
        (self.root / "notes.txt").write_bytes(b"\xff")
        ignored = self.root / "node_modules"
        ignored.mkdir()
        (ignored / "bad.js").write_bytes(b"\xff")
        self.assertEqual(audit._find_files(self.root), [included])

    def test_jsonc_bom_comments_and_trailing_commas(self) -> None:
        path = self.root / "app.json"
        path.write_text(
            '{\n// comment\n"pages": ["pages/home",], /* block */\n'
            '"url": "https://example.test/a,}", "text": "/* not a comment */",\n}',
            encoding="utf-8-sig",
        )
        payload = audit._load_jsonc(path)
        self.assertEqual(payload["pages"], ["pages/home"])
        self.assertEqual(payload["url"], "https://example.test/a,}")
        self.assertEqual(payload["text"], "/* not a comment */")

    def test_jsonc_requires_object_and_valid_utf8(self) -> None:
        path = self.root / "app.json"
        for text in ("[]", "null", "12", '"text"', "true", "", "{broken}"):
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(audit.AuditError) as context:
                    audit._load_jsonc(path)
                self.assertIn(str(path), str(context.exception))
        path.write_bytes(b'{"title":"\xff"}')
        with self.assertRaises(audit.AuditError):
            audit._load_jsonc(path)

    def test_package_dependencies_missing_or_valid(self) -> None:
        self.assertEqual(audit._package_dependencies(self.root), set())
        self.write_json("package.json", {})
        self.assertEqual(audit._package_dependencies(self.root), set())
        path = self.root / "package.json"
        path.write_text(
            '{/* deps */ "dependencies":{"@tarojs/taro":"^4",},'
            '"devDependencies":{"typescript":"*"}, "peerDependencies":{},}',
            encoding="utf-8-sig",
        )
        self.assertEqual(audit._package_dependencies(self.root), {"@tarojs/taro", "typescript"})

    def test_package_dependencies_reject_invalid_shapes(self) -> None:
        invalid = [None, [], "text", 12]
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            invalid.extend({key: value} for value in (None, [], "text", 12, True, {"x": None}))
        for payload in invalid:
            with self.subTest(payload=payload):
                path = self.write_json("package.json", payload)
                with self.assertRaises(audit.AuditError) as context:
                    audit._package_dependencies(self.root)
                self.assertIn(str(path), str(context.exception))

    def test_miniprogram_root_accepts_project_directories(self) -> None:
        self.write_json("app.json", {"pages": []})
        self.write_json("mini/app.json", {"pages": []})
        for route, expected in (("", self.root), ("./", self.root), ("mini/", self.root / "mini")):
            with self.subTest(route=route):
                self.write_json("project.config.json", {"miniprogramRoot": route})
                stack, _, app_root = audit._detect_stack(self.root)
                self.assertEqual(stack, "wechat-native")
                self.assertEqual(app_root, expected)

    def test_miniprogram_root_rejects_type_escape_and_non_directory(self) -> None:
        self.write_json("app.json", {"pages": []})
        invalid = [None, [], {}, 12, False, " ", "../outside", "..\\outside", "/outside",
                   "C:/outside", "C:outside", "\\\\server\\share", "missing", "app.json", "bad\x00path"]
        for route in invalid:
            with self.subTest(route=route):
                self.write_json("project.config.json", {"miniprogramRoot": route})
                with self.assertRaisesRegex(audit.AuditError, "miniprogramRoot"):
                    audit._detect_stack(self.root)

    def test_miniprogram_root_rejects_resolved_external_directory(self) -> None:
        self.write_json("project.config.json", {"miniprogramRoot": "linked"})
        original = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == self.root / "linked":
                return Path(self.temp.name).resolve()
            return original(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve):
            with self.assertRaisesRegex(audit.AuditError, "项目内路径"):
                audit._detect_stack(self.root)

    def test_pages_and_subpackages_support_native_and_uni(self) -> None:
        for stack in ("wechat-native", "uni-app"):
            for key in ("subPackages", "subpackages"):
                with self.subTest(stack=stack, key=key):
                    item = "pages/home" if stack == "wechat-native" else {"path": "pages/home", "style": {}}
                    subpage = "detail/index" if stack == "wechat-native" else {"path": "detail/index"}
                    config = {"pages": [item], key: [{"root": "features/", "pages": [subpage]}]}
                    pages, evidence = audit._extract_pages(self.project(config, stack))
                    self.assertEqual(pages, ["pages/home", "features/detail/index"])
                    self.assertEqual(len(evidence), 1)
                    self.assertEqual(evidence[0]["line"], 1)

    def test_pages_reject_invalid_shapes(self) -> None:
        invalid = [None, [], 12, "pages"]
        invalid.extend({"pages": value} for value in (None, 12, "pages/home", {}, True))
        invalid.extend({"pages": [value]} for value in (None, 12, [], {}, {"path": 12}))
        for key in ("subPackages", "subpackages"):
            invalid.extend({key: value} for value in (None, 12, "features", {}))
            invalid.extend({key: [value]} for value in (None, 12, "features", [], {}, {"root": "x"}))
            invalid.extend({key: [{"root": "x", "pages": value}]} for value in (None, 12, "home", {}))
            invalid.append({key: [{"root": 12, "pages": []}]})
        for config in invalid:
            with self.subTest(config=config):
                with self.assertRaises(audit.AuditError) as context:
                    audit._extract_pages(self.project(config))
                self.assertIn("app.json", str(context.exception))

    def test_pages_reject_absolute_and_traversal_paths(self) -> None:
        invalid = ["", " ", ".", "./", "/home", "\\home", "../home", "pages/../../home",
                   "..\\home", "C:/home", "C:home", "\\\\server\\share", "bad\x00path"]
        for route in invalid:
            configs = [
                {"pages": [route]}, {"pages": [{"path": route}]},
                {"subPackages": [{"root": route, "pages": ["home"]}]},
                {"subPackages": [{"root": "features", "pages": [route]}]},
                {"subpackages": [{"root": "features", "pages": [{"path": route}]}]},
            ]
            for config in configs:
                with self.subTest(config=config):
                    with self.assertRaises(audit.AuditError):
                        audit._extract_pages(self.project(config))

    def test_taro_page_paths_are_validated_without_execution(self) -> None:
        project = self.project({}, "taro")
        path = self.root / "app.config.ts"
        project["app_config_path"] = path
        path.write_text("export default { pages: ['pages/home'] }", encoding="utf-8")
        self.assertEqual(audit._extract_pages(project)[0], ["pages/home"])
        path.write_text("export default { pages: ['../outside'] }", encoding="utf-8")
        with self.assertRaises(audit.AuditError):
            audit._extract_pages(project)

    def test_page_candidates_reject_resolved_external_file(self) -> None:
        project = self.project({"pages": ["home"]})
        original = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == self.root / "home.wxml":
                return Path(self.temp.name) / "outside.wxml"
            return original(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve):
            with self.assertRaisesRegex(audit.AuditError, "项目内路径"):
                audit._page_candidates(project, "home")

    def test_cli_rejects_bad_config_without_report_or_traceback(self) -> None:
        cases = [
            ("package.json", "[]"), ("package.json", "null"),
            ("package.json", "{broken}"), ("package.json", '{"dependencies": []}'),
            ("project.config.json", "[]"), ("project.config.json", "null"),
            ("project.config.json", "{broken}"),
            ("project.config.json", '{"miniprogramRoot": 12}'),
            ("project.config.json", '{"miniprogramRoot": "../outside"}'),
            ("app.json", "[]"), ("app.json", "null"), ("app.json", "{broken}"),
            ("app.json", '{"pages": 12}'), ("app.json", '{"pages": "/home"}'),
            ("app.json", '{"pages": ["../outside"]}'),
            ("app.json", '{"subPackages": [{"root":"x", "pages":12}]}'),
            ("pages.json", "[]"), ("pages.json", "{broken}"),
            ("pages.json", '{"pages": [{"path": 12}]}'),
        ]
        for name, text in cases:
            with self.subTest(name=name, text=text):
                path = self.root / name
                path.write_text(text, encoding="utf-8")
                try:
                    self.assert_cli_error(name)
                finally:
                    path.unlink()

    def test_cli_rejects_invalid_page_config(self) -> None:
        self.write_json("app.json", {"pages": ["home"]})
        (self.root / "home.wxml").write_text("<view>首页</view>", encoding="utf-8")
        path = self.root / "home.json"
        for text in ("null", "[]", "{broken}"):
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                self.assert_cli_error("home.json")

    def test_cli_rejects_invalid_utf8_source_and_config(self) -> None:
        self.write_json("app.json", {"pages": []})
        for name in ("index.js", "app.json", "package.json", "project.config.json"):
            with self.subTest(name=name):
                path = self.root / name
                path.write_bytes(b'{"text":"\xff"}')
                try:
                    self.assert_cli_error(name)
                finally:
                    path.unlink()
                    self.write_json("app.json", {"pages": []})

    def test_main_read_failure_exits_two_instead_of_empty_success(self) -> None:
        self.write_json("app.json", {"pages": []})
        self.write_json("package.json", {})
        source = self.root / "index.js"
        source.write_text("document.querySelector('view')", encoding="utf-8")
        original = Path.read_text
        for name in ("app.json", "package.json", "index.js"):
            def read_text(path, *args, **kwargs):
                if path == self.root / name:
                    raise PermissionError(13, "denied", str(path))
                return original(path, *args, **kwargs)

            with self.subTest(name=name), patch.object(Path, "read_text", read_text):
                self.assert_main_error(name)

    def test_main_scan_failure_exits_two(self) -> None:
        self.write_json("app.json", {"pages": []})
        unreadable = self.root / "private"

        def broken_walk(root, *, onerror):
            onerror(PermissionError(13, "denied", str(unreadable)))
            return iter(())

        with patch.object(audit.os, "walk", side_effect=broken_walk):
            self.assert_main_error("private")

    def test_main_metadata_failure_exits_two(self) -> None:
        self.write_json("app.json", {"pages": []})
        original = Path.stat
        for name in ("project.config.json", "package.json", "app.json"):
            def stat(path, *args, **kwargs):
                if path == self.root / name:
                    raise PermissionError(13, "denied", str(path))
                return original(path, *args, **kwargs)

            with self.subTest(name=name), patch.object(Path, "stat", stat):
                self.assert_main_error(name)

    def test_main_wraps_root_resolution_failure(self) -> None:
        with patch.object(Path, "resolve", side_effect=ValueError("bad path")):
            self.assert_main_error(str(self.root))

    def test_cli_valid_jsonc_still_succeeds(self) -> None:
        (self.root / "app.json").write_text(
            '\ufeff{/* config */ "pages": ["home",],}', encoding="utf-8",
        )
        (self.root / "home.wxml").write_text("<view>首页</view>", encoding="utf-8")
        self.write_json("home.json", {})
        result = run_script("audit_mini_program.py", "--path", str(self.root), "--format", "json", cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["scope"]["pages_declared"], 1)
        self.assertEqual(report["scope"]["pages_found"], 1)
        self.assertEqual(report["environment"]["runtime"], "not_run")


if __name__ == "__main__":
    unittest.main()
