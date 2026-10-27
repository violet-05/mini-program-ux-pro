# 音乐播放器 · 小程序设计系统

> 本文件是项目级唯一设计事实源（Master）。页面规范默认继承本文件。
> 设计系统版本：1.0.0 · 生成器：MPUX Pro 1.0.0 · 生成时间：2026-10-27T10:51:12+00:00 · 技术栈：微信原生小程序
> 数据引用与未执行检查见第 16 节。任何未在真机执行的结论都不得标记为已验证。

## 使用约束

1. 先读本文件，再读 `pages/<page>.md`；页面覆盖只允许修改页面级顺序、局部间距与状态，不得另起配色或字体系统。
2. Token 以第 8 节和 `MASTER.json` 为准；组件不得硬编码未登记的颜色、圆角或间距。
3. 本节由静态知识库生成，不代表已完成视觉、键盘、安全区或真机验证。

## 1. 产品定位

- **项目名称**：音乐播放器
- **产品类型**：音乐播放器 (`prod-music`)
- **匹配方式**：精确匹配；置信度：1.0
- **产品摘要**：以内容发现、持续播放、收藏与歌单为核心，播放状态需要跨页面保持。
- **信息密度**：中低
- **首页结构**：问候与最近播放→继续收听→每日推荐/榜单→歌单与电台→迷你播放器
- **导航模式**：底部 TabBar：首页/发现/音乐库/我的；全屏播放页为独立层级，不重复 TabBar

## 2. 目标用户与场景

- **目标用户**：通勤、学习、运动、睡前等场景的听众和播客用户。
- **主要场景**：通勤听歌、发现新内容、收藏歌单、查看歌词与继续播放。

## 3. 核心任务与成功标准

- **核心任务**：继续播放、发现新歌、搜索、收藏、查看歌词/队列。
- **成功的界面**：用户能识别当前状态、完成下一动作，并在错误或中断后恢复；不是“所有卡片看起来一致”。

## 4. 设计风格

### 内容优先型 / Content-first

- **风格 ID**：`style-content-first`
- **选择方式**：产品推荐
- **关键词**：内容|阅读|信息|克制|content first|reading|focus|clarity
- **视觉特点**：标题、封面、摘要、作者与时间的层级经过设计；装饰让位于内容；阅读宽度和行高优先。
- **排版规则**：正文 30–34rpx；行高 1.65–1.85；标题最多三行；长文提供字号调节或至少保证系统缩放。
- **组件语言**：无边框列表；卡片仅用于需要整体点击的内容；底部操作不遮挡正文；进度清晰。
- **动效策略**：120–200ms；目录和操作面板滑入；滚动动效不干扰阅读；自动播放必须可关闭。
- **不适合场景**：需要强品牌氛围的营销首页、游戏、商品促销主会场。
- **组合注意**：适合与编辑式、极简或现代东方组合；数据密集型内容应提供表格和筛选而非纯信息流。

## 5. 设计选择理由与冲突

### 产品类型：音乐播放器 (prod-music)

音乐产品的主角是封面、曲目、播放状态与连续体验。首页应直接服务继续收听和发现，播放器控制必须始终可达；色彩可以沉浸，但不能牺牲歌词与操作的对比。

数据来源：`prod-music`

### 设计风格：内容优先型 (style-content-first)

由产品类型的推荐风格与设计推理规则推导。 标题、封面、摘要、作者与时间的层级经过设计；装饰让位于内容；阅读宽度和行高优先。

数据来源：`style-content-first`

### 配色：音乐夜色 (palette-music-night)

沉浸播放、封面、歌词和夜间浏览。 深色底上的正文对比充足；荧光品牌色不用于长文本；播放进度与错误状态需要额外图形线索。

数据来源：`palette-music-night`

### 排版：长文阅读排版 (type-reading-song)

阅读正文优先，标题略大；行高比默认更大；每屏保留稳定节奏。 正文建议 30–34rpx；尊重系统字号；长文提供字号调节或允许换行；底部栏不覆盖最后一段。

数据来源：`type-reading-song`

### 页面结构：首页、音乐播放器、搜索页、搜索结果页、个人中心

按产品核心任务排序，页面级覆盖默认继承 Master。

数据来源：`layout-home`、`layout-music-player`、`layout-search`、`layout-search-results`、`layout-profile`

### 技术栈：微信原生小程序 (wechat-native)

加载对应框架规则并区分静态审查、开发者工具与真机验证。

数据来源：`wx-project-structure`、`wx-wxml-binding`、`wx-wxss-rpx`、`wx-routing`、`wx-safe-area`、`wx-page-config`、`wx-native-component`、`wx-app-tabbar`、`wx-fixed-bottom`、`wx-share`

### 产品推理：内容消费

