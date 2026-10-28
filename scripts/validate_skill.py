#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 MPUX Pro Skill 的文件完整性、文档引用与 CLI 可用性。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from mpux_core import configure_utf8_stdio, utf8_subprocess_env

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "LICENSE",
    "NOTICE.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "package.json",
    "skill.json",
    ".gitignore",
    ".editorconfig",
    "data/products.csv",
    "data/styles.csv",
    "data/colors.csv",
    "data/layouts.csv",
    "data/typography.csv",
    "data/components.csv",
    "data/ux-guidelines.csv",
    "data/mini-program-rules.csv",
    "data/anti-patterns.csv",
    "data/ui-reasoning.csv",
    "data/stacks/wechat-native.csv",
    "data/stacks/uni-app.csv",
    "data/stacks/taro.csv",
    "references/design-principles.md",
    "references/visual-hierarchy.md",
    "references/typography.md",
    "references/color-systems.md",
    "references/spacing-systems.md",
    "references/layout-patterns.md",
    "references/interaction-design.md",
    "references/motion-design.md",
    "references/mini-program-platform.md",
    "references/navigation-and-routing.md",
    "references/safe-area.md",
    "references/touch-interactions.md",
    "references/accessibility.md",
    "references/component-design.md",
    "references/responsive-layout.md",
    "references/visual-review.md",
    "references/common-anti-patterns.md",
    "styles/minimal.md",
    "styles/editorial.md",
    "styles/swiss.md",
    "styles/oriental-modern.md",
    "styles/premium-commerce.md",
    "styles/playful.md",
    "styles/brutalist.md",
    "styles/organic.md",
    "styles/retro.md",
    "styles/futuristic.md",
    "styles/data-driven.md",
    "workflows/analyze-requirements.md",
    "workflows/generate-design-system.md",
    "workflows/implement-mini-program.md",
    "workflows/review-existing-project.md",
    "workflows/review-page.md",
    "workflows/review-interactions.md",
    "workflows/iterative-refinement.md",
    "workflows/final-delivery.md",
    "checklists/visual-quality.md",
    "checklists/interaction-quality.md",
    "checklists/mini-program-quality.md",
    "checklists/responsive-quality.md",
    "checklists/accessibility-quality.md",
    "checklists/release-quality.md",
    "scripts/search.py",
    "scripts/generate_design_system.py",
    "scripts/audit_mini_program.py",
    "scripts/mpux_core.py",
    "scripts/design_system.py",
    "scripts/validate_data.py",
    "scripts/validate_skill.py",
    "scripts/validate_project.py",
    "scripts/install_skill.py",
    "scripts/visual_review_adapter.py",
    "scripts/devtools_adapter.py",
    "verification/README.md",
    "verification/project.config.json",
    "verification/mini-program/app.json",
    "verification/devtools/package.json",
    "verification/devtools/verify.cjs",
    "verification/devtools/README.md",
    "schemas/design-system.schema.json",
    "schemas/search-result.schema.json",
    "schemas/review-report.schema.json",
    "templates/design-system-master.md",
    "templates/page-override.md",
    "templates/review-report.md",
    "examples/ecommerce-mini-program.md",
    "examples/music-mini-program.md",
    "examples/lifestyle-mini-program.md",
    "examples/education-mini-program.md",
    "examples/tool-mini-program.md",
    "examples/dashboard-mini-program.md",
    "tests/test_search.py",
    "tests/test_data_validation.py",
    "tests/test_design_system.py",
    "tests/test_skill_validation.py",
    "tests/test_audit.py",
    "docs/installation.md",
    "docs/usage.md",
    "docs/architecture.md",
    "docs/design-data.md",
    "docs/compatibility.md",
    "docs/troubleshooting.md",
    "docs/roadmap.md",
    "docs/reference-research.md",
    "docs/official-verification.md",
    "docs/acceptance-report.md",
]

