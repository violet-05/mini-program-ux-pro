# 故障排查

## 先检查安装

```bash
python mpux.py doctor
python mpux.py doctor --json
```

在源码或安装目录运行；其他目录中使用 `mpux.py` 的绝对路径。诊断会列出缺失文件、元数据/知识库错误和修复建议。它不检查用户项目，也不把未执行的模拟器或真机项目标成通过。

若提示「安装目标不能位于源目录内」，请使用 `python mpux.py install --project "../your-mini-program"` 指向你的小程序项目。不要在 Skill 源码中安装到它自身的 `.claude/skills`。

升级采用临时目录复制与检索验证，再替换已识别的旧 Skill；验证失败不会删除旧安装。若拒绝覆盖无关目录或符号链接，请换一个目标目录，不要通过删除文件绕过检查。

## Python 不可用

```bash
python --version
python3 --version
py -3 --version
```

本项目需要 Python 3.10+。Windows 上把命令中的 `python3` 换成 `python` 或 `py -3`。

## 中文输出乱码

项目脚本会在启动时尝试把 stdout/stderr 设为 UTF-8。如果终端仍乱码：

- Git Bash/PowerShell 设置 UTF-8 编码；
- 查询加引号；
- 把输出写入文件：
  ```bash
  python scripts/search.py "商品卡片" --domain components --json > result.json
  ```
- 不把 PowerShell 的 `>` 与 Python 重定向混用在不同编码下。

默认 GBK 控制台下可显式设置：

```bash
# Git Bash
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
```

```powershell
# PowerShell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
```

也可以用 `python -X utf8 scripts/validate_project.py --path .` 运行单次命令。项目 CI 包含 GBK stdio 回归测试，所有 CLI 的 stdout/stderr 应为 UTF-8。

## 审查扫描范围

审查器会跳过 `.claude`、`.qoder`、`.cursor`、`.codex`、`node_modules` 与构建产物，避免把安装的 Skill 或依赖误当成用户源码。超过 4000 个可审查文件时会中止并提示缩小 `--path`，不会悄悄输出截断报告。

## 检索没有结果

- 检查查询是否为空/全是标点；
- 用更具体的中文短语；
- 明确 `--domain`；
- 确认引用文件存在；
- 运行：
  ```bash
  python scripts/search.py "商品卡片" --domain components
  ```
- 0 结果是合法结果，不会伪造记录；根据 `suggestions` 改写。

常见分类：

```text
product / style / color / layout / component / ux / mini-program /
anti-pattern / typography / reasoning / all
```

复数别名（components/layouts/colors）也支持。

## 检索结果不相关

- 一次查询聚焦一个意图；
- 不用整段需求作为关键词；
- 指定 `--domain`；
- 使用记录 ID 或中文名称；
- 参考输出中的 `matched_fields`，调整关键词。

例如：

```bash
python scripts/search.py "底部安全区域" --domain mini-program
```

比“我的小程序底部被挡住了怎么办”更适合本地检索。

## 设计系统找不到产品

错误会列出建议。改用知识库中的产品名或别名：

```bash
python scripts/search.py "音乐" --domain product
```

然后：

```bash
python scripts/generate_design_system.py --product "音乐播放器小程序" ...
```

产品不存在时不会随机伪造。

## 风格找不到

查看可用风格：

```bash
python scripts/search.py "风格 极简 东方 数据" --domain style -n 20
```

使用风格 ID 或中文名。`--style` 找不到会报错并列出风格。

## MASTER.md 已存在，未覆盖

这是保护机制。先读现有 Master：

```bash
cat design-system/MASTER.md
```

确认需要更新后再：

```bash
python scripts/generate_design_system.py ... --force
```

`--force` 会覆盖 Master、token 和同名页面。备份你的设计。

## 页面文件未生成

- 默认只生成 3 个推荐页面；
- 页面名无法识别时用 `--pages all` 或传 layout ID；
- 已存在的同名页面不会覆盖，除非 `--force`；
- `--no-pages` 会关闭页面生成。

```bash
python scripts/generate_design_system.py ... --pages home,product-detail
```

## 审查识别错技术栈

检查项目根目录：

- 原生：`app.json`、`project.config.json`；
- uni-app：`pages.json`、`@dcloudio/*`；
- Taro：`app.config.ts/js`、`@tarojs/*`。

如果传入的是编译产物或子目录，请改传源码根：

```bash
python scripts/audit_mini_program.py --path ./src --format markdown
```

如果设计系统在项目根目录而 `--path` 指向 `miniprogramRoot` 子目录，可显式指定：

