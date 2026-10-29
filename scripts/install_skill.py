#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 MPUX Pro 安装到 Claude/Agent Skills 目录，并执行一次检索冒烟测试。

默认安装到 ~/.claude/skills/mini-program-ux-pro。
Codex、Cursor 等工具的用户可将同一目录复制到该工具约定的 skills 目录。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__":
    sys.dont_write_bytecode = True

from mpux_core import configure_utf8_stdio, utf8_subprocess_env

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "mini-program-ux-pro"
IGNORE = shutil.ignore_patterns(
    ".git",
    ".github",
    ".claude",
    ".qoder",
    ".cursor",
    ".codex",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".cache",
    ".venv",
    ".env",
    ".env.*",
    "project.private.config.json",
    "node_modules",
    "promo-video",
    ".DS_Store",
    "design-system",
    "tmp",
    "tmp*",
    "dist",
    "build",
    "*.pyc",
    "review.json",
    "review-report.json",
    "validation.json",
)
REQUIRED_INSTALL_FILES = (
    "SKILL.md",
    "skill.json",
    "mpux.py",
    "scripts/search.py",
    "data/products.csv",
)
PROJECT_HINT = (
    "请指定源码目录之外的项目：python mpux.py install --project /path/to/app；"
    "或使用 --target /path/to/skills。"
)


class InstallError(RuntimeError):
    pass


class InstallParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InstallError(message)


def _target_base(target: str | None, project: str | None) -> Path:
    if target is not None:
        return Path(target).expanduser()
    if project is not None:
        return Path(project).expanduser() / ".claude" / "skills"
    return Path.home() / ".claude" / "skills"


def _check_directory_path(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise InstallError(f"目标路径不能是符号链接或目录联接：{part}")
        if part.exists() and not part.is_dir():
            raise InstallError(f"目标路径不是目录：{part}")


def _check_skill_identity(path: Path) -> None:
    skill_file = path / "SKILL.md"
    metadata_file = path / "skill.json"
    if (
        skill_file.is_symlink()
        or metadata_file.is_symlink()
        or not skill_file.is_file()
        or not metadata_file.is_file()
    ):
        raise InstallError(f"不是可覆盖的 {SKILL_NAME} Skill 目录（需要 SKILL.md 和 skill.json）：{path}")
    try:
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InstallError(f"无法确认 Skill 身份：{metadata_file}：{exc}") from exc
    if not isinstance(metadata, dict) or metadata.get("name") != SKILL_NAME:
        raise InstallError(f"skill.json name 不匹配，拒绝覆盖无关目录：{path}")


def _check_target(target: Path, source: Path, force: bool) -> None:
    _check_directory_path(target)
    if target == source:
        raise InstallError("目标就是当前 Skill 目录，不能覆盖自身。" + PROJECT_HINT)
    if source in target.parents:
        raise InstallError("安装目标不能位于项目源目录内，以免递归复制。" + PROJECT_HINT)
    if target in source.parents:
        raise InstallError("安装目标包含源目录，不能覆盖源目录的祖先。" + PROJECT_HINT)
    if target.exists():
        if not force:
            raise InstallError(f"目标已存在：{target}；如确认覆盖同名 Skill，请传入 --force。")
        _check_skill_identity(target)


def _check_required_files(path: Path) -> None:
    missing = [str(path / relative) for relative in REQUIRED_INSTALL_FILES if not (path / relative).is_file()]
    if missing:
        raise InstallError("Skill 缺少必需文件：" + ", ".join(missing))


def _smoke_test(staged: Path) -> dict:
    _check_required_files(staged)
    _check_skill_identity(staged)
    command = [
        sys.executable,
        "-B",
        str(staged / "scripts" / "search.py"),
        "商品卡片",
        "--domain",
        "components",
        "--json",
        "-n",
        "1",
    ]
    env = utf8_subprocess_env()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        command,
        cwd=staged,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env=env,
        timeout=30,
    )
    if result.returncode != 0:
        raise InstallError(f"安装后检索冒烟测试失败（退出码 {result.returncode}）：{result.stderr[:500]}")
    try:
        payload = json.loads(result.stdout)
    except ValueError as exc:
        raise InstallError(f"安装后检索输出不是 JSON：{exc}") from exc
    if not isinstance(payload, dict):
        raise InstallError("安装后检索 JSON 必须是对象。")
    results = payload.get("results")
    if (
        type(payload.get("count")) is not int
        or payload["count"] != 1
        or not isinstance(results, list)
        or len(results) != 1
        or not isinstance(results[0], dict)
        or results[0].get("id") != "comp-product-card"
    ):
        raise InstallError("安装后检索结果无效：应返回 1 条结果，且首项为 comp-product-card。")
    return {"query": "商品卡片", "top_result": results[0]["id"], "count": payload["count"]}


