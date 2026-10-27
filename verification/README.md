# 运行时验收示例

这个目录包含一个真实的微信原生小程序，用于验证 MPUX Pro 生成的设计系统能否落地，并在微信开发者工具中运行。

它不是产品模板，也不是已完成真实音乐服务的应用；没有真实音频、账户、支付或网络请求。

## 设计来源

- 产品：音乐播放器小程序（`prod-music`）
- 设计系统：`design-system/MASTER.md` / `MASTER.json`
- 技术栈：微信原生
- 页面：首页、播放器、个人中心
- 验证环境：微信开发者工具模拟设备 390×844（基础库 3.17.4；截图实际 353×762）

`mini-program/styles/tokens.wxss` 是生成器输出的 token 文件副本；`design-system/` 是事实源。

## 验证覆盖

- 首页正常、加载骨架、错误、空状态；
- 继续播放跳转；
- 自定义导航（状态栏 + 胶囊 + 返回）；
- 播放/暂停、收藏、歌词收起/展开；
- 播放队列打开/关闭；
- 错误重试恢复、空状态恢复；
- 原生 TabBar 切换；
- 触摸目标尺寸；
- 固定底栏安全区；
- console.error 与未捕获异常；
- 自动截图 9 张。

## 截图

真实开发者工具模拟器截图保存在 `artifacts/`。查看：

- [首页](artifacts/01-home-normal.png)
- [播放器初始](artifacts/02-player-initial.png)
- [播放器播放态](artifacts/03-player-playing.png)
- [播放队列](artifacts/04-player-queue.png)
- [错误状态](artifacts/05-home-error.png)
- [空状态](artifacts/06-home-empty.png)
- [加载状态](artifacts/07-home-loading.png)
- [个人中心](artifacts/08-profile.png)
- [重试恢复](artifacts/09-home-recovered.png)

## 重新运行

1. 在开发者工具 **设置 → 安全设置** 开启服务端口 / CLI HTTP 调用；
2. 安装可选的 Node 验收依赖：
   ```bash
   cd verification/devtools
   npm install
   ```
3. 运行：
   ```bash
   python scripts/devtools_adapter.py --cli "<cli.bat 路径>" status
   python scripts/devtools_adapter.py --cli "<cli.bat 路径>" run --project verification --port 9420
   ```
   或直接：
   ```bash
   cd verification/devtools
   node verify.cjs --cli "<cli.bat 路径>" --project .. --artifacts ../artifacts --port 9420
   ```

命令中的 `<cli.bat 路径>` 需要替换为实际安装路径；仓库不会公开机器专属路径。

## 重要限制

- 自动化截图只来自开发者工具模拟器，官方截图 API 不支持客户端真机；
- 未执行 iOS/Android 真机、键盘、真实网络和音频中断验证；
- 工具安全设置不会被本项目自动修改；
- 自动化连接在验证结束后断开，开发者工具保留打开；
- `miniprogram-automator@0.13.0` 的 `launch()` 与当前 DevTools 2.02.2608070 的返回时序不兼容，因此采用官方 CLI `auto` + `automator.connect`；
- 截图与断言结果不能替代产品、品牌与真实设备验收。

## 当前结果

2026-10-27：

- 24/24 自动化检查通过；
- 9 张截图；
- 0 个 console.error；
- 0 个未捕获异常；
- 静态审查 0 个问题；
- 基础库 3.17.4；
- 自动化端口 9431（9420 也已复跑通过）；
- 详情见 `artifacts/results.json` 与 `artifacts/runtime-run.log`。