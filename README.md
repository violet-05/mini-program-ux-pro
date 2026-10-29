# Mini Program UX Pro（MPUX Pro）

**让 AI 做小程序时，有设计依据，也有验收边界。**

MPUX Pro 是面向微信小程序的中文 UI/UX Skill 与本地命令工具。把产品需求转成项目级设计系统，再用静态审查发现实现问题，而不是给每个产品套同一张模板。

**Python 3.10+ · 核心零依赖 · 无 API Key · 原生 / uni-app / Taro**

## 三分钟上手

下载源码后，在本目录运行；不需要 `npm install`：

```bash
python mpux.py doctor
python mpux.py search "商品卡片" --domain components -n 1
python mpux.py design --product "音乐播放器小程序" --stack wechat-native --output ./design-system --format both
```

预期：诊断显示「核心功能可用」，检索返回 `comp-product-card`，设计输出包含 `MASTER.md`、`MASTER.json`、`tokens.wxss` 与 `pages/`。已有 Master 默认保留，不会静默覆盖。

审查你自己的小程序：

```bash
python mpux.py audit --path "../your-mini-program" --format markdown
```

修改前后各保存一份 JSON，再比较新增、修复与遗留：

```bash
python mpux.py audit --path "../your-mini-program" --json --output review-before.json
# 修改后
python mpux.py audit --path "../your-mini-program" --json --output review-after.json
python mpux.py compare review-before.json review-after.json
```

| 你现在要做什么 | 入口 |
| --- | --- |
| 第一次使用 / 排查安装问题 | `python mpux.py doctor` |
| 找设计依据 | `python mpux.py search "关键词"` |
| 建立统一设计系统 | `python mpux.py design --help` |
| 检查已有页面 | `python mpux.py audit --help` |
| 比较两次审查结果 | `python mpux.py compare --help` |
| 接入 AI 编程工具 | [安装指南](docs/installation.md) |
| 查看完整参数与案例 | [使用指南](docs/usage.md) · [音乐案例](examples/music-mini-program.md) |

`doctor` 通过只表示本地安装可用，不代表用户项目、视觉效果或真机验收通过。遇到问题见 [故障排查](docs/troubleshooting.md)。

## 项目介绍

AI 在生成小程序时经常遇到：

- 所有页面都是顶部标题 + 搜索框 + 轮播 + 四宫格 + 三张卡片；
- 所有按钮都是胶囊、所有模块都是圆角卡片加阴影；
- 用无意义渐变/Emoji 图标伪装“高级”；
- 只在浏览器或模拟器中看过，就宣称“小程序完成”；
- 忽略安全区域、键盘、TabBar、返回、微信原生组件和真机差异；
- 把 Web HTML/CSS/DOM API 直接当 WXML/WXSS/小程序 API；
- 给所有产品同一套配色和排版。

MPUX Pro 用原创结构化知识库和本地检索解决这些问题，并提供 Master + Page Override 的设计系统持久化。

## 项目特色

- **小程序专属**：导航、TabBar、安全区域、路由、键盘、触摸、原生组件、隐私、真机验证独立建模。
- **技术栈分离**：微信原生、uni-app、Taro 各有独立规则；共享设计原则，不混淆实现。
- **原创中文知识库**：31 类产品、22 种风格、24 套配色、27 种布局、33 个组件、36 条 UX 规则、34 条微信平台规则、40 条反模式、12 套排版、16 组设计推理。
- **中英文本地检索**：BM25 + 字段权重 + 中文 bigram + 同义词扩展，显示匹配字段、命中词和匹配原因。
- **设计系统生成器**：读取知识库，做风格/配色/排版/布局/组件/平台规则组合，输出 Master/JSON/token/页面覆盖。
- **冲突检查**：指定风格与产品不一致、配色兼容性、密度冲突、对比度不足等。
- **反模板化**：不同产品有不同首页结构、页面优先级与设计理由。
- **静态审查**：识别技术栈、页面结构、浏览器标签/API、TabBar、自定义导航、安全区、触摸目标、字号、状态、图片、隐私和 token 一致性。
- **审查前后对比**：两次 JSON 报告按稳定问题指纹匹配，区分新增、已确认修复、遗留和无法确认；未执行的检查或缩小扫描范围不会被算作修复。
- **明确的验证边界**：静态审查、浏览器、微信开发者工具模拟器、真机分开记录；未执行不算通过。
- **可选的运行时验收**：提供 CLI/automator 适配器与真实小程序示例，可截图并自动验证交互，但只限开发者工具模拟器。
- **核心零第三方依赖**：Python 标准库；不联网；不需要 AI API Key。可选的 DevTools 运行时验收单独使用 Node/npm 开发依赖。
- **可安装、可测试**：提供安装器、数据/Skill/项目校验和 unittest 测试。

