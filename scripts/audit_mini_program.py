#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信小程序静态设计/交互审查。

只做静态代码审查。不会打开微信开发者工具、浏览器或真机，也不会修改项目。
输出 Markdown 或 JSON 报告，明确区分自动检查、规则辅助判断和需人工确认项。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from mpux_core import configure_utf8_stdio
from review_contract import SCHEMA_VERSION, ReportError, finding_fingerprint, validate_report

VERSION = "1.0.0"
SKIP_DIRS = {
    ".git",
    ".claude",
    ".qoder",
    ".cursor",
    ".codex",
    ".venv",
    ".idea",
    ".vscode",
    ".gradle",
    "node_modules",
    "miniprogram_npm",
    "unpackage",
    "dist",
    "build",
    ".nuxt",
    ".output",
    "design-system",
    "__pycache__",
    ".pytest_cache",
}
TEXT_EXTENSIONS = {
    ".wxml",
    ".wxss",
    ".wxs",
    ".json",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".vue",
    ".nvue",
    ".scss",
    ".sass",
    ".less",
    ".css",
}
CODE_EXTENSIONS = {".js", ".ts", ".tsx", ".jsx", ".vue", ".nvue"}
PAGE_TEMPLATE_EXTENSIONS = {".wxml", ".vue", ".nvue", ".tsx", ".jsx"}
STYLE_EXTENSIONS = {".wxss", ".scss", ".sass", ".less", ".css", ".vue", ".nvue"}
HTML_TAG_RE = re.compile(
    r"<\s*(div|span|img|a|p|section|header|footer|main|ul|li|table)\b",
    re.IGNORECASE,
)
BROWSER_API_PATTERNS = [
    ("document.", re.compile(r"\bdocument\s*\.")),
    ("window.", re.compile(r"\bwindow\s*\.")),
    ("localStorage", re.compile(r"\blocalStorage\b")),
    ("sessionStorage", re.compile(r"\bsessionStorage\b")),
    ("querySelector", re.compile(r"\bquerySelector(?:All)?\s*\(")),
    ("getElementById", re.compile(r"\bgetElementById\s*\(")),
    ("history.pushState", re.compile(r"\bhistory\s*\.\s*(?:pushState|replaceState)\s*\(")),
]
PRIVACY_API_RE = re.compile(
    r"\b(?:wx|uni|Taro)\s*\.\s*"
    r"(?:getLocation|chooseLocation|chooseMedia|chooseImage|chooseMessageFile|"
    r"getPhoneNumber|chooseAvatar|saveImageToPhotosAlbum|startRecord|getClipboardData|"
    r"getUserProfile)\b"
)
SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
STACK_LABELS = {
    "wechat-native": "微信原生小程序",
    "uni-app": "uni-app",
    "taro": "Taro",
    "browser-prototype": "浏览器原型",
    "unknown": "未识别",
}


class AuditError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _strip_trailing_commas(text: str) -> str:
    """删除字符串外的尾逗号，避免破坏值中的 ,} 或 ,] 。"""
    result: list[str] = []
    index = 0
    in_string = False
    escape = False
    length = len(text)
    while index < length:
        char = text[index]
        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < length and text[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < length and text[lookahead] in "}]":
                index += 1
                continue
        result.append(char)
        index += 1
    return "".join(result)


def _strip_json_comments(text: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escape = False
    length = len(text)
    while index < length:
        char = text[index]
        if in_string:
            result.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == "/" and index + 1 < length:
            next_char = text[index + 1]
            if next_char == "/":
                index += 2
                while index < length and text[index] not in "\r\n":
                    index += 1
                continue
            if next_char == "*":
                index += 2
                while index + 1 < length and text[index : index + 2] != "*/":
                    if text[index] in "\r\n":
                        result.append(text[index])
                    index += 1
                index += 2
                continue
        result.append(char)
        index += 1
    return _strip_trailing_commas("".join(result))


def _load_jsonc(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    try:
        payload = json.loads(_strip_json_comments(text))
    except (ValueError, RecursionError) as exc:
        raise AuditError(f"配置无法解析：{path}；{exc}") from exc
    if not isinstance(payload, dict):
        raise AuditError(f"配置根节点必须是 JSON 对象：{path}")
    return payload


def _input_exists(path: Path) -> bool:
    try:
        path.stat()
    except FileNotFoundError:
        return False
    except (OSError, ValueError) as exc:
        raise AuditError(f"无法检查输入路径：{path}；{exc}") from exc
    return True


def _inside_project(root: Path, path: Path, label: str) -> Path:
    try:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError, RuntimeError) as exc:
        raise AuditError(f"{label} 必须是可访问的项目内路径：{path}；{exc}") from exc
    return resolved


def _input_route(
    value: Any, root: Path, base: Path, label: str, *, allow_root: bool = False
) -> str:
    if not isinstance(value, str):
        raise AuditError(f"{label} 必须是字符串：{base}；收到 {value!r}")
    route = value.replace("\\", "/")
    if (
        (not route.strip() and not (allow_root and route == ""))
        or route.startswith("/")
        or re.match(r"^[A-Za-z]:", route)
        or ".." in route.split("/")
        or "\x00" in route
        or (not allow_root and all(part in {"", "."} for part in route.split("/")))
    ):
        raise AuditError(f"{label} 必须是项目内相对路径，不能使用绝对路径或 ..：{base}；{value!r}")
    _inside_project(root, base / route, label)
    return route.rstrip("/")


def _line_number(text: str, position: int) -> int:
    return text.count("\n", 0, max(0, position)) + 1


def _excerpt(line: str, limit: int = 180) -> str:
    value = " ".join(line.strip().split())
    return value[:limit] + ("…" if len(value) > limit else "")


def _walk_project_files(root: Path) -> Iterator[Path]:
    from stat import S_ISREG

    def onerror(exc: OSError) -> None:
        raise AuditError(f"无法遍历项目目录：{exc.filename or root}；{exc}") from exc

    current = root
    try:
        for directory, subdirectories, names in os.walk(root, onerror=onerror):
            current = Path(directory)
            _inside_project(root, current, "扫描目录")
            subdirectories[:] = sorted(name for name in subdirectories if name not in SKIP_DIRS)
            for name in sorted(names):
                current = Path(directory) / name
                if S_ISREG(current.lstat().st_mode):
                    yield current
    except (OSError, ValueError) as exc:
        raise AuditError(f"无法扫描输入文件：{current}；{exc}") from exc


def _find_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in _walk_project_files(root):
        if path.suffix.casefold() not in TEXT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > 800_000:
                continue
        except (OSError, ValueError) as exc:
            raise AuditError(f"无法读取文件状态：{path}；{exc}") from exc
        files.append(path)
        if len(files) > 4000:
            raise AuditError("待审查源码超过 4000 个文件；请用 --path 指向具体小程序目录，避免不完整审查。")
    return sorted(files)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="strict")
    except (OSError, ValueError) as exc:
        raise AuditError(f"无法读取 UTF-8 文本：{path}；{exc}") from exc


def _package_dependencies(root: Path) -> set[str]:
    package_path = root / "package.json"
    if not _input_exists(package_path):
        return set()
    _inside_project(root, package_path, "package.json")
    payload = _load_jsonc(package_path)
    dependencies: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        if key not in payload:
            continue
        section = payload[key]
        if not isinstance(section, dict) or not all(
            isinstance(value, str) for value in section.values()
        ):
            raise AuditError(f"package.json 的 {key} 必须是依赖名到版本字符串的对象：{package_path}")
        dependencies.update(section.keys())
    return dependencies


def _detect_stack(root: Path) -> tuple[str, str, Path]:
    from stat import S_ISDIR

    dependencies = _package_dependencies(root)
    project_path = root / "project.config.json"
    has_project_config = _input_exists(project_path)
    app_root = root
    if has_project_config:
        _inside_project(root, project_path, "project.config.json")
        project_config = _load_jsonc(project_path)
        if "miniprogramRoot" in project_config:
            route = _input_route(
                project_config["miniprogramRoot"], root, root,
                f"{project_path} 的 miniprogramRoot", allow_root=True,
            )
            app_root = _inside_project(root, root / route, "miniprogramRoot")
            try:
                is_directory = S_ISDIR(app_root.stat().st_mode)
            except (OSError, ValueError) as exc:
                raise AuditError(f"miniprogramRoot 目录无法读取：{app_root}；{exc}") from exc
            if not is_directory:
                raise AuditError(f"miniprogramRoot 必须是项目内目录：{app_root}")
    if "@tarojs/taro" in dependencies or any(item.startswith("@tarojs/") for item in dependencies):
        return "taro", "package.json 检测到 @tarojs/* 依赖", root
    if "@dcloudio/uni-app" in dependencies or any(
        item.startswith("@dcloudio/") for item in dependencies
    ):
        return "uni-app", "package.json 检测到 @dcloudio/* 依赖", root
    if has_project_config:
        if _input_exists(app_root / "app.json") or _input_exists(root / "app.json"):
            return "wechat-native", "检测到 project.config.json 与 app.json（含 miniprogramRoot）", app_root
    if _input_exists(root / "app.json"):
        return "wechat-native", "检测到 app.json", root
    if _input_exists(root / "pages.json") or _input_exists(root / "src" / "pages.json"):
        return "uni-app", "检测到 pages.json", root / "src" if _input_exists(root / "src" / "pages.json") else root
    if _input_exists(root / "app.config.ts") or _input_exists(root / "app.config.js"):
        return "taro", "检测到 app.config.*", root
    if any(path.suffix.casefold() == ".html" for path in _walk_project_files(root)):
        return "browser-prototype", "仅检测到浏览器 HTML，未发现小程序工程配置", root
    return "unknown", "未发现 app.json、pages.json、app.config 或 @tarojs/@dcloudio 依赖", root


def _find_config_path(root: Path, app_root: Path, names: list[str]) -> Path | None:
    for base in (app_root, root, root / "src"):
        for name in names:
            candidate = base / name
            if _input_exists(candidate):
                _inside_project(root, candidate, "配置文件")
                return candidate
    return None


def _extract_pages(project: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    stack = project["stack"]
    root: Path = project["root"]
    app_root: Path = project["app_root"]
    config = project.get("app_config")
    config_path: Path | None = project.get("app_config_path")
    label = str(config_path or app_root)
    pages: list[str] = []
    evidence: list[dict[str, Any]] = []

    def page_list(raw_pages: Any, field: str, package_root: str = "") -> None:
        if not isinstance(raw_pages, list):
            raise AuditError(f"{label} 的 {field} 必须是数组")
        for index, item in enumerate(raw_pages):
            value = item.get("path") if isinstance(item, dict) else item
            route = _input_route(
                value, root, app_root / package_root, f"{label} 的 {field}[{index}]",
            )
            pages.append(f"{package_root}/{route}" if package_root else route)

    if stack in {"wechat-native", "uni-app"}:
        if config is None and config_path is None:
            config = {}
        if not isinstance(config, dict):
            raise AuditError(f"配置根节点必须是 JSON 对象：{label}")
        page_list(config.get("pages", []), "pages")
        for key in ("subPackages", "subpackages"):
            if key not in config:
                continue
            subpackages = config[key]
            if not isinstance(subpackages, list):
                raise AuditError(f"{label} 的 {key} 必须是数组")
            for index, package in enumerate(subpackages):
                field = f"{key}[{index}]"
                if not isinstance(package, dict):
                    raise AuditError(f"{label} 的 {field} 必须是对象")
                package_root = _input_route(
                    package.get("root"), root, app_root, f"{label} 的 {field}.root",
                )
                page_list(package.get("pages"), f"{field}.pages", package_root)
        if config_path:
            config_file = _inside_project(root, config_path, "配置文件")
            evidence.append({"file": str(config_file.relative_to(root.resolve())).replace("\\", "/"), "line": 1})
    elif stack == "taro":
        if config_path:
            config_file = _inside_project(root, config_path, "配置文件")
            text = _read_text(config_path)
            match = re.search(r"pages\s*:\s*\[(.*?)\]", text, re.DOTALL)
            if match:
                page_list(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)), "pages")
                evidence.append(
                    {
                        "file": str(config_file.relative_to(root.resolve())).replace("\\", "/"),
                        "line": _line_number(text, match.start()),
                    }
                )
    return pages, evidence


