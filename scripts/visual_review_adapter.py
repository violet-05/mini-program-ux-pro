#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视觉审查模型的可选适配器契约。

本模块不调用任何模型或网络。它只定义统一请求/响应格式，并将模型判断与
程序测量分开。默认适配器不可用（UnavailableVisualAdapter）。
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Protocol

SCHEMA_VERSION = "1.0.0"
ENVIRONMENTS = {"browser", "wechat-devtools", "ios-device", "android-device", "unknown"}
SEVERITIES = {"P0", "P1", "P2", "P3"}


class VisualReviewError(ValueError):
    pass


class VisualModelUnavailable(RuntimeError):
    """未配置视觉模型时由默认适配器抛出。"""


class VisualReviewAdapter(Protocol):
    name: str

    def review(self, request: dict[str, Any]) -> dict[str, Any]:
        """返回符合本模块契约的视觉审查响应。"""


class UnavailableVisualAdapter:
    name = "unavailable"

    def review(self, request: dict[str, Any]) -> dict[str, Any]:
        raise VisualModelUnavailable(
            "未配置视觉模型适配器。本版本只提供请求/响应契约，不调用远程服务。"
        )


def _design_system_payload(value: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    path = Path(value)
    if not path.exists():
        raise VisualReviewError(f"设计系统文件不存在：{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VisualReviewError(f"设计系统不是合法 JSON：{exc}") from exc
    if not isinstance(payload, dict):
        raise VisualReviewError("设计系统必须是 JSON 对象")
    return payload


def build_request(
    screenshot: str | Path,
    page_type: str,
    design_system: str | Path | dict[str, Any],
    product: str | dict[str, Any],
    review_goal: str,
    *,
    environment: str = "unknown",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """构建视觉审查请求。截图路径必须存在，但本函数不读取/上传图片。"""
    screenshot_path = Path(screenshot)
    if not screenshot_path.exists():
        raise VisualReviewError(f"截图不存在：{screenshot_path}")
    if screenshot_path.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise VisualReviewError("截图应为 PNG/JPG/JPEG/WebP")
    if environment not in ENVIRONMENTS:
        raise VisualReviewError(f"未知环境：{environment}")
    if not page_type.strip():
        raise VisualReviewError("page_type 不能为空")
    if not review_goal.strip():
        raise VisualReviewError("review_goal 不能为空")
    design = _design_system_payload(design_system)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "request_id": f"vr-{uuid.uuid4().hex[:12]}",
        "environment": environment,
        "screenshot": {
            "path": str(screenshot_path.resolve()),
            "kind": screenshot_path.suffix.casefold().lstrip("."),
            "size_bytes": screenshot_path.stat().st_size,
            "note": "仅提供本地路径元数据；上传与否由用户显式授权的适配器决定。",
        },
        "page_type": page_type,
        "product": product,
        "review_goal": review_goal,
        "design_system": design,
        "review_dimensions": [
            "visual-hierarchy",
            "typography",
            "color-contrast",
            "spacing-alignment",
            "image-consistency",
            "component-consistency",
            "template-risk",
            "platform-adaptation",
        ],
        "separation_of_evidence": {
            "program_measurements": "由 audit/其他工具产生，不能与模型判断混在一起",
            "model_judgements": "必须标注 confidence，并作为建议而非客观测量",
            "human_confirmation": "业务/品牌取舍与最终验收由人决定",
        },
        "metadata": metadata or {},
    }
    return payload


def validate_response(response: dict[str, Any]) -> list[str]:
    """校验视觉模型响应契约，返回错误列表（空列表表示通过）。"""
    errors: list[str] = []
    if not isinstance(response, dict):
        return ["响应必须是 JSON 对象"]
    if response.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version 必须为 {SCHEMA_VERSION}")
    issues = response.get("issues")
    if not isinstance(issues, list):
        errors.append("issues 必须是数组")
        issues = []
    for index, issue in enumerate(issues):
        prefix = f"issues[{index}]"
        if not isinstance(issue, dict):
            errors.append(f"{prefix} 必须是对象")
            continue
        for field in ("category", "title", "evidence", "suggestion"):
            if not isinstance(issue.get(field), str) or not issue[field].strip():
                errors.append(f"{prefix}.{field} 不能为空")
        if issue.get("severity") not in SEVERITIES:
            errors.append(f"{prefix}.severity 必须是 P0–P3")
        confidence = issue.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append(f"{prefix}.confidence 必须在 0–1 之间")
        if issue.get("source", "visual-model") != "visual-model":
            errors.append(f"{prefix}.source 应为 visual-model")
    if "limitations" in response and not isinstance(response["limitations"], list):
        errors.append("limitations 必须是数组")
    return errors


def require_valid_response(response: dict[str, Any]) -> None:
    errors = validate_response(response)
    if errors:
        raise VisualReviewError("视觉审查响应不合法：" + "；".join(errors))


def review_with_adapter(
    adapter: VisualReviewAdapter, request: dict[str, Any]
) -> dict[str, Any]:
    if not hasattr(adapter, "review"):
        raise VisualReviewError("适配器必须实现 review(request)")
    response = adapter.review(request)
    require_valid_response(response)
    return response


def _cmd_build(args: argparse.Namespace) -> int:
    try:
        request = build_request(
            args.screenshot,
            args.page_type,
            args.design_system,
            args.product,
            args.goal,
            environment=args.environment,
        )
    except VisualReviewError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    text = json.dumps(request, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"请求已写入：{args.output}")
    else:
        print(text)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.response)
    if not path.exists():
        print(f"错误：响应文件不存在：{path}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"错误：响应不是合法 JSON：{exc}", file=sys.stderr)
        return 2
    errors = validate_response(payload)
    if errors:
        print("视觉审查响应不合法：")
        for error in errors:
            print(f"- {error}")
        return 1
    print("视觉审查响应契约通过。注意：通过契约不代表审美判断正确。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="视觉审查模型适配器契约（不调用模型/网络）",
    )
    subparsers = parser.add_subparsers(dest="command")

    build = subparsers.add_parser("build-request", help="构建请求 JSON")
    build.add_argument("--screenshot", required=True)
    build.add_argument("--page-type", required=True)
    build.add_argument("--design-system", required=True, help="MASTER.json 路径")
    build.add_argument("--product", required=True, help="产品名称或 JSON 字符串")
    build.add_argument("--goal", required=True)
    build.add_argument("--environment", choices=sorted(ENVIRONMENTS), default="unknown")
    build.add_argument("--output", "-o", default=None)
    build.set_defaults(func=_cmd_build)

    validate = subparsers.add_parser("validate-response", help="校验模型响应 JSON")
    validate.add_argument("--response", required=True)
    validate.set_defaults(func=_cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())