REQUIRED_TOPICS = {
    "适用场景": ["适用场景", "When to"],
    "触发条件": ["触发条件", "Trigger"],
    "设计原则": ["设计原则", "Principles"],
    "项目识别": ["识别项目", "技术栈识别", "Project detection"],
    "产品类型": ["产品类型", "Product"],
    "设计系统": ["设计系统", "design system"],
    "知识库检索": ["检索", "search.py"],
    "页面实现": ["页面实现", "implementation"],
    "现有项目审查": ["现有项目", "audit_mini_program.py"],
    "视觉审查": ["视觉审查", "visual review"],
    "交互审查": ["交互审查", "interaction review"],
    "问题优先级": ["P0", "P1", "P2", "P3"],
    "自动修复": ["自动迭代", "修复"],
    "微信平台": ["微信平台", "安全区域", "TabBar"],
    "完成标准": ["完成标准", "验收"],
    "安全要求": ["安全", "隐私"],
    "文档引用": ["references/", "工作流"],
}

CLI_SCRIPTS = [
    "search.py",
    "generate_design_system.py",
    "audit_mini_program.py",
    "validate_data.py",
    "validate_skill.py",
    "validate_project.py",
    "install_skill.py",
    "visual_review_adapter.py",
    "devtools_adapter.py",
]
FORBIDDEN_NETWORK = re.compile(
    r"^\s*(?:import|from)\s+(?:requests|httpx|urllib\.request|aiohttp)\b",
    re.MULTILINE,
)
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)(?:appsecret|api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
]


def _read_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}, text
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith(('"', "'")) and value.endswith(('"', "'")):
            value = value[1:-1]
        data[key.strip()] = value
    return data, "\n".join(lines[end + 1 :])


def _check_text_files(root: Path, errors: list[str], warnings: list[str]) -> int:
    markdown_files = [
        path
        for path in root.rglob("*.md")
        if ".git" not in path.parts and "node_modules" not in path.parts
    ]
    checked = 0
    for path in markdown_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        checked += 1
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#", "tel:")):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target or "<" in target or ">" in target:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                warnings.append(f"{path.relative_to(root)} 链接到项目外：{target}")
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(root)} 的相对链接不存在：{target}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.relative_to(root)} 可能包含密钥")
    return checked