内容型产品应优先阅读/播放体验、持续状态和内容识别；装饰性卡片、自动播放和持续动效应让位于内容。

数据来源：`reason-content`

未发现数据层面需阻断的冲突。仍需在实现后进行视觉、交互和真机检查。

## 6. 配色系统

配色方案：**音乐夜色** (`palette-music-night`) · 模式：dark

沉浸播放、封面、歌词和夜间浏览。

| Token | 值 | 用途 |
| --- | --- | --- |
| `background` | `#0D0F12` | 页面背景 |
| `surface` | `#171A1F` | 卡片/表面 |
| `surface_alt` | `#161915` | 弱分区表面 |
| `text_primary` | `#F5F1E8` | 主文字 |
| `text_secondary` | `#B2B6BE` | 次级文字 |
| `brand` | `#D7E94C` | 品牌主色/主操作 |
| `on_brand` | `#111111` | 品牌色上的文字 |
| `brand_soft` | `#252919` | 品牌弱底 |
| `accent` | `#8B7CFF` | 辅助强调 |
| `on_accent` | `#111111` | 辅助色上的文字 |
| `border` | `#2C3037` | 边框 |
| `divider` | `#24282E` | 分隔线 |
| `success` | `#5BD98A` | 成功 |
| `warning` | `#F0B429` | 警告 |
| `error` | `#FF7D7D` | 错误 |
| `on_error` | `#111111` | 错误色上的文字 |
| `link` | `#D7E94C` | 链接 |
| `disabled` | `#4C4E53` | 禁用 |
| `overlay` | `rgba(12, 14, 18, 0.48)` | 遮罩 |

### 对比度检查

| 组合 | 对比度 | 阈值 | 结果 |
| --- | ---: | ---: | --- |
| 主文字/背景 | 17.03:1 | 4.5:1 | 通过 |
| 主文字/表面 | 15.47:1 | 4.5:1 | 通过 |
| 次级文字/背景 | 9.44:1 | 4.5:1 | 通过 |
| 次级文字/表面 | 8.58:1 | 4.5:1 | 通过 |
| 链接/背景 | 14.3:1 | 4.5:1 | 通过 |
| 品牌按钮文字/品牌色 | 14.07:1 | 4.5:1 | 通过 |
| 错误按钮文字/错误色 | 7.63:1 | 4.5:1 | 通过 |

深色底上的正文对比充足；荧光品牌色不用于长文本；播放进度与错误状态需要额外图形线索。

## 7. 字体与排版

字体方案：**长文阅读排版** (`type-reading-song`)

- **标题字体**：`-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif`
- **正文字体**：`-apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif`
- **数字字体**：`SF Pro Display,Helvetica Neue,Arial,sans-serif`
- **比例依据**：阅读正文优先，标题略大；行高比默认更大；每屏保留稳定节奏。
- **行高规则**：正文 1.75–1.9；标题 1.3–1.45；注释 1.5。
- **小程序注意**：正文建议 30–34rpx；尊重系统字号；长文提供字号调节或允许换行；底部栏不覆盖最后一段。

| 层级 | 字号 | 行高 |
| --- | ---: | ---: |
| `caption` | 24rpx | 1.4 |
| `meta` | 28rpx | 1.4 |
| `body` | 32rpx | 1.82 |
| `body_lg` | 36rpx | 1.82 |
| `title` | 44rpx | 1.47 |
| `display` | 52rpx | 1.47 |

## 8. 间距、圆角、阴影、动效与尺寸

密度：**低** · 页面边距：32rpx · 区块间距：64rpx · 卡片间距：24rpx

| Token | 值 |
| --- | --- |
| `space-1` | 8rpx |
| `space-2` | 16rpx |
| `space-3` | 24rpx |
| `space-4` | 32rpx |
| `space-5` | 48rpx |
| `space-6` | 64rpx |
| `space-7` | 96rpx |
| `radius_sm` | 0rpx |
| `radius_md` | 6rpx |
| `radius_lg` | 10rpx |
| `radius_pill` | 999rpx |
| `shadow-card` | none |
| `shadow-raised` | 0 12rpx 32rpx rgba(0, 0, 0, 0.45) |
| `motion-fast` | 120ms |
| `motion-normal` | 180ms |
| `motion-slow` | 240ms |
| `touch-target` | 88rpx |
| `button-height` | 88rpx |
| `input-height` | 88rpx |
| `tabbar-height` | 100rpx |

动效策略：动效只表达状态和空间关系；避免无限循环动画；低端设备与系统减少动效时降级。

安全区域：`calc(24rpx + env(safe-area-inset-bottom))`。固定底栏必须为内容设置等高占位；具体支持需在目标基础库和真机验证。

### 技术栈 Token 落地

