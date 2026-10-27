#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MPUX Pro 本地知识检索 CLI。

示例：
  python scripts/search.py "商品卡片" --domain components
  python scripts/search.py "微信小程序 底部安全区域" --domain mini-program
  python scripts/search.py "原生小程序" --stack wechat-native --json
  python scripts/search.py "电商首页 高级感 商品展示" --design-system
"""

from __future__ import annotations

import argparse
import json
import sys

from design_system import DesignSystemError, generate_design_system
from mpux_core import (
    DOMAIN_ALIASES,
    DOMAIN_CONFIG,
    STACK_CONFIG,
    configure_utf8_stdio,
    format_markdown,
    resolve_domain,
    search_knowledge,
    search_stack,
)


def _domain_choices() -> list[str]:
    return sorted({*DOMAIN_CONFIG, *DOMAIN_ALIASES})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MPUX Pro 中文/英文小程序设计知识检索，本地 BM25，无外部 API。",
    )
    parser.add_argument("query", nargs="+", help="一个或多个关键词；整个查询应表达一个主要意图")
    parser.add_argument(
        "--domain",
        "-d",
        choices=_domain_choices(),
        default=None,
        help="知识库分类；省略时自动识别，all 表示全库合并",
    )
    parser.add_argument(
        "--stack",
        "-s",
        choices=sorted(STACK_CONFIG),
        default=None,
        help="按技术栈检索：wechat-native、uni-app、taro",
    )
    parser.add_argument(
        "--product",
        default=None,
        help="产品类型 ID/名称/别名，作为推荐结果的检索上下文",
    )
    parser.add_argument(
        "--max-results",
        "--limit",
        "-n",
        dest="max_results",
        type=int,
        default=5,
        help="结果数量 1–20，默认 5",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式；也可以用 --json",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--full", action="store_true", help="Markdown 中不截断长字段")
    parser.add_argument(
        "--design-system",
        "-ds",
        action="store_true",
        help="基于查询生成完整设计系统（Markdown 或 JSON）",
    )
    parser.add_argument("--style", default=None, help="设计系统模式：指定风格")
    parser.add_argument("--project-name", "-p", default=None, help="设计系统模式：项目名称")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="设计系统模式：将结果写入 --output 指定的目录",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="设计系统模式：持久化目录；配合 --persist 时写入文件",
    )
    parser.add_argument(
        "--pages",
        action="append",
        default=None,
        help="设计系统模式：页面覆盖，逗号分隔或重复传入",
    )
    parser.add_argument("--no-pages", action="store_true", help="设计系统模式：不生成页面覆盖")
    parser.add_argument("--force", action="store_true", help="设计系统模式：明确覆盖已有文件")
    return parser


def _parse_pages(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    pages: list[str] = []
    for value in values:
        pages.extend(part.strip() for part in value.split(",") if part.strip())
    return pages


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    query = " ".join(args.query).strip()
    if not query:
        print("错误：查询不能为空。", file=sys.stderr)
        return 2
    if args.domain and args.stack:
        print("错误：--domain 与 --stack 不能同时使用；请分别检索设计知识和实现规则。", file=sys.stderr)
        return 2
    if args.max_results < 1 or args.max_results > 20:
        print("错误：--max-results 必须在 1–20 之间。", file=sys.stderr)
        return 2

    if args.design_system:
        try:
            result = generate_design_system(
                query,
                style=args.style,
                stack=args.stack or "wechat-native",
                project_name=args.project_name,
                pages=_parse_pages(args.pages),
                no_pages=args.no_pages,
                output_dir=args.output if args.persist else None,
                output_format="both",
                force=args.force,
            )
        except (DesignSystemError, ValueError) as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 2
        if args.json or args.format == "json":
            print(json.dumps(result["design_system"], ensure_ascii=False, indent=2))
        else:
            print(result["markdown"])
            if args.persist:
                persistence = result["persistence"]
                print("\n---\n" + persistence["message"], file=sys.stderr)
        return 0

    try:
        if args.stack:
            result = search_stack(query, args.stack, args.max_results)
        else:
            domain = resolve_domain(args.domain) if args.domain else None
            result = search_knowledge(
                query,
                domain=domain,
                limit=args.max_results,
                product=args.product,
            )
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    if args.json or args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(result, full=args.full))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())