```bash
python scripts/audit_mini_program.py --path ./miniprogram --design-system ./design-system
```

不指定时，审查器会在当前目录及上级目录查找 `design-system/MASTER.json`。

纯 HTML 会被标记为浏览器原型，不会当作小程序。

## 审查漏报/误报

静态审查是启发式：

- 检查 `verification` 与 `confidence`；
- 自动扫描看不到运行时/真实视觉；
- 阴影/内边距可能让视觉热区大于 CSS 尺寸；
- 条件编译代码需要人工确认；
- 请结合微信开发者工具和真机。

工具不会修改项目。

## JSON 输出解析失败

- 确保命令使用 `--json` 或 `--format json`；
- 不要把提示文字混入 stdout；
- 输出重定向时使用 UTF-8；
- 检查脚本退出码；
- 报告可以写入文件：
  ```bash
  python scripts/audit_mini_program.py --path . --format json --output review.json
  ```

## 数据验证失败

```bash
python scripts/validate_data.py
```

按错误逐项修复：

- 缺少列；
- 重复/非法 ID；
- 空字段；
- 引用不存在（产品/风格/颜色/组件/布局/规则）；
- 非法 HEX；
- 对比度不足；
- 平台字段错误；
- 来源 URL/日期。

修改后用：

```bash
python scripts/validate_project.py --path .
```

## Skill 验证失败

```bash
python scripts/validate_skill.py
```

常见：

- 缺少必需文件；
- frontmatter 缺失/name 不一致；
- Markdown 相对链接指向不存在文件；
- 文档命令引用不存在脚本；
- CLI `--help` 失败；
- 文档主题缺失。

按错误补齐；不要删除检查来“通过”。

## 安装失败

- 目标已存在 → `--force`（确认目录属于本 Skill）；
- 权限不足 → 换用户目录或用 `--project`；
- Python 不在 PATH → 使用完整解释器路径；
- 安装后冒烟失败 → 检查目标目录是否复制了 `data/` 和 `scripts/`。

## 安全区/键盘问题

- 不用开发者工具作为最终结论；
- 真机 iOS/Android 分别测试；
- 固定底栏加安全区 padding；
- 内容加等高占位；
- 输入页处理键盘；
- `env()` 不可用时使用运行时信息/回退；
- 参考 [安全区域](../references/safe-area.md)。

## CSS 变量不生效

部分基础库/渲染引擎可能不支持或行为不同：

- 使用生成器输出中的字面值；
- 用 SCSS/构建期变量；
- 关键组件不依赖 CSS 变量；
- 在目标环境验证。

## 输出链接/文件在工具中打不开

只把文件写到用户项目目录或安装目录；不要从临时目录/外部地址声称可点击。使用项目相对路径。

## 微信开发者工具 / 运行时验收

### CLI 提示服务端口关闭

```text
IDE service port disabled
```

打开微信开发者工具 → 设置 → 安全设置 → 开启服务端口 / CLI HTTP 调用。适配器不会自动修改这个安全设置。

检查：

```bash
python scripts/devtools_adapter.py --cli "<cli.bat>" status
```

### 自动化连接失败

当前验证过的组合：

- DevTools 2.02.2608070；
- 基础库 3.17.4；
- `miniprogram-automator@0.13.0`；
- Node 24。

`automator.launch()` 可能在当前版本立即失败。验收脚本使用官方 CLI `auto` + `automator.connect`，不依赖旧 `launch()` 时序。

如果端口 9420 被占用，换一个端口：

```bash
python scripts/devtools_adapter.py --cli "<cli.bat>" run --project verification --port 9431
```

### 首次导入需要信任项目

验收脚本向 CLI 传递 `--trust-project`，仅针对 `verification/` 本地示例。不要把该参数用于来源不明的项目。

### 截图失败

`miniProgram.screenshot()` 只支持开发者工具模拟器，不支持客户端真机。真机请手动截图并记录设备/系统/微信版本。

### 没有 Node 或 automator

核心检索/生成/审查仍可用。运行时验收需要：

```bash
cd verification/devtools
npm install
```

### 截图出现但结果失败

查看：

- `verification/artifacts/results.json`
- `verification/artifacts/runtime-run.log`
- `console`、`exceptions` 字段。

自动截图通过不等于真机通过，也不等于视觉模型认为审美合格。

## 仍无法解决

运行完整自检并保留输出：

```bash
python scripts/validate_project.py --path . --json > validation.json
```

然后在 Issue 中提供：操作系统、Python 版本、命令、完整错误、最小复现项目（去除隐私/密钥）。