def _page_candidates(project: dict[str, Any], page: str) -> list[Path]:
    stack = project["stack"]
    root: Path = project["root"]
    app_root: Path = project["app_root"]
    page = _input_route(page, root, app_root, "页面路径")
    bases: list[Path] = []
    for candidate in (app_root, root, root / "src", root / "miniprogram"):
        if candidate not in bases and _input_exists(candidate):
            _inside_project(root, candidate, "页面目录")
            bases.append(candidate)
    if stack == "wechat-native":
        extensions = [".wxml", ".js", ".ts", ".json", ".wxss", ".wxs"]
    elif stack == "uni-app":
        extensions = [".vue", ".nvue", ".json", ".uts", ".ts"]
    elif stack == "taro":
        extensions = [".tsx", ".jsx", ".vue", ".ts", ".js", ".config.ts", ".config.js"]
    else:
        extensions = [".wxml", ".vue", ".tsx", ".jsx", ".html"]
    paths: list[Path] = []
    for base in bases:
        for extension in extensions:
            candidate = base / f"{page}{extension}"
            _inside_project(root, candidate, "页面文件")
            if candidate not in paths:
                paths.append(candidate)
    return paths


def _load_project(
    path: Path, design_system_path: Path | None = None
) -> dict[str, Any]:
    from stat import S_ISDIR

    try:
        root = path.resolve()
        is_directory = S_ISDIR(root.stat().st_mode)
    except FileNotFoundError as exc:
        raise AuditError(f"项目路径不存在：{path}") from exc
    except (OSError, ValueError, RuntimeError) as exc:
        raise AuditError(f"项目路径无法读取：{path}；{exc}") from exc
    if not is_directory:
        raise AuditError(f"项目路径不是目录：{path}")
    stack, reason, app_root = _detect_stack(root)
    project: dict[str, Any] = {
        "root": root,
        "stack": stack,
        "stack_reason": reason,
        "app_root": app_root,
        "app_config": None,
        "app_config_path": None,
        "files": _find_files(root),
    }
    config_names = ["app.json", "pages.json", "app.config.ts", "app.config.js"]
    config_path = _find_config_path(root, app_root, config_names)
    project["app_config_path"] = config_path
    if config_path and config_path.suffix == ".json":
        project["app_config"] = _load_jsonc(config_path)
    elif config_path:
        project["app_config"] = {}
    pages, page_evidence = _extract_pages(project)
    project["pages"] = pages
    project["page_evidence"] = page_evidence
    project["page_files"] = {page: _page_candidates(project, page) for page in pages}
    project["existing_page_files"] = {
        page: [candidate for candidate in candidates if _input_exists(candidate)]
        for page, candidates in project["page_files"].items()
    }
    try:
        project["design_system"] = _find_design_system(root, design_system_path)
    except (OSError, ValueError) as exc:
        raise AuditError(f"设计系统路径无法读取：{design_system_path or root}；{exc}") from exc
    if design_system_path is not None and project["design_system"] is None:
        raise AuditError(
            f"指定设计系统不存在或不是有效 MASTER.json：{design_system_path}"
        )
    return project


