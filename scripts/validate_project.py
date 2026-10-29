#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MPUX Pro 项目自检：编译、数据、Skill、CLI、生成器与静态审查冒烟测试。"""

from __future__ import annotations

import argparse
import json
import py_compile
import stat
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path, PureWindowsPath
from typing import Any

from mpux_core import configure_utf8_stdio, utf8_subprocess_env

ROOT = Path(__file__).resolve().parent.parent


def _run(command: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=utf8_subprocess_env(),
        timeout=timeout,
    )


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def _evidence_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON 字段重复：{key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> Any:
    raise ValueError(f"JSON 非法常量：{value}")


def _png_structure_error(data: bytes) -> str | None:
    """仅检查 PNG 容器结构；不解码像素，不验证截图内容或交互。"""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG 签名无效"
    offset = 8
    seen_ihdr = False
    seen_idat = False
    idat_closed = False
    idat_bytes = 0
    palette_entries = 0
    bit_depth = color_type = -1
    while offset < len(data):
        if len(data) - offset < 12:
            return "PNG 分块头或 CRC 截断"
        length, kind = struct.unpack_from(">I4s", data, offset)
        end = offset + 12 + length
        if length > 0x7FFFFFFF or end > len(data):
            return "PNG 分块长度越界或数据截断"
        chunk = data[offset + 8:end - 4]
        expected_crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(chunk, zlib.crc32(kind)) & 0xFFFFFFFF != expected_crc:
            return f"PNG {kind!r} CRC 不匹配"
        if not all(65 <= byte <= 90 or 97 <= byte <= 122 for byte in kind) or kind[2] & 32:
            return "PNG 分块类型无效"
        if not seen_ihdr and kind != b"IHDR":
            return "PNG 首块必须为 IHDR"
        if kind == b"IHDR":
            if seen_ihdr or length != 13:
                return "PNG IHDR 重复或长度无效"
            width, height, bit_depth, color_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", chunk)
            )
            if not (0 < width <= 0x7FFFFFFF and 0 < height <= 0x7FFFFFFF):
                return "PNG IHDR 尺寸无效"
            depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
            if (
                bit_depth not in depths.get(color_type, ())
                or compression != 0
                or filtering != 0
                or interlace not in (0, 1)
            ):
                return "PNG IHDR 编码参数无效"
            seen_ihdr = True
        elif kind == b"PLTE":
            if (
                palette_entries or seen_idat or color_type in (0, 4)
                or length == 0 or length % 3 or length > 768
                or (color_type == 3 and length // 3 > 2 ** bit_depth)
            ):
                return "PNG PLTE 长度、顺序或颜色类型无效"
            palette_entries = length // 3
        elif kind == b"IDAT":
            if idat_closed or (color_type == 3 and not palette_entries):
                return "PNG IDAT 顺序无效或缺少 PLTE"
            seen_idat = True
            idat_bytes += length
        elif kind == b"IEND":
            if length != 0 or end != len(data):
                return "PNG IEND 长度无效或存在尾随数据"
            if not seen_idat or not idat_bytes:
                return "PNG 缺少非空 IDAT 数据"
            return None
        elif not kind[0] & 32:
            return f"PNG 未知关键分块：{kind!r}"
        if seen_idat and kind != b"IDAT":
            idat_closed = True
        offset = end
    return "PNG 缺少 IEND 或分块截断"


def _runtime_evidence(root: Path) -> tuple[bool, str]:
    runtime_results = root / "verification" / "artifacts" / "results.json"
    try:
        payload = json.loads(
            runtime_results.read_text(encoding="utf-8"),
            object_pairs_hook=_evidence_json_object,
            parse_constant=_reject_json_constant,
        )
        root = root.resolve(strict=True)
    except FileNotFoundError:
        return False, "未找到 verification/artifacts/results.json 或项目目录"
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        return False, f"证据无法读取（UTF-8 JSON 或路径无效）：{exc}"

    if not isinstance(payload, dict):
        return False, "证据 JSON 根对象必须为 dict"
    for field in ("status", "checks", "screenshots", "console_error_count", "exceptions"):
        if field not in payload:
            return False, f"证据缺少必填字段：{field}"
    if payload["status"] != "passed":
        return False, "status 必须为 passed"
    checks = payload["checks"]
    if not isinstance(checks, list) or len(checks) < 20:
        return False, "checks 必须为非空 list 且至少包含 20 项"
    for index, item in enumerate(checks):
        if not isinstance(item, dict) or item.get("passed") is not True:
            return False, f"checks[{index}] 必须为 dict 且 passed 必须为 true"
    screenshots = payload["screenshots"]
    if not isinstance(screenshots, list) or not screenshots:
        return False, "screenshots 必须为非空 list"
    if type(payload["console_error_count"]) is not int or payload["console_error_count"] != 0:
        return False, "console_error_count 必须为整数 0（不接受 bool）"
    if not isinstance(payload["exceptions"], list) or payload["exceptions"]:
        return False, "exceptions 必须为 list 且为空"

    for index, item in enumerate(screenshots):
        label = f"screenshots[{index}].path"
        if not isinstance(item, dict):
            return False, f"screenshots[{index}] 必须为 dict"
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return False, f"{label} 必须为非空字符串"
        try:
            # 同时拒绝 POSIX、Windows 绝对/驱动器路径，避免跨平台绕过。
            relative_path = Path(raw_path.replace("\\", "/"))
            if relative_path.is_absolute() or PureWindowsPath(raw_path).anchor:
                return False, f"{label} 必须为项目内相对路径"
            if "\x00" in raw_path or ":" in raw_path:
                return False, f"{label} 包含非法路径字符"
            screenshot = (root / relative_path).resolve(strict=True)
            if not screenshot.is_relative_to(root):
                return False, f"{label} resolve 后逃逸项目目录"
            file_stat = screenshot.stat()
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size == 0:
                return False, f"{label} 必须指向常规非空文件"
            png_error = _png_structure_error(screenshot.read_bytes())
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            return False, f"{label} 截图缺失、无法读取或路径无效：{exc}"
        if png_error:
            return False, f"{label}：{png_error}"
    return True, (
        f"status=passed checks={len(checks)} screenshots={len(screenshots)}"
        "；PNG 结构完整性检查通过（未解码像素，未验证截图内容或交互）"
    )


def validate_project(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir() or not (root / "SKILL.md").is_file():
        raise ValueError("--path 必须指向 MPUX Pro 源码仓库；检查安装用 doctor，审查小程序用 audit。")
    checks: list[dict[str, Any]] = []
    scripts = root / "scripts"

    # 1. Python 语法
    compile_failures: list[str] = []
    for path in [root / "mpux.py", *sorted(scripts.glob("*.py"))]:
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
        "../mpux.py",
        "doctor.py",
        "search.py",
        "generate_design_system.py",
        "audit_mini_program.py",
        "review_compare.py",
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

    # 7. 静态审查冒烟 + 报告契约/对比冒烟
    with tempfile.TemporaryDirectory(prefix="mpux-review-") as temp_dir:
        review_path = Path(temp_dir) / "review.json"
        audit_result = _run(
            [
                sys.executable,
                str(scripts / "audit_mini_program.py"),
                "--path",
                "tests/fixtures/wechat-native",
                "--format",
                "json",
                "--output",
                str(review_path),
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
        compare_result = _run(
            [
                sys.executable,
                str(scripts / "review_compare.py"),
                str(review_path),
                str(review_path),
                "--json",
            ],
            root,
        )
        compare_payload: dict[str, Any] = {}
        try:
            compare_payload = json.loads(compare_result.stdout)
        except json.JSONDecodeError:
            pass
        compare_summary = compare_payload.get("summary", {})
        compare_ok = (
            compare_result.returncode == 0
            and compare_summary.get("new") == 0
            and compare_summary.get("resolved") == 0
            and compare_summary.get("remaining", 0) >= 1
        )
        checks.append(
            _check(
                "审查对比冒烟",
                compare_ok,
                f"new={compare_summary.get('new')} resolved={compare_summary.get('resolved')} remaining={compare_summary.get('remaining')}",
            )
        )

    # 8. 已保存的开发者工具模拟器证据（不重新启动 DevTools）
    runtime_ok, runtime_detail = _runtime_evidence(root)
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
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="MPUX Pro 项目级自检")
    parser.add_argument("--path", default=str(ROOT), help="Skill 项目根目录，默认当前项目")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)
    try:
        result = validate_project(Path(args.path))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"错误：{exc}", file=sys.stderr)
        return 2
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