- 文件：`tokens.wxss`
- 说明：WXSS 自定义属性支持取决于目标基础库；若旧版本不支持，使用 MASTER.json 中的字面值或编译期样式，不要假设所有小程序环境都有 CSS 变量。
- 主路径：为组件提供字面值 token；tokens.wxss 仅作为可验证的变量层。

```wxss
/* MPUX Pro design tokens - generated from local knowledge base. */
/* Do not treat CSS custom properties as universally supported; verify the target base library. */

page {
  --mpux-color-background: #0D0F12;
  --mpux-color-surface: #171A1F;
  --mpux-color-surface-alt: #161915;
  --mpux-color-text-primary: #F5F1E8;
  --mpux-color-text-secondary: #B2B6BE;
  --mpux-color-brand: #D7E94C;
  --mpux-color-on-brand: #111111;
  --mpux-color-brand-soft: #252919;
  --mpux-color-accent: #8B7CFF;
  --mpux-color-on-accent: #111111;
  --mpux-color-border: #2C3037;
  --mpux-color-divider: #24282E;
  --mpux-color-success: #5BD98A;
  --mpux-color-warning: #F0B429;
  --mpux-color-error: #FF7D7D;
  --mpux-color-on-error: #111111;
  --mpux-color-link: #D7E94C;
  --mpux-color-disabled: #4C4E53;
  --mpux-color-overlay: rgba(12, 14, 18, 0.48);
  --mpux-font-caption: 24rpx;
  --mpux-font-meta: 28rpx;
  --mpux-font-body: 32rpx;
  --mpux-font-body-lg: 36rpx;
  --mpux-font-title: 44rpx;
  --mpux-font-display: 52rpx;
  --mpux-font-family-heading: -apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif;
  --mpux-font-family-body: -apple-system,BlinkMacSystemFont,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif;
  --mpux-font-family-numeric: SF Pro Display,Helvetica Neue,Arial,sans-serif;
  --mpux-space-1: 8rpx;
  --mpux-space-2: 16rpx;
  --mpux-space-3: 24rpx;
  --mpux-space-4: 32rpx;
  --mpux-space-5: 48rpx;
  --mpux-space-6: 64rpx;
  --mpux-space-7: 96rpx;
  --mpux-space-page-gutter: 32rpx;
  --mpux-space-section-gap: 64rpx;
  --mpux-space-card-gap: 24rpx;
  --mpux-space-content-max-width: 1120rpx;
  --mpux-radius-sm: 0rpx;
  --mpux-radius-md: 6rpx;
  --mpux-radius-lg: 10rpx;
  --mpux-radius-pill: 999rpx;
  --mpux-shadow-card: none;
  --mpux-shadow-raised: 0 12rpx 32rpx rgba(0, 0, 0, 0.45);
  --mpux-motion-fast: 120ms;
  --mpux-motion-normal: 180ms;
  --mpux-motion-slow: 240ms;
  --mpux-easing-standard: cubic-bezier(0.2, 0.8, 0.2, 1);
  --mpux-touch-target: 88rpx;
  --mpux-button-height: 88rpx;
  --mpux-input-height: 88rpx;
  --mpux-tabbar-height: 100rpx;
  --mpux-nav-content-height: 88rpx;
  --mpux-safe-bottom: env(safe-area-inset-bottom);
}

/* Content wrapper example: */
/* .mpux-page { padding-bottom: calc(var(--mpux-bottom-bar-height, 112rpx) + env(safe-area-inset-bottom)); } */
```

## 9. 页面布局

默认页面覆盖文件：`pages/home.md`、`pages/music-player.md`、`pages/profile.md`

| 页面 | 目标 | 主要内容 | 主操作顺序 |
| --- | --- | --- | --- |
| 首页 (`layout-home`) | 让用户在首屏识别产品价值并进入最重要的一个任务，同时保留必要的探索入口。 | 身份与上下文区；一个主任务区；动态或推荐区；服务入口 | 先识别身份/位置→完成主任务→浏览推荐→进入次级服务 |
| 音乐播放器 (`layout-music-player`) | 让封面、播放状态和主控操作形成稳定的持续播放体验。 | 封面；曲名/歌手；进度；播放控制；收藏/分享；队列入口 | 识别曲目→播放/暂停→拖动进度→切换/收藏→查看队列 |
| 搜索页 (`layout-search`) | 帮助用户表达意图，并在输入前后提供可执行的检索辅助。 | 输入框；取消；清空；历史；建议；热门词 | 输入→选择建议或提交→进入结果 |
| 搜索结果页 (`layout-search-results`) | 让用户判断结果是否相关，并快速比较、筛选和打开结果。 | 搜索词回显；筛选条；结果列表；结果状态 | 确认查询→筛选→比较→打开→返回保持位置 |
| 个人中心 (`layout-profile`) | 汇聚身份、资产、订单与设置，但不成为功能广告墙。 | 头像/昵称；会员或积分；订单快捷状态；服务列表；退出/设置 | 确认身份→查看关键状态→进入服务→管理设置 |

