# 微信官方文档核验记录

> 核验日期：2026-10-27。官方文档会更新；标记“需验证”的规则不能视作永久事实。

## 核验方式

- 通过 `curl` 获取官方页面 HTML；
- 本地解析可见文本；
- 只提取事实，不复制整篇文档；
- 将事实写入 `data/mini-program-rules.csv` / stack 数据；
- 每条带来源 URL、核验状态和日期。

## 已核对的主要事实

### 设计指南

来源：https://developers.weixin.qq.com/miniprogram/design/index.html

- 每个页面应有重点，避免无关元素干扰。
- 导航应明确、来去自如；页面应有返回路径。
- Tab 导航数量不得少于 2、最多 5；官方建议不超过 4 项以保证点击区域。
- 点击物理尺寸大致 7–9mm。
- 小程序字体与系统字体保持一致，常用字号为 22、17、15、14、12(pt)。
- 设计稿可采用 375px 或 390px 基准；页面需适配。
- 原生 TabBar 可用于首页，图标/文案可配置；自定义 TabBar 需关注可用性。
- 异常状态应可控、有路可退。

### app.json / TabBar

来源：https://developers.weixin.qq.com/miniprogram/dev/reference/configuration/app.html

- `tabBar.list` 最少 2、最多 5。
- TabBar 图标建议 81×81px，大小限制 40KB，不支持网络图片。
- 当 `position: top` 时不显示图标。
- `navigationStyle: custom` 时只保留右上角胶囊按钮。
- iOS/Android 低版本、web-view 等有自定义导航兼容注意。

### 路由与页面栈

来源：https://developers.weixin.qq.com/miniprogram/dev/framework/app-service/route.html

- 页面栈由跳转页面组成，另有悬垂页面（如 tabBar、画中画）。
- `navigateTo`/`redirectTo` 目标必须不是 tabBar 页面。
- `switchTab` 用于 tabBar 页面。
- 路由一旦确定执行不可取消；连续路由会排队。
- `getCurrentPages` 可获取页面栈。
- 页面生命周期包括 onLoad/onShow/onHide/onUnload/onRouteDone 等。

### button

来源：https://developers.weixin.qq.com/miniprogram/dev/component/button.html

- `open-type="share"` 触发用户转发。
- `open-type="chooseAvatar"` 获取头像。
- `open-type="agreePrivacyAuthorization"` 处理隐私同意。
- `open-type` 各能力有最低版本，需按基础库检查。

### 胶囊位置

来源：https://developers.weixin.qq.com/miniprogram/dev/api/ui/menu/wx.getMenuButtonBoundingClientRect.html

- 提供 `wx.getMenuButtonBoundingClientRect()` 获取胶囊位置。
- 自定义导航应结合窗口/状态栏信息计算，不硬编码。

### WXSS

来源：https://developers.weixin.qq.com/miniprogram/dev/framework/view/wxss.html

- WXSS 支持 rpx 等小程序样式能力。
- 具体选择器/CSS 能力需按渲染环境验证；不等于完整浏览器 CSS。

### 自定义组件

来源：https://developers.weixin.qq.com/miniprogram/dev/framework/custom-component/

- 组件有 properties、事件、生命周期和样式隔离。
- 外部样式与页面选择器不总是直接穿透组件。

### 深色模式

来源：https://developers.weixin.qq.com/miniprogram/dev/framework/ability/darkmode.html

- 平台提供深色模式适配能力；配置/组件表现需按目标基础库验证。
- 深色不能简单等同自动反色。

## 未完全核实的事项

以下事项因依赖具体版本/设备，未标记为已核实：

- `env(safe-area-inset-bottom)` 在每种基础库/渲染引擎中的具体行为；
- 不同 iOS/Android/输入法的键盘高度与 adjust-position 表现；
- Skyline 当前对每种 CSS/组件的支持；
- 原生组件在所有引擎中的覆盖/层级矩阵；
- 各隐私接口的最新完整合规要求；
- 微信开发者工具当前自动化接口（是否可用于导入/编译/截图）；
- 各框架（uni-app/Taro）最新版本的全部平台差异。

数据中的 `verification_status` 会显示“需按目标基础库/真机验证”。项目应在目标环境补充验证，而不是把本文件当保证。

## 本机 DevTools 运行时观察（非官方规范摘录）

2026-10-27 在 DevTools 2.02.2608070 / 基础库 3.17.4 实际验证：

- 安全设置关闭时，CLI 返回 `IDE service port disabled`，需用户手动在“设置 → 安全设置”开启服务端口；
- `cli auto --project <path> --auto-port <port> --trust-project` 可启动项目自动化；
- `miniprogram-automator@0.13.0` 的 `automator.connect({ wsEndpoint })` 可连接；
- 该版本旧 `launch()` 与 DevTools 返回时序不兼容，本项目改用 CLI auto + connect；
- `miniProgram.screenshot()` 只支持开发者工具模拟器，不支持客户端真机；
- 自动截图/点击结果记录在 `verification/artifacts/`，不作为真机结论。

这些是本机实测行为，不是对所有 DevTools 版本的保证。

## 证据保存

本轮未将官方 HTML 全文纳入仓库，只保留事实摘要与 URL。若后续需要自动跟踪，应：

1. 按官方许可获取；
2. 记录抓取日期/版本；
3. 只保存必要事实；
4. 更新 `verified_at`；
5. 运行数据验证。

## 相关

- [小程序平台参考](../references/mini-program-platform.md)
- [数据说明](design-data.md)
- [兼容性](compatibility.md)
- [小程序规则数据](../data/mini-program-rules.csv)