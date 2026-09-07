---
name: omnimodal
description: 为纯文本主模型提供多模态能力：识别图片、视频、音频，并生成图片、视频、音频。遇到图片路径、截图、UI/网页截图、图表、错误弹窗、OCR、音频/视频理解、文生图/文生视频/TTS 或任何需要多模态能力的任务时自动启用。
---

# Omnimodal

主模型使用纯文本模型时，只要任务需要看媒体、听媒体或生成媒体，就自动调用 `omnimodal_*` MCP 工具，不要等用户手动开启，也不要自行假设媒体内容。

## 自动触发

- 用户消息中有图片、视频、音频路径或附件。
- 任务包含 OCR、截图、UI、设计稿、图表、表格图片、错误弹窗、音频/视频理解。
- 主任务不是媒体任务，但为了完成它必须知道媒体内容。
- 用户要求生成图片、视频、语音、音乐、声音克隆或声音设计。

## 识别工具

- 单张图片：`omnimodal_recognize_image(image, task, mode)`。`image` 支持本地路径、`data:` URL 和可解码的 base64。
- 多张图片：`omnimodal_recognize_images_batch(images, task, mode, max_workers)`。
- 单个视频：`omnimodal_recognize_video(video, task, mode)`。
- 批量视频：`omnimodal_recognize_videos_batch(videos, task, mode, max_workers)`。
- 单个音频：`omnimodal_recognize_audio(audio, task, mode)`，长音频自动走 ASR 转写。
- 批量音频：`omnimodal_recognize_audios_batch(audios, task, mode, max_workers)`。
- 剪贴板图片：`omnimodal_read_clipboard_image(task, mode)`。
- 拖拽媒体：`omnimodal_read_dragged_image` / `omnimodal_read_dragged_video` / `omnimodal_read_dragged_audio`。

网页动态内容先调用 `omnimodal_capture_page(url, actions, viewport, output_dir)`，再把截图路径交给批量识别。Windows 全屏、主屏或指定窗口截图先调用 `omnimodal_list_windows()`，再调用 `omnimodal_capture_windows(mode, window, output_dir)`。

## 生成工具

- `omnimodal_generate_image(prompt, tier, size, n, wait, confirm)`：文生图。
- `omnimodal_generate_video(prompt, tier, duration, resolution, wait, confirm)`：文生视频。
- `omnimodal_generate_video_from_image(image, prompt, tier, duration, resolution, wait, confirm)`：图生视频。
- `omnimodal_edit_video(video, prompt, tier, duration, resolution, reference_image, wait, confirm)`：视频编辑。
- `omnimodal_generate_audio(text, voice, tier, kind, preview_text, wait, confirm)`：TTS、声音克隆、声音设计、音乐生成。
- `omnimodal_get_task_result(task_id)`：查询异步任务。

**费用确认是强制规则**：生成工具必须在调用时传 `confirm=true`；否则返回预计费用且不实际调用付费接口。不要绕过确认。

**生成后不要自动识别验证**：用户要求生成图片、视频或音频时，只调用对应生成工具并直接返回结果路径；不要为了“检查生成效果”再自动调用识别工具。只有用户明确要求检查生成结果、或生成结果明显异常时才允许追加识别。

## mode 档位

识别档位统一为：

- `ocr`：仅图片文字提取。
- `quick`：快速识别，关闭思考，短输出。
- `standard`：标准提取，默认。
- `full`：完整提取，不限制输出。
- `quick_analysis` / `balanced_analysis` / `deep_analysis`：逐步加强的分析档。

档位可通过插件目录 `config/profiles.json` 覆盖；本机私有覆盖写在 `config/local.json`，不会进入 Git。

## 配置

API Key 只写在插件根目录 `.env`：

```powershell
OMNIMODAL_API_KEY=你的千问或DashScope API Key
OMNIMODAL_PROVIDER=dashscope
OMNIMODAL_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OMNIMODAL_IMAGE_MODEL=qwen3.7-flash
OMNIMODAL_VIDEO_MODEL=qwen3.7-flash
OMNIMODAL_AUDIO_MODEL_STANDARD=qwen3.5-omni-flash
OMNIMODAL_AUDIO_MODEL_PRO=qwen3.5-omni-plus
```

可切换厂商：

- `OMNIMODAL_PROVIDER=zai`：GLM 图片/视频/音频理解、GLM 文生图、GLM 文生视频和 GLM ASR。
- `OMNIMODAL_PROVIDER=openai_compatible`：识别和 OpenAI Images 风格图片生成；视频/音频生成会返回明确的不支持提示。

模型目录、档位、超时、输出目录等默认值位于 `config/model_catalog.json` 和 `config/profiles.json`，均可用 `config/local.json` 覆盖。

## Claude 桌面端

Claude 桌面端跨窗口拖入的媒体不落盘。图片复制进剪贴板后调用 `omnimodal_read_clipboard_image`；视频和音频请用户保存为文件后提供明确路径。禁止扫描 `Temp`、按时间戳猜文件，或输出“很可能/可能是你刚粘贴的图片”。

## 命令行兜底

```powershell
uv run --project <插件根目录> omnimodal-recognize --image <图片路径> --task "<任务>" --mode standard
uv run --project <插件根目录> omnimodal-recognize --video <视频路径> --task "<任务>" --mode standard
uv run --project <插件根目录> omnimodal-recognize --audio <音频路径> --task "<任务>" --mode standard
```

生成服务仅支持 stdio MCP 模式；异步任务超时后返回 `task_id`，可稍后查询。