页面级覆盖默认继承本文件。不得为每个页面建立独立配色或字体；如页面任务确实需要例外，在页面文件记录理由。

## 10. 组件规范

| 组件 | 使用场景 | 触摸/状态 | 常见错误 |
| --- | --- | --- | --- |
| 搜索框 (`comp-search-bar`) | 列表、分类、首页的检索入口或搜索页输入。 | 输入区高度至少 80rpx；清空/取消等图标按钮至少 88rpx 热区。；空闲、聚焦、有内容、搜索中、禁用 | 搜索框太矮；清空按钮难点；按键盘搜索无响应；输入时页面被键盘遮挡。 |
| 图片预览 (`comp-image-preview`) | 商品图、内容配图、凭证和头像查看。 | 缩略图可点区域至少 88rpx；预览关闭由平台提供。；加载中、成功、失败、预览中、多图 | 把关键信息做成图片；缩略图变形；预览索引错误；失败没有占位。 |
| 用户头像 (`comp-avatar`) | 用户身份、评论、聊天和群组。 | 头像本身可点区域至少 88rpx，视觉可小。；加载、成功、失败、默认、在线状态 | 默认头像风格不一；头像图片变形；点击无反应；在线状态只靠绿点。 |
| 底部固定操作栏 (`comp-bottom-action`) | 商品购买、报名、结算、聊天输入等持续可用的主操作。 | 按钮高度至少 88rpx；次要操作有足够间距；安全区 padding 必须计算。；常规、禁用、加载、成功、错误、键盘/安全区 | 固定栏遮住最后一段内容；安全区计算错误；一个栏里放三个主按钮；加载时仍可点击。 |
| 空状态 (`comp-empty`) | 列表为空、搜索无结果、未登录、未收藏等。 | 主按钮至少 88rpx 高；空状态内不要放多个同等按钮。；首次为空、筛选为空、无权限、未登录 | 所有空态同一句“暂无数据”；只有插画没有行动；错误与空状态混淆。 |
| 加载状态 (`comp-loading`) | 首次加载、提交中、局部刷新和长任务。 | 若提供取消按钮，至少 88rpx。；首屏、局部、提交中、超时、可取消 | 全屏 loading 遮住导航；无超时；加载失败后仍显示 loading；重复点击叠加。 |
| 轻提示 (`comp-toast`) | 短时、非阻塞的操作结果反馈。 | 不含交互；如包含“撤销”等操作，必须用可交互条并保证热区。；成功、失败、普通、加载、隐藏 | 用 toast 代替字段错误；toast 文案过长；连续弹多个覆盖；关键错误无持久提示。 |
| 分享入口 (`comp-share`) | 分享给好友、生成海报、分享内容或邀请。 | 分享按钮至少 88rpx；悬浮分享不遮挡主操作。；可分享、生成中、成功、失败、取消 | 所有页面都放悬浮分享；分享图标无文字；分享路径丢失参数；未授权也显示成功。 |
| 数据图表 (`comp-chart`) | 趋势、分布、对比、进度和异常数据。 | 图表内可交互区域按平台触摸规则；筛选按钮至少 88rpx。；加载、成功、空、部分失败、实时更新、无权限 | 图表没有单位；只靠颜色；图例拥挤；小屏坐标不可读。 |
| 原生导航栏 (`comp-nav-native`) | 需要系统级返回、标题和胶囊按钮的标准页面。 | 返回和胶囊由平台提供；页面内相邻控件仍按 88rpx 基线。；默认、加载中、标题变化、深色/浅色文字 | 自定义导航与原生导航叠加；标题过长被截断；右侧按钮压住胶囊。 |
| 自定义导航栏 (`comp-nav-custom`) | 品牌沉浸页、媒体详情或需要特殊顶部结构的页面。 | 返回键至少 88rpx×88rpx；可点区域不得与胶囊重叠。；初始透明、滚动后实色、加载、错误、深浅背景 | 硬编码状态栏高度；只在模拟器测试；右侧放按钮与胶囊冲突；透明导航不随滚动变化。 |
| 底部 TabBar (`comp-tabbar`) | 存在 2–5 个稳定、同层级主区域的首页级导航。 | 每项可点宽度按屏宽分配，高度和图标区域不应压缩点击；安全区另行处理。；默认、选中、未读、禁用/隐藏 | TabBar 超过 5 项；只放图标没有文字；图标尺寸和线宽不一致；自定义 TabBar 忘记安全区。 |

