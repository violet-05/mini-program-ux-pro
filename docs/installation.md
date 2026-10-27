# 安装

## 环境要求

- Python 3.10 或更高版本（当前验证：Python 3.12.6）；
- 基础检索、设计系统生成、静态审查不需要 Node.js、数据库或 AI API Key；
- 可选的微信开发者工具运行时验收需要 Node.js 18+、npm 和已安装的 DevTools；
- 建议保留项目目录结构，不要只复制 `SKILL.md`。

## 方式一：安装到当前项目（推荐试用）

在 Skill 项目根目录运行：

```bash
python scripts/install_skill.py --project
```

会把 Skill 复制到当前项目的 `.claude/skills/mini-program-ux-pro/`，并执行一次“商品卡片”检索冒烟测试。

## 方式二：安装到用户级 Claude Skills 目录

```bash
python scripts/install_skill.py
```

默认目标：

- macOS/Linux：`~/.claude/skills/mini-program-ux-pro/`
- Windows：`%USERPROFILE%\.claude\skills\mini-program-ux-pro\`

如果目标已存在：

```bash
python scripts/install_skill.py --force
```

`--force` 会先删除同名安装目录，请确认该目录属于本 Skill。

只检查不复制：

```bash
python scripts/install_skill.py --check
```

## 方式三：手动安装

把整个项目目录复制/移动到目标工具的 skills 目录，并确保最终结构为：

```text
<skills-dir>/
└── mini-program-ux-pro/
    ├── SKILL.md
    ├── data/
    ├── references/
    ├── scripts/
    └── ...
```

不要只复制 `SKILL.md`：它依赖 `data/` 和 `scripts/`。

## 其他 AI 工具

`SKILL.md` 使用通用 YAML frontmatter（`name`、`description`）。不同工具的 Skill 安装机制可能不同：

- 支持 Agent Skills 的工具：放入其约定的 skills 目录；
- Codex/Cursor 等工具：按其当前官方文档把 `SKILL.md` 和资源目录纳入工作区；
- 只支持提示词的工具：可把 `SKILL.md` 作为项目说明，但仍需要 `data/` 和 `scripts/` 才能执行检索。

本项目**不声称**会被所有工具自动识别。请以目标工具的安装文档为准。

## 验证安装

### 1. Skill 文件与命令

```bash
python scripts/validate_skill.py
```

### 2. 检索

```bash
python scripts/search.py "商品卡片" --domain components -n 1
```

期望：返回 `comp-product-card`。

### 3. 设计系统

```bash
python scripts/generate_design_system.py --product "音乐播放器小程序" --style "现代极简" --stack wechat-native --output ./design-system --format both
```

期望生成：

- `design-system/MASTER.md`
- `design-system/MASTER.json`
- `design-system/tokens.wxss`
- `design-system/pages/*.md`

### 4. 静态审查

```bash
python scripts/audit_mini_program.py --path . --format markdown
```

只审查，不修改项目。

### 5. 项目自检

```bash
python scripts/validate_project.py --path .
```

## Windows 说明

- 如果 `python` 不可用，尝试 `py -3` 或 `python3`；
- 本项目命令在 Windows 的 Git Bash / Claude Code 中验证；
- 输出使用 UTF-8；中文查询建议加引号；
- 路径含空格时用引号包裹，例如 `--path "<项目目录>\tests\fixtures\wechat-native"`。

## 可选：微信开发者工具运行时验收

核心 Skill 不应因缺少 DevTools 而不可用；以下只在需要模拟器截图/交互验收时启用：

1. 微信开发者工具 → 设置 → 安全设置 → 开启服务端口 / CLI HTTP 调用；
2. Node.js 18+；
3. 安装可选依赖：
   ```bash
   cd verification/devtools
   npm install
   ```
4. 检查：
   ```bash
   python scripts/devtools_adapter.py --cli "<cli.bat 路径>" status
   ```
5. 运行：
   ```bash
   python scripts/devtools_adapter.py --cli "<cli.bat 路径>" run --project verification --port 9420
   ```

产物位于 `verification/artifacts/`。适配器不会修改安全设置。截图只来自开发者工具模拟器，不是真机。

本机实际验证：DevTools 2.02.2608070、基础库 3.17.4，24/24 检查通过、9 张截图。

## 卸载

删除安装目录即可：

```text
<skills-dir>/mini-program-ux-pro
```

不会影响用户项目文件。

## 升级

1. 备份已修改的 `design-system/`（设计输出不属于 Skill 源码）；
2. 用新版目录覆盖安装（`--force`）；
3. 运行 `python scripts/validate_project.py --path .`；
4. 重新阅读 CHANGELOG 与 docs。

## 安全

- 不要求 API Key；
- 不默认上传项目数据；
- 静态审查只读项目，不执行项目代码；
- 自动写入只发生在显式 `--output` 与安装目录；
- 覆盖已有设计系统需要显式 `--force`。

## 常见安装问题

见 [故障排查](troubleshooting.md)。