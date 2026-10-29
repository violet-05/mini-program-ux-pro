# 使用指南

## 统一命令入口

| 需求 | 命令 |
| --- | --- |
| 检查安装 | `python mpux.py doctor` |
| 查设计知识 | `python mpux.py search` |
| 生成设计系统 | `python mpux.py design` |
| 审查现有小程序 | `python mpux.py audit` |
| 比较两次审查结果 | `python mpux.py compare` |
| 安装到目标项目 | `python mpux.py install --project "../your-mini-program"` |
| 维护者仓库自检 | `python mpux.py validate` |
| 可选的模拟器验收 | `python mpux.py verify --help` |

在源码或安装目录运行；其他目录中请使用 `mpux.py` 的绝对路径。所有路径参数仍相对于当前工作目录，不会自动切换到 Skill 目录。每个命令支持 `--help`，版本查询使用 `python mpux.py --version`。

检索、生成、审查均在本地运行，不调用远程 AI API。以下底层脚本入口仍可直接使用，参数与统一入口一致。

### 诊断与退出码

`python mpux.py doctor --json` 输出安装路径、Python 路径、版本、检查结果、修复建议与未检查项；它不启动微信开发者工具，也不执行用户项目代码。`validate` 面向维护者完整源码仓库，检查历史证据，但不重跑模拟器；不要用它代替用户项目的 `audit`。

- `0`：命令执行成功；无结果搜索也可能返回 `0`，应检查结果数量。
- `1`：诊断/验证未通过，审查达到 `--fail-on` 阈值，或对比出现达到 `--fail-on-new` 阈值的已确认新增问题。
- `2`：参数或输入错误，例如设计文件损坏、安装目标不合法。

自动化按退出码判断，不要只匹配终端中的「通过」文字。审查默认只出报告，不因发现问题而失败；CI 中请显式设置 `--fail-on P1`。

---

## 1. 检索设计知识

### 中文、分类检索

```bash
python scripts/search.py "商品卡片" --domain components
python scripts/search.py "微信小程序 底部安全区域" --domain mini-program
python scripts/search.py "现代东方美学" --domain style
python scripts/search.py "电商首页 商品卡片" --domain layouts
```

分类可用：

- `product`
- `style`
- `color`
- `layout`
- `component`
- `ux`
- `mini-program`
- `anti-pattern`
- `typography`
- `reasoning`
- `all`

也接受常见复数别名，如 `components`、`layouts`、`colors`。

### 技术栈检索

```bash
python scripts/search.py "原生小程序" --stack wechat-native
python scripts/search.py "uni-app 导航栏" --stack uni-app
python scripts/search.py "Taro 路由" --stack taro
```

`--domain` 与 `--stack` 不能同时使用；请分别检索设计知识和实现规则。

### 控制结果

```bash
python scripts/search.py "表单 错误 重试" --domain ux -n 8
```

`-n/--max-results` 范围 1–20。

### 输出 JSON

```bash
python scripts/search.py "底部安全区" --domain mini-program --json
```

JSON 包含：

- 查询、分类、数据源；
- `id`、`name`、`score`；
- `matched_terms` 与 `matched_fields`（匹配依据）；
- `reasons`（精确匹配/产品偏好加权）；
- 完整 `record`；
- 0 结果时的 `notice` 与 `suggestions`。

### 产品上下文

```bash
python scripts/search.py "反馈 加载 错误" --domain ux --product prod-ecommerce
```

产品推荐记录会获得额外加权，并在输出中显示产品上下文。这不是硬过滤，避免丢失通用规则。

### 检索机制与限制

- BM25 + 字段权重；
- 中文二字 bigram 与完整短语；
- 中英文同义词扩展；
- ID/名称/别名精确匹配加权；
- 不联网、不调用分词服务。

局限：同义词表是人工维护的，复杂自然语言长句可能不如精确短语；0 结果时应重写查询，而不是编造命中。

---

## 2. 生成设计系统

### 基本用法