def _find_design_system(
    root: Path, explicit: Path | None = None
) -> dict[str, Any] | None:
    if explicit is not None:
        explicit = explicit.expanduser().resolve()
        if explicit.is_dir():
            candidates = [
                explicit / "MASTER.json",
                explicit / "design-system" / "MASTER.json",
                *sorted((explicit / "design-system").glob("*/MASTER.json")),
            ]
        else:
            candidates = [explicit]
    else:
        candidates = []
        for base in [root, *list(root.parents)[:2]]:
            design_root = base / "design-system"
            candidates.append(design_root / "MASTER.json")
            if design_root.exists():
                candidates.extend(sorted(design_root.glob("*/MASTER.json")))
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if not candidate.is_file():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError) as exc:
            raise AuditError(f"设计系统无法读取：{candidate}；{exc}") from exc
        if not isinstance(payload, dict):
            raise AuditError(f"设计系统根节点必须是 JSON 对象：{candidate}")
        for field in ("project", "tokens"):
            if not isinstance(payload.get(field), dict):
                raise AuditError(f"设计系统 {field} 必须是对象：{candidate}")
        name = payload["project"].get("name")
        if not isinstance(name, str) or not name.strip():
            raise AuditError(f"设计系统 project.name 必须是非空字符串：{candidate}")
        colors = payload["tokens"].get("colors")
        if not isinstance(colors, dict) or not colors or not all(
            isinstance(value, str) and value.strip() for value in colors.values()
        ):
            raise AuditError(f"设计系统 tokens.colors 必须是非空的字符串映射：{candidate}")
        generator = payload.get("generator", {})
        if not isinstance(generator, dict):
            raise AuditError(f"设计系统 generator 必须是对象：{candidate}")
        if "version" in generator and not isinstance(generator["version"], str):
            raise AuditError(f"设计系统 generator.version 必须是字符串：{candidate}")
        for field in ("schema_version", "generated_at"):
            if field in payload and not isinstance(payload[field], str):
                raise AuditError(f"设计系统 {field} 必须是字符串：{candidate}")
        return {
            "path": candidate,
            "data": payload,
            "version": generator.get("version"),
            "schema_version": payload.get("schema_version"),
            "tokens": {value.upper() for value in colors.values() if value.startswith("#")},
        }
    return None


def _config_navigation_custom(project: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    config = project.get("app_config") or {}
    evidence: list[dict[str, Any]] = []
    if isinstance(config, dict):
        window = config.get("window")
        if isinstance(window, dict) and window.get("navigationStyle") == "custom":
            evidence.append({"file": _relative(project, project.get("app_config_path")), "line": 1})
    for page, files in project.get("existing_page_files", {}).items():
        for page_file in files:
            if page_file.suffix != ".json":
                continue
            page_config = _load_jsonc(page_file)
            style = page_config.get("style") if isinstance(page_config, dict) else None
            if isinstance(page_config, dict) and (
                page_config.get("navigationStyle") == "custom"
                or (isinstance(style, dict) and style.get("navigationStyle") == "custom")
            ):
                evidence.append({"file": _relative(project, page_file), "line": 1})
    if project["stack"] == "taro" and project.get("app_config_path"):
        text = _read_text(project["app_config_path"])
        if "navigationStyle" in text and "custom" in text:
            evidence.append({"file": _relative(project, project["app_config_path"]), "line": _line_number(text, text.find("navigationStyle"))})
    return bool(evidence), evidence


def _relative(project: dict[str, Any], path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(project["root"])).replace("\\", "/")
    except ValueError:
        return str(path)


def _finding(
    severity: str,
    category: str,
    title: str,
    evidence: list[dict[str, Any]],
    why: str,
    recommendation: str,
    rule_ids: list[str],
    verification: str = "automated",
    confidence: str = "high",
) -> dict[str, Any]:
    return {
        "severity": severity,
        "category": category,
        "title": title,
        "evidence": [item for item in evidence if item.get("file")],
        "why": why,
        "recommendation": recommendation,
        "rule_ids": rule_ids,
        "verification": verification,
        "confidence": confidence,
    }


def _add(
    findings: list[dict[str, Any]],
    seen: set[tuple[str, str, tuple[str, ...]]],
    *,
    severity: str,
    category: str,
    title: str,
    evidence: list[dict[str, Any]],
    why: str,
    recommendation: str,
    rule_ids: list[str],
    verification: str = "automated",
    confidence: str = "high",
) -> None:
    key = (category, title, tuple(sorted({item["file"] for item in evidence if item.get("file")})))
    if key in seen:
        return
    seen.add(key)
    findings.append(
        _finding(
            severity,
            category,
            title,
            evidence[:4],
            why,
            recommendation,
            rule_ids,
            verification,
            confidence,
        )
    )


def _page_source_texts(project: dict[str, Any]) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for page, files in project.get("existing_page_files", {}).items():
        for path in files:
            if path.suffix.casefold() in PAGE_TEMPLATE_EXTENSIONS or path.suffix.casefold() in {".js", ".ts"}:
                results.append((_relative(project, path), _read_text(path)))
    if not results:
        for path in project["files"]:
            if path.suffix.casefold() in {".wxml", ".vue", ".nvue", ".tsx"}:
                results.append((_relative(project, path), _read_text(path)))
    return results


def _extract_style_blocks(path: Path, text: str) -> list[tuple[str, str, int]]:
    if path.suffix.casefold() in {".vue", ".nvue"}:
        blocks = []
        for match in re.finditer(r"<style[^>]*>(.*?)</style>", text, re.DOTALL | re.IGNORECASE):
            content = match.group(1)
            line = _line_number(text, match.start(1))
            blocks.append((_relative(_PROJECT, path), content, line))
        return blocks
    return [(_relative(_PROJECT, path), text, 1)]


def _check_project_structure(
    project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]
) -> int:
    count = 0
    if project["stack"] in {"browser-prototype", "unknown"}:
        return 0
    if not project.get("pages"):
        _add(
            findings,
            seen,
            severity="P1",
            category="工程结构",
            title="未发现页面声明",
            evidence=[{"file": _relative(project, project.get("app_config_path")) or ".", "line": 1}],
            why="静态审查无法确认页面范围，也不能验证是否为可运行的小程序。",
            recommendation="确认项目路径或检查 app.json/pages.json 的 pages 配置。",
            rule_ids=["mp-route-stack"],
            verification="rule-assisted",
            confidence="medium",
        )
        count += 1
    for page, candidates in project.get("page_files", {}).items():
        existing = [candidate for candidate in candidates if candidate.exists()]
        stack = project["stack"]
        if not any(candidate.suffix.casefold() in PAGE_TEMPLATE_EXTENSIONS for candidate in existing):
            _add(
                findings,
                seen,
                severity="P0",
                category="工程结构",
                title=f"声明的页面缺少模板文件：{page}",
                evidence=[{"file": _relative(project, project.get("app_config_path")), "line": 1, "excerpt": f"已声明页面：{page}"}],
                why=f"路由指向不存在的页面模板，用户进入后会失败。目标技术栈：{STACK_LABELS.get(stack, stack)}。",
                recommendation="补齐页面模板或从配置中移除该路由；修复后重新编译。",
                rule_ids=["mp-route-stack", "wx-project-structure" if stack == "wechat-native" else "uni-project"],
            )
            count += 1
            continue
        if stack == "wechat-native":
            required = {
                ".js": "页面逻辑",
                ".ts": "页面逻辑",
                ".json": "页面配置",
            }
            missing_js = not any(candidate.suffix.casefold() in {".js", ".ts"} for candidate in existing)
            if missing_js:
                _add(
                    findings,
                    seen,
                    severity="P1",
                    category="工程结构",
                    title=f"页面缺少逻辑文件：{page}",
                    evidence=[{"file": _relative(project, project.get("app_config_path")), "line": 1, "excerpt": page}],
                    why="小程序页面通常需要 JS/TS 逻辑文件；仅有模板无法完成数据与事件。",
                    recommendation="补齐页面逻辑或确认是否为静态占位页，并在配置中移除不可用路由。",
                    rule_ids=["wx-project-structure"],
                )
                count += 1
            if not any(candidate.suffix.casefold() == ".json" for candidate in existing):
                _add(
                    findings,
                    seen,
                    severity="P3",
                    category="工程结构",
                    title=f"页面缺少独立 JSON 配置：{page}",
                    evidence=[{"file": _relative(project, project.get("app_config_path")), "line": 1, "excerpt": page}],
                    why="页面标题和局部导航配置可能缺失；并非所有页面都必须有 JSON，但应确认是否使用全局配置。",
                    recommendation="确认标题、导航和组件配置；需要时补充页面 JSON。",
                    rule_ids=["wx-page-config"],
                    verification="rule-assisted",
                    confidence="low",
                )
                count += 1
    return count


