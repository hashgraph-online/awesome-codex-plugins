# Omnimodal v3.1.0

Omnimodal 是给纯文本主模型（DeepSeek、Codex 文本模型等）使用的多模态插件：识别图片、视频、音频，并生成图片、视频和音频。默认通过千问/阿里 DashScope API 工作，也可切换 Z.AI/GLM 或通用 OpenAI 兼容服务。

[English](README.en.md)

## 项目定位

Omnimodal 不是模型封装，而是一套面向 Agent 的 MCP 多模态能力层。DeepSeek 等纯文本模型目前缺少原生视觉与音频能力；Omnimodal 在不更换主模型的前提下，通过标准 MCP 工具让 Agent 获得媒体感知、生成和处理能力。

设计目标：

- 工具名、参数和返回格式稳定，便于 Agent 自动调用。
- 识别和生成分离，生成后不自动重复识别，避免浪费 tokens。
- 支持批量、剪贴板、拖拽、网页截图和 Windows 原生截图等 Agent 常用交互。
- 默认带费用确认、超时返回 task_id、媒体格式转换/压缩、日志脱敏和远程 URL 防护。

## 功能

- 图片识别：单图、批量、剪贴板、拖拽图片。
- 视频识别：本地文件、远程 URL、格式转换、超限压缩。
- 音频识别：短音频理解、长音频自动转写。
- 图片生成：文生图、图生图、图片编辑。
- 视频生成：文生视频、图生视频、视频编辑。
- 音频生成：TTS、声音克隆、声音设计、音乐生成。
- 网页截图：Playwright 动态交互截图。
- Windows 截图：全屏、主屏、指定窗口截图。

## DeepSeek Harness 接入

当前项目已具备作为 DSH 生态 plugin / skill / MCP 组件接入的条件：

- 提供 `omnimodal-recognize`、`omnimodal-generation`、`omnimodal-capture-page`、`omnimodal-windows-capture` 四个 stdio MCP server。
- 工具命名、配置和返回格式已稳定，适配 Agent Harness 的自动工具发现与调用。
- 图片、视频、音频识别和生成均支持异步任务，超时后返回 `task_id` 可继续查询。
- DSH 开放后，可优先完成 MCP 注册、工具清单、媒体上传/清理和费用确认适配。

## 架构

```text
Agent (Codex / Claude Code / DSH)
         │  MCP stdio
         ▼
omnimodal-recognize / omnimodal-generation
omnimodal-capture-page / omnimodal-windows-capture
         │  HTTP
         ▼
Qwen / DashScope, Z.AI, OpenAI-compatible APIs
```

## 安装

项目同时支持 Codex 和 Claude Code。需要 Python 3.10+ 和 `uv`。

```powershell
git clone https://github.com/good-boy4069/Deepseek-omnimodal.git
cd Deepseek-omnimodal
Copy-Item .env.example .env
```

在 `.env` 中填写：

```powershell
OMNIMODAL_API_KEY=你的千问或DashScope API Key
OMNIMODAL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

要使用 Z.AI/GLM，改为：

```powershell
OMNIMODAL_PROVIDER=zai
OMNIMODAL_BASE_URL=https://api.z.ai/api/paas/v4
OMNIMODAL_IMAGE_MODEL=glm-5v-turbo
OMNIMODAL_OCR_MODEL=glm-ocr
OMNIMODAL_ASR_MODEL=glm-asr-2512
OMNIMODAL_IMAGE_GEN_MODEL_STANDARD=glm-image
OMNIMODAL_VIDEO_GEN_MODEL_STANDARD=cogvideox-3
OMNIMODAL_VIDEO_GEN_BASE_URL=https://api.z.ai/api/paas/v4
```

要使用 OpenAI 或 OpenAI 兼容服务，改为：

```powershell
OMNIMODAL_PROVIDER=openai_compatible
OMNIMODAL_BASE_URL=https://api.openai.com/v1
OMNIMODAL_IMAGE_MODEL=gpt-4o-mini
```

### Codex

在 Codex 中把项目根目录注册为插件，或使用 `.mcp.json` 启动四个 stdio MCP 服务：

- `omnimodal-recognize`
- `omnimodal-capture-page`
- `omnimodal-windows-capture`
- `omnimodal-generation`

### Claude Code

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_claude_plugin.ps1
```

安装后会写入 `~/.claude/skills/omnimodal`，重启 Claude Code 后加载。

## 工具

### 识别

- `omnimodal_recognize_image(image, task, mode)`
- `omnimodal_recognize_images_batch(images, task, mode, max_workers)`
- `omnimodal_recognize_video(video, task, mode)`
- `omnimodal_recognize_videos_batch(videos, task, mode, max_workers)`
- `omnimodal_recognize_audio(audio, task, mode)`
- `omnimodal_recognize_audios_batch(audios, task, mode, max_workers)`
- `omnimodal_read_clipboard_image(task, mode)`
- `omnimodal_read_dragged_image(task, mode, path)`
- `omnimodal_read_dragged_video(task, mode, path)`
- `omnimodal_read_dragged_audio(task, mode, path)`

### 生成

- `omnimodal_generate_image(prompt, tier, size, n, wait, confirm)`
- `omnimodal_generate_video(prompt, tier, duration, resolution, wait, confirm)`
- `omnimodal_generate_video_from_image(image, prompt, tier, duration, resolution, wait, confirm)`
- `omnimodal_edit_video(video, prompt, tier, duration, resolution, reference_image, wait, confirm)`
- `omnimodal_generate_audio(text, voice, tier, kind, preview_text, wait, confirm)`
- `omnimodal_transcribe_audio(audio, language, wait)`
- `omnimodal_get_task_result(task_id)`

