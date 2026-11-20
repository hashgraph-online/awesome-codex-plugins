# Kling AI for Claude · Global

Create and edit images, generate videos, reuse Elements, and check your Kling
tasks and credits in Claude. This plugin uses your Global Kling account at
`kling.ai`. If your account is on `klingai.com`, use the
[China plugin](https://github.com/klingai-tech/claude-plugin-cn). Accounts,
credits, and tasks are separate between regions.

[Official Kling MCP and CLI guide](https://kling.ai/app/mcp/guide)

## Quick start

Choose the instructions for the Claude interface you use.

### Claude web and desktop

1. Open the [Kling AI listing in Claude](https://claude.ai/customize/plugins/id/d9941d90-877f-4972-ab4d-00ffe5b57c4e%40anthropic-plugin-directory) and select **Add to Claude**.
2. Select **Connect** under the plugin's **Connectors**, then sign in with your Global Kling account to authorize it in your browser.
3. Start a new chat and [check your connection](#try-it). If the Kling connector is off in that chat, turn it on from the **+** menu.

For marketplace installation, open **Plugins** in the sidebar (or
**Customize → Plugins**), choose **Add → Add marketplace**, add
`https://github.com/klingai-tech/claude-plugin`, and install **Kling AI**.

### Claude Code

With Claude Code installed, run these commands in your terminal.

```bash
claude plugin marketplace add klingai-tech/claude-plugin
claude plugin install kling-ai@klingai
claude
```

In Claude Code, enter `/mcp`, select the plugin's `kling-ai` server, and
choose **Authenticate**. Sign in with your Global Kling account in the browser,
then return to Claude Code and check that the server is connected.

On Claude Code 2.1.292 or later, `claude plugin install kling-ai --marketplace klingai-tech/claude-plugin`
adds the marketplace and installs the plugin in one command.

### Try it

- **Check the connection** — “Show my Kling account, available models, and credit balance.”
- **Generate an image** — “Use Kling to create a portrait of a Shiba Inu sitting by a café window in afternoon light.”
- **Animate an image** — Attach an image and ask “Use Kling to turn this image into a 5-second video with a slow camera push-in.”
- **Generate an HDR video** — “Use Kling 4.0 to generate a 5-second, 1080p HDR video. Neon signs reflect off a rain-soaked street as the camera slowly moves forward.”

The connection check uses no credits. When you generate with the plugin,
review the model, settings, and references in chat and confirm to submit the
task. Save the task ID and ask “Is my Kling task ready? Give me the result
link.” in the same chat. Result links expire after 24 hours.

### Connection help

- **`kling-ai` is missing in Claude Code.** Run `/reload-plugins` or restart Claude Code, then open `/mcp` again.
- **Authorization expired or you selected the wrong account.** Disconnect the current authorization in the MCP or connector panel and sign in again. Before switching regions, check any pending tasks in the original region, disconnect that connection, and enable the plugin for the new region.
- **Your usable balance is too low.** Kling MCP uses paid credits in your Personal workspace. Top up the same Kling account and ask Claude to continue in the same chat.

### Connect MCP manually or use the CLI

Use one Kling integration per assistant. The plugin already registers
`https://kling.ai/mcp/plugin` for you.

- **Manual MCP** — In Claude web or desktop, open **Plugins** (or **Customize → Connectors**), add `https://kling.ai/mcp` as a custom connector, then select **Connect** and authorize your Global Kling account.
- **Standalone CLI** — To use Kling from the terminal, run `npm i -g @klingai/cli-global --registry=https://registry.npmjs.org`, then `kling login` and `kling --help`.

[Official instructions for other MCP clients and CLI commands](https://kling.ai/app/mcp/guide)

## What the plugin includes

This plugin contains:

- a remote OAuth MCP connection to the Global endpoint `https://kling.ai/mcp/plugin`;
- three Claude Code Skills with shared connection and billing rules:

| Skill | Purpose |
| --- | --- |
| `kling-ai` | Request routing, Elements, motion-library browsing, uploads, credits, task status, and account switching |
| `kling-ai-generate-image` | Text-to-image, image-to-image, reference handling, prompt construction, and image scene guidance |
| `kling-ai-generate-video` | Text-to-video, image-to-video, omni reference, keyframes, supported audio inputs, motion control, and single-shot or multi-shot planning |

It does not bundle a local MCP server, MCP App, command, hook, agent, or API
key. Generation runs on the remote Kling service.

## Install for local review

Load a checkout for one Claude Code session.

```bash
git clone https://github.com/klingai-tech/claude-plugin.git
cd claude-plugin
claude --plugin-dir "$PWD"
```

If you have a plugin ZIP and your Claude Code version supports ZIP plugin
directories, pass the archive path to `claude --plugin-dir`.

## Use

Ask Claude in natural language. You can name the model you want to use.

### Suggested prompts

**English**

- Use Kling Image 4.0 to generate a series of three 8K images in one request. Show the same red panda in a vintage spacesuit exiting a space station through an airlock, drifting past a porthole, and turning to look at the blue Earth. Keep the panda's appearance and spacesuit consistent across all three images.
- Use Kling 4.0 to generate a 20-second cinematic video. A mech warrior drops from high above and slams into the ground. The shockwave instantly sends rubble and dust flying as the camera pushes in fast to emphasize the impact.
- Use Kling 4.0 Flash to create a 20-second, 720p video with my sneaker product photo as the first frame. Have the camera slowly orbit the shoe and hold on a close-up of the upper.
- Open my Kling AI motion library and show me previews of my saved motions. After I pick one, use a compatible motion control model to apply it to the subject image I provided and generate a video.
- Use Kling AI to create my first reusable Element named “Xiaobai” from the front and side views of my character, so I can keep the character consistent in future projects.

**简体中文**

- 使用可灵图片 4.0 一次生成 3 张 8K 连续组图。让同一只身穿复古宇航服的小熊猫依次从空间站出舱、掠过舷窗、转身望向蓝色地球
- 使用可灵 4.0 生成一段 20 秒电影感视频：机甲战士从高空重砸地面，冲击波瞬间震开碎石与尘雾，镜头快速推近，充满力量感
- 使用可灵 4.0 Flash，把我提供的运动鞋商品图作为首帧，生成一段 20 秒、720p 的视频，镜头缓慢绕过鞋身，最后停在鞋面细节上
- 使用可灵AI查看动作库，预览已保存的动作；选定后，用可用的动作控制模型将该动作应用到我提供的主体图片生成视频
- 使用可灵AI将我提供的角色正面图和侧面图保存为第一个可复用主体，命名为“小白”，方便后续创作时保持角色一致

### Image and video models

When you leave the model choice open, the plugin prefers Kling Image 4.0 for
image generation and reference-guided editing when it is available and meets
your requirements. Otherwise, it prefers the selected tool's compatible default
model. A continuous image series requires support for the requested image count
and resolution in one task. The [Kling Image 4.0 User Guide](https://kling.ai/quickstart/kling-image-4-user-guide)
describes native 8K and Series Mode. The plugin can submit the 8K example only
if the connected account's live MCP capabilities support 8K with Series Mode
and the requested count. If 8K is unavailable, the Skill explains the limit
before any generation.

| Video model | Generation modes | Output |
| --- | --- | --- |
| Kling 4.0 | Text-to-video, image-to-video with first, last, and intermediate keyframes, and Omni Reference with images, videos, audio, and Elements | 3–30 seconds at 720p, with 1080p and 4K for eligible accounts and optional HDR where supported |
| Kling 4.0 Flash | Text-to-video, image-to-video from a single first-frame image, and Omni Reference with images, videos, and Elements | 3–20 seconds at 720p |

For HDR output, the plugin checks whether the connected account's live MCP
supports HDR at 1080p or 4K on the selected generation mode.

Both Omni Reference models support smart shot splitting. Where the selected
model exposes the audio controls, choose either synchronized sound generation
or retention of the reference video's original sound. A separate audio
reference requires a declared audio input, such as on Kling 4.0 Omni Reference.

Element workflows cover creation, listing, details, updates, deletion, and
reuse with compatible models. Motion-library management is read-only; the
Skill does not invent motion creation or deletion tools. Motion control needs
a subject image and exactly one motion source. Available models, arguments,
and resource limits always come from the live MCP tools.

Video discovery includes `omni_ref_video` when available, even for text-only
requests. The plugin prefers a compatible Kling 4.0 Omni Reference model when
the user leaves model selection open. Kling 4.0 Flash is preferred when it fits
the request and the user prioritizes speed or credit savings. Model access,
identifiers, output settings, and reference limits come from the current
account's `who_am_i` response. If no model in the Kling 4.0 family fits, the
plugin can use a compatible live default when the user allows it. An explicitly
requested unavailable model is reported without silently substituting another model.

The Skills require explicit approval of the final settings before a
credit-consuming generation and submit each approved intent at most once.
They check the connected account's balance immediately before submission.

Library queries and uploads do not authorize generation. They discover the
live tool schemas at runtime and let the host render any MCP App resource
returned by the remote server.

The [skills.sh Snyk audit](https://www.skills.sh/klingai-tech/claude-plugin/kling-ai/security/snyk)
flags credit-consuming generation as W009. Balance lookup and approved
generation run through Kling's OAuth MCP. Manage credit purchases directly on
the [Global Kling website](https://kling.ai/).

If credits are insufficient, recharge the same account through
the official Kling site, then ask Claude to continue in the same conversation.
Claude checks any known task number first and rechecks the balance before a
new submission. If a status refresh fails, Claude reports the task number
and the last confirmed status when available.

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
npm run check
npm test
```

The repository-local check validates metadata, the remote connection, Skill
identities and bundled links, including support for V4 names in public
documentation. It does not submit paid generation tasks or prove account
access to a model; live routing and generation still require an authorized
Claude Code connection.

For Claude's component validation, inspect the per-file `contents` in
`claude plugin validate skills --strict --json`. An empty `contents` array
does not establish that the Skills were checked. Local validation also does
not replace the developer portal's directory checks or security review; see
the [official pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist).

The public ZIP must contain only the plugin manifest, remote MCP declaration,
Skill files, README, and LICENSE. It must not contain `mcp-app`, a local server,
credentials, or generated media.

## Claude Desktop and Cowork

Claude supports plugins in chat, Claude Desktop, and Cowork, with component
support varying by surface; see [Use plugins in Claude](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).
Use the native plugin and connector controls on those surfaces. This
repository's validation covers the Claude Code package.