def _check_tabbar(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> int:
    config = project.get("app_config") or {}
    if not isinstance(config, dict):
        return 0
    tabbar = config.get("tabBar")
    if not isinstance(tabbar, dict):
        return 0
    count = 0
    items = tabbar.get("list")
    config_path = _relative(project, project.get("app_config_path"))
    if isinstance(items, list):
        if len(items) > 5:
            _add(
                findings,
                seen,
                severity="P1",
                category="导航",
                title="TabBar 项目超过平台上限",
                evidence=[{"file": config_path, "line": 1, "excerpt": f"tabBar.list 共 {len(items)} 项"}],
                why="官方配置限制 tabBar 最少 2 项、最多 5 项；官方设计指南建议不超过 4 项。",
                recommendation="将入口压缩到 3–4 个稳定一级区域，把次要入口移到首页或“我的”。",
                rule_ids=["mp-tabbar", "ux-navigation"],
            )
            count += 1
        elif len(items) == 5:
            _add(
                findings,
                seen,
                severity="P3",
                category="导航",
                title="TabBar 使用 5 项，点击区可能过窄",
                evidence=[{"file": config_path, "line": 1, "excerpt": f"tabBar.list 共 {len(items)} 项"}],
                why="平台允许 5 项，但官方设计指南建议不超过 4 项以保证点击区域。",
                recommendation="评估低频入口，优先减少到 4 项以内。",
                rule_ids=["mp-tabbar", "ux-touch-target"],
                verification="rule-assisted",
                confidence="medium",
            )
            count += 1
        if len(items) < 2:
            _add(
                findings,
                seen,
                severity="P1",
                category="导航",
                title="TabBar 项目少于平台下限",
                evidence=[{"file": config_path, "line": 1, "excerpt": f"tabBar.list 共 {len(items)} 项"}],
                why="tabBar 至少需要 2 项；少于 2 项时不应使用 TabBar。",
                recommendation="移除 tabBar 或补充真正的同级主区域。",
                rule_ids=["mp-tabbar"],
            )
            count += 1
        for item in items:
            if not isinstance(item, dict):
                continue
            if not item.get("text"):
                _add(
                    findings,
                    seen,
                    severity="P2",
                    category="导航",
                    title="TabBar 项目缺少文字标签",
                    evidence=[{"file": config_path, "line": 1, "excerpt": str(item)[:120]}],
                    why="只放图标的 TabBar 可访问性和可理解性较差。",
                    recommendation="为每项提供简短文字标签。",
                    rule_ids=["mp-tabbar", "ux-touch-target"],
                    verification="automated",
                )
                count += 1
            for icon_key in ("iconPath", "selectedIconPath"):
                icon = item.get(icon_key)
                if isinstance(icon, str) and (icon.startswith("http://") or icon.startswith("https://")):
                    _add(
                        findings,
                        seen,
                        severity="P2",
                        category="导航",
                        title="TabBar 使用网络图标",
                        evidence=[{"file": config_path, "line": 1, "excerpt": icon}],
                        why="官方配置说明 TabBar 图标不支持网络图片。",
                        recommendation="使用本地图标资源并检查 81×81px 与 40KB 限制。",
                        rule_ids=["mp-tabbar-icon"],
                    )
                    count += 1
    custom = tabbar.get("custom") is True
    if custom and project["stack"] == "wechat-native":
        custom_dirs = list(project["root"].glob("custom-tab-bar")) + list(project["root"].glob("miniprogram/custom-tab-bar"))
        has_component = any(
            any(directory.glob(f"index{suffix}") for suffix in (".js", ".ts", ".json", ".wxml", ".wxss"))
            for directory in custom_dirs
            if directory.is_dir()
        )
        if not has_component:
            _add(
                findings,
                seen,
                severity="P1",
                category="导航",
                title="启用 customTabBar 但未找到 custom-tab-bar 组件",
                evidence=[{"file": config_path, "line": 1, "excerpt": "\"custom\": true"}],
                why="自定义 TabBar 需要项目内对应的组件实现，否则首页导航不可用。",
                recommendation="补齐 custom-tab-bar，并同步选中态、未读和安全区。",
                rule_ids=["mp-tabbar", "wx-custom-tabbar"],
            )
            count += 1
    return count


def _check_navigation(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> int:
    custom, evidence = _config_navigation_custom(project)
    if not custom:
        return 0
    combined = "\n".join(text for _, text in _page_source_texts(project))
    combined += "\n" + "\n".join(_read_text(path) for path in project["files"] if path.suffix.casefold() in CODE_EXTENSIONS)
    has_capsule_measurement = bool(
        re.search(r"getMenuButtonBoundingClientRect|menuButtonBoundingClientRect", combined)
    )
    has_status_height = bool(
        re.search(r"statusBarHeight|getWindowInfo|safeArea|safe-area-inset", combined)
    )
    if not (has_capsule_measurement and has_status_height):
        _add(
            findings,
            seen,
            severity="P1",
            category="导航",
            title="自定义导航未发现完整的胶囊/状态栏计算",
            evidence=evidence,
            why="开启 navigationStyle=custom 后平台只保留右上角胶囊，导航高度与返回热区必须按设备计算，不能硬编码。",
            recommendation="使用 wx.getWindowInfo 与 wx.getMenuButtonBoundingClientRect（或对应框架封装）计算状态栏和胶囊区域，并真机验证。",
            rule_ids=["mp-custom-nav", "mp-status-bar"],
            verification="rule-assisted",
            confidence="medium",
        )
        return 1
    return 0


def _check_dom_and_apis(
    project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]
) -> int:
    count = 0
    stack = project["stack"]
    for path in project["files"]:
        suffix = path.suffix.casefold()
        text = _read_text(path)
        rel = _relative(project, path)
        if suffix == ".wxml":
            matches = list(HTML_TAG_RE.finditer(text))
            if matches:
                evidence = [
                    {
                        "file": rel,
                        "line": _line_number(text, match.start()),
                        "excerpt": _excerpt(text.splitlines()[_line_number(text, match.start()) - 1]),
                    }
                    for match in matches[:3]
                ]
                _add(
                    findings,
                    seen,
                    severity="P0",
                    category="平台兼容",
                    title="WXML 使用浏览器 HTML 标签",
                    evidence=evidence,
                    why="WXML 不是 HTML；div、span、img、a 等标签不具备小程序组件行为。",
                    recommendation="替换为 view、text、image、navigator 等小程序基础组件，并使用 bindtap 事件。",
                    rule_ids=["wx-wxml-binding", "mp-native-components"],
                )
                count += 1
            if re.search(r"\bon(?:click|change|input|submit)\s*=", text, re.IGNORECASE) or re.search(
                r"\s@(?:click|change|input)=", text
            ):
                lines = text.splitlines()
                evidence = [
                    {"file": rel, "line": index + 1, "excerpt": _excerpt(line)}
                    for index, line in enumerate(lines)
                    if re.search(r"\bon(?:click|change|input|submit)\s*=|\s@(?:click|change|input)=", line, re.IGNORECASE)
                ][:3]
                _add(
                    findings,
                    seen,
                    severity="P0",
                    category="平台兼容",
                    title="WXML 使用浏览器/Vue 事件语法",
                    evidence=evidence,
                    why="原生 WXML 不执行 onclick、@click 等 Web/Vue 事件属性。",
                    recommendation="改用 bindtap/catchtap 并在 JS/TS 中实现处理器。",
                    rule_ids=["wx-wxml-binding"],
                )
                count += 1
        elif suffix in {".vue", ".nvue"} and stack in {"uni-app", "taro"}:
            match = HTML_TAG_RE.search(text)
            if match:
                _add(
                    findings,
                    seen,
                    severity="P2",
                    category="平台兼容",
                    title="模板使用浏览器语义标签，需确认条件编译",
                    evidence=[
                        {
                            "file": rel,
                            "line": _line_number(text, match.start()),
                            "excerpt": _excerpt(text.splitlines()[_line_number(text, match.start()) - 1]),
                        }
                    ],
                    why="uni-app/Taro 的 H5 目标可使用 HTML 标签，但微信小程序目标不一定等价；必须按项目编译配置确认。",
                    recommendation="微信目标使用 view/text/image 等跨端组件；仅 H5 分支使用 HTML 标签并条件编译。",
                    rule_ids=["uni-components" if stack == "uni-app" else "taro-components", "mp-custom-vs-native"],
                    verification="rule-assisted",
                    confidence="medium",
                )
                count += 1
        if suffix in CODE_EXTENSIONS:
            lines = text.splitlines()
            api_hits: list[tuple[str, int]] = []
            conditional_hits = 0
            for api_name, pattern in BROWSER_API_PATTERNS:
                for match in pattern.finditer(text):
                    line_index = _line_number(text, match.start())
                    context_start = max(0, line_index - 8)
                    context = "\n".join(lines[context_start:line_index])
                    if re.search(
                        r"#ifdef\s+H5|#ifndef\s+MP|TARO_ENV\s*===?\s*['\"]h5['\"]|process\.env\.TARO_ENV[^\n]*h5|typeof\s+window",
                        context,
                    ):
                        conditional_hits += 1
                    api_hits.append((api_name, line_index))
            unique_hits: list[tuple[str, int]] = []
            seen_lines: set[int] = set()
            for api_name, line_index in api_hits:
                if line_index in seen_lines:
                    continue
                seen_lines.add(line_index)
                unique_hits.append((api_name, line_index))
            if unique_hits:
                conditional = bool(api_hits) and conditional_hits == len(api_hits)
                api_names = sorted({name for name, _ in api_hits})
                evidence = [
                    {
                        "file": rel,
                        "line": line_index,
                        "excerpt": _excerpt(lines[line_index - 1]),
                    }
                    for _, line_index in unique_hits[:3]
                ]
                _add(
                    findings,
                    seen,
                    severity="P3" if conditional else "P1",
                    category="平台兼容",
                    title="检测到浏览器 DOM/BOM API",
                    evidence=evidence,
                    why=(
                        "调用附近都有 H5 条件编译线索，但仍需确认微信目标不会执行。"
                        if conditional
                        else f"微信小程序页面没有浏览器 DOM/BOM；检测到 {', '.join(api_names)}，在微信目标可能直接报错。"
                    ),
                    recommendation="改用小程序 API/组件；如果仅用于 H5，必须放入 H5 条件编译并验证微信包不包含执行路径。",
                    rule_ids=["wx-browser-api", "uni-dom" if stack == "uni-app" else "taro-no-dom"],
                    verification="rule-assisted",
                    confidence="medium" if conditional else "high",
                )
                count += 1
            if re.search(r"\bgetSystemInfoSync\s*\(", text):
                match = re.search(r"\bgetSystemInfoSync\s*\(", text)
                line_index = _line_number(text, match.start()) if match else 1
                _add(
                    findings,
                    seen,
                    severity="P3",
                    category="平台兼容",
                    title="使用 getSystemInfoSync，需按基础库确认替代方案",
                    evidence=[{"file": rel, "line": line_index, "excerpt": _excerpt(lines[line_index - 1])}],
                    why="平台系统信息接口可能随基础库演进，旧接口不一定是最新推荐方案。",
                    recommendation="按目标基础库查看当前推荐的窗口/设备信息接口，并保留低版本回退。",
                    rule_ids=["mp-status-bar"],
                    verification="rule-assisted",
                    confidence="low",
                )
                count += 1
    return count


def _check_safe_area_and_css(
    project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]
) -> tuple[int, int, int]:
    safe_area_count = 0
    touch_count = 0
    font_count = 0
    for _path, text, line_offset in _styles(project):
        rel = _path
        if re.search(r"position\s*:\s*fixed", text, re.IGNORECASE) and re.search(
            r"bottom\s*:\s*0(?:rpx|px)?\s*;", text, re.IGNORECASE
        ):
            has_safe_area = bool(
                re.search(r"safe-area-inset|constant\s*\(\s*safe-area", text, re.IGNORECASE)
            )
            if not has_safe_area:
                fixed_match = re.search(r"position\s*:\s*fixed", text, re.IGNORECASE)
                line = line_offset + text.count("\n", 0, fixed_match.start() if fixed_match else 0)
                _add(
                    findings,
                    seen,
                    severity="P1",
                    category="安全区域",
                    title="固定底部元素未发现安全区处理",
                    evidence=[{"file": rel, "line": line, "excerpt": "position: fixed; bottom: 0"}],
                    why="全面屏底部手势区可能覆盖固定操作栏；内容也可能被底栏遮挡。",
                    recommendation="为底栏加 env(safe-area-inset-bottom)（或目标框架等价能力），为内容加等高占位，并真机验证。",
                    rule_ids=["mp-safe-area", "mp-fixed-bottom", "ux-bottom-bar"],
                )
                safe_area_count += 1
        for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
            selector = " ".join(match.group(1).strip().split())
            block = match.group(2)
            lowered = selector.casefold()
            if not any(keyword in lowered for keyword in ("btn", "button", "close", "tab", "tap", "cell")):
                continue
            sizes = []
            for size_match in re.finditer(
                r"(?:min-)?(?:width|height)\s*:\s*(\d+(?:\.\d+)?)\s*(rpx|px)",
                block,
                re.IGNORECASE,
            ):
                value = float(size_match.group(1))
                unit = size_match.group(2).casefold()
                threshold = 88.0 if unit == "rpx" else 44.0
                if 0 < value < threshold:
                    sizes.append((value, unit, threshold))
            if sizes:
                line = line_offset + text.count("\n", 0, match.start())
                _add(
                    findings,
                    seen,
                    severity="P2",
                    category="触摸交互",
                    title="CSS 中出现过小的可点击目标",
                    evidence=[
                        {
                            "file": rel,
                            "line": line,
                            "excerpt": f"{selector} 使用 {sizes[0][0]:g}{sizes[0][1]}，低于 {sizes[0][2]:g}{sizes[0][1]} 基线",
                        }
                    ],
                    why="可点击热区过小会增加误触；官方设计指南建议约 7–9mm 的物理点击尺寸。",
                    recommendation="扩大 padding/伪元素热区；视觉图标可以保持小，但可点击区至少 88rpx×88rpx（或 44px×44px）。",
                    rule_ids=["ux-touch-target", "mp-touch-target"],
                    verification="rule-assisted",
                    confidence="medium",
                )
                touch_count += 1
        for match in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)\s*(rpx|px)", text, re.IGNORECASE):
            value = float(match.group(1))
            unit = match.group(2).casefold()
            threshold = 24.0 if unit == "rpx" else 12.0
            if 0 < value < threshold:
                line = line_offset + text.count("\n", 0, match.start())
                _add(
                    findings,
                    seen,
                    severity="P2",
                    category="可读性",
                    title="存在过小字号",
                    evidence=[
                        {"file": rel, "line": line, "excerpt": match.group(0)}
                    ],
                    why="小字号在手机上阅读困难，也不利于系统字号放大和适老场景。",
                    recommendation="正文建议 28–32rpx，辅助信息不低于 24rpx；通过层级和留白而不是缩小字号组织信息。",
                    rule_ids=["ux-font-readability"],
                    verification="automated",
                    confidence="medium",
                )
                font_count += 1
    return safe_area_count, touch_count, font_count