生成工具必须传 `confirm=true` 才会调用付费接口。生成结果默认保存到 `~/.omnimodal/outputs`。
生成完成后直接返回结果路径，不要自动再调用识别工具验证；只有用户明确要求检查生成结果时才追加识别。

视频生成分辨率只支持 `720P/1080P`，传入 `480P` 会自动升级为 `720P`。
`omnimodal_generate_audio` 的 `kind` 支持 `tts`、`clone`、`voice_design`、`music`；其中 `music` 使用 `fun-music-v1`，该模型目前是阿里云邀测接口，若账号未开通会返回 `AccessDenied`。

### 截图

- `omnimodal_capture_page(url, actions, viewport, output_dir)`
- `omnimodal_list_windows()`
- `omnimodal_capture_windows(mode, window, output_dir)`

## 档位

识别档位：`ocr`、`quick`、`standard`、`full`、`quick_analysis`、`balanced_analysis`、`deep_analysis`。

生成档位：`standard`、`pro`、`max`，默认 `standard`，可通过 `OMNIMODAL_DEFAULT_TIER` 修改。

## 配置

默认配置位于：

- `config/model_catalog.json`：模型、能力、价格、超时。
- `config/profiles.json`：识别档位默认值。
- `config/local.json`：本机私有覆盖，已加入 `.gitignore`。

常用环境变量：

- `OMNIMODAL_API_KEY`
- `OMNIMODAL_PROVIDER`：`dashscope` / `zai` / `openai_compatible`
- `OMNIMODAL_BASE_URL`
- `OMNIMODAL_IMAGE_MODEL`
- `OMNIMODAL_VIDEO_MODEL`
- `OMNIMODAL_AUDIO_MODEL_STANDARD`
- `OMNIMODAL_AUDIO_MODEL_PRO`
- `OMNIMODAL_VIDEO_GEN_MODEL_STANDARD_I2V`
- `OMNIMODAL_VIDEO_GEN_MODEL_MAX_I2V`
- `OMNIMODAL_VIDEO_GEN_MODEL_EDIT`
- `OMNIMODAL_OCR_MODEL`
- `OMNIMODAL_ASR_MODEL`
- `OMNIMODAL_GENERATION_MODEL`
- `OMNIMODAL_VIDEO_GEN_BASE_URL`
- `OMNIMODAL_AUDIO_GEN_BASE_URL`
- `OMNIMODAL_IMAGE_GEN_TIMEOUT_SEC`
- `OMNIMODAL_VIDEO_GEN_TIMEOUT_SEC`
- `OMNIMODAL_AUDIO_GEN_TIMEOUT_SEC`
- `OMNIMODAL_MAX_VIDEO_DURATION`
- `OMNIMODAL_GENERATION_OUTPUT_DIR`
- `OMNIMODAL_ALLOWED_OUTPUT_DIRS`
- `OMNIMODAL_ALLOW_PRIVATE_URLS`

## 厂商能力

- `dashscope`：完整识别 + 图片/视频/音频生成，默认配置。
- `zai`：GLM 图片/视频/音频理解，GLM 文生图、文生视频和 GLM ASR；暂不支持图片编辑、TTS、声音克隆和音乐生成。
- `openai_compatible`：图片/视频/音频识别和 OpenAI Images 风格图片生成；视频/音频生成无统一标准，当前返回清晰的不支持提示。

## Demo / 效果展示

示例图是本地生成的 OCR/视觉演示素材，不包含任何个人媒体：

![Demo source](docs/demo-source.png)

识别命令：

```powershell
uv run --project <插件根目录> omnimodal-recognize --image docs/demo-source.png --task "提取图片中的文字、表格和标签" --mode standard
```

真实输出摘要保存在 `docs/demo-output.txt`，可用于核对 OCR 与图片理解效果。生成图片时仍必须先传 `confirm=true`：

```powershell
uv run --project <插件根目录> omnimodal-generation --help
```

## 安全

- API Key 只存在于 `.env` 或系统环境变量，公开仓库不包含 Key。
- 远程 URL 默认禁止本机、内网和云元数据地址。
- 截图输出目录和生成输出目录走路径白名单。
- 日志会脱敏 API Key、query 参数、Base64 和媒体正文。
- 生成工具必须确认费用，避免意外大额扣费。

## 命令行

```powershell
uv run --project <插件根目录> omnimodal-recognize --image <图片路径> --task "<任务>" --mode standard
uv run --project <插件根目录> omnimodal-recognize --video <视频路径> --task "<任务>" --mode standard
uv run --project <插件根目录> omnimodal-recognize --audio <音频路径> --task "<任务>" --mode standard
```

## 故障排查

- API Key 无效：检查 `.env` 中 `OMNIMODAL_API_KEY`，然后重新加载插件。
- 远程 URL 被拒绝：确需访问内网时设置 `OMNIMODAL_ALLOW_PRIVATE_URLS=1`。
- 网页截图失败：确认 Playwright 浏览器已安装，或设置 `OMNIMODAL_CAPTURE_PAGE_BROWSER=msedge` / `chrome`。
- Windows 截图失败：先用 `omnimodal_list_windows()` 查看准确窗口标题。
- 生成超时：生成任务会返回 `task_id`，用 `omnimodal_get_task_result` 查询。

## 维护者

- GitHub：https://github.com/good-boy4069
- 项目地址：https://github.com/good-boy4069/Deepseek-omnimodal