### 关键实现边界

- **搜索框**：点击进入搜索页或聚焦输入；清空按钮命中区足够大；确认键显示“搜索”；提交有 loading。
  - 无障碍：输入有可访问名称；清空按钮有文案或 aria-label；错误提示靠近输入。
  - 原生实现：原生 input 设置 confirm-type='search'、placeholder、value；避免用 view 模拟输入框；处理键盘遮挡。
- **图片预览**：点击打开预览；支持滑动和关闭；图片失败可重试；避免预览遮挡关键操作。
  - 无障碍：图片有替代文本；重要文字不要只存在于图片；预览有可关闭方式。
  - 原生实现：image mode 按用途选择；wx.previewImage 打开大图；本地占位图；长列表 lazy-load。
- **用户头像**：点击可选头像/查看资料；加载失败回退；无权限时显示默认。
  - 无障碍：头像有用户可识别名称；在线状态不只靠点；图片失败仍有替代。
  - 原生实现：button open-type='chooseAvatar' 用于获取头像；image 失败绑定 binderror；避免盗用默认头像。
- **底部固定操作栏**：滚动时保持；键盘弹起时上移或让位；点击有 loading 和防重复；禁用原因可见。
  - 无障碍：按钮名称具体；禁用原因可读；安全区适配后仍可触达。
  - 原生实现：fixed 容器加 padding-bottom: calc(24rpx + env(safe-area-inset-bottom))；页面内容加等价 padding-bottom；键盘用 adjust-position。
- **空状态**：按钮可执行；无结果可修改筛选或返回；加载失败不要伪装为空。
  - 无障碍：文案可读且具体；插画有替代说明或隐藏；主操作名称明确。
  - 原生实现：普通 view/image；插画使用本地资源并提供失败占位；搜索空态保留关键词。
- **加载状态**：超时后给出重试；可取消的长任务提供取消；不要重复叠加 loading。
  - 无障碍：有文本说明正在做什么；动画不引发闪烁；屏幕阅读器可获知繁忙状态。
  - 原生实现：wx.showLoading 适合短提交；长时间任务使用页面状态；避免 loading 与 toast 同时出现。

## 11. 交互与反馈规范

| 优先级 | 规则 | 检查方法 | 修复方向 |
| --- | --- | --- | --- |
| P1 | 首屏焦点唯一 | 眯眼或快速扫视首屏，确认最先看到的两项是否符合业务优先级；移除色彩后检查字号和位置层级是否仍成立。 | 明确唯一主任务，放大或前置；合并重复模块；减少同权重操作。 |
| P1 | 所有可操作元素都有反馈 | 逐一点击首屏与核心路径控件，记录是否出现视觉状态或页面变化；断网重试。 | 为按钮绑定真实动作；增加 hover-class、loading、toast 或页面内状态；移除无功能入口。 |
| P1 | 等待有范围且有出路 | 在正常网络、弱网和断网下观察首屏与分页；记录等待时间和退出方式。 | 区分首屏/局部/提交加载；增加超时与重试；修正骨架尺寸。 |
| P1 | 错误说明影响与恢复方式 | 模拟接口 4xx/5xx、超时和权限拒绝，检查文案、重试、返回和敏感信息。 | 建立错误映射；区分可重试与不可恢复；只记录技术细节到日志。 |
| P1 | 可点击目标足够大且不拥挤 | 逐项测量实际可点区域而不是图标大小；用拇指和不同机型测试；检查间距。 | 扩大 padding 或伪元素热区；拆分危险操作；把并列图标移入动作面板。 |
| P1 | 返回不丢上下文也不误退出 | 逐页测试系统返回、左上角返回和手势返回，核对页面与状态。 | 修复路由和自定义返回；保存页面状态；在 onUnload/onHide 前提供未保存提示。 |
| P2 | 只有明确的主滚动容器 | 从顶部滚到底部，打开/关闭模态，检查滚动位置、背景滚动和最后一项可见性。 | 简化滚动容器；固定栏用占位 padding；锁背景滚动。 |
| P1 | 固定操作栏不遮挡内容 | 滚到页面最底部，检查最后内容、按钮与安全区；在刘海屏和键盘下复查。 | 增加内容底部占位；使用 env(safe-area-inset-bottom)；处理键盘布局。 |
| P2 | 深色模式可用且不是简单反色 | 切换系统深色；检查文字、图标、图片、弹窗、输入框和错误态。 | 建立深色配色映射；验证对比；调整图片遮罩和阴影。 |
| P2 | 空状态解释原因并给出下一步 | 构造搜索无结果、新账号、无权限和网络失败四种状态，检查文案与操作是否不同。 | 为不同空态配置文案与主操作；搜索空态保留关键词并提供改词建议；错误态不要混为空。 |
| P2 | 长文本可读且可展开 | 使用超长中英文、数字和无空格字符串测试；检查截断、换行和完整信息入口。 | 统一行数限制；为可展开内容提供明确按钮；调整容器为自适应高度。 |
| P2 | 图片失败不破坏布局 | 断网、慢网和错误 URL 下检查图片占位、布局和重试。 | 统一图片容器比例；添加占位和错误态；关键信息以文本呈现。 |