def _quoted(value: str) -> str:
    if os.name == "nt":
        return '"' + value + '"'
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _next_commands(target: Path) -> dict[str, str]:
    prefix = f"{_quoted(sys.executable)} {_quoted(str(target / 'mpux.py'))}"
    return {
        "doctor": f"{prefix} doctor",
        "search": f"{prefix} search {_quoted('商品卡片')} --domain components --json -n 1",
    }


def install(target_base: Path, *, force: bool = False, check_only: bool = False) -> dict:
    source = ROOT.resolve()
    target_base = Path(target_base).expanduser().absolute()
    _check_directory_path(target_base / SKILL_NAME)
    target_base = target_base.resolve()
    target = target_base / SKILL_NAME
    _check_target(target, source, force)
    _check_required_files(source)
    _check_skill_identity(source)
    if check_only:
        return {
            "ok": True,
            "status": "ready",
            "source": str(source),
            "target": str(target),
            "message": "源 Skill 可安装；未写入磁盘，未执行复制或检索冒烟测试。",
        }
    target_base.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}-", dir=target_base))
    staged = workspace / "staged"
    backup = workspace / "previous"
    published = False
    warnings: list[str] = []
    try:
        shutil.copytree(source, staged, ignore=IGNORE)
        smoke = _smoke_test(staged)
        _check_target(target, source, force)
        try:
            if target.exists():
                target.rename(backup)
            staged.rename(target)
        except BaseException as exc:
            if backup.exists():
                try:
                    backup.rename(target)
                except OSError as rollback_error:
                    raise InstallError(
                        f"替换失败：{exc}；自动回滚失败：{rollback_error}。旧安装完整保留在：{backup}"
                    ) from rollback_error
            raise
        published = True
    finally:
        if published or not backup.exists():
            try:
                shutil.rmtree(workspace)
            except OSError as exc:
                warnings.append(f"临时目录清理失败，请手动清理 {workspace}：{exc}")
    return {
        "ok": True,
        "status": "installed",
        "source": str(source),
        "target": str(target),
        "smoke_test": smoke,
        "commands": _next_commands(target),
        "warnings": warnings,
        "message": "安装完成，已通过本地检索冒烟测试。",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = InstallParser(
        description="安装 MPUX Pro Skill 到 skills 目录",
        epilog=PROJECT_HINT,
        allow_abbrev=False,
    )
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--target", default=None, help="目标 skills 目录；默认 ~/.claude/skills")
    destination.add_argument(
        "--project", nargs="?", const=".", default=None,
        metavar="PATH", help="安装到指定项目的 .claude/skills；省略 PATH 时使用当前目录",
    )
    parser.add_argument("--force", action="store_true", help="仅覆盖身份匹配的已有 Skill")
    parser.add_argument("--check", action="store_true", help="只检查是否可安装，不写入磁盘或运行冒烟测试")
    parser.add_argument("--json", action="store_true", help="输出机器可读的 JSON 结果或错误")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)
    json_output = "--json" in argv
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        result = install(
            _target_base(args.target, args.project),
            force=args.force,
            check_only=args.check,
        )
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        if json_output:
            print(json.dumps({"ok": False, "status": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            parser.print_usage(sys.stderr)
            print(f"错误：{exc}", file=sys.stderr)
        return 2
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(result["message"])
    print(f"目标：{result['target']}")
    if result.get("smoke_test"):
        print(f"冒烟测试：{result['smoke_test']['top_result']} ({result['smoke_test']['count']} 条)")
        print(f"下一步诊断：{result['commands']['doctor']}")
        print(f"下一步检索：{result['commands']['search']}")
    for warning in result.get("warnings", []):
        print(f"警告：{warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