## 与参考项目的区别

架构研究参考了 MIT 许可的 [`nextlevelbuilder/ui-ux-pro-max-skill`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)，但本项目是独立实现：

| 方面 | 参考方向 | 本项目 |
| --- | --- | --- |
| 平台 | Web/多框架 | 微信小程序为核心 |
| 数据 | 其原创数据集 | 全新字段、中文内容、ID 与规则，不复制其数据集 |
| 技术栈 | Web/桌面/移动多栈 | 原生/uni-app/Taro，独立 CSV |
| 平台规则 | Web UX 为主 | 34 条微信平台规则 + 3 个技术栈规则库 |
| 设计生成 | 多领域检索/推理 | 产品任务 + 中文推理 + 小程序 token + 页面覆盖 |
| 审查 | 设计规则为主 | 可运行静态审查 CLI + 证据/置信度/环境边界 |
| 安装 | npm/CLI 等 | Python 本地安装器 + 检索冒烟测试 |

详见 [参考项目研究](docs/reference-research.md) 与 [NOTICE](NOTICE.md)。

## 支持的平台与技术栈

设计上跨平台（Python 3.10+），当前实际验证环境：

- Windows 11 Pro
- Python 3.12.6
- Git Bash / Claude Code
- 微信开发者工具 2.02.2608070 · 基础库 3.17.4 · 390×844 模拟器
- Node.js 24.11.0（仅可选运行时验收使用）
- 微信官方文档核验日期：2026-10-27

核心 CLI 已通过 Ubuntu/Windows × Python 3.10/3.12 的 CI；macOS 尚未实测。开发者工具的交互与截图证据仍仅来自上述 Windows 环境。

技术栈：

| 技术栈 | 支持 |
| --- | --- |
| 微信原生小程序 | ✅ 设计系统 + 静态审查 + 技术栈规则 |
| uni-app（微信目标） | ✅ 设计系统 + 静态审查 + 技术栈规则 |
| Taro（微信目标） | ✅ 设计系统 + 静态审查 + 技术栈规则 |
| 浏览器原型 | ⚠️ 可审查并明确标记，但不是已验证的小程序 |

不支持支付宝/抖音等其他小程序平台、Flutter、React Native 或技术栈自动迁移。

## 安装

要求：Python 3.10+，无第三方 Python 依赖。可选的 DevTools 运行时验收另需 Node.js 18+ 与 `npm install`。

在源码目录安装到你的小程序项目（请替换目标路径，不要指向 Skill 源码自身）：

```bash
python mpux.py install --project "../your-mini-program"
```

安装到用户级 Claude Skills：

```bash
python mpux.py install
```

安装器先在临时目录执行检索验证，再替换旧版；已有安装须显式 `--force`，不会覆盖未识别的目录。宣传视频和工具缓存不进入 Skill 安装目录。

手动安装、其他 AI 工具与验证见 [安装文档](docs/installation.md)。

> 不同工具识别 Skill 的方式不同，本项目不声称会被所有工具自动加载。

## 快速开始

### 1. 检索

```bash
python scripts/search.py "电商首页 高级感 商品展示" --design-system
```

分类检索：

```bash
python scripts/search.py "商品卡片" --domain components
python scripts/search.py "微信小程序 底部安全区域" --domain mini-program
python scripts/search.py "现代东方美学" --domain style
```

技术栈：

```bash
python scripts/search.py "原生小程序" --stack wechat-native
python scripts/search.py "uni-app 导航栏" --stack uni-app
```

JSON：

