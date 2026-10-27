# 运行时验收说明

这个目录不是 Skill 的核心依赖，而是可选的微信开发者工具运行时验收环境。

## 目标

- 用真实生成的 `design-system/` 驱动一个原生小程序；
- 在微信开发者工具模拟器中检查页面渲染、自定义导航、固定底栏安全区、TabBar、状态页与核心交互；
- 保存真实截图和机器可读结果；
- 明确这些结果仍不等于 iOS/Android 真机验证。

## 前置

1. 安装微信开发者工具，并将下方占位符替换为实际 `cli.bat` 路径；
2. 在开发者工具 **设置 → 安全设置** 中开启 **服务端口 / CLI HTTP 调用**；
3. 进入本目录安装可选验收依赖：
   ```bash
   cd verification/devtools
   npm install
   ```

## 运行

```bash
cd verification/devtools
node verify.cjs --cli "<cli.bat 的绝对路径>" --project ".." --port 9420
```

或使用 Python 适配器（若已实现）：

```bash
python scripts/devtools_adapter.py --cli "<cli.bat 的绝对路径>" run --project verification
```

需要开发者工具已打开且服务端口开启。

## 产物

- `verification/artifacts/01-home-normal.png`
- `02-player-initial.png`
- `03-player-playing.png`
- `04-player-queue.png`
- `05-home-error.png`
- `06-home-empty.png`
- `07-home-loading.png`
- `08-profile.png`
- `results.json`：检查项、系统信息、console 错误、异常、截图路径。

截图只来自开发者工具模拟器，官方 automator 截图 API 不支持客户端真机。

## 验收覆盖

- 首页正常/加载/错误/空状态；
- 继续播放跳转；
- 播放器初始态、播放态、收藏态；
- 播放队列打开/关闭；
- 自定义导航返回；
- 自定义导航状态栏/胶囊计算；
- TabBar 切换；
- 按钮尺寸；
- console error / 未捕获异常。

不覆盖：

- 真实音频播放；
- iOS/Android 真机键盘与安全区；
- 真实网络、支付、授权；
- 真机性能；
- 视觉模型审美判断。