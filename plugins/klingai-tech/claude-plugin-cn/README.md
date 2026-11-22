# 可灵 AI 国内版 Claude 插件（Kling AI CN）

在 Claude 里用自然语言生成或编辑图片、生成视频、复用主体，并查询任务进度和灵感值。本插件使用 `klingai.com` 的国内版账号。若你的账号在 `kling.ai`，请选择 [国际版插件](https://github.com/klingai-tech/claude-plugin)。两区的账号、灵感值和任务各自独立。

[可灵 MCP & CLI 官方使用指南（国内版）](https://klingai.com/app/mcp/guide)

## 快速开始

### Claude 网页端和桌面端

1. 在 Claude 侧栏打开 **Plugins**（也可能显示为 **Customize → Plugins**），选择 **Add → Add marketplace**。
2. 填入 `https://github.com/klingai-tech/claude-plugin-cn`，安装并启用 **Kling AI CN**。
3. 在插件的 **Connectors** 中点击 **Connect**，在浏览器中登录可灵国内版账号并授权。
4. 新开一个会话，发送下面的连接测试提示词。如果该会话里的可灵连接器处于关闭状态，从 **+** 菜单开启。

### Claude Code

先安装 Claude Code，再在终端运行以下命令。

```bash
claude plugin marketplace add klingai-tech/claude-plugin-cn
claude plugin install kling-ai-cn@klingai-cn
claude
```

在 Claude Code 中输入 `/mcp`，选择插件里的 `kling-ai` 服务并点击 **Authenticate**。在浏览器中登录可灵国内版账号并授权，回到 Claude Code 确认连接状态。

Claude Code 2.1.292 及以上版本也可以用 `claude plugin install kling-ai-cn --marketplace klingai-tech/claude-plugin-cn` 一次完成添加市场和安装。

### 第一次使用

- **检查连接** · “帮我查看当前可灵账号、可用模型和灵感值余额。”
- **生成图片** · “用可灵生成一张午后咖啡馆的照片，窗边坐着一只柴犬，光线柔和。”
- **图片转视频** · 附上一张图，发送“用可灵把这张图作为首帧，做成一段 5 秒短片，镜头缓慢推近。”
- **HDR 视频** · 用可灵 4.0 生成一段 5 秒、1080p 的 HDR 视频。雨后的街道映着霓虹灯，镜头沿路面缓慢向前移动。

查询账号和余额不会消耗灵感值。使用插件创作时，先核对 Claude 给出的模型、参数和参考素材，确认后才会提交生成任务。记下任务 ID，可以在同一会话追问“刚才的可灵任务完成了吗？给我结果链接。”结果链接有效期为 24 小时，拿到后请及时下载。

### 常见问题

- **Claude Code 里找不到 `kling-ai`** · 运行 `/reload-plugins` 或重启 Claude Code，再打开 `/mcp`。
- **授权过期或账号选错** · 在连接器或 `/mcp` 面板断开旧连接，再登录正确账号。切换地区前，先在原地区查完待处理任务，再断开原连接并启用目标地区的插件。
- **可用灵感值不足** · 可灵 MCP 使用个人空间的付费灵感值。给同一个可灵账号充值后，在原会话里让 Claude 继续。

### 手动接入 MCP 或使用 CLI

同一个 AI 助手选择一种可灵接入方式即可。安装插件会自动配置 `https://klingai.com/mcp/plugin`。

- **手动接入 MCP** · 在 Claude 网页端或桌面端打开 **Plugins**（或 **Customize → Connectors**），添加自定义连接器 `https://klingai.com/mcp`，再点击 **Connect**，登录国内版账号并授权。
- **终端 CLI** · 运行 `npm i -g @klingai/cli-cn --registry=https://registry.npmjs.org`，再运行 `kling login` 登录和 `kling --help` 查看命令。

[其他客户端的 MCP 配置和 CLI 命令](https://klingai.com/app/mcp/guide)

## 插件内容

插件通过 OAuth 连接国内版可灵 MCP `https://klingai.com/mcp/plugin`，生成任务由可灵服务执行。插件内置三个 Skill。

| Skill | 用途 |
| --- | --- |
| `kling-ai` | 请求分流、主体库、动作库浏览、素材上传、灵感值查询、任务进度和账号切换 |
| `kling-ai-generate-image` | 文生图、图生图、参考图处理、提示词和场景指导 |
| `kling-ai-generate-video` | 文生视频、图生视频、全能参考、关键帧、受支持的音频输入、动作控制和分镜规划 |

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
Use the native plugin and connector controls on those surfaces. This
repository's validation covers the Claude Code package.

## China service policies and data flow

- [Privacy policy](https://klingai.com/docs/privacy-policy)
- [User service agreement and support contacts](https://klingai.com/docs/user-policy)

The plugin connects to the declared China MCP server at `https://klingai.com/mcp/plugin`. Prompts and reference media are sent to Kling AI for processing. When the server returns an upload ticket, the host sends the selected file and ticket directly to the provider-supplied upload URL; this is an additional HTTP upload step outside the MCP transport. Do not log the ticket or signed URL.

Image and video generation consumes Kling AI credits. The bundled skills do not implement checkout, payment, or credit purchases. Refer to the China service policies for account, content storage, deletion, and paid-service terms. The privacy policy does not specify a fixed retention period for data received from Claude.