```bash
python scripts/generate_design_system.py \
  --product "文创商城小程序" \
  --stack wechat-native \
  --output ./design-system
```

### 指定风格

```bash
python scripts/generate_design_system.py \
  --product "音乐播放器小程序" \
  --style "现代极简" \
  --stack wechat-native \
  --output ./design-system
```

`--style` 支持风格 ID、中文名、英文名和关键词。若找不到会报错并列出可用风格，不会静默套默认色。

### 指定页面覆盖

```bash
python scripts/generate_design_system.py \
  --product "综合电商小程序" \
  --stack wechat-native \
  --pages home,product-detail,profile \
  --output ./design-system
```

`--pages all` 生成产品推荐的全部布局；`--no-pages` 不生成页面文件。

默认只生成 3 个推荐页面覆盖。

### 输出格式

```bash
# Markdown + JSON + token + pages（默认）
... --output ./design-system --format both

# 仅 MASTER.md（仍会写 token/pages）
... --output ./design-system --format md

# 仅 MASTER.json（仍会写 token/pages）
... --output ./design-system --format json
```

不指定 `--output` 时打印 Markdown；加 `--json` 或 `--format json` 打印结构化设计系统。

### 保护已有文件

如果 `MASTER.md` 已存在，生成器默认跳过，不覆盖任何文件。先读现有设计，确认要更新后：

```bash
... --force
```

### 产物

```text
design-system/
├── MASTER.md
├── MASTER.json
├── tokens.wxss        # uni-app/Taro 为 tokens.scss
└── pages/
    ├── home.md
    ├── product-detail.md
    └── profile.md
```

- `MASTER.md` 是人读事实源；
- `MASTER.json` 包含完整规则、token、来源 ID；
- 页面覆盖继承 Master；
- `tokens.*` 提供技术栈变量层。

### 设计系统检查

阅读：

- 第 5 节冲突；
- 第 6 节对比度；
- 第 12 节微信平台未执行项；
- 第 16 节数据来源与限制。

生成器不会伪造不存在的记录。若产品没有匹配，命令失败并给建议，而不是随便选一个产品。

---

## 3. 审查现有小程序

```bash
python scripts/audit_mini_program.py --path . --format markdown
```

只读，不修改项目。

### JSON 报告

```bash
python scripts/audit_mini_program.py --path . --format json --output review.json
```

### CI 阈值

```bash
python scripts/audit_mini_program.py --path . --fail-on P1
```

发现 P1 或更严重问题时返回退出码 1。

### 能检查什么

- 技术栈识别；
- 页面注册/模板缺失；
- TabBar 数量/图标/自定义组件；
- 自定义导航；
- WXML 浏览器标签/事件；
- 浏览器 DOM/BOM API；
- 固定底栏安全区；
- CSS 触摸目标/字号；
- 加载/空/错误状态线索；
- 图片 mode/懒加载；
- 隐私 API 线索；
- 设计 token 硬编码；
- wx:for key；
- 过多 !important/无限动画。

### 不能检查什么

- 实际视觉；
- 真机键盘/安全区；
- 分享/授权真实流程；
- 帧率与首屏性能；
- 读屏；
- 视觉模型审美。

报告中 `environment`、`skipped_checks` 与 `coverage` 会明确写出。不要把静态审查当运行时验收。

### 前后对比

```bash
python scripts/audit_mini_program.py --path . --json --output review-before.json
# 修改页面后
python scripts/audit_mini_program.py --path . --json --output review-after.json
python mpux.py compare review-before.json review-after.json --format markdown
```

对比结果分五类：

- `new`：已确认新增（本次范围内、上次也检查过同类问题）；
- `new_unverified`：新增但无法归因，例如问题所在文件上次未扫描、或该检查上次未执行；
- `resolved`：已确认修复（本次执行了同一检查，且相关文件仍在扫描范围内）；
- `unconfirmed`：上次有、本次没有，但检查未执行或扫描范围缩小，不能确认；
- `remaining`：两次都存在；行号变化不影响匹配。

