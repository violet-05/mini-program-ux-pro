#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MPUX Pro 项目自检：编译、数据、Skill、CLI、生成器与静态审查冒烟测试。"""

from __future__ import annotations

import argparse
import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _run(command: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def validate_project(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []
    scripts = root / "scripts"

    # 1. Python 语法
    compile_failures: list[str] = []
    for path in sorted(scripts.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            compile_failures.append(f"{path.name}: {exc}")
    for path in sorted((root / "tests").glob("test_*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            compile_failures.append(f"tests/{path.name}: {exc}")
    checks.append(
        _check(
            "Python 语法",
            not compile_failures,
            "全部脚本与测试可编译" if not compile_failures else "; ".join(compile_failures),
        )
    )

    # 2. 数据验证
    data_result = _run([sys.executable, str(scripts / "validate_data.py"), "--json"], root)
    data_payload: dict[str, Any] = {}
    try:
        data_payload = json.loads(data_result.stdout)
    except json.JSONDecodeError:
        pass
    checks.append(
        _check(
            "知识库验证",
            data_result.returncode == 0 and data_payload.get("ok") is True,
            f"rows={data_payload.get('counts', {})} errors={len(data_payload.get('errors', []))}",
        )
    )

    # 3. Skill 验证
    skill_result = _run([sys.executable, str(scripts / "validate_skill.py"), "--json"], root)
    skill_payload: dict[str, Any] = {}
    try:
        skill_payload = json.loads(skill_result.stdout)
    except json.JSONDecodeError:
        pass
    checks.append(
        _check(
            "Skill 结构验证",
            skill_result.returncode == 0 and skill_payload.get("ok") is True,
            f"errors={len(skill_payload.get('errors', []))} warnings={len(skill_payload.get('warnings', []))}",
        )
    )

    # 4. 文档脚本命令帮助
    help_failures = []
    for name in (
        "search.py",
        "generate_design_system.py",
        "audit_mini_program.py",
        "validate_data.py",
        "validate_skill.py",
        "install_skill.py",
        "visual_review_adapter.py",
        "devtools_adapter.py",
    ):
        result = _run([sys.executable, str(scripts / name), "--help"], root, timeout=20)
        if result.returncode != 0:
            help_failures.append(name)
    checks.append(
        _check(
            "CLI --help",
            not help_failures,
            "全部 CLI 可用" if not help_failures else "失败：" + ", ".join(help_failures),
        )
    )

    # 5. 检索冒烟测试
    search_result = _run(
        [
            sys.executable,
            str(scripts / "search.py"),
            "商品卡片",
            "--domain",
            "components",
            "--json",
            "-n",
            "1",
        ],
        root,
    )
    search_payload: dict[str, Any] = {}
    try:
        search_payload = json.loads(search_result.stdout)
    except json.JSONDecodeError:
        pass
    top_id = (
        search_payload.get("results", [{}])[0].get("id")
        if search_payload.get("results")
        else None
    )
    checks.append(
        _check(
            "检索冒烟",
            search_result.returncode == 0 and top_id == "comp-product-card",
            f"top={top_id}",
        )
    )

    # 6. 设计系统生成 + 不覆盖检查
    with tempfile.TemporaryDirectory(prefix="mpux-validate-") as temp_dir:
        output = Path(temp_dir) / "design-system"
        generation = _run(
            [
                sys.executable,
                str(scripts / "generate_design_system.py"),
                "--product",
                "音乐播放器小程序",
                "--style",
                "现代极简",
                "--stack",
                "wechat-native",
                "--output",
                str(output),
                "--format",
                "both",
            ],
            root,
        )
        required_outputs = [
            output / "MASTER.md",
            output / "MASTER.json",
            output / "tokens.wxss",
            output / "pages" / "home.md",
        ]
        generated_ok = generation.returncode == 0 and all(path.exists() for path in required_outputs)
        second = _run(
            [
                sys.executable,
                str(scripts / "generate_design_system.py"),
                "--product",
                "音乐播放器小程序",
                "--style",
                "现代极简",
                "--output",
                str(output),
                "--format",
                "both",
            ],
            root,
        )
        skip_ok = second.returncode == 0 and "已存在" in second.stdout
        checks.append(
            _check(
                "设计系统生成与防覆盖",
                generated_ok and skip_ok,
                f"generated={generated_ok} no_clobber={skip_ok}",
            )
        )

    # 7. 静态审查冒烟
    audit_result = _run(
        [
            sys.executable,
            str(scripts / "audit_mini_program.py"),
            "--path",
            "tests/fixtures/wechat-native",
            "--format",
            "json",
        ],
        root,
    )
    audit_payload: dict[str, Any] = {}
    try:
        audit_payload = json.loads(audit_result.stdout)
    except json.JSONDecodeError:
        pass
    audit_ok = (
        audit_result.returncode == 0
        and audit_payload.get("project", {}).get("stack") == "wechat-native"
        and audit_payload.get("summary", {}).get("P0", 0) >= 1
    )
    checks.append(
        _check(
            "静态审查冒烟",
            audit_ok,
            f"stack={audit_payload.get('project', {}).get('stack')} P0={audit_payload.get('summary', {}).get('P0')}",
        )
    )

    # 8. 已保存的开发者工具模拟器证据（不重新启动 DevTools）
    runtime_results = root / "verification" / "artifacts" / "results.json"
    runtime_ok = False
    runtime_detail = "未找到 verification/artifacts/results.json"
    if runtime_results.exists():
        try:
            runtime_payload = json.loads(runtime_results.read_text(encoding="utf-8"))
            screenshots = runtime_payload.get("screenshots", [])
            screenshot_ok = all(
                (root / item.get("path", "")).exists()
                for item in screenshots
                if isinstance(item, dict)
            )
            runtime_ok = (
                runtime_payload.get("status") == "passed"
                and len(runtime_payload.get("checks", [])) >= 20
                and bool(screenshots)
                and screenshot_ok
            )
            runtime_detail = (
                f"status={runtime_payload.get('status')} "
                f"checks={len(runtime_payload.get('checks', []))} "
                f"screenshots={len(screenshots)}"
            )
        except (json.JSONDecodeError, OSError) as exc:
            runtime_detail = f"证据无法读取：{exc}"
    checks.append(_check("开发者工具模拟器验收证据", runtime_ok, runtime_detail))

    # 9. Schema JSON 可解析
    schema_failures = []
    for path in sorted((root / "schemas").glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            schema_failures.append(f"{path.name}: {exc}")
    checks.append(
        _check(
            "JSON Schema",
            not schema_failures,
            "全部可解析" if not schema_failures else "; ".join(schema_failures),
        )
    )

    # 10. 文档命令路径
    documented = skill_payload.get("documented_script_commands", 0)
    checks.append(
        _check(
            "文档脚本命令",
            documented > 0,
            f"文档中识别到 {documented} 个脚本命令",
        )
    )

    passed = all(check["passed"] for check in checks)
    return {
        "ok": passed,
        "root": str(root),
        "checks": checks,
        "data_warnings": data_payload.get("warnings", []),
        "skill_warnings": skill_payload.get("warnings", []),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MPUX Pro 项目级自检")
    parser.add_argument("--path", default=str(ROOT), help="Skill 项目根目录，默认当前项目")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)
    result = validate_project(Path(args.path))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("MPUX Pro 项目自检")
        print("=" * 68)
        for check in result["checks"]:
            marker = "OK  " if check["passed"] else "FAIL"
            print(f"[{marker}] {check['name']}：{check['detail']}")
        print("=" * 68)
        if result["data_warnings"]:
            print("数据警告：")
            for warning in result["data_warnings"]:
                print(f"  - {warning}")
        if result["skill_warnings"]:
            print("Skill 警告：")
            for warning in result["skill_warnings"]:
                print(f"  - {warning}")
        print("结果：" + ("通过" if result["ok"] else "未通过"))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())