#!/usr/bin/env python3
"""MPUX Pro 的统一命令入口。"""

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMMANDS = {
    "doctor": ("doctor", "检查安装完整性、知识库与检索，不启动开发者工具"),
    "search": ("search", "检索本地设计知识与技术栈规则"),
    "design": ("generate_design_system", "生成 Master、设计 token 与页面覆盖"),
    "audit": ("audit_mini_program", "只读审查现有小程序，可设置 CI 阈值"),
    "install": ("install_skill", "安装 Skill，先验证再替换旧版本"),
    "validate": ("validate_project", "维护者仓库自检，包含历史模拟器证据检查"),
    "verify": ("devtools_adapter", "可选的微信开发者工具模拟器验收"),
    "visual": ("visual_review_adapter", "视觉审查请求与响应契约，不内置视觉模型"),
}


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    if sys.version_info < (3, 10):
        print("错误：MPUX Pro 需要 Python 3.10+。请升级 Python 后重试。", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(
        description="MPUX Pro · 微信小程序设计智能 · 本地运行 / 无 API Key",
        epilog="首次使用：python mpux.py doctor；查看参数：python mpux.py <命令> --help",
    )
    parser.add_argument("--version", action="store_true", help="显示安装版本")
    commands = parser.add_subparsers(dest="command", title="命令")
    for name, (_, description) in COMMANDS.items():
        commands.add_parser(name, help=description, add_help=False)
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(argv[:1])
    if args.version:
        if len(argv) > 1:
            parser.error("--version 不接受其他参数")
        try:
            metadata = json.loads((ROOT / "skill.json").read_text(encoding="utf-8-sig"))
            version = metadata.get("version") if isinstance(metadata, dict) else None
            if not isinstance(version, str) or not version:
                raise ValueError("缺少 version")
        except (OSError, ValueError) as exc:
            print(f"错误：无法读取安装版本：{exc}；请运行 doctor 检查安装。", file=sys.stderr)
            return 2
        print(f"MPUX Pro {version}")
        return 0
    if not args.command:
        parser.print_help()
        return 0
    if args.command in {"install", "doctor"}:
        sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        module = importlib.import_module(COMMANDS[args.command][0])
    except ImportError as exc:
        print(f"错误：命令模块无法加载：{exc}；请重新安装完整 Skill。", file=sys.stderr)
        return 2
    original_program = sys.argv[0]
    try:
        sys.argv[0] = f"{original_program} {args.command}"
        return module.main(argv[1:])
    finally:
        sys.argv[0] = original_program


if __name__ == "__main__":
    raise SystemExit(main())
