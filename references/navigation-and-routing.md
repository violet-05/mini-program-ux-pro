# 导航与路由

## 导航的职责

导航回答：

- 我在哪？
- 我可以去哪？
- 我怎么回去？
- 当前任务中断后如何恢复？

小程序导航必须简单、稳定、可预测，不应模仿多层级桌面后台。

## 原生导航栏

默认使用原生导航：

- 平台提供返回和胶囊；
- 页面标题可配置；
- 背景/文字颜色可配置；
- 不需要自己计算状态栏。

页面 JSON：

```json
{
  "navigationBarTitleText": "订单详情",
  "navigationBarBackgroundColor": "#FFF8F3",
  "navigationBarTextStyle": "black"
}
```

原生导航下不要再自绘返回按钮/标题，避免两套导航叠加。

## 自定义导航栏

`navigationStyle: "custom"` 适合沉浸式媒体、品牌首页等。平台只保留右上角胶囊。需要：

1. 读取状态栏高度/窗口信息；
2. 读取胶囊位置；
3. 计算导航内容区高度；
4. 左右预留胶囊区；
5. 提供可点击返回；
6. 滚动时确保标题可读；
7. 低版本/web-view 回退；
8. 真机验证。

示意（API 名称按目标基础库确认）：

```js
const windowInfo = wx.getWindowInfo()
const menu = wx.getMenuButtonBoundingClientRect()
const navBarHeight = menu.bottom + (menu.top - windowInfo.statusBarHeight)
```

不要硬编码 44px/88rpx 覆盖所有设备。

## TabBar

- 2–5 项，官方建议 ≤4；
- 只放稳定的一级区域；
- 每项有文字；
- 图标本地、风格一致；
- 未读徽标与消息页同步；
- 自定义 TabBar 处理选中态、安全区和页面切换；
- Tab 切换不叠加页面栈。

## 路由 API

| 目的 | API |
| --- | --- |
| 打开非 tabBar 页面 | `navigateTo` |
| 替换当前页 | `redirectTo` |
| 切换 tabBar 页面 | `switchTab` |
| 关闭所有页面打开新页 | `reLaunch` |
| 返回栈中页面 | `navigateBack` |

`navigateTo`/`redirectTo` 不能指向 tabBar 页面。路由一旦确定执行不可取消；连续点击可能排队，必须防重复。

## 返回

常见问题：

- 详情页自定义返回跳到首页；
- 从分享/扫码进入后 `navigateBack` 无反应；
- 返回后筛选和滚动丢失；
- 表单未保存直接清空；
- 支付结果页返回导致重复支付。

设计：

- 有栈：返回上一页；
- 无栈：回到安全首页/任务页；
- 保留筛选、滚动、Tab 状态；
- 未保存提示/草稿；
- 支付结果使用 `redirectTo`/`reLaunch` 并支持查单。

## 分享与扫码进入

分享路径可能是任意深层页面：

- 页面不依赖上一页存在；
- 校验参数；
- 登录后回到原页面；
- 提供安全的退出路径；
- 分享卡信息完整。

## 页面层级

- 不设计过深页面链；
- 流程步骤优先单页分步/状态化，减少页面栈；
- 深层页面提供“回首页/回任务”；
- 避免通过反复 `navigateTo` 堆叠同类页面。

## 导航审查

- [ ] 每个入口有合理返回；
- [ ] 从分享/扫码进入可恢复；
- [ ] TabBar 数量/文字/图标正确；
- [ ] 不重复导航；
- [ ] 路由 API 语义正确；
- [ ] 防重复导航；
- [ ] 真机检查手势返回与胶囊。

## 相关文件

- [小程序平台](mini-program-platform.md)
- [安全区域](safe-area.md)
- [微信平台规则](../data/mini-program-rules.csv)