## 12. 微信平台注意事项

> 下列规则的核验状态来自知识库。标记为需验证的项目在真实基础库/真机上通过前，不能算已完成。

| 严重度 | 规则 | 推荐做法 | 核验状态 |
| --- | --- | --- | --- |
| P1 | 优先使用微信原生导航栏 | 没有明确品牌需求时使用原生导航；标题与页面主标题一致；页面内不再绘制第二套返回栏。 | 已核对官方文档 |
| P1 | 底部和顶部安全区域不能靠猜测 | 为固定底栏增加安全区 padding；页面内容增加等量占位；使用 env(safe-area-inset-bottom) 等能力时提供可视检查和无变量时的回退。 | 需按目标基础库与真机验证 |
| P1 | 点击区域按物理尺寸校验 | 把 88rpx×88rpx 作为工程基线，关键操作用更大热区；相邻操作留间距；图标按钮扩大 padding。 | 已核对官方文档 |
| P1 | 自定义返回必须与路由栈一致 | 返回按钮检查页面栈深度；无上一页或来自分享时回到明确的安全页面；未保存内容先确认。 | 已核对官方文档 |
| P2 | onShow 与 onHide 不是可忽略细节 | 在 onShow 刷新对实时性敏感的数据；清理定时器/监听器；避免在 onShow 无限重复请求；理解缓存和状态恢复。 | 已核对官方文档 |
| P1 | 首屏与 setData 影响设计实现 | 首屏只加载必要内容；图片控制尺寸和懒加载；减少大对象 setData；动画优先 transform/opacity；复杂图表做降级。 | 需按项目基础库与真机验证 |
| P1 | 开发者工具通过不等于真机通过 | 静态审查、开发者工具、真机和弱网分别记录；未执行的检查明确标为未执行；不得把模拟器截图当真实体验。 | 项目原则；平台差异需实测 |
| P1 | 原生 TabBar 控制在 2–5 项且主任务稳定 | 只有存在 2–5 个稳定一级区域时才使用 TabBar；优先 3–4 项；文字不可省略；未读状态同步。 | 已核对官方文档 |
| P2 | TabBar 图标资源符合平台约束 | 使用本地 PNG/SVG 支持范围内的资源；普通态和选中态视觉线宽一致；文字仍显示；准备多倍率检查。 | 已核对官方文档 |
| P1 | 固定底栏不得遮挡页面内容 | 固定栏高度加安全区作为内容 padding-bottom 的基线；键盘场景动态计算；底部唯一主操作。 | 需按目标基础库与真机验证 |
| P2 | 页面滚动与 scroll-view 只选一个主容器 | 默认让页面滚动；需要固定头部/局部滚动时才用 scroll-view，并明确高度；禁止多层同向滚动嵌套。 | 已核对官方文档 |

### 本轮明确未执行的验证

- 未运行页面截图或视觉模型评审。
- 未导入微信开发者工具执行编译、交互与真机截图。
- 未在真实 iOS/Android 设备验证键盘、安全区、分享、性能与原生组件。
- 未验证项目实际基础库、渲染引擎和第三方组件兼容性。

## 13. 技术栈约束

目标技术栈：**微信原生小程序** (`wechat-native`)

