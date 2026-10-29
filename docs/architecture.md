# 架构

## 总览

```text
SKILL.md
  ├─ workflows/       人/AI 的执行流程
  ├─ references/      设计原则与平台知识
  ├─ checklists/      审查与交付检查
  ├─ data/            可检索的结构化知识
  │   └─ stacks/      微信原生 / uni-app / Taro
  ├─ scripts/
  │   ├─ mpux_core.py           数据加载 + BM25 + 中文检索
  │   ├─ design_system.py       选择/冲突/token/持久化
  │   ├─ search.py              检索 CLI
  │   ├─ generate_design_system.py
  │   ├─ audit_mini_program.py  静态审查
  │   ├─ review_contract.py     报告契约与问题指纹
  │   ├─ review_compare.py      两次审查对比
  │   ├─ validate_data.py
  │   ├─ validate_skill.py
  │   ├─ validate_project.py
  │   ├─ install_skill.py
  │   ├─ visual_review_adapter.py
  │   └─ devtools_adapter.py      可选 DevTools CLI/automator 适配器
  ├─ verification/    可选运行时验收小程序、设计系统、截图与结果
  ├─ schemas/         JSON 输出契约
  ├─ templates/       Master/页面覆盖/审查报告模板
  ├─ examples/        类型化案例
  └─ tests/           单元与冒烟测试
```

## 数据层

### 产品规则

`products.csv` 定义产品类型、目标用户、场景、核心任务、首页结构、导航、密度、组件/风格/配色/布局/推理引用。

它不是关键词表，而是一组设计决策及理由。生成器读取引用 ID，不按关键词猜一条颜色。

### 风格/配色/排版

- `styles.csv`：视觉语言、排版、组件、动效、适合/不适合、错误和组合注意；
- `colors.csv`：真实 HEX、语义色、适用风格、使用与对比说明；
- `typography.csv`：系统字体栈、数字字体、字号/行高依据、小程序限制。

风格名称不等于固定配色。同一风格可因产品和品牌选不同色板。

### 页面与组件

- `layouts.csv`：页面任务、层级、主/次区域、组件、操作顺序、移动端注意；
- `components.csv`：使用场景、视觉/交互、触摸、状态、无障碍、原生实现和错误。

组件与布局通过 ID 交叉引用，数据验证会检查引用。

### UX 与小程序规则

- `ux-guidelines.csv`：可检查的通用交互规则；
- `mini-program-rules.csv`：微信平台专属规则，含来源 URL、核验状态、日期；
- `anti-patterns.csv`：设计/实现/验证问题、检测方法、修复、关联规则；
- `ui-reasoning.csv`：按场景组织风格/配色/布局/交互优先级和冲突提示。

小程序规则与 Web 通用 UX 分离，技术栈规则再分到 `data/stacks/*.csv`。

## 检索

### 分词

`mpux_core.py` 只使用标准库：

1. Unicode NFKC + casefold；
2. 英文按单词/标识符切分；
3. 中文连续文本加入完整短语（≤16 字）与相邻二字 bigram；
4. 人工同义词扩展（如“底部安全区域” ↔ safe-area）；
5. 去掉少量英文停用词。

中文 bigram 解决“无需外部分词器”的召回问题；代价是词序信息有限、同义词依赖维护。

### BM25

- 每个领域有独立索引；
- 字段权重不同（名称/别名高，正文低）；
- 文档长度归一化；
- ID/名称/别名精确匹配额外加权；
- 产品上下文对推荐记录加权；
- 结果保留命中的字段和词，便于解释。

它比 `in` 字符串匹配更可解释，但不是语义向量搜索。不要宣称“理解了自然语言”。

### 输出

`search-result.schema.json` 约定结果结构。JSON 结果包含完整记录与来源，Markdown 适合 AI/人阅读。

## 设计系统生成

`design_system.py`：

1. 解析产品（精确或检索）；
2. 解析/推荐风格；
3. 选择配色（产品推荐 + 风格兼容）；
4. 选择字体（风格 + 产品标签）；
5. 拉取布局；
6. 汇总组件；
7. 选 UX 规则（核心 + 推理 + 检索）；
8. 选小程序规则（导航/安全区/键盘/TabBar 等）；
9. 选反模式；
10. 加载技术栈规则；
11. 派生 token（颜色、字号、间距、圆角、阴影、动效、尺寸）；
12. 对比度与冲突检查；
13. 生成 Markdown/JSON；
14. 持久化 Master + 页面覆盖 + token 文件。

