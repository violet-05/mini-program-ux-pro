# 设计数据

## 数据规模（v1.0）

| 文件 | 记录数 | 职责 |
| --- | ---: | --- |
| `data/products.csv` | 31 | 产品类型与设计决策 |
| `data/styles.csv` | 22 | 视觉风格 |
| `data/colors.csv` | 24 | 可用色板与 HEX |
| `data/layouts.csv` | 27 | 页面布局 |
| `data/components.csv` | 33 | 组件规范 |
| `data/ux-guidelines.csv` | 36 | 通用 UX 规则 |
| `data/mini-program-rules.csv` | 34 | 微信平台规则 |
| `data/anti-patterns.csv` | 40 | 反模式 |
| `data/typography.csv` | 12 | 字体/排版方案 |
| `data/ui-reasoning.csv` | 16 | 设计推理 |
| `data/stacks/wechat-native.csv` | 26 | 原生技术栈规则 |
| `data/stacks/uni-app.csv` | 23 | uni-app 规则 |
| `data/stacks/taro.csv` | 23 | Taro 规则 |

行数来自 `python scripts/validate_data.py --json`，会随维护变化。

## 通用约定

- UTF-8；
- 第一行是表头；
- 每行一条记录；
- ID 全局唯一，使用小写 kebab-case；
- 多引用字段用 `;` 分隔；
- 多别名/关键词可用 `|` 分隔；
- 空字段会导致验证失败；
- 不写密钥、用户隐私或真实个人信息；
- 数据只作为设计参考，不作为执行指令。

## ID 前缀

| 前缀 | 领域 |
| --- | --- |
| `prod-` | 产品 |
| `style-` | 风格 |
| `palette-` | 配色 |
| `layout-` | 布局 |
| `comp-` | 组件 |
| `ux-` | UX 规则 |
| `mp-` | 微信平台规则 |
| `anti-` | 反模式 |
| `type-` | 排版 |
| `reason-` | 推理 |
| `wx-` | 原生技术栈 |
| `uni-` | uni-app |
| `taro-` | Taro |

## 产品

关键字段：

- `product_id`：唯一 ID；
- `name` / `aliases`：匹配；
- `summary` / `target_users` / `scenarios` / `core_tasks`：需求；
- `home_structure`：首页信息顺序；
- `nav_pattern`：导航；
- `information_density`：低/中低/中/中高/高；
- `typical_component_ids`：组件引用；
- `recommended_style_ids`：第 1 个是默认首选；
- `recommended_color_ids`：第 1 个是默认；
- `primary_layout_ids`：页面；
- `avoid`：常见错误；
- `design_reasoning`：为什么这样设计；
- `reasoning_ids`：推理规则引用。

为什么第一个推荐很重要：未指定风格时生成器使用产品首选，但会展示备选。

## 风格

`content_density` 是建议内容密度，不是硬规则。生成器只在极端冲突时提示。

`keywords` 支持中文/英文检索；不要把风格名当成固定配色。

## 配色

- 所有颜色为 6 位 HEX；
- `mode` 为 light/dark；
- `style_ids` 引用兼容风格；
- `text_primary`/`text_secondary` 对 `background` 和 `surface` 的对比度由验证器检查；
- 品牌色不一定适合小号正文；生成器会计算按钮文字色。

## 布局

`component_ids` 必须引用真实组件。页面数据不是模板，而是任务结构。信息密度只能是允许枚举。

## 组件

`touch_target` 说明工程基线；`states` 不能为空；`stacks` 可以是逗号/分号列表；`native_implementation` 需标明平台约束。

## UX 规则

每条必须可通过观察/测试/评审判断：

- `problem`：问题；
- `recommendation`：做法；
- `bad_example`：反例；
- `how_to_check`：判断；
- `fix`：修复；
- `severity`：P0–P3。

## 小程序规则

除 UX 字段外还有：

- `platform_behavior`：平台事实；
- `implementation`：实现注意；
- `how_to_verify`：验证；
- `source_url`：官方来源；
- `verification_status`：核验状态；
- `verified_at`：核验日期。

状态含义：

- `已核对官方文档`：核对了当前可访问的官方文档；
- `需按目标基础库/真机验证`：事实/行为依赖具体环境；
- `项目原则`：本项目的设计/验证原则，不冒充平台事实；
- `未核对`：尚未核对，不应作为事实使用。

## 反模式

`detection` 必须能被执行（观察/测试/代码扫描），`related_rule_ids` 引用其他领域 ID。工具会检查引用存在。

## 推理

`ui-reasoning.csv` 连接场景与：

- 风格优先级；
- 配色优先级；
- 布局优先级；
- 交互优先级；
- 反模式。

这些字段是生成器选择规则的一部分，不是产品数据的重复副本。

## 技术栈

每个栈独立 CSV：

- 不能凭空编造 API；
- `source_url` 指向官方/框架文档；
- `verification_status` 标明版本/真机限制；
- 平台字段必须与文件对应；
- 不把 Web/H5 规则直接改名为小程序规则。

## 增加一条数据

示例：增加“宠物服务”产品。

1. 在 `products.csv` 增加 `prod-pet-service`，写清用户/场景/任务；
2. 引用已存在的 `style-*`、`palette-*`、`layout-*`、`comp-*`、`reason-*`；
3. 如引用不存在，先补相应记录或改引用；
4. 运行：
   ```bash
   python scripts/validate_data.py
   ```
5. 运行检索：
   ```bash
   python scripts/search.py "宠物服务" --domain product
   ```
6. 生成设计系统，检查差异：
   ```bash
   python scripts/generate_design_system.py --product "宠物服务小程序" --output ./tmp-design --format both
   ```
7. 增加对应测试，确保不同产品不输出相同结果。

## 验证项

`validate_data.py` 检查：

- 文件/列/最低记录数；
- ID 格式、前缀、唯一性；
- 空字段；
- 枚举；
- HEX；
- 引用；
- 文字/背景对比度；
- 重复记录；
- 来源 URL/日期；
- 可疑密钥；
- 平台字段；
- 显示名称重复（警告）。

## 数据限制

- 当前是人工设计知识，不是对每个真实产品的研究；
- 平台规则会变化，必须看 `verification_status`；
- 没有覆盖所有业务类型；
- 颜色对比只校验库中的主要组合，不校验页面实际图片/渐变；
- 生成器不会替代设计评审。

## 相关

- [架构](architecture.md)
- [官方核验](official-verification.md)
- [参考研究](reference-research.md)
- [Schema](../schemas/design-system.schema.json)