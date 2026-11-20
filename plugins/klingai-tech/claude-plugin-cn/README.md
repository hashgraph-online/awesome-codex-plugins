# 可灵 AI 国内版插件 · Kling AI CN for Claude

在 Claude 里用自然语言生成图片和视频、复用主体、预览动作库，或查询灵感值和任务进度。
本插件使用 `klingai.com` 的国内账号。使用 `kling.ai` 账号的用户请安装
[海外版插件](https://github.com/klingai-tech/claude-plugin)。国内外账号、灵感值和任务各自独立。

[国内版可灵 MCP 与 CLI 官方指南](https://klingai.com/app/mcp/guide)

## 快速开始

### Claude 网页版和桌面端

1. 打开 **Customize → Plugins → Add → Add marketplace**，添加 `https://github.com/klingai-tech/claude-plugin-cn`，安装并启用 **Kling AI CN**。
2. 在插件的 **Connectors** 中点击 **Connect**，在浏览器中登录国内可灵账号并授权。
3. 在启用了插件的对话中发送下面的[试用提示词](#第一次使用)。

### Claude Code

在终端运行以下命令安装插件并启动 Claude Code。

```bash
claude plugin marketplace add klingai-tech/claude-plugin-cn
claude plugin install kling-ai-cn@klingai-cn
claude
```

进入 Claude Code 后输入 `/mcp`，选择插件提供的 `kling-ai`，在浏览器中登录国内可灵账号并授权。
回到 Claude Code 确认连接成功后，即可开始使用。授权由 Claude Code 管理，使用可灵账号即可完成。

### 第一次使用

可以先发一条查询来确认连接，再试生成。

- **查询** · 帮我查看可灵账号当前的灵感值余额。
- **文生图** · 用可灵生成一张竖版图片，画面是一只柴犬坐在窗边，午后的阳光照在它身上。
- **图生视频** · 附上一张图片后发送「用这张图作首帧，生成一段 5 秒视频，让镜头缓慢推近。」
- **HDR 视频** · 用可灵 4.0 生成一段 5 秒、1080p 的 HDR 视频。雨后的街道映着霓虹灯，镜头沿路面缓慢向前移动。

生成会消耗灵感值。使用插件的创作 Skill 时，先确认 Claude 列出的模型、参数和参考素材，再提交生成。
提交后可在同一对话里问「刚才的可灵任务完成了吗？请给我作品链接。」

### 连接排查

- **Claude Code 里找不到 `kling-ai`。** 安装后重新启动 Claude Code，再打开 `/mcp`。
- **授权过期或连接到另一个账号。** 在客户端的 MCP 或连接器面板断开当前授权，再登录需要使用的国内账号。切换区域前，先查完原区域待跟进的任务，再关闭原连接并启用对应区域插件。

### 手动连接 MCP 或使用 CLI

在支持远程 MCP 和 OAuth 的客户端里，可以添加 `https://klingai.com/mcp` 作为自定义连接器，
再用国内可灵账号授权。安装本插件时会自动配置 `https://klingai.com/mcp/plugin`。
同一个助手保留一种可灵接入方式。其他客户端的具体设置和终端 CLI 安装见[国内版官方指南](https://klingai.com/app/mcp/guide)。

## 插件内容

This plugin contains:

- a remote OAuth MCP connection to the China endpoint `https://klingai.com/mcp/plugin`;
- three Skills with shared connection and billing rules:

| Skill | Purpose |
| --- | --- |
| `kling-ai` | Request routing, Elements, motion-library browsing, uploads, credits, task status, and account switching |
| `kling-ai-generate-image` | Text-to-image, image-to-image, reference handling, prompt construction, and image scene guidance |
| `kling-ai-generate-video` | Text-to-video, image-to-video, omni reference, keyframes, supported audio inputs, motion control, and single-shot or multi-shot planning |

It does not bundle a local MCP server, MCP App, command, hook, agent, or API
key. Generation runs on the remote Kling service.

## Install for local review

Load the plugin directory for one Claude Code session:

```bash
claude --plugin-dir /absolute/path/to/claude-plugin-cn
```

If you already have a compatible plugin ZIP on your machine and your version of
Claude Code supports ZIP plugin directories, load it from its local path:

```bash
claude --plugin-dir /absolute/path/to/plugin.zip
```

## Use with Agent Plugins clients

Install the plugin through a client that supports Agent Plugins 1.0. The root
`plugin.json` declares the plugin, and `mcp.json` registers the same China MCP
endpoint as the Claude package. Connect your China account through the client's
native MCP OAuth flow. The client needs to support Streamable HTTP and OAuth.

## Use

Try one of these prompts in Claude.

- Use Kling Image 4.0 to generate three separate, coherent 8K images in one request. Keep the same red panda, vintage spacesuit, and lighting throughout. In image 1, the red panda exits the space station. In image 2, it drifts past a porthole. In image 3, it turns to look at the blue Earth.
- Use Kling 4.0 to generate a 20-second cinematic video. A mech warrior falls from high above and slams into the ground. A shockwave sends rubble and dust outward on impact as the camera rapidly pushes in on the mech.
- Use Kling 4.0 Flash to generate a 20-second, 720p video with my sneaker product photo as the first frame. Slowly orbit the shoe, keeping its shape, color, and logo consistent, and end on a close-up of the upper.
- Use Kling AI to browse the motion library and preview saved motions. After I select one, apply it to my subject image with an available motion-control model to generate a video.
- Use Kling AI to save the front and side views of my character as my first reusable Element, named “Xiaobai”, to help keep the character consistent in later creations.

[中文推荐提示词](skills/kling-ai/references/prompt-examples.md#suggested-prompts-in-chinese) · [More examples](skills/kling-ai/references/prompt-examples.md#natural-language-requests)

Element workflows cover creation, listing, details, updates, deletion, and
reuse with compatible models. Motion-library management is read-only; the
Skill does not invent motion creation or deletion tools. Motion control needs
a subject image and exactly one motion source. Available models, arguments,
and resource limits always come from the live MCP tools.

- **Kling Image 4.0** supports native 8K and up to 10 related images in one generation in Series Mode. The plugin checks the current account's MCP for the model and the requested combination of resolution, count, series mode, and references. When no model is specified, it prefers Kling Image 4.0 for image generation and editing if available and compatible, then a compatible live default or another compatible model. See the [official image guide](https://kling.ai/quickstart/kling-image-4-user-guide).
- **Kling 4.0** supports text-to-video, image-to-video with first, last, or intermediate keyframes, and omni reference with images, videos, audio, and Elements. It supports 3–30 seconds at 720p, with 1080p and 4K available to eligible accounts. All three entry points offer optional HDR output at 1080p or 4K.
- **Kling 4.0 Flash** supports text-to-video, image-to-video with a single first frame, and omni reference with images, videos, and Elements. It supports 3–20 seconds at 720p.
- Both models support smart shot splitting in omni reference, with a choice between generating synchronized sound and retaining source-video audio. A separate audio reference requires a declared audio input slot, as offered by Kling 4.0 omni reference.

Video discovery includes `omni_ref_video` when available, even for text-only requests. The plugin prefers an eligible Kling 4.0 model for standard delivery and Kling 4.0 Flash when speed or credit savings matter and its capabilities fit. Available models, settings, and reference limits come from the current account's live MCP response. When the user leaves the model open and no compatible 4.0 model is available, the plugin uses a compatible live default. If a named model is unavailable or incompatible, Claude reports the specific limitation.

The Skills require explicit approval of the final settings before a
credit-consuming generation and submit each approved intent at most once.
Library queries and uploads do not authorize generation. They discover the
live tool schemas at runtime and let the host render any MCP App resource
returned by the remote server.

Claude checks the current balance before submitting. If credits are
insufficient, top up the same China account on the Kling AI website and say
“Continue the previous generation” in the same conversation. Claude checks
the original task first if it has a task number. If a new submission is
eligible, Claude rechecks the balance and resumes with the approved settings.

Generation sends the prompt, selected settings, and reference media URLs or
Element IDs to Kling. Local reference files are uploaded only when needed
through the upload flow returned by Kling. Generation and asset storage run
on the remote service; account and task queries also contact Kling.

Quality defaults follow the reference plugin: live-supported `2k` images and
`1080p` video for normal delivery, with higher quality for commercial work and
lower-cost modes when requested. Final settings are shown before submission.

## Validate

```bash
claude plugin validate . --strict
claude plugin validate .claude-plugin/plugin.json --strict
```

Check the frontmatter and bundled links for all three Skills. Run the
developer portal's directory check for the exact release commit. See the
[official pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist).

Keep development scripts, tests, local servers, credentials, and generated
media out of the plugin directory submitted for review.

## Claude Desktop and Cowork

Claude supports plugins in chat, Claude Desktop, and Cowork, with component
support varying by surface; see [Use plugins in Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).
Authentication, uploads, and result presentation have not been validated on
these Claude surfaces. Use each host's native plugin and connector controls.

## China service policies and data flow

- [Privacy policy](https://klingai.com/docs/privacy-policy)
- [User service agreement and support contacts](https://klingai.com/docs/user-policy)

The plugin connects to the declared China MCP server at `https://klingai.com/mcp/plugin`. Prompts and reference media are sent to Kling AI for processing. When the server returns an upload ticket, the host sends the selected file and ticket directly to the provider-supplied upload URL; this is an additional HTTP upload step outside the MCP transport. Do not log the ticket or signed URL.

Image and video generation consumes Kling AI credits. The bundled skills do not implement checkout, payment, or credit purchases. Refer to the China service policies for account, content storage, deletion, and paid-service terms. The privacy policy does not specify a fixed retention period for data received from Claude.
