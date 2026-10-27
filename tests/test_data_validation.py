from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT  # noqa: E402

from validate_data import DATA_DIR, validate  # noqa: E402


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def _write_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=headers,
            quoting=csv.QUOTE_ALL,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


class DataValidationTests(unittest.TestCase):
    def test_current_data_passes(self) -> None:
        result = validate(DATA_DIR)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["errors"], [])

    def test_minimum_counts(self) -> None:
        result = validate(DATA_DIR)
        counts = result["counts"]
        self.assertGreaterEqual(counts["product"], 30)
        self.assertGreaterEqual(counts["style"], 22)
        self.assertGreaterEqual(counts["color"], 16)
        self.assertGreaterEqual(counts["layout"], 26)
        self.assertGreaterEqual(counts["component"], 33)
        self.assertGreaterEqual(counts["ux"], 34)
        self.assertGreaterEqual(counts["mini-program"], 30)
        self.assertGreaterEqual(counts["anti-pattern"], 40)
        self.assertGreaterEqual(counts["stack:wechat-native"], 18)
        self.assertGreaterEqual(counts["stack:uni-app"], 18)
        self.assertGreaterEqual(counts["stack:taro"], 18)

    def test_duplicate_id_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-data-") as temp:
            copy = Path(temp) / "data"
            shutil.copytree(DATA_DIR, copy)
            headers, rows = _read_rows(copy / "products.csv")
            rows[1]["product_id"] = rows[0]["product_id"]
            _write_rows(copy / "products.csv", headers, rows)
            result = validate(copy)
            self.assertFalse(result["ok"])
            self.assertTrue(any("重复 ID" in error for error in result["errors"]))

    def test_invalid_hex_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-data-") as temp:
            copy = Path(temp) / "data"
            shutil.copytree(DATA_DIR, copy)
            headers, rows = _read_rows(copy / "colors.csv")
            rows[0]["background"] = "#GGGGGG"
            _write_rows(copy / "colors.csv", headers, rows)
            result = validate(copy)
            self.assertFalse(result["ok"])
            self.assertTrue(any("不是合法 HEX" in error for error in result["errors"]))

    def test_invalid_reference_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-data-") as temp:
            copy = Path(temp) / "data"
            shutil.copytree(DATA_DIR, copy)
            headers, rows = _read_rows(copy / "products.csv")
            rows[0]["recommended_style_ids"] += ";style-does-not-exist"
            _write_rows(copy / "products.csv", headers, rows)
            result = validate(copy)
            self.assertFalse(result["ok"])
            self.assertTrue(any("不存在的 style" in error for error in result["errors"]))

    def test_empty_field_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-data-") as temp:
            copy = Path(temp) / "data"
            shutil.copytree(DATA_DIR, copy)
            headers, rows = _read_rows(copy / "ux-guidelines.csv")
            rows[0]["fix"] = ""
            _write_rows(copy / "ux-guidelines.csv", headers, rows)
            result = validate(copy)
            self.assertFalse(result["ok"])
            self.assertTrue(any("字段 fix 为空" in error for error in result["errors"]))

    def test_obvious_contradiction_detected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-data-") as temp:
            copy = Path(temp) / "data"
            shutil.copytree(DATA_DIR, copy)
            headers, products = _read_rows(copy / "products.csv")
            style_headers, styles = _read_rows(copy / "styles.csv")
            first_style = products[0]["recommended_style_ids"].split(";")[0]
            for style in styles:
                if style["style_id"] == first_style:
                    style["avoid_scenarios"] += "；" + products[0]["name"]
                    break
            _write_rows(copy / "styles.csv", style_headers, styles)
            result = validate(copy)
            self.assertFalse(result["ok"])
            self.assertTrue(any("明确避免" in error for error in result["errors"]))

    def test_source_dates_and_urls(self) -> None:
        _, rows = _read_rows(DATA_DIR / "mini-program-rules.csv")
        for row in rows:
            self.assertTrue(row["source_url"].startswith("https://"))
            self.assertRegex(row["verified_at"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertTrue(row["verification_status"])

    def test_no_secret_markers(self) -> None:
        result = validate(DATA_DIR)
        self.assertFalse(any("密钥" in error for error in result["errors"]))

    def test_cli_json_exit_code(self) -> None:
        import subprocess

        process = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_data.py"), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn('"ok": true', process.stdout.lower())


if __name__ == "__main__":
    unittest.main()