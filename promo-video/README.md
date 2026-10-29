# MPUX Pro 宣传片（Remotion）

为 Mini Program UX Pro 制作的 52 秒宣传片。使用 Remotion 以代码方式生成，所有画面、动效和排版都在 `src/` 中。

## 成片规格

- 时长：52 秒
- 分辨率：1920 × 1080
- 帧率：30 fps
- 视频：H.264
- 音频：AAC 立体声（氛围底音 + 中文旁白）
- 成片：`out/mpux-promo.mp4`
- 字幕：`out/mpux-promo.srt`
- 封面：`out/mpux-promo-poster.png`

`out/` 被 `.gitignore` 忽略，不会被提交到仓库。

## 叙事结构

| 时间 | 场景 | 内容 |
| --- | --- | --- |
| 0–6s | The Problem | AI 小程序模板化：同一套首页结构 |
| 6–13s | Meet the System | 品牌与定位：设计决策系统，不是模板库 |
| 13–22s | Workflow | 识别栈 → 分析 → 检索 → Master → 实现 → 验收 |
| 22–31s | Knowledge Base | 347 条结构化知识、本地 BM25 检索 |
| 31–40s | Design System | Master + 页面覆盖 + token 约束 |
| 40–48s | Verification | 真实截图、24/24 模拟器检查、测试边界 |
| 48–52s | Get Started | 主张、GitHub、MIT / 本地运行 |

## 运行

```bash
cd promo-video
npm install
npm run dev
```

渲染成片：

```bash
npm run render
```

如果 Remotion 无法下载 Chrome Headless Shell，可指定本机 Chrome：

```bash
npx remotion render MPUXPromo out/mpux-promo.mp4 \
  --codec=h264 --crf=18 \
  --browser-executable="C:/Program Files/Google/Chrome/Application/chrome.exe"
```

渲染半分辨率草稿：

```bash
npm run render:draft
```

重新生成海报：

```bash
npm run still
```

## 配音与字幕

`captions.json` 同时驱动旁白和字幕：

- `scripts/generate_voiceover.py` 读取每一段的 `start` 和 `text`；
- 使用 `edge-tts` 的 `zh-CN-XiaoxiaoNeural` 生成中文旁白；
- 自动把分段旁白放到对应时间点，生成 `public/audio/voiceover.mp3`；
- 自动更新字幕结束时间，并写出 `out/mpux-promo.srt`；
- Remotion 中的 `src/Captions.tsx` 读取同一份 `captions.json` 渲染内嵌字幕。

重新生成：

```bash
pip install -r scripts/requirements.txt
npm run voice
```

需要网络访问微软语音服务。替换声音可直接修改脚本里的 `VOICE`（如 `zh-CN-YunxiNeural`）。如果只替换成片音轨，替换 `public/audio/voiceover.mp3` 后重新渲染即可。

## 修改

- 颜色、字体、时间轴：`src/theme.ts`
- 字幕与旁白文本：`captions.json`
- 场景：`src/scenes/*.tsx`
- 公共组件：`src/components.tsx`
- 截图素材：`public/screens/`
- 音轨：`public/audio/bed.mp3`、`public/audio/voiceover.mp3`

重新生成氛围音轨需要 ffmpeg：

```bash
npm run audio
```

音轨由 `scripts/generate_audio.py` 本地合成，不使用外部音乐/采样。

## 证据边界

- 截图来自 `verification/artifacts/` 的微信开发者工具模拟器，不是真机。
- 24/24 检查、9 张截图、0 console.error 来自项目的运行时验收结果。
- 视频不声称真机、键盘、性能或视觉模型验证已通过。

## 依赖

- Remotion 4.0.539
- React 19
- Node.js `^20.19.0 || ^22.13.0 || >=24`

Remotion 自身有独立的许可条款；本项目代码使用 MIT License。
