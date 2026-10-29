from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT, load_json_output, run_script  # noqa: E402

from mpux_core import (  # noqa: E402
    DATA_DIR,
    DOMAIN_CONFIG,
    STACK_CONFIG,
    resolve_product_reference,
    search_knowledge,
    search_stack,
    tokenize,
)


class SearchCoreTests(unittest.TestCase):
    def test_chinese_exact_component(self) -> None:
        result = search_knowledge("商品卡片", domain="component", limit=3)
        self.assertGreaterEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "comp-product-card")
        self.assertIn("商品卡片", result["results"][0]["matched_terms"])
        self.assertTrue(result["results"][0]["source"].startswith("data/"))

    def test_english_query(self) -> None:
        result = search_knowledge("product card", domain="component", limit=3)
        self.assertEqual(result["results"][0]["id"], "comp-product-card")

    def test_synonym_chinese_to_safe_area(self) -> None:
        result = search_knowledge("底部安全区域", domain="mini-program", limit=3)
        self.assertEqual(result["results"][0]["id"], "mp-safe-area")

    def test_english_safe_area(self) -> None:
        result = search_knowledge("bottom safe area", domain="mini-program", limit=3)
        self.assertEqual(result["results"][0]["id"], "mp-safe-area")

    def test_multi_keyword(self) -> None:
        result = search_knowledge("微信小程序 底部安全区域", domain="mini-program", limit=2)
        self.assertEqual(result["results"][0]["id"], "mp-safe-area")
        self.assertIn("matched_fields", result["results"][0])
        self.assertGreater(result["results"][0]["score"], 0)

    def test_product_resolution_rejects_generic_program_term(self) -> None:
        self.assertIsNone(resolve_product_reference("宠物殡葬小程序"))
        self.assertIsNone(resolve_product_reference("量子计算小程序"))

    def test_product_resolution_accepts_fuzzy_identity_match(self) -> None:
        product = resolve_product_reference("电商小程序")
        self.assertIsNotNone(product)
        self.assertEqual(product["product_id"], "prod-ecommerce")

    def test_category_filter(self) -> None:
        result = search_knowledge("触控区域", domain="ux", limit=5)
        self.assertTrue(result["results"])
        for item in result["results"]:
            self.assertTrue(item["id"].startswith("ux-"))
            self.assertEqual(item["source"], "data/ux-guidelines.csv")

    def test_plural_domain_alias_via_cli(self) -> None:
        process = run_script("search.py", "商品卡片", "--domain", "components", "--json", "-n", "2")
        self.assertEqual(process.returncode, 0, process.stderr)
        payload = load_json_output(process)
        self.assertEqual(payload["domain"], "component")
        self.assertEqual(payload["results"][0]["id"], "comp-product-card")

    def test_stack_search(self) -> None:
        result = search_stack("uni-app 导航栏", "uni-app", limit=3)
        self.assertGreaterEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "uni-navbar")
        self.assertEqual(result["stack_label"], "uni-app")

    def test_taro_stack_search(self) -> None:
        result = search_stack("Taro 路由", "taro", limit=2)
        self.assertEqual(result["results"][0]["id"], "taro-route")

    def test_no_result_is_explicit(self) -> None:
        result = search_knowledge("little purple elephant", domain="component", limit=1)
        self.assertEqual(result["count"], 0)
        self.assertIn("未找到", result["notice"])
        self.assertIsInstance(result["suggestions"], list)

    def test_special_characters_do_not_crash(self) -> None:
        result = search_knowledge("!!! <script> 商品 & 卡片 ???", domain="component", limit=2)
        self.assertIsInstance(result["count"], int)
        self.assertIsInstance(result["results"], list)

    def test_empty_query_raises(self) -> None:
        with self.assertRaises(ValueError):
            search_knowledge("   ", domain="component")

    def test_limit_validation(self) -> None:
        with self.assertRaises(ValueError):
            search_knowledge("卡片", domain="component", limit=0)
        with self.assertRaises(ValueError):
            search_knowledge("卡片", domain="component", limit=21)

    def test_auto_detect_safe_area(self) -> None:
        result = search_knowledge("底部安全区域")
        self.assertTrue(result["auto_detected"])
        self.assertEqual(result["domain"], "mini-program")
        self.assertEqual(result["results"][0]["id"], "mp-safe-area")

    def test_product_context_boosts(self) -> None:
        result = search_knowledge(
            "反馈 加载 错误",
            domain="ux",
            limit=8,
            product="prod-ecommerce",
        )
        self.assertEqual(result["product_context"]["product_id"], "prod-ecommerce")
        self.assertTrue(result["results"])
        reasons = [reason for item in result["results"] for reason in item["reasons"]]
        self.assertIn("与指定产品类型的推荐记录一致", reasons)

    def test_json_serializable(self) -> None:
        result = search_knowledge("音乐", domain="product", limit=3)
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertIn("prod-music", encoded)

    def test_sources_exist(self) -> None:
        for domain, config in DOMAIN_CONFIG.items():
            path = DATA_DIR / config["file"]
            self.assertTrue(path.exists(), f"{domain} source missing")
        for stack, config in STACK_CONFIG.items():
            path = DATA_DIR / config["file"]
            self.assertTrue(path.exists(), f"{stack} source missing")

    def test_tokenizer_chinese_bigrams(self) -> None:
        tokens = tokenize("底部安全区域")
        self.assertIn("底部", tokens)
        self.assertIn("安全", tokens)
        self.assertIn("区域", tokens)

    def test_design_system_search_cli(self) -> None:
        process = run_script(
            "search.py",
            "电商首页 高级感 商品展示",
            "--design-system",
            "--project-name",
            "测试电商",
            "--json",
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        payload = load_json_output(process)
        self.assertEqual(payload["product"]["id"], "prod-ecommerce")
        self.assertIn("tokens", payload)

    def test_domain_and_stack_conflict_cli(self) -> None:
        process = run_script(
            "search.py",
            "商品",
            "--domain",
            "components",
            "--stack",
            "wechat-native",
        )
        self.assertEqual(process.returncode, 2)
        self.assertIn("不能同时使用", process.stderr)

    def test_invalid_domain_cli(self) -> None:
        process = run_script("search.py", "商品", "--domain", "nope")
        self.assertEqual(process.returncode, 2)


if __name__ == "__main__":
    unittest.main()