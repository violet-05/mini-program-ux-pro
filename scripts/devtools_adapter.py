#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""可选的微信开发者工具适配器。

只调用本机官方 CLI / 可选 Node automator 脚本，不开启安全设置、不伪造 CLI 参数。
服务端口需要用户手动在开发者工具“设置 → 安全设置”中开启。
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SUITE = ROOT / "verification" / "devtools" / "verify.cjs"
DEFAULT_PROJECT = ROOT / "verification"
DEFAULT_ARTIFACTS = ROOT / "verification" / "artifacts"


class DevToolsUnavailable(RuntimeError):
    pass


def _common_cli_paths() -> list[Path]:
    paths: list[Path] = []
    env_value = os.environ.get("WECHAT_DEVTOOLS_CLI")
    if env_value:
        paths.append(Path(env_value).expanduser())
    local = os.environ.get("LOCALAPPDATA")
    if local:
        paths.extend(
            [
                Path(local) / "Programs" / "微信开发者工具" / "cli.bat",
                Path(local) / "微信开发者工具" / "cli.bat",
            ]
        )
    paths.extend(
        [
            Path("C:/Program Files (x86)/Tencent/微信web开发者工具/cli.bat"),
            Path("C:/Program Files/Tencent/微信web开发者工具/cli.bat"),
            Path("/Applications/wechatwebdevtools.app/Contents/MacOS/cli"),
        ]
    )
    return paths


def find_cli(explicit: str | None = None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path.resolve() if path.exists() else None
    for candidate in _common_cli_paths():
        if candidate.exists():
            return candidate.resolve()
    return None


def _cli_command(cli_path: Path, args: list[str]) -> list[str]:
    if platform.system() == "Windows" and cli_path.suffix.casefold() in {".bat", ".cmd"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", str(cli_path), *args]
    return [str(cli_path), *args]


def _run(cmd: list[str], timeout: int = 45) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def classify_status(output: str, returncode: int) -> tuple[str, str]:
    text = (output or "").casefold()
    if "service port" in text and ("disabled" in text or "关闭" in text):
        return (
            "service_port_disabled",
            "开发者工具服务端口未开启。请在“设置 → 安全设置”开启服务端口 / CLI HTTP 调用。",
        )
    if "服务端口" in output and ("关闭" in output or "未开启" in output):
        return (
            "service_port_disabled",
            "开发者工具服务端口未开启。请在“设置 → 安全设置”开启服务端口 / CLI HTTP 调用。",
        )
    if "not login" in text or "未登录" in output or "需要登录" in output:
        return (
            "login_required",
            "开发者工具未登录。请先登录微信开发者工具后重试。",
        )
    if returncode != 0:
        return ("error", f"CLI 返回退出码 {returncode}，请检查开发者工具状态。")
    return ("ready", "CLI 可用。")


def probe(cli_path: Path) -> dict[str, Any]:
    try:
        result = _run(_cli_command(cli_path, ["islogin"]), timeout=45)
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "status": "timeout",
            "message": "CLI 查询超时，请手动检查开发者工具服务端口。",
            "cli": str(cli_path),
        }
    except OSError as exc:
        return {
            "ok": False,
            "status": "error",
            "message": f"CLI 无法启动：{exc}",
            "cli": str(cli_path),
        }
    output = (result.stdout or "") + (result.stderr or "")
    status, message = classify_status(output, result.returncode)
    return {
        "ok": status == "ready",
        "status": status,
        "message": message,
        "cli": str(cli_path),
        "returncode": result.returncode,
        "output_tail": output[-1200:],
        "remediation": (
            "打开微信开发者工具 → 设置 → 安全设置，开启服务端口 / CLI HTTP 调用。"
            if status == "service_port_disabled"
            else None
        ),
    }


def check_node_dependency() -> dict[str, Any]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    module_path = ROOT / "verification" / "devtools" / "node_modules" / "miniprogram-automator"
    return {
        "node": node,
        "npm": npm,
        "automator_installed": module_path.exists(),
        "install_hint": "cd verification/devtools && npm install" if not module_path.exists() else None,
    }


def run_suite(
    cli_path: Path,
    project: Path = DEFAULT_PROJECT,
    artifacts: Path = DEFAULT_ARTIFACTS,
    *,
    port: int = 9420,
    suite: Path = DEFAULT_SUITE,
) -> dict[str, Any]:
    status = probe(cli_path)
    if not status["ok"]:
        raise DevToolsUnavailable(status["message"])
    dependency = check_node_dependency()
    if not dependency["node"]:
        raise DevToolsUnavailable("未找到 Node.js；运行时验收需要 Node 18+。")
    if not dependency["automator_installed"]:
        raise DevToolsUnavailable(
            "未安装 miniprogram-automator。请运行：" + (dependency["install_hint"] or "")
        )
    if not suite.exists():
        raise DevToolsUnavailable(f"验收脚本不存在：{suite}")
    command = [
        dependency["node"],
        str(suite),
        "--cli",
        str(cli_path),
        "--project",
        str(project.resolve()),
        "--artifacts",
        str(artifacts.resolve()),
        "--port",
        str(port),
    ]
    result = _run(command, timeout=180)
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": command,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="可选的微信开发者工具运行时验收适配器（不修改安全设置）",
    )
    parser.add_argument("--cli", default=None, help="cli.bat/cli 的绝对路径；也可设置 WECHAT_DEVTOOLS_CLI")
    sub = parser.add_subparsers(dest="command")

    status_parser = sub.add_parser("status", help="检查 CLI 与可选依赖")
    status_parser.add_argument("--json", action="store_true")

    run_parser = sub.add_parser("run", help="运行 verification/devtools/verify.cjs")
    run_parser.add_argument("--project", default=str(DEFAULT_PROJECT))
    run_parser.add_argument("--artifacts", default=str(DEFAULT_ARTIFACTS))
    run_parser.add_argument("--port", type=int, default=9420)
    run_parser.add_argument("--json", action="store_true")

    open_parser = sub.add_parser("open", help="打开指定项目（不执行自动化）")
    open_parser.add_argument("--project", default=str(DEFAULT_PROJECT))

    return parser


def _print_status(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"CLI：{payload.get('cli') or '(未找到)'}")
    print(f"状态：{payload.get('status')}")
    print(payload.get("message", ""))
    dep = payload.get("dependencies") or {}
    if dep:
        print(f"Node：{dep.get('node') or '(缺失)'}")
        print(f"automator：{'已安装' if dep.get('automator_installed') else '未安装'}")
        if dep.get("install_hint"):
            print(f"安装：{dep['install_hint']}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cli_path = find_cli(args.cli)
    if not cli_path:
        print(
            "错误：未找到微信开发者工具 CLI。请用 --cli 指定 cli.bat 的绝对路径，"
            "或设置 WECHAT_DEVTOOLS_CLI。",
            file=sys.stderr,
        )
        return 2
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "status":
        payload = probe(cli_path)
        payload["dependencies"] = check_node_dependency()
        _print_status(payload, args.json)
        return 0 if payload["ok"] else 1

    if args.command == "open":
        try:
            result = _run(_cli_command(cli_path, ["open", "--project", str(Path(args.project).resolve())]))
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 2
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode

    if args.command == "run":
        try:
            result = run_suite(
                cli_path,
                Path(args.project),
                Path(args.artifacts),
                port=args.port,
            )
        except (DevToolsUnavailable, OSError, subprocess.TimeoutExpired) as exc:
            print(f"错误：{exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result["stdout"])
            if result["stderr"]:
                print(result["stderr"], file=sys.stderr)
        return 0 if result["ok"] else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())