_PROJECT: dict[str, Any] = {}


def _styles(project: dict[str, Any]) -> list[tuple[str, str, int]]:
    global _PROJECT
    _PROJECT = project
    blocks: list[tuple[str, str, int]] = []
    for path in project["files"]:
        if path.suffix.casefold() not in STYLE_EXTENSIONS:
            continue
        text = _read_text(path)
        for rel, content, line_offset in _extract_style_blocks(path, text):
            blocks.append((rel, content, line_offset))
    return blocks


def _check_ui_states(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> int:
    texts = _page_source_texts(project)
    if not texts:
        return 0
    combined = "\n".join(text for _, text in texts).casefold()
    categories = {
        "加载状态": ("loading", "加载", "skeleton", "骨架"),
        "空状态": ("empty", "空状态", "暂无", "还没有"),
        "错误/重试状态": ("error", "错误", "失败", "重试", "重试"),
    }
    missing = [label for label, terms in categories.items() if not any(term in combined for term in terms)]
    rules = {"加载状态": "ux-loading-states", "空状态": "ux-empty-states", "错误/重试状态": "ux-error-states"}
    for label in missing:
        _add(
            findings,
            seen,
            severity="P2",
            category="交互状态",
            title=f"未发现{label}线索",
            evidence=[{"file": texts[0][0], "line": 1}],
            why="静态扫描没有找到该状态的关键词或组件线索；只实现成功路径会在慢网、空数据或失败时留下空白/死路。",
            recommendation="逐页补齐加载、空、错误与重试状态；如果使用共享组件，请确保页面确实引用并验证。",
            rule_ids=[rules[label]],
            verification="rule-assisted",
            confidence="low",
        )
    return len(missing)


def _check_images(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> int:
    count = 0
    for path in project["files"]:
        if path.suffix.casefold() not in {".wxml", ".vue", ".nvue", ".tsx", ".jsx"}:
            continue
        text = _read_text(path)
        for match in re.finditer(r"<\s*(?:image|Image)\b([^>]*)>", text):
            attrs = match.group(1)
            if re.search(r"\bmode\s*=", attrs) or re.search(r"\blazyLoad\b|\blazy-load\b", attrs):
                continue
            line = _line_number(text, match.start())
            rel = _relative(project, path)
            _add(
                findings,
                seen,
                severity="P3",
                category="媒体",
                title="图片未声明 mode 或懒加载策略",
                evidence=[{"file": rel, "line": line, "excerpt": _excerpt(text.splitlines()[line - 1])}],
                why="未明确 mode 可能导致拉伸或裁切不一致；长列表图片未懒加载会增加首屏压力。这是静态启发式，需结合具体用途确认。",
                recommendation="为图片容器设定比例，按用途使用 aspectFill/aspectFit，长列表加 lazy-load，并处理加载失败。",
                rule_ids=["ux-image-fallback", "mp-performance"],
                verification="rule-assisted",
                confidence="low",
            )
            count += 1
            break
    return count


def _check_privacy(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> int:
    all_code = "\n".join(
        _read_text(path) for path in project["files"] if path.suffix.casefold() in CODE_EXTENSIONS
    )
    privacy_handling = bool(
        re.search(r"隐私|privacy|agreePrivacyAuthorization|onNeedPrivacyAuthorization", all_code, re.IGNORECASE)
    )
    matches = list(PRIVACY_API_RE.finditer(all_code))
    if not matches or privacy_handling:
        return 0
    match = matches[0]
    file_containing = None
    text_containing = ""
    for path in project["files"]:
        if path.suffix.casefold() not in CODE_EXTENSIONS:
            continue
        text = _read_text(path)
        if PRIVACY_API_RE.search(text):
            file_containing = path
            text_containing = text
            break
    line = 1
    if text_containing:
        local = PRIVACY_API_RE.search(text_containing)
        if local:
            line = _line_number(text_containing, local.start())
    _add(
        findings,
        seen,
        severity="P2",
        category="隐私与授权",
        title="发现敏感 API 调用，但未发现隐私处理线索",
        evidence=[
            {
                "file": _relative(project, file_containing),
                "line": line,
                "excerpt": _excerpt(text_containing.splitlines()[line - 1]) if text_containing else "",
            }
        ],
        why="位置、相册、手机号、头像等能力可能涉及隐私授权；静态扫描只确认到调用，无法判断线上是否合规。",
        recommendation="按当前微信隐私规则接入同意/撤回流程，在具体任务前请求最小权限；在真机验证拒绝路径。",
        rule_ids=["mp-privacy", "mp-auth", "ux-privacy"],
        verification="rule-assisted",
        confidence="medium",
    )
    return 1


def _check_tokens(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> int:
    color_positions: list[tuple[str, int, str]] = []
    unique_colors: set[str] = set()
    for path in project["files"]:
        if path.suffix.casefold() not in STYLE_EXTENSIONS:
            continue
        if path.suffix.casefold() in {".vue", ".nvue"}:
            text = "\n".join(block for _, block, _ in _extract_style_blocks(path, _read_text(path)))
        else:
            text = _read_text(path)
        rel = _relative(project, path)
        for match in re.finditer(r"#[0-9a-fA-F]{3,8}\b", text):
            value = match.group(0).upper()
            unique_colors.add(value)
            color_positions.append((rel, _line_number(text, match.start()), value))
    design = project.get("design_system")
    if design and isinstance(design.get("tokens"), set) and design["tokens"]:
        unregistered = [item for item in color_positions if item[2] not in design["tokens"]]
        if len({item[2] for item in unregistered}) >= 3:
            _add(
                findings,
                seen,
                severity="P2",
                category="设计系统一致性",
                title="样式中存在设计系统未登记的硬编码颜色",
                evidence=[
                    {"file": file, "line": line, "excerpt": f"颜色 {color}"}
                    for file, line, color in unregistered[:3]
                ],
                why="Token 之外的硬编码颜色会导致页面之间不一致，也使暗色模式和品牌调整失效。",
                recommendation="将颜色映射到 MASTER.json 的语义 token；新增颜色先更新设计系统，再使用。",
                rule_ids=["anti-token-mismatch"],
                verification="automated",
                confidence="high",
            )
            return 1
    elif len(unique_colors) > 12:
        _add(
            findings,
            seen,
            severity="P3",
            category="设计系统一致性",
            title="样式中颜色数量较多，未检测到设计系统",
            evidence=[
                {"file": file, "line": line, "excerpt": f"颜色 {color}"}
                for file, line, color in color_positions[:3]
            ],
            why="没有可检测的 Master token 时，多颜色值通常意味着逐页手写样式和一致性风险。",
            recommendation="建立 Master + token 映射，收敛颜色数量并记录语义用途。",
            rule_ids=["anti-token-mismatch"],
            verification="rule-assisted",
            confidence="medium",
        )
        return 1
    return 0


def _check_wxml_keys(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> int:
    count = 0
    for path in project["files"]:
        if path.suffix.casefold() != ".wxml":
            continue
        text = _read_text(path)
        for match in re.finditer(r"<([a-zA-Z-]+)([^>]*\bwx:for\b[^>]*)>", text):
            attrs = match.group(2)
            if "wx:key" in attrs:
                continue
            line = _line_number(text, match.start())
            _add(
                findings,
                seen,
                severity="P3",
                category="列表渲染",
                title="wx:for 列表缺少 wx:key",
                evidence=[
                    {"file": _relative(project, path), "line": line, "excerpt": _excerpt(text.splitlines()[line - 1])}
                ],
                why="缺少稳定 key 可能导致列表复用时状态错乱和额外渲染。",
                recommendation="为列表项提供稳定的业务 ID 作为 wx:key，避免使用 index 作为默认方案。",
                rule_ids=["mp-performance"],
                verification="automated",
                confidence="high",
            )
            count += 1
            break
    return count


def _check_misc(project: dict[str, Any], findings: list[dict[str, Any]], seen: set[tuple[str, str, tuple[str, ...]]]) -> tuple[int, int]:
    important_count = 0
    infinite_count = 0
    example_file = ""
    example_line = 1
    for path in project["files"]:
        if path.suffix.casefold() not in STYLE_EXTENSIONS:
            continue
        text = _read_text(path)
        important_count += len(re.findall(r"!important", text, re.IGNORECASE))
        infinite_count += len(re.findall(r"\binfinite\b", text, re.IGNORECASE))
        if not example_file and ("!important" in text or "infinite" in text):
            example_file = _relative(project, path)
            match = re.search(r"!important|infinite", text, re.IGNORECASE)
            if match:
                example_line = _line_number(text, match.start())
    if important_count > 5:
        _add(
            findings,
            seen,
            severity="P3",
            category="样式维护",
            title="过多 !important",
            evidence=[{"file": example_file, "line": example_line, "excerpt": f"共发现 {important_count} 处 !important"}],
            why="大量强制覆盖通常意味着样式作用域和 token 边界不清，升级框架或组件时容易失效。",
            recommendation="收敛全局选择器，明确组件作用域与 token；只在无法避免的第三方覆盖中使用 !important。",
            rule_ids=["mp-style-isolation", "anti-token-mismatch"],
            verification="automated",
            confidence="medium",
        )
    if infinite_count > 2:
        _add(
            findings,
            seen,
            severity="P3",
            category="动效",
            title="存在多个无限动画",
            evidence=[{"file": example_file, "line": example_line, "excerpt": f"共发现 {infinite_count} 处 infinite 动画"}],
            why="无穷动画可能持续消耗性能并干扰注意力；加载动画除外，但也应有明确状态。",
            recommendation="仅保留必要的加载动画，装饰动画设置时长/次数限制，并提供低动效路径。",
            rule_ids=["ux-motion-preference", "mp-performance"],
            verification="rule-assisted",
            confidence="low",
        )
    return (1 if important_count > 5 else 0), (1 if infinite_count > 2 else 0)


def audit_project(
    path: Path, design_system_path: Path | None = None
) -> dict[str, Any]:
    project = _load_project(path, design_system_path)
    global _PROJECT
    _PROJECT = project
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    check_counts: dict[str, int] = {}

    def run(check_id: str, function, *args) -> Any:
        start = len(findings)
        result = function(*args)
        for finding in findings[start:]:
            finding["check_id"] = check_id
        check_counts[check_id] = len(findings) - start
        return result

    run("project-structure", _check_project_structure, project, findings, seen)
    run("tabbar-config", _check_tabbar, project, findings, seen)
    run("custom-navigation", _check_navigation, project, findings, seen)
    run("dom-browser-api", _check_dom_and_apis, project, findings, seen)
    start = len(findings)
    _check_safe_area_and_css(project, findings, seen)
    css_checks = {"安全区域": "safe-area", "触摸交互": "touch-target-css", "可读性": "font-size-css"}
    for finding in findings[start:]:
        finding["check_id"] = css_checks[finding["category"]]
    for check_id in css_checks.values():
        check_counts[check_id] = sum(item["check_id"] == check_id for item in findings[start:])
    run("ui-states", _check_ui_states, project, findings, seen)
    run("images", _check_images, project, findings, seen)
    run("privacy", _check_privacy, project, findings, seen)
    run("design-tokens", _check_tokens, project, findings, seen)
    run("wxml-keys", _check_wxml_keys, project, findings, seen)
    run("misc-css", _check_misc, project, findings, seen)

    if project["stack"] == "browser-prototype":
        html_file = next(iter(sorted(project["root"].rglob("*.html"))), project["root"])
        _add(
            findings,
            seen,
            severity="P2",
            category="环境",
            title="这是浏览器原型，不是已验证的微信小程序",
            evidence=[{"file": _relative(project, html_file), "line": 1}],
            why="静态审查只发现 HTML 文件，无法证明 WXML/WXSS、页面路由或微信 API 可用。",
            recommendation="将其明确标记为浏览器原型；转为小程序时应按目标技术栈重新实现并验证。",
            rule_ids=["mp-devtools-vs-device", "anti-web-only"],
            verification="automated",
            confidence="high",
        )
        check_counts["environment"] = 1
    if project["stack"] == "unknown":
        _add(
            findings,
            seen,
            severity="P1",
            category="环境",
            title="无法识别项目技术栈",
            evidence=[{"file": ".", "line": 1}],
            why="无法确定应加载原生、uni-app 还是 Taro 规则，审查结果可能误判。",
            recommendation="确认项目根目录包含 app.json、pages.json 或 Taro 配置，或显式指定正确的项目路径。",
            rule_ids=["mp-custom-vs-native"],
            verification="automated",
            confidence="high",
        )
        check_counts["environment"] = 1

    findings.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(item["severity"], 9),
            (item.get("evidence") or [{}])[0].get("file", ""),
            item.get("title", ""),
        )
    )
    for index, finding in enumerate(findings, start=1):
        finding["id"] = f"F-{index:03d}"
        finding.setdefault("check_id", "environment")
        finding["evidence"] = [
            {**item, "file": item.get("file", "."), "line": item.get("line", 1)}
            for item in finding.get("evidence", [])
        ]
        finding["fingerprint"] = finding_fingerprint(finding)

    summary = {level: 0 for level in ("P0", "P1", "P2", "P3")}
    for finding in findings:
        summary[finding["severity"]] += 1
    existing_pages = sum(
        1
        for files in project.get("existing_page_files", {}).values()
        if any(path.suffix.casefold() in PAGE_TEMPLATE_EXTENSIONS for path in files)
    )
    design = project.get("design_system")
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": "static-mini-program-review",
        "generator": {"name": "mini-program-ux-pro", "version": VERSION},
        "project": {
            "name": project["root"].name or str(project["root"]),
            "path": str(project["root"]),
            "stack": project["stack"],
            "stack_label": STACK_LABELS.get(project["stack"], project["stack"]),
            "stack_detection": project["stack_reason"],
        },
        "generated_at": _now_iso(),
        "environment": {
            "mode": "static-code-review",
            "runtime": "not_run",
            "browser_preview": "not_run",
            "wechat_devtools": "not_run",
            "real_device": "not_run",
            "visual_model": "not_run",
        },
        "scope": {
            "files_scanned": len(project["files"]),
            "source_files": [_relative(project, path) for path in project["files"]],
            "ruleset": "static-1",
            "scan_policy": {
                "max_file_bytes": 800_000,
                "excluded_directories": sorted(SKIP_DIRS),
                "extensions": sorted(TEXT_EXTENSIONS),
            },
            "pages_declared": len(project.get("pages", [])),
            "pages_found": existing_pages,
            "page_paths": list(project.get("pages", [])),
            "design_system": (
                {
                    "path": _relative(project, design["path"]),
                    "project": design["data"].get("project", {}).get("name"),
                    "version": design.get("version"),
                    "schema_version": design.get("schema_version"),
                    "generated_at": design["data"].get("generated_at"),
                    "fingerprint": hashlib.sha256(json.dumps(sorted(design["tokens"])).encode("utf-8")).hexdigest(),
                }
                if design
                else None
            ),
        },
        "executed_checks": [
            {"id": check_id, "finding_groups": count, "mode": "static"}
            for check_id, count in check_counts.items()
        ],
        "skipped_checks": [
            {"id": "runtime-render", "reason": "未运行微信开发者工具或真实项目"},
            {"id": "visual-hierarchy", "reason": "没有页面截图，视觉模型未接入"},
            {"id": "keyboard-safe-area", "reason": "需要 iOS/Android 真机与输入法"},
            {"id": "performance", "reason": "静态代码无法测量帧率、首屏和 setData 成本"},
            {"id": "screen-reader", "reason": "需要 VoiceOver/TalkBack 等运行时辅助技术"},
            {"id": "network-weak", "reason": "需要限速、断网与真实接口环境"},
            {"id": "share-auth-privacy", "reason": "需要平台环境、账号授权和人工确认"},
        ],
        "findings": findings,
        "summary": summary,
        "coverage": {
            "static_code": True,
            "automated_checks": True,
            "heuristic_checks": True,
            "runtime_checks": False,
            "visual_checks": False,
            "real_device_checks": False,
            "note": "未执行的检查不能视为通过；本报告不能证明页面在微信真机中可用。",
        },
        "next_steps": _next_steps(findings),
    }
    validate_report(report)
    return report


def _next_steps(findings: list[dict[str, Any]]) -> list[str]:
    steps: list[str] = []
    if any(item["severity"] == "P0" for item in findings):
        steps.append("先修复所有 P0：路由/模板缺失或微信目标无法执行的代码。")
    if any(item["severity"] == "P1" for item in findings):
        steps.append("修复 P1 安全区域、导航、平台兼容或核心交互问题，再进行真机检查。")
    if any(item["severity"] == "P2" for item in findings):
        steps.append("处理 P2 字号、状态、隐私和设计一致性问题。")
    if steps:
        steps.append("修复后重新运行本工具，确认没有引入新问题；不要仅通过改变颜色宣称完成。")
    else:
        steps.append("静态规则未发现明显问题；仍需在微信开发者工具和真机走核心路径，不能将本报告当作通过证明。")
    steps.append("如需运行视觉审查，请提供截图或接入视觉模型适配器；当前项目未内置该能力。")
    return steps


def _md_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def format_markdown(report: dict[str, Any]) -> str:
    project = report["project"]
    summary = report["summary"]
    lines: list[str] = []
    add = lines.append
    add(f"# 小程序静态审查报告 · {project['name']}")
    add("")
    add("> 检查环境：**静态代码审查**。未运行浏览器预览、微信开发者工具、真实设备或视觉模型。")
    add(f"> 生成器：MPUX Pro {report['generator']['version']} · 检查时间：{report['generated_at']}")
    add("")
    add("## 摘要")
    add("")
    add(f"- **项目路径**：`{project['path']}`")
    add(f"- **技术栈**：{project['stack_label']} (`{project['stack']}`)")
    add(f"- **识别依据**：{project['stack_detection']}")
    add(f"- **页面**：声明 {report['scope']['pages_declared']}，找到模板 {report['scope']['pages_found']}")
    add(f"- **扫描文件**：{report['scope']['files_scanned']}")
    design_scope = report["scope"]["design_system"]
    if design_scope:
        design_text = design_scope["path"]
        if design_scope.get("version"):
            design_text += f"（生成器 {design_scope['version']}）"
    else:
        design_text = "未检测到"
    add(f"- **设计系统**：{design_text}")
    add("")
    add("| P0 | P1 | P2 | P3 |")
    add("| ---: | ---: | ---: | ---: |")
    add(f"| {summary['P0']} | {summary['P1']} | {summary['P2']} | {summary['P3']} |")
    add("")
    add("P0=核心功能不可用；P1=严重视觉/交互/平台问题；P2=明显一致性与可用性问题；P3=细节优化。")
    add("")
    add("## 检查范围与未执行项")
    add("")
    add("### 已执行（静态）")
    add("")
    add("| 检查 | 问题组数 | 方式 |")
    add("| --- | ---: | --- |")
    for check in report["executed_checks"]:
        add(f"| `{check['id']}` | {check['finding_groups']} | 静态/规则辅助 |")
    add("")
    add("### 未执行")
    add("")
    for check in report["skipped_checks"]:
        add(f"- **{check['id']}**：{check['reason']}")
    add("")
    add("> 未执行的检查在审查结论中一律视为“未验证”，不得算作通过。")
    add("")
    add("## 问题列表")
    add("")
    if not report["findings"]:
        add("静态规则未发现明显问题。这不等于页面已经通过真机、视觉或交互验收。")
        add("")
    for finding in report["findings"]:
        add(f"### {finding['id']} · [{finding['severity']}] {finding['title']}")
        add("")
        add(f"- **类别**：{finding['category']}")
        add(f"- **判断方式**：{finding['verification']} · 置信度 {finding['confidence']}")
        add(f"- **适用规则**：{'、'.join(f'`{rule}`' for rule in finding['rule_ids'])}")
        add(f"- **为什么是问题**：{finding['why']}")
        add(f"- **建议修复**：{finding['recommendation']}")
        add("- **证据**：")
        for evidence in finding["evidence"]:
            add(f"  - `{evidence['file']}:{evidence['line']}`")
            if evidence.get("excerpt"):
                add(f"    - `{_md_escape(evidence['excerpt'])}`")
        add("")
    add("## 覆盖率与后续建议")
    add("")
    add(f"- 静态代码：{report['coverage']['static_code']}")
    add(f"- 自动/规则辅助检查：{report['coverage']['heuristic_checks']}")
    add(f"- 运行时：{report['coverage']['runtime_checks']}")
    add(f"- 视觉审查：{report['coverage']['visual_checks']}")
    add(f"- 真机：{report['coverage']['real_device_checks']}")
    add("")
    add(report["coverage"]["note"])
    add("")
    for step in report["next_steps"]:
        add(f"- {step}")
    add("")
    add("## 环境声明")
    add("")
    add("本报告来自静态代码读取，不能证明页面在微信开发者工具或 iOS/Android 真机中的视觉效果、键盘、安全区、分享、授权和性能。若要声称“已验证”，必须保留对应环境的实际执行记录。")
    add("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="静态审查微信小程序/uni-app/Taro 项目的设计、交互与平台问题；不修改项目。",
    )
    parser.add_argument("--path", default=".", help="项目目录，默认当前目录")
    parser.add_argument(
        "--design-system",
        default=None,
        help="可选：MASTER.json 或包含它的目录；默认在当前目录及上级目录查找 design-system/",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式，默认 markdown",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--output", "-o", default=None, help="将报告写入文件")
    parser.add_argument(
        "--fail-on",
        choices=["none", "P0", "P1", "P2", "P3"],
        default="none",
        help="发现指定等级及以上问题时返回退出码 1；默认 none",
    )
    return parser


def _exit_code(report: dict[str, Any], fail_on: str) -> int:
    if fail_on == "none":
        return 0
    threshold = SEVERITY_ORDER[fail_on]
    return 1 if any(SEVERITY_ORDER[item["severity"]] <= threshold for item in report["findings"]) else 0


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = audit_project(
            Path(args.path),
            Path(args.design_system) if args.design_system else None,
        )
    except (AuditError, ReportError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    markdown = format_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if args.json or args.format == "json":
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            output.write_text(markdown, encoding="utf-8")
    if args.json or args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(markdown)
    return _exit_code(report, args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())