# Changelog

All notable changes to Mini Program UX Pro are documented here.

## [Unreleased]

### Fixed

- 统一 `validate_data`、`validate_skill`、`validate_project`、`install_skill`、`visual_review_adapter`、`devtools_adapter` 的 UTF-8 输出。
- 修复 Windows 默认 GBK 控制台下 `test_cli_build_and_validate` 失败，以及 `validate_project` 打印数据警告时抛出 `UnicodeEncodeError`。
- 验证器与安装器调用 Python 子进程时强制 UTF-8 环境，避免继承 Windows 默认代码页。
- 安装 Skill 时排除 `.github`。

### Added

- `tests/test_encoding.py`：在 `PYTHONIOENCODING=gbk` 下回归所有 CLI 的 UTF-8 输出。
- GitHub Actions CI：Ubuntu/Windows × Python 3.10/3.12，以及独立 GBK stdio 回归任务。

## [1.0.0] - 2026-10-27

### Added

- 首个可运行版本：阶段 A 小程序审美 Skill + 阶段 B 基础静态审查工具。
- `SKILL.md` 入口，包含适用场景、触发、设计原则、工作流、平台限制、安全与完成标准。
- 原创知识库：
  - 31 类产品；
  - 22 种风格；
  - 24 套配色；
  - 27 种页面布局；
  - 33 个组件；
  - 36 条 UX 规则；
  - 34 条微信平台规则；
  - 40 条反模式；
  - 12 套排版方案；
  - 16 组设计推理；
  - 微信原生/uni-app/Taro 技术栈规则。
- 本地 BM25 检索：
  - 中文 bigram；
  - 中英文同义词；
  - 字段权重；
  - 名称/ID 精确匹配；
  - 匹配字段与原因；
  - Markdown/JSON 输出；
  - 无结果提示与建议。
- 设计系统生成器：
  - 产品/风格/配色/排版/布局/组件选择；
  - 对比度检查；
  - 冲突检查；
  - Master/JSON/token/页面覆盖；
  - 已有 Master 默认不覆盖；
  - 多技术栈 token 输出。
- 静态审查工具：
  - 技术栈识别；
  - 页面/TabBar/自定义导航；
  - WXML HTML/事件检查；
  - 浏览器 API 检查；
  - 安全区/触摸/字号；
  - 状态/图片/隐私/token；
  - P0–P3 分级与证据；
  - Markdown/JSON 报告；
  - `--fail-on` 退出码。
- 校验与安装：
  - `validate_data.py`；
  - `validate_skill.py`；
  - `validate_project.py`；
  - `install_skill.py`（含安装后检索冒烟）；
  - `visual_review_adapter.py`（视觉审查请求/响应契约；不调用模型）；
  - `devtools_adapter.py` + `verification/devtools/`（可选的微信开发者工具模拟器验收）。
- 运行时验收示例：微信原生音乐小程序，覆盖首页/加载/错误/空、播放器、自定义导航、安全区、TabBar、队列与恢复。
  - DevTools 2.02.2608070 / 基础库 3.17.4 / 390×844 模拟器；
  - 24/24 自动化检查通过；
  - 9 张真实模拟器截图、0 console.error、0 未捕获异常；
  - 采用 CLI `auto` + `automator.connect`，规避旧 automator `launch()` 兼容问题。
- 17 份设计/平台参考、11 份风格指南、8 个工作流、6 个检查表、6 个产品示例、3 个模板、3 个 JSON Schema。
- 自动化测试与原生/uni-app/Taro/浏览器原型夹具。
- 中文 README、安装、使用、架构、数据、兼容性、故障排查、路线图、参考研究与官方核验文档。

### Known limitations

- 微信开发者工具自动化仅覆盖模拟器，不包含真机自动化。
- 未内置视觉模型。
- 未内置独立自动修复器。
- macOS/Linux 未在本版实际运行验证。
- 平台能力需按目标基础库与真机复核。