| 规则 | 应该做 | 不要做 | 核验状态 |
| --- | --- | --- | --- |
| 以 app.json 的页面注册为路由事实来源 | 先读 app.json/project.config.json 再改 UI；页面路径与文件名一致；新增页面同步注册。 | 只创建 page.wxml 不注册页面；把 Web 的 index.html 当作小程序入口。 | 已核对官方文档 |
| 数据绑定和列表渲染使用 WXML 语法 | 使用 view/text/image/button 等小程序组件；列表加 wx:key；事件名称使用 bindtap/catchtap。 | 在 WXML 写 onclick、document.querySelector 或 div；用 v-if/React JSX 语法。 | 已核对官方文档 |
| WXSS 使用 rpx 建立跨屏比例 | 设计稿按 750 宽标注；正文用 rpx；避免依赖未确认的浏览器特性；复杂效果准备回退。 | 把 px 固定宽度、vh 魔法值和浏览器专属选择器直接搬入 WXSS。 | 已核对官方文档 |
| 根据页面类型选择路由 API | 封装路由并防重复；tabBar 用 switchTab；支付结果等使用 redirectTo/reLaunch 避免返回重复支付；检查页面栈。 | 用 navigateTo 打开 tabBar；连续点击创建三个详情；依赖取消路由。 | 已核对官方文档 |
| 固定底部元素加安全区与内容占位 | 底栏 padding-bottom 加安全区；页面内容同样留出高度；真机检查最后一项。 | bottom: 0 且没有 padding，按钮贴边被遮。 | 需按目标基础库与真机验证 |
| 页面标题、导航和滚动行为放在页面 JSON 中 | 逐页设置标题；需要自定义导航才设 navigationStyle custom；开启下拉刷新同时实现回调。 | 在 JS 中动态伪造所有导航配置；页面没有标题。 | 已核对官方文档 |
| 原生组件层级和覆盖能力需要实测 | 避免把关键交互层叠在原生组件上；使用官方支持的覆盖方式；准备降级；在目标渲染引擎测试。 | 用 z-index 覆盖 map 上的筛选弹窗；假设 video 上任何 view 都可点击。 | 需按渲染引擎与组件版本验证 |
| 原生 TabBar 配置符合平台限制 | 保持 3–4 个稳定主区域；每项有文字；图标本地提供；选中态明确。 | 配置 6 个 Tab；只放图标；TabBar 指向不存在页面。 | 已核对官方文档 |
| 固定底栏高度参与布局计算 | 统一定义底栏高度 token；内容区用变量或类增加 padding；键盘弹起时调整。 | 详情页最后内容被购买栏覆盖；表单提交按钮被键盘遮挡。 | 需按目标基础库与真机验证 |
| 分享配置属于页面而不是按钮动画 | 分享卡提供标题、封面和路径；从分享进入可回到详情；不泄露隐私。 | 自己画一个分享面板但不触发平台分享。 | 已核对官方文档 |

⚠️ 框架差异与平台能力需按项目依赖、基础库和真机复核。

## 14. 需要主动避免的反模式

| 严重度 | 反模式 | 表现 | 检查方法 | 修复 |
| --- | --- | --- | --- | --- |
| P2 | 所有组件都使用圆角卡片 | 页面、列表、表单、设置、统计都包在同样的白底圆角阴影卡里，模块之间只靠卡片分隔。 | 检查页面是否连续出现三层以上卡片；移除阴影和圆角后是否仍有清晰分组；不同内容是否使用同一容器。 | 建立页面分区、列表行、数据块和卡片四种容器；卡片只用于需要整体点击或独立比较的内容。 |
| P2 | 动画过多 | 每个模块入场、悬浮、无限粒子、按钮持续弹跳，影响阅读和性能。 | 统计动画数量与持续时间；检查是否无限循环、是否可关闭、低端机帧率。 | 动效只表达状态/空间关系；限制时长 120–240ms；移除无限装饰；提供低动效路径。 |
| P3 | 不必要的装饰图标 | 每个标题、列表项和状态都配一个图标，图标与语义无关，增加噪音。 | 移除图标后检查信息是否仍然清楚；统计图标数量及用途；寻找重复语义。 | 只保留帮助识别或执行动作的图标；统一图标库；装饰交给排版和图像。 |
| P1 | 固定底部按钮遮挡内容 | 页面最后一段文字、按钮或图片被购买栏/输入栏永久覆盖。 | 滚到最底部检查最后内容；测量底栏高度和安全区；打开键盘复测。 | 内容区 padding-bottom = 底栏高度 + 安全区；组件化底栏；键盘场景动态更新。 |
| P1 | 低对比度文本 | 浅灰字放在白底或米色底，价格、说明和禁用态难以阅读。 | 用对比度工具测量正文和背景，目标至少 4.5:1；灰度检查；深色模式单独测量。 | 加深文字或调整背景；重新定义次级文字 token；禁止用浅灰承载关键信息。 |
| P2 | 过度使用阴影 | 每个卡片、按钮、标签和输入框都有阴影，背景与表面没有明确层次。 | 统计阴影层数；在低端设备和深色模式下检查灰边、脏色和性能。 | 最多保留两档阴影；用边框、背景和间距分担层次；深色模式改用亮度和边框。 |
| P1 | 视觉层级不清晰 | 标题、正文、价格和按钮字号接近，颜色权重相同，用户扫视后不知道该看哪里。 | 灰度截图检查层级；眯眼测试第一视觉焦点；去掉颜色后检查字号、字重、间距和位置。 | 为主信息、次信息、辅助信息定义三级以上差异；确保首屏只有一个焦点；用位置和留白加强。 |
| P2 | 字号层级混乱 | 相邻模块字号无规律，标题比上一级还小，辅助文字过多且字号过小。 | 收集所有 font-size 值并去重排序；检查是否超过 5–7 个层级；测量正文与辅助字号。 | 建立 5–7 级字号 token；正文 28–32rpx；辅助不低于 24rpx；所有页面使用同一比例。 |
| P2 | 无意义渐变背景 | 首屏和卡片大量使用紫粉、蓝紫或彩虹渐变，渐变与品牌、内容或状态没有关系。 | 统计渐变使用位置，逐个询问它是否表达品牌、光源、状态或层级；移除后若信息完全不受影响，即为装饰性渐变。 | 只保留有业务含义的渐变，如品牌资产或状态过渡；改用纯色、图文或编辑式层级建立识别。 |
| P1 | 页面返回行为不符合预期 | 从详情返回首页、筛选状态丢失、表单内容清空、无栈时返回无反应。 | 从每个入口进入再返回，记录页面与状态；测试系统手势返回和分享冷启动。 | 返回目标与入口一致；保存筛选/滚动/表单；无栈回安全页；提示未保存。 |