匹配使用报告中的 `fingerprint`，它由检查 ID、类别、标题、规则和涉及文件组成，不包含行号、时间或排序位置。重命名文件会被视为“旧问题消失 + 新问题出现”。JSON 输出的 `resolved` 只表示静态规则不再报告该问题，不代表视觉、交互或真机验收通过。

CI 中可用 `--fail-on-new P1`：只有已确认的新增问题达到阈值才返回退出码 1，`new_unverified` 不计入。

当前报告格式为 1.1.0；旧版 1.0.0 报告没有稳定指纹，必须用当前版本重新生成后才能比较，工具会直接拒绝不兼容的格式。`compare` 不会覆盖输入报告。

### 推荐流程

见 [现有项目审查工作流](../workflows/review-existing-project.md)。

---

## 4. 视觉模型接口（未接入模型）

本版不调用视觉模型，但提供统一的请求/响应契约：

```bash
python scripts/visual_review_adapter.py --help
```

- `build-request`：生成包含截图路径、页面类型、设计系统、产品与审查目标的 JSON；
- `validate-response`：校验模型响应结构；
- 默认 `UnavailableVisualAdapter` 会明确报“不可用”；
- 契约通过不代表审美判断正确；
- 上传截图需由用户显式授权的适配器完成。

## 5. 微信开发者工具运行时验收（可选）

本版提供可选的模拟器自动化适配器；核心检索/生成/静态审查仍不依赖 Node。

### 前置

1. 安装微信开发者工具，并在 **设置 → 安全设置** 手动开启 **服务端口 / CLI HTTP 调用**；
2. Node.js 18+；
3. 安装可选验收依赖：

```bash
cd verification/devtools && npm install
```

### 检查 CLI 与依赖

```bash
python scripts/devtools_adapter.py --cli "<cli.bat 的绝对路径>" status
```

如果服务端口未开启，适配器只报告状态和修复步骤，不会修改安全设置。

### 运行验收

```bash
python scripts/devtools_adapter.py --cli "<cli.bat 的绝对路径>" run --project verification --port 9420
```

本机实测路径为 `<cli.bat 的绝对路径>`。如果 9420 被占用，换一个端口。

### 结果

- `verification/artifacts/results.json`
- `verification/artifacts/*.png`
- `verification/artifacts/runtime-run.log`

覆盖首页/加载/错误/空状态、播放器、自定义导航、安全区、TabBar、队列、重试和恢复。

当前实测：24/24 检查通过、9 张截图、0 console.error、0 异常，基础库 3.17.4。截图仅来自开发者工具模拟器，不是真机。

**兼容性说明：**当前 `miniprogram-automator@0.13.0` 的 `launch()` 与 DevTools 2.02.2608070 返回时序不兼容，适配器使用官方的 CLI `auto` + `automator.connect`。

## 6. 验证

```bash
python scripts/validate_data.py
```

```bash
python scripts/validate_skill.py
```

```bash
python scripts/validate_project.py --path .
```

- 数据验证：CSV 结构、ID、引用、颜色对比度；
- Skill 验证：文件、frontmatter、链接、CLI 命令；
- 项目自检：编译、数据、Skill、检索、生成器、审查与对比冒烟，以及已保存的模拟器验收证据。

## 7. 安装

```bash
python mpux.py install --project "../your-mini-program"
```

请替换为你的小程序项目目录。详见 [安装](installation.md)。

## 8. 退出码

- `0`：命令成功/无结果但仍为合法查询；
- `1`：验证失败，或审计达到 `--fail-on` 阈值；
- `2`：参数错误、未知分类/风格/产品、路径不存在等技术错误。

## 9. 数据与隐私

- 不联网检索本地数据；
- 不默认调用远程 AI；
- 不在命令中提交密钥；
- 项目内容只在本机读取；
- 写入只发生在显式输出目录/安装目录；
- DevTools 自动化只在本机连接，截图保存在本地 artifacts；
- 不自动开启服务端口、不绕过安全设置。

## 10. 已知限制

见 [兼容性](compatibility.md) 与 [路线图](roadmap.md)。