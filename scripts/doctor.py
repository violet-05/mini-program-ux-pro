#!/usr/bin/env python3
"""诊断本机 Skill 安装，不审查用户项目或启动可选服务。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CORE_FILES = (
    "mpux.py", "SKILL.md", "skill.json", "package.json",
    "scripts/mpux_core.py", "scripts/search.py", "scripts/design_system.py",
    "scripts/generate_design_system.py", "scripts/audit_mini_program.py",
    "scripts/review_contract.py", "scripts/review_compare.py",
    "scripts/install_skill.py", "scripts/doctor.py", "scripts/validate_data.py",
    "scripts/validate_skill.py", "scripts/validate_project.py",
    "scripts/devtools_adapter.py", "scripts/visual_review_adapter.py",
    "schemas/design-system.schema.json", "schemas/search-result.schema.json",
    "schemas/review-report.schema.json", "schemas/review-comparison.schema.json",
)


def diagnose(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    def record(name: str, passed: bool, detail: str, remedy: str = "") -> None:
        checks.append({"name": name, "passed": passed, "detail": detail,
                       "remedy": remedy if not passed else ""})

    record("Python", sys.version_info >= (3, 10), sys.version.split()[0], "安装 Python 3.10+。")
    missing = []
    for relative in CORE_FILES:
        path = root / relative
        try:
            if not path.is_file() or path.stat().st_size == 0:
                missing.append(relative)
        except OSError:
            missing.append(relative)
    record("核心文件", not missing, "完整" if not missing else "缺失或为空：" + ", ".join(missing),
           "重新安装完整 Skill，不要只复制 SKILL.md。")

    version = None
    try:
        metadata = json.loads((root / "skill.json").read_text(encoding="utf-8-sig"))
        package = json.loads((root / "package.json").read_text(encoding="utf-8-sig"))
        if not isinstance(metadata, dict) or not isinstance(package, dict):
            raise ValueError("元数据根节点必须是对象")
        version = metadata.get("version")
        if metadata.get("name") != "mini-program-ux-pro" or package.get("name") != metadata["name"]:
            raise ValueError("产品名称不一致")
        if not isinstance(version, str) or not version or package.get("version") != version:
            raise ValueError("安装版本缺失或不一致")
        record("版本信息", True, version)
    except (OSError, ValueError) as exc:
        record("版本信息", False, str(exc), "从同一版本重新安装，避免混用文件。")

    try:
        from validate_data import validate
        data = validate(root / "data")
        total = sum(data["counts"].values())
        record("知识库", data["ok"], f"{total} 条记录；{len(data['errors'])} 个错误"
               + ("；" + "；".join(data["errors"][:5]) if data["errors"] else ""),
               "运行 python scripts/validate_data.py 查看具体错误，或重新安装数据文件。")
        warnings.extend(data["warnings"])
    except (ImportError, OSError, ValueError) as exc:
        record("知识库", False, str(exc), "重新安装 scripts/ 与 data/ 目录。")

    if any(not check["passed"] for check in checks):
        record("独立检索", False, "安装检查未通过，未执行检索", "先修复上述安装问题，再运行 doctor。")
    else:
        try:
            result = subprocess.run(
                [sys.executable, str(root / "mpux.py"), "search", "商品卡片",
                 "--domain", "components", "--json", "-n", "1"],
                cwd=root, capture_output=True, text=True, encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}, timeout=30,
            )
            if result.returncode != 0:
                raise ValueError(result.stderr.strip()[:500] or f"检索退出码 {result.returncode}")
            payload = json.loads(result.stdout)
            results = payload.get("results") if isinstance(payload, dict) else None
            top = results[0].get("id") if isinstance(results, list) and results and isinstance(results[0], dict) else None
            record("独立检索", top == "comp-product-card", f"商品卡片 → {top}",
                   "重新安装当前版本，检查脚本和知识库是否配套。")
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            record("独立检索", False, str(exc), "重新安装后重试；doctor 不需要联网或 API Key。")

    return {
        "ok": all(check["passed"] for check in checks),
        "version": version,
        "root": str(root),
        "python": sys.executable,
        "checks": checks,
        "warnings": warnings,
        "scope": "local-installation",
        "not_checked": ["用户项目代码", "微信开发者工具服务端口", "模拟器交互", "iOS/Android 真机", "视觉效果"],
    }


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="检查 MPUX Pro 安装是否可用；不代表用户小程序验收通过。")
    parser.add_argument("--json", action="store_true", help="输出机器可读诊断报告")
    args = parser.parse_args(argv)
    result = diagnose()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"MPUX Pro {result['version'] or '(版本未知)'} · 安装诊断")
        print(f"位置：{result['root']}")
        print(f"Python：{result['python']}")
        for check in result["checks"]:
            print(f"[{'OK' if check['passed'] else 'FAIL'}] {check['name']}：{check['detail']}")
            if check["remedy"]:
                print(f"  修复：{check['remedy']}")
        for warning in result["warnings"]:
            print(f"[WARN] {warning}")
        print("未检查：" + "、".join(result["not_checked"]))
        print("结果：" + ("核心功能可用" if result["ok"] else "请按提示修复安装"))
        if result["ok"]:
            print(f'下一步：python "{ROOT / "mpux.py"}" design --help')
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
