#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 MPUX Pro 安装到 Claude/Agent Skills 目录，并执行一次检索冒烟测试。

默认安装到 ~/.claude/skills/mini-program-ux-pro。
Codex、Cursor 等工具的用户可将同一目录复制到该工具约定的 skills 目录。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from mpux_core import configure_utf8_stdio, utf8_subprocess_env

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "mini-program-ux-pro"
IGNORE = shutil.ignore_patterns(
    ".git",
    ".github",
    ".claude",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
    ".DS_Store",
    "design-system",
    "tmp",
    "tmp*",
    "dist",
    "build",
    "*.pyc",
    "*.log",
    "review*.json",
    "validation.json",
)


class InstallError(RuntimeError):
    pass


def _target_base(target: str | None, project: bool) -> Path:
    if target:
        return Path(target).expanduser().resolve()
    if project:
        return (Path.cwd() / ".claude" / "skills").resolve()
    return (Path.home() / ".claude" / "skills").resolve()


def install(target_base: Path, *, force: bool = False, check_only: bool = False) -> dict:
    source = ROOT
    if not (source / "SKILL.md").exists():
        raise InstallError(f"源目录没有 SKILL.md：{source}")
    target = target_base / SKILL_NAME
    if target.resolve() == source.resolve():
        raise InstallError("目标就是当前 Skill 目录，不能覆盖自身。")
    if target_base == source or source in target_base.parents or target == source or source in target.parents:
        raise InstallError("安装目标不能位于项目源目录内，以免递归复制。")
    if target.exists() and not force:
        raise InstallError(f"目标已存在：{target}；如确认覆盖，请传入 --force。")
    if check_only:
        return {
            "status": "ready",
            "source": str(source),
            "target": str(target),
            "message": "源 Skill 可安装；未执行复制。",
        }
    target_base.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=IGNORE)
    required = [
        target / "SKILL.md",
        target / "scripts" / "search.py",
        target / "data" / "products.csv",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise InstallError("安装后缺少文件：" + ", ".join(missing))
    command = [
        sys.executable,
        str(target / "scripts" / "search.py"),
        "商品卡片",
        "--domain",
        "components",
        "--json",
        "-n",
        "1",
    ]
    result = subprocess.run(
        command,
        cwd=target,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=utf8_subprocess_env(),
        timeout=30,
    )
    if result.returncode != 0:
        raise InstallError(f"安装后检索冒烟测试失败：{result.stderr[:500]}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise InstallError(f"安装后检索输出不是 JSON：{exc}") from exc
    if payload.get("count", 0) < 1:
        raise InstallError("安装后检索没有返回结果。")
    return {
        "status": "installed",
        "source": str(source),
        "target": str(target),
        "smoke_test": {
            "query": "商品卡片",
            "top_result": payload["results"][0]["id"],
            "count": payload["count"],
        },
        "message": "安装完成，已通过本地检索冒烟测试。",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="安装 MPUX Pro Skill 到 skills 目录")
    parser.add_argument("--target", default=None, help="目标 skills 目录；默认 ~/.claude/skills")
    parser.add_argument("--project", action="store_true", help="安装到当前项目 .claude/skills")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的同名 Skill")
    parser.add_argument("--check", action="store_true", help="只检查是否可安装，不复制")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = install(
            _target_base(args.target, args.project),
            force=args.force,
            check_only=args.check,
        )
    except (InstallError, OSError, subprocess.SubprocessError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    print(result["message"])
    print(f"目标：{result['target']}")
    if result.get("smoke_test"):
        print(f"冒烟测试：{result['smoke_test']['top_result']} ({result['smoke_test']['count']} 条)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())