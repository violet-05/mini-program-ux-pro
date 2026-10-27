# 微信小程序平台

## 平台范围

本项目首先服务微信小程序，并区分三类实现：

1. **微信原生小程序**：WXML、WXSS、JS/TS、JSON，`app.json` 注册页面。
2. **uni-app**：Vue 体系，最终编译到微信小程序；同时可能运行到 H5/App。
3. **Taro**：React/Vue 等技术栈，编译到微信小程序；也可能运行到 H5。

必须读取项目依赖和配置判断技术栈，不能看到 `.vue` 就认为所有端行为一致，也不能把原生项目改写成 React 网页。

## 官方事实（2026-10-27 核对）

以下事实来自当前可访问的微信官方文档和设计指南，已写入 `data/mini-program-rules.csv`，并保留核验状态：

- TabBar 配置最少 2 项、最多 5 项；官方设计指南建议不超过 4 项以保证点击区域。
  - https://developers.weixin.qq.com/miniprogram/design/index.html
  - https://developers.weixin.qq.com/miniprogram/dev/reference/configuration/app.html
- TabBar 图标建议 81×81px，单张小于 40KB，不支持网络图片。
- 官方设计指南建议点击物理尺寸约 7–9mm。
- `navigationStyle: custom` 只保留右上角胶囊按钮；低版本和 web-view 有兼容注意。
- 小程序页面被组织为页面栈加悬垂页面；`navigateTo`/`redirectTo` 目标不能是 tabBar 页面；`switchTab` 用于 tabBar；路由一旦确定执行不能取消。
- 设计稿可采用 375px 或 390px 基准，页面需要适配。
- 原生导航、TabBar、表单等都是平台能力；自定义要理解胶囊、安全区和原生组件限制。

官方文档会更新。标记为“需按目标基础库验证”的规则不能当作永久事实。

## 与 Web 的区别

| Web | 微信小程序 |
| --- | --- |
| HTML 标签 | WXML/框架组件 |
| DOM/BOM API | 小程序 API |
| `localStorage` | `wx.setStorageSync` 等 |
| 浏览器路由 | 页面栈/路由 API |
| CSS 完整能力 | WXSS/渲染引擎支持范围 |
| 鼠标 hover | 触摸/按压 |
| 浏览器安全区 | 微信客户端/设备安全区 |
| 浏览器 DevTools | 微信开发者工具 + 真机 |
| `window/document` | 不存在或需框架特定条件 |

uni-app/Taro 可以编译到 H5，但微信目标不等于 H5。不要用 H5 通过代替微信验证。

## 渲染引擎

小程序可能使用 WebView 或 Skyline 等渲染路径。CSS 支持、原生组件层级、动画和事件行为可能有差异。具体项目需确认：

- 基础库版本；
- 渲染引擎配置；
- 组件支持矩阵；
- 原生组件叠加行为；
- 真机结果。

不能假设“开发者工具通过 = 所有引擎通过”。

## 页面生命周期

常见：

- `onLoad`：接收参数、初始化；
- `onShow`：页面再次显示，适合轻量刷新；
- `onHide`：进入后台/其他页面；
- `onUnload`：页面销毁；
- `onPullDownRefresh`、`onReachBottom` 等交互回调。

TabBar 页面可能被保留而不是每次重建；路由有排队行为。设计上要处理：

- 返回后数据是否更新；
- 定时器/监听清理；
- 支付/分享返回；
- 页面状态恢复。

## 权限与隐私

位置、相册、相机、手机号、头像昵称、文件、剪贴板等能力可能有独立授权和隐私要求。设计应：

- 在具体任务前请求；
- 说明用途；
- 拒绝后保留替代；
- 提供隐私协议和撤回；
- 真机验证。

不把 AppSecret 放在小程序包。登录通过 `wx.login` 获取临时 code，由服务端交换身份。

## 验证环境

严格区分：

1. **静态代码审查**：结构、状态、规则、明显错误。
2. **浏览器预览**：仅浏览器/H5，不是微信。
3. **微信开发者工具**：编译、模拟交互、部分 API。
4. **真机**：键盘、安全区、性能、分享、权限、原生组件。
5. **弱网**：真实网络状况。

每项检查都要记录环境。未执行不能算通过。

## 相关文件

- [导航与路由](navigation-and-routing.md)
- [安全区域](safe-area.md)
- [触摸交互](touch-interactions.md)
- [兼容性](../docs/compatibility.md)
- [官方核验记录](../docs/official-verification.md)
- [微信平台规则数据](../data/mini-program-rules.csv)