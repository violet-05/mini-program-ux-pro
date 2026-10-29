from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import helpers  # noqa: E402,F401

from validate_project import _runtime_evidence  # noqa: E402


def _png_chunk(kind: bytes, data: bytes = b"") -> bytes:
    return (
        struct.pack(">I", len(data)) + kind + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def _png_ihdr(
    width: int = 1,
    height: int = 1,
    depth: int = 8,
    color: int = 6,
    compression: int = 0,
    filtering: int = 0,
    interlace: int = 0,
) -> bytes:
    return _png_chunk(
        b"IHDR", struct.pack(">IIBBBBB", width, height, depth, color, compression, filtering, interlace)
    )


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# 标准库合成的有效 1x1 RGBA PNG：filter=0，随后为一个像素。
PNG_PIXELS = b"\x00\x12\x34\x56\xff"
PNG_IDAT = _png_chunk(b"IDAT", zlib.compress(PNG_PIXELS))
PNG_IEND = _png_chunk(b"IEND")
VALID_PNG = PNG_SIGNATURE + _png_ihdr() + PNG_IDAT + PNG_IEND
SCREEN_PATH = "verification/artifacts/screen.png"


class RuntimeEvidenceTests(unittest.TestCase):
    def _make_root(
        self,
        temp: str,
        *,
        checks: list[dict] | None = None,
        screenshots: list[object] | None = None,
        console_errors: int = 0,
        exceptions: list[dict] | None = None,
        status: str = "passed",
    ) -> Path:
        root = Path(temp)
        artifacts = root / "verification" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "screen.png").write_bytes(VALID_PNG)
        payload = {
            "status": status,
            "checks": checks if checks is not None else [{"passed": True} for _ in range(20)],
            "screenshots": (
                screenshots
                if screenshots is not None
                else [{"path": "verification/artifacts/screen.png"}]
            ),
            "console_error_count": console_errors,
            "exceptions": exceptions if exceptions is not None else [],
        }
        (artifacts / "results.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        return root

    def test_valid_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            ok, detail = _runtime_evidence(self._make_root(temp))
        self.assertTrue(ok, detail)

    def test_failed_check_rejected(self) -> None:
        checks = [{"passed": True} for _ in range(20)]
        checks[3] = {"passed": False}
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            ok, detail = _runtime_evidence(self._make_root(temp, checks=checks))
        self.assertFalse(ok, detail)

    def test_missing_screenshot_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            ok, detail = _runtime_evidence(
                self._make_root(
                    temp,
                    screenshots=[{"path": "verification/artifacts/missing.png"}],
                )
            )
        self.assertFalse(ok, detail)

    def test_invalid_screenshot_entry_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            ok, detail = _runtime_evidence(
                self._make_root(temp, screenshots=["verification/artifacts/screen.png"])
            )
        self.assertFalse(ok, detail)

    def test_console_errors_and_exceptions_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            ok, detail = _runtime_evidence(
                self._make_root(
                    temp,
                    console_errors=1,
                    exceptions=[{"message": "boom"}],
                )
            )
        self.assertFalse(ok, detail)

    def test_failed_status_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            ok, detail = _runtime_evidence(self._make_root(temp, status="failed"))
        self.assertFalse(ok, detail)

    def test_missing_evidence_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            ok, detail = _runtime_evidence(Path(temp))
        self.assertFalse(ok)
        self.assertIn("未找到", detail)

    def _write_payload(self, root: Path, payload: object) -> None:
        (root / "verification/artifacts/results.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def _read_payload(self, root: Path) -> dict:
        return json.loads((root / "verification/artifacts/results.json").read_text(encoding="utf-8"))

    def _assert_rejected(self, root: Path, reason: str) -> None:
        result = _runtime_evidence(root)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        ok, detail = result
        self.assertIs(ok, False, detail)
        self.assertIsInstance(detail, str)
        self.assertIn(reason, detail)

    def test_non_object_json_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            for payload in (None, [], [{"status": "passed"}], "passed", 0, 1.5, True):
                with self.subTest(payload=payload):
                    self._write_payload(root, payload)
                    self._assert_rejected(root, "根对象")

    def test_each_required_field_missing_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            payload = self._read_payload(root)
            for field in payload:
                with self.subTest(field=field):
                    self._write_payload(root, {key: value for key, value in payload.items() if key != field})
                    self._assert_rejected(root, f"缺少必填字段：{field}")

    def test_malformed_fields_rejected(self) -> None:
        cases = {
            "status": (None, False, True, 0, 1, [], {}, "", "failed", "Passed", "passed "),
            "checks": (None, False, 0, "checks", {}, [], [{"passed": True}] * 19),
            "screenshots": (None, False, 0, "screen.png", {}, {"path": SCREEN_PATH}, []),
            "console_error_count": (None, False, True, 0.0, 1.0, 1, -1, "0", "", [], {}, [0]),
            "exceptions": (None, False, True, 0, 1, 1.5, "", "boom", {}, {"message": "boom"}, [None]),
        }
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            payload = self._read_payload(root)
            for field, values in cases.items():
                for value in values:
                    with self.subTest(field=field, value=value):
                        self._write_payload(root, {**payload, field: value})
                        self._assert_rejected(root, field)

    def test_every_check_requires_dict_and_literal_true(self) -> None:
        invalid = [None, False, True, 0, 1, "passed", [], {}]
        invalid += [{"passed": value} for value in (None, False, 0, 1, "true", [], {})]
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            payload = self._read_payload(root)
            for entry in invalid:
                # 即使前 20 项已经通过，末尾无效项也不能被忽略。
                for index in (0, 20):
                    with self.subTest(entry=entry, index=index):
                        checks = [{"passed": True} for _ in range(20)]
                        checks.insert(index, entry)
                        self._write_payload(root, {**payload, "checks": checks})
                        self._assert_rejected(root, f"checks[{index}]")

    def test_invalid_and_mixed_screenshot_entries_rejected(self) -> None:
        invalid = [None, False, 0, 1.5, SCREEN_PATH, [], {}]
        invalid += [{"path": value} for value in (None, False, 0, [], {}, "", " \t\n")]
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            payload = self._read_payload(root)
            valid = {"path": SCREEN_PATH}
            for entry in invalid:
                for screenshots, index in (([entry], 0), ([valid, entry], 1), ([entry, valid], 0)):
                    with self.subTest(entry=entry, index=index, count=len(screenshots)):
                        self._write_payload(root, {**payload, "screenshots": screenshots})
                        self._assert_rejected(root, f"screenshots[{index}]")

    def test_mixed_missing_screenshot_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp, screenshots=[
                {"path": SCREEN_PATH}, {"path": "verification/artifacts/missing.png"}
            ])
            self._assert_rejected(root, "screenshots[1].path")

    def test_valid_multiple_screenshots_and_extra_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp, checks=[{"passed": True}] * 21, screenshots=[
                {"path": SCREEN_PATH}, {"path": "verification/artifacts/second.png"}
            ])
            (root / "verification/artifacts/second.png").write_bytes(VALID_PNG)
            ok, detail = _runtime_evidence(root)
            self.assertIs(ok, True, detail)
            self.assertIn("checks=21 screenshots=2", detail)
            self.assertIn("未验证截图内容或交互", detail)

    def test_screenshot_directory_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            screen = root / SCREEN_PATH
            screen.unlink()
            screen.mkdir()
            self._assert_rejected(root, "常规非空文件")

    def test_screenshot_empty_file_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            (root / SCREEN_PATH).write_bytes(b"")
            self._assert_rejected(root, "常规非空文件")

    def test_absolute_and_drive_relative_paths_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            payload = self._read_payload(root)
            paths = (
                str((root / SCREEN_PATH).resolve()), "/screen.png", "//server/share/screen.png",
                "C:\\screen.png", "C:screen.png", "\\screen.png", "\\\\server\\share\\screen.png",
            )
            for path in paths:
                with self.subTest(path=path):
                    self._write_payload(root, {**payload, "screenshots": [{"path": path}]})
                    self._assert_rejected(root, "项目内相对路径")

    def test_parent_traversal_to_existing_file_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(str(Path(temp) / "project"))
            (Path(temp) / "outside.png").write_bytes(VALID_PNG)
            payload = self._read_payload(root)
            for path in ("../outside.png", "..\\outside.png", "verification/artifacts/../../../outside.png"):
                with self.subTest(path=path):
                    self._write_payload(root, {**payload, "screenshots": [{"path": path}]})
                    self._assert_rejected(root, "逃逸项目目录")

    def test_resolved_escape_rejected(self) -> None:
        # 即使平台禁止创建符号链接，也独立测试 resolve 后的边界判断。
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(str(Path(temp) / "project"))
            outside = Path(temp) / "outside.png"
            outside.write_bytes(VALID_PNG)
            with patch.object(Path, "resolve", side_effect=[root, outside]):
                self._assert_rejected(root, "逃逸项目目录")

    def test_symlink_escape_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(str(Path(temp) / "project"))
            outside = Path(temp) / "outside.png"
            outside.write_bytes(VALID_PNG)
            screen = root / SCREEN_PATH
            screen.unlink()
            try:
                screen.symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"此平台不能创建符号链接：{exc}")
            self._assert_rejected(root, "逃逸项目目录")

    def test_internal_relative_paths_still_accepted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            payload = self._read_payload(root)
            for path in ("verification/artifacts/../artifacts/screen.png", SCREEN_PATH.replace("/", "\\")):
                with self.subTest(path=path):
                    self._write_payload(root, {**payload, "screenshots": [{"path": path}]})
                    ok, detail = _runtime_evidence(root)
                    self.assertIs(ok, True, detail)

    def test_invalid_path_characters_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            payload = self._read_payload(root)
            for path in ("bad\x00.png", SCREEN_PATH + ":stream", "\ud800.png"):
                with self.subTest(path=repr(path)):
                    self._write_payload(root, {**payload, "screenshots": [{"path": path}]})
                    self._assert_rejected(root, "screenshots[0].path")

    def test_screenshot_io_and_resolve_errors_return_false(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            with patch.object(Path, "read_bytes", side_effect=PermissionError("denied")):
                self._assert_rejected(root, "无法读取")
            with patch.object(Path, "resolve", side_effect=[root, RuntimeError("symlink loop")]):
                self._assert_rejected(root, "路径无效")

    def test_invalid_utf8_bom_and_json_return_false(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            result_file = root / "verification/artifacts/results.json"
            valid_json = result_file.read_bytes()
            for content in (
                b"", b"{", b"{} trailing", b"\xff", b'{"status": "\xff"}',
                b"\xef\xbb\xbf" + valid_json, b"\xff\xfe" + valid_json,
            ):
                with self.subTest(content=content[:30]):
                    result_file.write_bytes(content)
                    self._assert_rejected(root, "证据无法读取")

    def test_duplicate_keys_and_non_json_constants_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            result_file = root / "verification/artifacts/results.json"
            valid_json = result_file.read_text(encoding="utf-8")
            variants = [
                valid_json.replace('"status": "passed"', '"status": "failed", "status": "passed"'),
                valid_json.replace('"passed": true', '"passed": false, "passed": true', 1),
            ]
            variants += [valid_json[:-1] + f', "extra": {value}}}' for value in ("NaN", "Infinity", "-Infinity")]
            for content in variants:
                with self.subTest(content=content[:80]):
                    result_file.write_text(content, encoding="utf-8")
                    self._assert_rejected(root, "证据无法读取")

    def test_evidence_directory_and_read_error_return_false(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                self._assert_rejected(root, "证据无法读取")
            with patch("validate_project.json.loads", side_effect=RecursionError("JSON nesting")):
                self._assert_rejected(root, "证据无法读取")
            result_file = root / "verification/artifacts/results.json"
            result_file.unlink()
            result_file.mkdir()
            self._assert_rejected(root, "证据无法读取")

    def test_every_truncated_png_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            for size in range(len(VALID_PNG)):
                with self.subTest(size=size):
                    (root / SCREEN_PATH).write_bytes(VALID_PNG[:size])
                    self._assert_rejected(root, "screenshots[0].path")

    def test_relabelled_and_mixed_corrupt_png_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp, screenshots=[
                {"path": SCREEN_PATH}, {"path": "verification/artifacts/broken.png"}
            ])
            for data in (b"not a PNG", b"\xff\xd8\xff\xd9", PNG_SIGNATURE, VALID_PNG[:-1]):
                with self.subTest(data=data[:12]):
                    (root / "verification/artifacts/broken.png").write_bytes(data)
                    self._assert_rejected(root, "screenshots[1].path：PNG")

    def test_png_crc_checked_on_every_chunk(self) -> None:
        chunks = [_png_ihdr(), PNG_IDAT, _png_chunk(b"tEXt", b"key\x00value"), PNG_IEND]
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            for index in range(len(chunks)):
                with self.subTest(index=index):
                    broken = chunks.copy()
                    broken[index] = broken[index][:-1] + bytes([broken[index][-1] ^ 1])
                    (root / SCREEN_PATH).write_bytes(PNG_SIGNATURE + b"".join(broken))
                    self._assert_rejected(root, "CRC")

    def test_png_ihdr_dimensions_and_encoding_rejected(self) -> None:
        invalid = (
            {"width": 0}, {"height": 0}, {"width": 0x80000000}, {"height": 0xFFFFFFFF},
            {"depth": 0}, {"depth": 1}, {"color": 1}, {"color": 7},
            {"compression": 1}, {"filtering": 1}, {"interlace": 2},
        )
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            for values in invalid:
                with self.subTest(values=values):
                    (root / SCREEN_PATH).write_bytes(PNG_SIGNATURE + _png_ihdr(**values) + PNG_IDAT + PNG_IEND)
                    self._assert_rejected(root, "IHDR")

    def test_png_chunk_structure_rejected(self) -> None:
        ihdr = _png_ihdr()
        text = _png_chunk(b"tEXt", b"key\x00value")
        variants = {
            "missing IHDR": PNG_IDAT + PNG_IEND,
            "IHDR not first": text + ihdr + PNG_IDAT + PNG_IEND,
            "duplicate IHDR": ihdr + ihdr + PNG_IDAT + PNG_IEND,
            "short IHDR": _png_chunk(b"IHDR", b"\x00" * 12) + PNG_IDAT + PNG_IEND,
            "long IHDR": _png_chunk(b"IHDR", b"\x00" * 14) + PNG_IDAT + PNG_IEND,
            "missing IDAT": ihdr + PNG_IEND,
            "empty IDAT": ihdr + _png_chunk(b"IDAT") + PNG_IEND,
            "missing IEND": ihdr + PNG_IDAT,
            "IEND before IDAT": ihdr + PNG_IEND + PNG_IDAT,
            "nonempty IEND": ihdr + PNG_IDAT + _png_chunk(b"IEND", b"x"),
            "duplicate IEND": ihdr + PNG_IDAT + PNG_IEND + PNG_IEND,
            "trailing bytes": ihdr + PNG_IDAT + PNG_IEND + b"junk",
            "split IDAT": ihdr + PNG_IDAT + text + PNG_IDAT + PNG_IEND,
            "invalid type": ihdr + _png_chunk(b"bad!") + PNG_IDAT + PNG_IEND,
            "reserved bit": ihdr + _png_chunk(b"test") + PNG_IDAT + PNG_IEND,
            "unknown critical": ihdr + _png_chunk(b"ABCD") + PNG_IDAT + PNG_IEND,
            "length overflow": ihdr + struct.pack(">I4s", 0x80000000, b"IDAT") + b"\x00" * 4,
            "length overrun": ihdr + struct.pack(">I4s", 100, b"IDAT") + b"\x00" * 4,
            "missing palette": _png_ihdr(color=3) + PNG_IDAT + PNG_IEND,
            "empty palette": ihdr + _png_chunk(b"PLTE") + PNG_IDAT + PNG_IEND,
            "partial palette": ihdr + _png_chunk(b"PLTE", b"12") + PNG_IDAT + PNG_IEND,
            "late palette": ihdr + PNG_IDAT + _png_chunk(b"PLTE", b"123") + PNG_IEND,
        }
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            for name, chunks in variants.items():
                with self.subTest(name=name):
                    (root / SCREEN_PATH).write_bytes(PNG_SIGNATURE + chunks)
                    self._assert_rejected(root, "PNG")

    def test_valid_png_ancillary_palette_and_contiguous_idat(self) -> None:
        compressed = zlib.compress(PNG_PIXELS)
        variants = [
            _png_ihdr() + _png_chunk(b"tEXt", b"key\x00value") + PNG_IDAT + PNG_IEND,
            _png_ihdr() + _png_chunk(b"IDAT", compressed[:4]) + _png_chunk(b"IDAT", compressed[4:]) + PNG_IEND,
            _png_ihdr(color=3) + _png_chunk(b"PLTE", b"\x12\x34\x56")
            + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00")) + PNG_IEND,
        ]
        with tempfile.TemporaryDirectory(prefix="mpux-evidence-") as temp:
            root = self._make_root(temp)
            for index, chunks in enumerate(variants):
                with self.subTest(index=index):
                    (root / SCREEN_PATH).write_bytes(PNG_SIGNATURE + chunks)
                    ok, detail = _runtime_evidence(root)
                    self.assertIs(ok, True, detail)


if __name__ == "__main__":
    unittest.main()