def _check_commands(root: Path, errors: list[str], warnings: list[str]) -> int:
    documents = [root / "SKILL.md", root / "README.md", *sorted((root / "docs").glob("*.md"))]
    found_commands: set[str] = set()
    for document in documents:
        if not document.exists():
            continue
        text = document.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"python3?\s+scripts/([A-Za-z0-9_./-]+\.py)", text):
            script = match.group(1)
            found_commands.add(script)
            if not (root / "scripts" / script).exists():
                errors.append(f"{document.relative_to(root)} 引用了不存在的脚本：scripts/{script}")
    for script in CLI_SCRIPTS:
        command = [sys.executable, str(root / "scripts" / script), "--help"]
        try:
            result = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=utf8_subprocess_env(),
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"{script} --help 执行失败：{exc}")
            continue
        if result.returncode != 0:
            errors.append(f"{script} --help 返回 {result.returncode}：{result.stderr[:200]}")
    if not found_commands:
        warnings.append("SKILL.md/README 中没有检测到 python scripts/... 命令示例")
    return len(found_commands)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    root = root.resolve()
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.exists():
            errors.append(f"缺少必需文件：{relative}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"必需文件为空：{relative}")

    skill_path = root / "SKILL.md"
    frontmatter: dict[str, str] = {}
    skill_text = ""
    if skill_path.exists():
        skill_text = skill_path.read_text(encoding="utf-8", errors="replace")
        frontmatter, body = _read_frontmatter(skill_text)
        if not frontmatter:
            errors.append("SKILL.md 缺少 YAML frontmatter")
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not name:
            errors.append("SKILL.md frontmatter 缺少 name")
        elif not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", name):
            errors.append(f"SKILL.md name 不符合 Skill 命名规范：{name!r}")
        if not description:
            errors.append("SKILL.md frontmatter 缺少 description")
        elif len(description) < 80:
            warnings.append("SKILL.md description 偏短，可能无法让工具正确判断触发场景")
        if name and name != "mini-program-ux-pro":
            errors.append(f"SKILL.md name 应为 mini-program-ux-pro，实际为 {name}")
        for topic, needles in REQUIRED_TOPICS.items():
            if not any(needle.casefold() in skill_text.casefold() for needle in needles):
                errors.append(f"SKILL.md 缺少主题：{topic}")
        if "微信小程序" not in skill_text:
            errors.append("SKILL.md 没有明确声明微信小程序平台范围")

    skill_json_path = root / "skill.json"
    if skill_json_path.exists():
        try:
            skill_meta = json.loads(skill_json_path.read_text(encoding="utf-8"))
            if skill_meta.get("name") != frontmatter.get("name"):
                errors.append("skill.json 与 SKILL.md 的 name 不一致")
            for field in ("displayName", "description", "version", "license"):
                if not skill_meta.get(field):
                    warnings.append(f"skill.json 缺少 {field}")
        except json.JSONDecodeError as exc:
            errors.append(f"skill.json 无法解析：{exc}")

    package_path = root / "package.json"
    if package_path.exists():
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
            if package.get("name") != "mini-program-ux-pro":
                warnings.append("package.json name 不是 mini-program-ux-pro")
            if not package.get("scripts"):
                warnings.append("package.json 没有便捷命令脚本")
        except json.JSONDecodeError as exc:
            errors.append(f"package.json 无法解析：{exc}")

    for schema_name in (
        "design-system.schema.json",
        "search-result.schema.json",
        "review-report.schema.json",
    ):
        schema_path = root / "schemas" / schema_name
        if schema_path.exists():
            try:
                json.loads(schema_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{schema_name} 无法解析：{exc}")

    for script in (root / "scripts").glob("*.py"):
        if script.name == "validate_skill.py":
            continue
        text = script.read_text(encoding="utf-8", errors="replace")
        if FORBIDDEN_NETWORK.search(text):
            errors.append(f"{script.name} 引入了网络库；基础检索不应依赖网络")
        if re.search(r"\bTODO\b|\bFIXME\b", text):
            warnings.append(f"{script.name} 含有 TODO/FIXME")

    markdown_checked = _check_text_files(root, errors, warnings)
    command_count = _check_commands(root, errors, warnings)

    readme_path = root / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8", errors="replace")
        required_readme_sections = [
            "项目介绍",
            "项目特色",
            "参考",
            "支持",
            "安装",
            "检索",
            "设计系统",
            "审查",
            "持久化",
            "微信开发者工具",
            "常见问题",
            "已知限制",
            "路线",
        ]
        for section in required_readme_sections:
            if section not in readme:
                warnings.append(f"README 缺少主题：{section}")

    return {
        "ok": not errors,
        "root": str(root),
        "frontmatter": frontmatter,
        "markdown_files_checked": markdown_checked,
        "documented_script_commands": command_count,
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="验证 MPUX Pro Skill 文件与命令")
    parser.add_argument("--root", default=str(ROOT), help="Skill 根目录，默认项目根目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)
    result = validate(Path(args.root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("MPUX Pro Skill 验证")
        print("=" * 60)
        print(f"根目录：{result['root']}")
        print(f"name：{result['frontmatter'].get('name', '(缺失)')}")
        print(f"Markdown 文件：{result['markdown_files_checked']}")
        print(f"文档脚本命令：{result['documented_script_commands']}")
        print(f"错误：{len(result['errors'])}  警告：{len(result['warnings'])}")
        for error in result["errors"]:
            print(f"[ERROR] {error}")
        for warning in result["warnings"]:
            print(f"[WARN]  {warning}")
        print("结果：" + ("通过" if result["ok"] else "未通过"))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())