```bash
python scripts/search.py "表单 错误 重试" --domain ux --json -n 5
```

### 2. 生成设计系统

```bash
python scripts/generate_design_system.py \
  --product "文创商城小程序" \
  --stack wechat-native \
  --output ./design-system
```

指定风格：

```bash
python scripts/generate_design_system.py \
  --product "音乐播放器小程序" \
  --style "现代极简" \
  --stack wechat-native \
  --output ./design-system
```

### 3. 审查现有小程序

```bash
python scripts/audit_mini_program.py --path . --format markdown
```

如果 `--path` 指向 `miniprogramRoot` 子目录，可用 `--design-system` 指定 `MASTER.json` 或 `design-system/` 目录；默认会在当前及上级目录查找。

只读，不修改项目。CI 阈值：

```bash
python scripts/audit_mini_program.py --path . --fail-on P1
```

修改后比较两份报告：

```bash
python mpux.py compare review-before.json review-after.json --fail-on-new P1
```

`compare` 输出 `new`、`new_unverified`、`resolved`、`unconfirmed`、`remaining` 五类。只有本次确实执行了同一检查、且相关文件仍在扫描范围内时才确认修复；否则标记为“无法确认”。`--fail-on-new` 只对已确认的新增问题生效。

### 4. 验证

使用者检查安装：

```bash
python mpux.py doctor
```

维护者检查完整源码仓库：

```bash
python scripts/validate_data.py
python scripts/validate_skill.py
python mpux.py validate
```

`validate` 检查已保存的模拟器证据，不会重跑开发者工具；也不是对用户项目的验收。

## 设计系统持久化

生成目录：

```text
design-system/
├── MASTER.md        # 全局事实源
├── MASTER.json      # 结构化 token/规则/来源 ID
├── tokens.wxss      # native；uni-app/Taro 为 tokens.scss
└── pages/
    ├── home.md
    ├── product-detail.md
    └── profile.md
```

规则：

- 页面覆盖默认继承 Master；
- 不允许为每页建立独立配色/字体；
- 允许页面级顺序、局部间距和本页状态；
- 已存在 `MASTER.md` 时生成器跳过；
- 只有明确 `--force` 才覆盖；
- 生成的 token/规则/来源可追溯。

## 微信开发者工具运行时验收与真机

本版提供一个**可选**的微信开发者工具模拟器适配器，核心 Skill 仍不依赖 Node：

- [devtools_adapter.py](scripts/devtools_adapter.py)：检测 CLI、检查服务端口、调用可选的 Node 验收脚本；
- [验收小程序](verification/README.md)：真实微信原生页面、当前设计系统、自动化脚本与截图；
- 需要用户手动在开发者工具“设置 → 安全设置”开启服务端口；
- 自动化只截取开发者工具模拟器，官方截图 API 不支持真机客户端。

本机实测（2026-10-27）：

- 微信开发者工具 2.02.2608070，基础库 3.17.4，模拟器 390×844；
- 24/24 自动化检查通过；
- 9 张真实模拟器截图；
- 0 个 `console.error`，0 个未捕获异常；
- 验收小程序静态审查 0 个问题。

```bash
python scripts/devtools_adapter.py --cli "<cli.bat 的绝对路径>" status
```

```bash
python scripts/devtools_adapter.py --cli "<cli.bat 的绝对路径>" run --project verification --port 9420
```

运行前需在 `verification/devtools` 执行 `npm install`，并自行开启服务端口。适配器不会修改安全设置。真实 iOS/Android 真机、键盘、音频中断和弱网仍未验证，不能把模拟器截图当作真机通过。

静态审查报告仍提供 `executed_checks`、`skipped_checks` 与 `coverage` 字段；运行时结果另存于 `verification/artifacts/results.json`。

## 常见问题

**为什么搜索不到结果？**  
本地检索不是语义大模型。用具体的中文短语/分类重试，见 [故障排查](docs/troubleshooting.md)。

**为什么生成器不覆盖已有设计？**  
保护已有设计决策。确认后显式 `--force`。

**为什么不同产品输出不同？**  
生成器按产品、推理、风格、配色、布局、组件和密度选择；不是固定模板。可以对比 6 个 [示例](examples/ecommerce-mini-program.md)。

