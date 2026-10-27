from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT, load_json_output, run_script  # noqa: E402

from design_system import DesignSystemError, generate_design_system  # noqa: E402
from mpux_core import load_domain  # noqa: E402

CASES = [
    ("综合电商小程序", "wechat-native"),
    ("音乐播放器小程序", "uni-app"),
    ("智慧农业小程序", "wechat-native"),
    ("教育学习小程序", "taro"),
    ("文创商城小程序", "wechat-native"),
]

REQUIRED_KEYS = {
    "schema_version",
    "generator",
    "generated_at",
    "project",
    "stack",
    "product",
    "style",
    "palette",
    "typography",
    "tokens",
    "layouts",
    "components",
    "ux_rules",
    "mini_program_rules",
    "anti_patterns",
    "stack_rules",
    "conflicts",
    "design_rationale",
    "acceptance_criteria",
    "sources",
    "limitations",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DesignSystemTests(unittest.TestCase):
    def test_required_schema_keys(self) -> None:
        design = generate_design_system("综合电商小程序", no_pages=True)["design_system"]
        self.assertTrue(REQUIRED_KEYS.issubset(design))
        self.assertEqual(design["product"]["id"], "prod-ecommerce")
        self.assertEqual(design["stack"]["id"], "wechat-native")
        json.dumps(design, ensure_ascii=False)

    def test_products_produce_different_systems(self) -> None:
        generated = []
        for product, stack in CASES:
            result = generate_design_system(product, stack=stack, no_pages=True)
            generated.append(result["design_system"])
        style_ids = {design["style"]["id"] for design in generated}
        palette_ids = {design["palette"]["id"] for design in generated}
        layout_sets = {tuple(row["id"] for row in design["layouts"]) for design in generated}
        type_ids = {design["typography"]["id"] for design in generated}
        origins = {design["tokens"]["colors"]["background"] for design in generated}
        self.assertEqual(len(style_ids), 5, style_ids)
        self.assertEqual(len(palette_ids), 5, palette_ids)
        self.assertEqual(len(layout_sets), 5, layout_sets)
        self.assertGreaterEqual(len(type_ids), 3, type_ids)
        self.assertEqual(len(origins), 5, origins)
        self.assertNotEqual(
            generated[0]["anti_patterns"],
            generated[1]["anti_patterns"],
        )

    def test_source_ids_exist(self) -> None:
        design = generate_design_system("文创商城小程序", no_pages=True)["design_system"]
        domain_map = {
            "product": "product",
            "style": "style",
            "palette": "color",
            "typography": "typography",
            "layouts": "layout",
            "components": "component",
            "ux_rules": "ux",
            "mini_program_rules": "mini-program",
            "anti_patterns": "anti-pattern",
            "reasoning": "reasoning",
        }
        id_fields = {
            "product": "product_id",
            "style": "style_id",
            "color": "palette_id",
            "typography": "typography_id",
            "layout": "layout_id",
            "component": "component_id",
            "ux": "rule_id",
            "mini-program": "rule_id",
            "anti-pattern": "anti_pattern_id",
            "reasoning": "reasoning_id",
        }
        for source_key, domain in domain_map.items():
            valid = {row[id_fields[domain]] for row in load_domain(domain)}
            for item in design["sources"][source_key]:
                self.assertIn(item, valid, f"unknown {source_key} source {item}")
        from mpux_core import read_csv, DATA_DIR, STACK_CONFIG

        stack_valid = {
            row["rule_id"]
            for row in read_csv(DATA_DIR / STACK_CONFIG[design["stack"]["id"]]["file"])
        }
        for item in design["sources"]["stack_rules"]:
            self.assertIn(item, stack_valid)

    def test_contrast_checks_pass(self) -> None:
        for product, _ in CASES:
            design = generate_design_system(product, no_pages=True)["design_system"]
            self.assertTrue(design["palette"]["contrast_checks"])
            for check in design["palette"]["contrast_checks"]:
                self.assertTrue(check["passes"], (product, check))
                self.assertGreaterEqual(check["ratio"], 4.5)

    def test_typography_minimums(self) -> None:
        design = generate_design_system("智慧农业小程序", no_pages=True)["design_system"]
        scale = design["tokens"]["typography"]["scale"]
        self.assertGreaterEqual(int(scale["caption"].replace("rpx", "")), 24)
        self.assertGreaterEqual(int(scale["body"].replace("rpx", "")), 28)
        self.assertEqual(design["tokens"]["sizes"]["touch_target"], "88rpx")

    def test_explicit_style(self) -> None:
        design = generate_design_system(
            "音乐播放器小程序",
            style="现代极简",
            no_pages=True,
        )["design_system"]
        self.assertEqual(design["style"]["id"], "style-minimal")
        self.assertEqual(design["style"]["selection"], "explicit")
        self.assertTrue(
            any(conflict["id"].startswith("conflict-style-vs-product") for conflict in design["conflicts"])
        )

    def test_unknown_product_raises(self) -> None:
        with self.assertRaises(DesignSystemError):
            generate_design_system("完全不存在的产品类型 abcdef", no_pages=True)

    def test_unknown_style_raises(self) -> None:
        with self.assertRaises(DesignSystemError):
            generate_design_system("音乐播放器小程序", style="不存在的风格 abcdef", no_pages=True)

    def test_persistence_and_no_clobber(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-ds-") as temp:
            output = Path(temp) / "design-system"
            first = generate_design_system(
                "音乐播放器小程序",
                style="现代极简",
                project_name="音乐测试",
                output_dir=output,
                output_format="both",
            )
            self.assertEqual(first["persistence"]["status"], "success")
            required = [
                output / "MASTER.md",
                output / "MASTER.json",
                output / "tokens.wxss",
                output / "pages" / "home.md",
                output / "pages" / "music-player.md",
                output / "pages" / "profile.md",
            ]
            for path in required:
                self.assertTrue(path.exists(), path)
            master_hash = _sha256(output / "MASTER.md")
            payload = json.loads((output / "MASTER.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["project"]["name"], "音乐测试")
            self.assertTrue((output / "MASTER.md").read_text(encoding="utf-8").startswith("# 音乐测试"))
            second = generate_design_system(
                "音乐播放器小程序",
                style="现代极简",
                project_name="音乐测试",
                output_dir=output,
                output_format="both",
            )
            self.assertEqual(second["persistence"]["status"], "skipped_exists")
            self.assertEqual(_sha256(output / "MASTER.md"), master_hash)
            forced = generate_design_system(
                "音乐播放器小程序",
                style="现代极简",
                project_name="音乐测试",
                output_dir=output,
                output_format="both",
                force=True,
            )
            self.assertEqual(forced["persistence"]["status"], "success")

    def test_pages_custom_selection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-pages-") as temp:
            output = Path(temp) / "ds"
            result = generate_design_system(
                "综合电商小程序",
                pages=["home", "product-detail"],
                output_dir=output,
            )
            page_files = {Path(item["file"]).name for item in result["design_system"]["pages"]}
            self.assertEqual(page_files, {"home.md", "product-detail.md"})
            self.assertTrue((output / "pages" / "home.md").exists())
            self.assertTrue((output / "pages" / "product-detail.md").exists())
            self.assertFalse((output / "pages" / "profile.md").exists())

    def test_uni_app_token_file_and_content(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-uni-ds-") as temp:
            output = Path(temp) / "ds"
            result = generate_design_system(
                "音乐播放器小程序",
                stack="uni-app",
                output_dir=output,
                output_format="md",
            )
            self.assertEqual(result["design_system"]["token_implementation"]["file"], "tokens.scss")
            self.assertTrue((output / "tokens.scss").exists())
            token_text = (output / "tokens.scss").read_text(encoding="utf-8")
            self.assertIn("$mpux-color-background", token_text)
            self.assertTrue((output / "MASTER.md").exists())
            self.assertFalse((output / "MASTER.json").exists())

    def test_markdown_sections(self) -> None:
        markdown = generate_design_system("数据看板小程序", no_pages=True)["markdown"]
        for index in range(1, 17):
            self.assertIn(f"## {index}.", markdown)
        self.assertIn("未运行页面截图", markdown)
        self.assertIn("MASTER.json", markdown)

    def test_page_override_inherits_master(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-page-") as temp:
            output = Path(temp) / "ds"
            generate_design_system("生活服务小程序", pages=["booking"], output_dir=output)
            page_text = (output / "pages" / "booking.md").read_text(encoding="utf-8")
            self.assertIn("继承 `MASTER.md`", page_text)
            self.assertIn("禁止覆盖", page_text)
            self.assertIn("88rpx", page_text)
            self.assertIn("安全区", page_text)

    def test_cli_generation_and_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-cli-ds-") as temp:
            output = Path(temp) / "ds"
            process = run_script(
                "generate_design_system.py",
                "--product",
                "智慧农业小程序",
                "--stack",
                "wechat-native",
                "--output",
                str(output),
                "--format",
                "both",
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertTrue((output / "MASTER.md").exists())
            payload = json.loads((output / "MASTER.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["product"]["id"], "prod-smart-agriculture")
            invalid = run_script(
                "generate_design_system.py",
                "--product",
                "不存在的产品",
                "--output",
                str(Path(temp) / "bad"),
            )
            self.assertEqual(invalid.returncode, 2)
            self.assertIn("不能安全地生成", invalid.stderr)


if __name__ == "__main__":
    unittest.main()