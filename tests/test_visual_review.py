from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import load_json_output, run_script  # noqa: E402

from design_system import generate_design_system  # noqa: E402
from visual_review_adapter import (  # noqa: E402
    UnavailableVisualAdapter,
    VisualModelUnavailable,
    VisualReviewError,
    build_request,
    review_with_adapter,
    validate_response,
)


class VisualReviewContractTests(unittest.TestCase):
    def _screenshot(self, directory: Path) -> Path:
        path = directory / "screen.png"
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0aIDATx\x9cc\x00"
            b"\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return path

    def test_build_request(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-visual-") as temp:
            screenshot = self._screenshot(Path(temp))
            design = generate_design_system("综合电商小程序", no_pages=True)["design_system"]
            request = build_request(
                screenshot,
                "商品详情",
                design,
                {"name": "综合电商", "id": "prod-ecommerce"},
                "检查首屏层级与主操作",
                environment="wechat-devtools",
            )
            self.assertEqual(request["schema_version"], "1.0.0")
            self.assertEqual(request["environment"], "wechat-devtools")
            self.assertEqual(request["screenshot"]["kind"], "png")
            self.assertEqual(request["page_type"], "商品详情")
            self.assertIn("design_system", request)
            self.assertIn("model_judgements", request["separation_of_evidence"])
            json.dumps(request, ensure_ascii=False)

    def test_build_request_requires_existing_image(self) -> None:
        with self.assertRaises(VisualReviewError):
            build_request(
                "no-such-screen.png",
                "首页",
                {"tokens": {}},
                "测试",
                "检查",
            )

    def test_unavailable_adapter(self) -> None:
        with self.assertRaises(VisualModelUnavailable):
            UnavailableVisualAdapter().review({})

    def test_response_validation(self) -> None:
        valid = {
            "schema_version": "1.0.0",
            "issues": [
                {
                    "category": "视觉层级",
                    "title": "首屏主操作被挤出",
                    "severity": "P1",
                    "evidence": "390×844 截图中购买按钮在第二屏",
                    "suggestion": "将活动区下移并固定主操作",
                    "confidence": 0.86,
                    "source": "visual-model",
                }
            ],
            "limitations": ["仅检查一张截图"],
        }
        self.assertEqual(validate_response(valid), [])
        invalid = {
            "schema_version": "1.0.0",
            "issues": [
                {
                    "category": "",
                    "title": "",
                    "severity": "CRITICAL",
                    "evidence": "",
                    "suggestion": "",
                    "confidence": 2,
                }
            ],
        }
        errors = validate_response(invalid)
        self.assertTrue(errors)
        self.assertTrue(any("severity" in error for error in errors))
        self.assertTrue(any("confidence" in error for error in errors))

    def test_review_with_invalid_adapter_response(self) -> None:
        class BadAdapter:
            name = "bad"

            def review(self, request: dict) -> dict:
                return {"schema_version": "1.0.0", "issues": [{}]}

        with self.assertRaises(VisualReviewError):
            review_with_adapter(BadAdapter(), {})

    def test_cli_build_and_validate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mpux-visual-cli-") as temp:
            temp_path = Path(temp)
            output = temp_path / "ds"
            generate_design_system("音乐播放器小程序", output_dir=output, no_pages=True)
            screenshot = self._screenshot(temp_path)
            request_path = temp_path / "request.json"
            process = run_script(
                "visual_review_adapter.py",
                "build-request",
                "--screenshot",
                str(screenshot),
                "--page-type",
                "音乐播放器",
                "--design-system",
                str(output / "MASTER.json"),
                "--product",
                "音乐播放器",
                "--goal",
                "检查播放控制层级",
                "--environment",
                "ios-device",
                "--output",
                str(request_path),
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            request = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(request["environment"], "ios-device")
            response_path = temp_path / "response.json"
            response_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "issues": [],
                        "limitations": ["空响应用于契约测试"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            validate = run_script(
                "visual_review_adapter.py",
                "validate-response",
                "--response",
                str(response_path),
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("契约通过", validate.stdout)


if __name__ == "__main__":
    unittest.main()