## 15. 验收标准

- [ ] 首屏主任务清晰可见，且只保留一个主操作或主信息焦点。
- [ ] 核心任务路径覆盖：继续播放、发现新歌、搜索、收藏、查看歌词/队列。
- [ ] 所有可点击热区不小于 88rpx，相邻操作保持足够间距。
- [ ] 固定底部操作栏包含安全区处理，并为页面内容设置等高占位。
- [ ] 列表、表单、支付或长任务包含加载、空、错误与恢复状态，不以静态稿替代。
- [ ] 正文与背景、次级文字与背景的对比度不低于 4.5:1（以自动化检查结果为准）。
- [ ] 页面级规范只覆盖必要规则，不引入 Master 之外的新配色、字体或圆角语言。
- [ ] 设计 token 与组件样式一致，不允许新增未登记颜色或魔法间距。
- [ ] 静态检查、微信开发者工具和至少一台 iOS/一台 Android 真机的执行状态分别记录。
- [ ] 未执行的真机、键盘、安全区、分享与性能检查不得标记为通过。

## 16. 数据来源、未完成项与限制

### 引用的数据记录 ID

- **product**：`prod-music`
- **style**：`style-content-first`
- **palette**：`palette-music-night`
- **typography**：`type-reading-song`
- **layouts**：`layout-home`、`layout-music-player`、`layout-search`、`layout-search-results`、`layout-profile`
- **components**：`comp-search-bar`、`comp-image-preview`、`comp-avatar`、`comp-bottom-action`、`comp-empty`、`comp-loading`、`comp-toast`、`comp-share`、`comp-chart`、`comp-nav-native`、`comp-nav-custom`、`comp-tabbar`
- **ux_rules**：`ux-hierarchy`、`ux-action-feedback`、`ux-loading-states`、`ux-error-states`、`ux-touch-target`、`ux-back-behavior`、`ux-scroll`、`ux-bottom-bar`、`ux-dark-theme`、`ux-empty-states`、`ux-long-text`、`ux-image-fallback`
- **mini_program_rules**：`mp-native-nav`、`mp-safe-area`、`mp-touch-target`、`mp-back`、`mp-page-lifecycle`、`mp-performance`、`mp-devtools-vs-device`、`mp-tabbar`、`mp-tabbar-icon`、`mp-fixed-bottom`、`mp-scroll`
- **anti_patterns**：`anti-card-everywhere`、`anti-animation-overload`、`anti-decorative-icons`、`anti-bottom-bar-overlap`、`anti-low-contrast`、`anti-shadow-overuse`、`anti-weak-hierarchy`、`anti-type-chaos`、`anti-meaningless-gradient`、`anti-unexpected-back`
- **stack_rules**：`wx-project-structure`、`wx-wxml-binding`、`wx-wxss-rpx`、`wx-routing`、`wx-safe-area`、`wx-page-config`、`wx-native-component`、`wx-app-tabbar`、`wx-fixed-bottom`、`wx-share`
- **reasoning**：`reason-content`

### 生成限制

- 本设计系统由本地知识库和可解释规则生成，不包含运行截图、视觉模型判断或真机结果。
- CSS 自定义属性、安全区、原生组件和渲染引擎能力必须在目标基础库与真机验证。
- 平台规则带有核验状态；标记为“需按目标基础库验证”的规则不能当作已验证事实。
- 设计系统生成不等于页面实现；可选 DevTools 模拟器验收需要用户开启服务端口，且模拟器不等于真机。
- 设计系统不能替代对现有业务逻辑、权限和数据安全的审查。

### 维护方式

修改设计前先更新本文件或页面覆盖，再改组件；如果数据本身需要扩展，运行 `python scripts/validate_data.py` 并补充相应记录。