**支持 React/Vue 网页吗？**  
只支持能编译到微信小程序的 uni-app/Taro。普通网页不是小程序。

**会调用 AI API 吗？**  
不会。除非未来增加显式可选适配器并以用户授权为前提。

**能在微信开发者工具里自动验证吗？**  
可以，但属于可选能力：需 Node.js、可选 npm 依赖和用户手动开启服务端口。当前已验证模拟器截图与交互，不支持真机自动化。

**能自动修改代码吗？**  
本版本提供 Skill 工作流与静态审查，没有独立自动修复器；由 AI 编程工具在用户授权下修改并复查。

## 已知限制

- 知识库是人工设计规则，不是对所有真实产品的研究结论；
- 中文检索不是语义向量搜索；
- 微信平台能力随基础库/框架版本变化，需看 `verification_status`；
- 静态审查可能漏报/误报；
- 前后对比只比较静态规则结果与扫描范围，不能替代人工确认、运行时或真机验收；1.0.0 版审查报告需要重新生成后才能与当前版本对比；
- 未内置视觉模型；提供独立的请求/响应契约与不可用适配器，不调用远程服务；
- 微信开发者工具自动化只覆盖模拟器，不包含 iOS/Android 真机；模拟器截图不能替代真机；
- 可选运行时验收需要 Node.js、npm 依赖和用户手动开启服务端口；
- macOS 未实测；Ubuntu CI 覆盖核心 CLI，不代表 Linux 开发者工具已验证；
- 生成器不能验证页面真实视觉、键盘、安全区、性能或业务正确性。

## 项目结构

```text
.
├── mpux.py                  # 统一 CLI：doctor / search / design / audit / compare / install
├── SKILL.md                 # AI 工作流入口与执行原则
├── data/                    # 原创知识库（产品/风格/配色/布局/规则/技术栈）
├── references/              # 设计/平台参考
├── styles/                  # 11 份风格应用指南
├── workflows/               # 8 个工作流
├── checklists/              # 6 个质量检查表
├── scripts/                 # 检索/生成/审查/校验/安装
├── schemas/                 # JSON 契约
├── templates/               # Master/页面覆盖/报告模板
├── examples/                # 6 个产品案例
├── verification/            # 可选的 DevTools 运行时验收小程序、截图与结果
├── promo-video/             # Remotion 宣传片工程（52s / 1080p / 独立 npm 项目）
├── tests/                   # unittest + fixtures
└── docs/                    # 安装/使用/架构/兼容性等
```

## 开发与测试

```bash
python -m unittest discover -s tests -v
python scripts/validate_project.py --path .
```

Windows 控制台建议设置 `PYTHONUTF8=1`；所有 CLI 也会主动把 stdout/stderr 切到 UTF-8。CI 在 Ubuntu/Windows 与 GBK stdio 环境下运行回归测试。

实际验收结果、五类产品差异、24 项 DevTools 模拟器检查和未验证项见 [验收报告](docs/acceptance-report.md)。运行时截图与机器可读结果在 [verification/artifacts](verification/artifacts/)。

## 宣传视频

源码仓库中的 `promo-video/` 是独立的 Remotion 工程，提供 52 秒、1920×1080、30fps 的项目宣传片，含中文神经语音、内嵌字幕和 SRT 字幕。成片与字幕位于 `promo-video/out/`（不纳入 Git），重新渲染见 `promo-video/README.md`；该目录不会随 Skill 安装。

视频工程有独立的 npm/Python 依赖；配音生成会连接在线 TTS 服务，不属于核心 CLI 的离线功能。Remotion 适用其自身许可条款。

## 未来路线

阶段 A 已完成；阶段 B 有基础静态审查；阶段 C 已完成开发者工具模拟器适配与截图/交互验收，视觉模型、真机自动化和自动迭代仍是规划。见 [路线图](docs/roadmap.md)。

## 许可证与致谢

本项目使用 MIT License。参考项目研究见 [docs/reference-research.md](docs/reference-research.md)，第三方许可与边界见 [NOTICE.md](NOTICE.md)。

微信、微信小程序等名称归腾讯所有。本项目不是腾讯官方产品。