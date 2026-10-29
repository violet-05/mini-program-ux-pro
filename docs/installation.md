# 安装

## 环境要求

- Python 3.10 或更高版本（当前验证：Python 3.12.6）；
- 基础检索、设计系统生成、静态审查不需要 Node.js、数据库或 AI API Key；
- 可选的微信开发者工具运行时验收需要 Node.js 18+、npm 和已安装的 DevTools；
- 建议保留项目目录结构，不要只复制 `SKILL.md`。

## 方式一：安装到你的小程序项目

在 MPUX Pro 源码目录运行，将路径替换为你的小程序项目目录（不是本 Skill 源码目录）：

```bash
python mpux.py install --project "../your-mini-program"
```

会安装到该项目的 `.claude/skills/mini-program-ux-pro/`。也可以在小程序项目目录中，通过绝对路径运行 `python "<MPUX源码目录>/mpux.py" install --project`。

安装前可使用 `--check` 预检而不复制；成功后会显示完整的诊断和检索命令。不能将 Skill 安装到自身源码目录内，以免递归复制。

只想先试用 CLI 时，无需安装：在源码目录运行 `python mpux.py doctor` 即可。

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

`--force` 只接受有 `SKILL.md` 和匹配名称 `skill.json` 的旧 Skill 目录。新副本先在临时目录完成检索验证，再替换旧版；复制或验证失败时保留旧版，替换异常时尝试回滚。不保证断电恢复，也不会保留安装目录内的用户定制，请先备份。

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

安装后在目标 Skill 目录运行以下命令，或直接复制安装成功提示中的完整路径命令。

### 1. 安装诊断

```bash
python mpux.py doctor
```

只需 Python，不要求 Node.js 或微信开发者工具。诊断包含版本、核心文件、知识库与真正的独立检索，失败时显示修复建议。自动化可加 `--json`。

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

### 5. 维护者源码自检

只有在维护完整源码仓库时才需要运行 `python mpux.py validate`。安装可用性用 `doctor`，自己的小程序用 `audit --path "<小程序目录>"`；不要混淆这三种检查。

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
3. 在新安装目录运行 `python mpux.py doctor`；
4. 重新阅读 CHANGELOG 与 docs。

## 安全

- 不要求 API Key；
- 不默认上传项目数据；
- 静态审查只读项目，不执行项目代码；
- 自动写入只发生在显式 `--output` 与安装目录；
- 覆盖已有设计系统需要显式 `--force`。

## 常见安装问题

见 [故障排查](troubleshooting.md)。