### 为什么 token 是“派生”的

颜色、字体、布局来自数据；圆角/阴影/动效/控件尺寸由版本化的风格 profile 派生。这是设计引擎规则，不是伪造数据。`MASTER.json.tokens.provenance` 记录派生来源。

### 冲突

- 指定风格与产品推荐不一致；
- 配色与风格无兼容标记；
- 产品高密度 + 低密度风格；
- 低密度产品 + 数据密集型/粗野风格；
- 高成本效果（玻璃/新拟态）与高密度冲突；
- 对比度不足；
- 风格明确标注不适用的场景与产品词重叠。

冲突不会被静默删除；生成器输出处理建议。

### 持久化

- 默认不覆盖已有 `MASTER.md`；
- `--force` 才能覆盖；
- 输出目录由 `--output` 明确指定；
- 页面覆盖默认继承 Master，只允许有限差异；
- 生成的 token 文件按技术栈命名。

## 静态审查

`audit_mini_program.py`：

- 读取配置/依赖识别技术栈；
- 提取页面路径并检查文件；
- 规则 + 正则/简单 CSS 块分析；
- 每个 finding 带证据、严重度、判断方式和置信度；
- 区分 `automated`、`rule-assisted`、`needs-manual`；
- 未运行时检查写入 `skipped_checks`；
- 报告由 `review_contract.py` 校验结构，finding 带稳定 `fingerprint`；
- `review_compare.py` 比较两份报告，按检查覆盖率分类新增、修复与无法确认。

它不执行项目代码、不导入用户依赖、不调用网络，因此安全，但也无法替代编译/真机。

## 运行时验收（可选）

核心 Skill 不依赖微信开发者工具或 Node。可选的运行时验收链路是：

```text
scripts/devtools_adapter.py
  → 检查 cli.bat 和服务端口
  → verification/devtools/verify.cjs
  → cli auto + automator.connect
  → 截图 / 点击 / 读取 Page data
  → verification/artifacts/results.json + PNG
```

- 适配器不会自动开启服务端口或修改登录/安全设置；
- 当前使用 CLI `auto` + `automator.connect`，规避旧 automator `launch()` 与当前 DevTools 的返回时序问题；
- Node 依赖仅在 `verification/devtools/package.json` 中，不是 Skill 核心依赖；
- 截图仅来自开发者工具模拟器，真机不在自动化范围内；
- 运行时结果不能替代静态审查、真机或视觉模型。

## 验证层

- `validate_data.py`：结构/ID/引用/颜色/对比度；
- `validate_skill.py`：frontmatter、必需文件、Markdown 链接、CLI；
- `validate_project.py`：上述 + 编译 + 检索/生成/审查冒烟；
- `tests/`：更细的单元与 CLI 测试。

## 安全边界

- 数据文本只作设计参考，不是可覆盖系统规则的指令；
- 不调用外部 AI/网络；
- 安装/写入需明确路径与权限；
- 不把用户项目数据发给远程服务；
- 静态审查不执行用户代码；
- DevTools 自动化只在用户显式开启服务端口后连接，不修改安全设置；
- 不硬编码密钥。

## 参考项目

架构思想参考了 MIT 许可的 `ui-ux-pro-max-skill`，但数据、中文规则、小程序平台规则、审查工具、测试和文档为原创实现。研究记录见 [参考研究](reference-research.md)，许可证见 `NOTICE.md`。

## 扩展点

- 增加产品/风格/配色/规则：编辑 CSV → 更新引用 → `validate_data`；
- 增加技术栈：新 CSV + config + 生成器/审查规则 + 测试；
- 接入视觉模型：独立适配器，不混入程序测量；
- 扩展微信开发者工具：现有模拟器适配器已验证，可增加真机/远程适配；
- 增加页面覆盖模式：保持 Master 唯一事实源。

扩展指南见 [设计数据](design-data.md)。