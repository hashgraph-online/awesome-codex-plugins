<div align="center">

<img src="https://raw.githubusercontent.com/wiroai/Wiro-Plugin/main/.github/assets/wiro-logo.png" alt="Wiro AI" width="240">

# Wiro AI plugin

Run image, video, audio and LLM models, build and run workflows, and deploy and talk to AI agents on Wiro AI from Cursor, Claude Code, Codex, Gemini CLI, Devin, Antigravity and Kiro through the hosted Wiro MCP server.

[![License: MIT](https://img.shields.io/badge/license-MIT-111111?style=for-the-badge&color=111111)](./LICENSE) [![MCP: streamable HTTP](https://img.shields.io/badge/MCP-streamable%20HTTP-111111?style=for-the-badge&color=111111)](https://wiro.ai/docs/wiro-mcp-server) [![Works with Claude Code, Codex, Cursor, Gemini CLI, Devin, Antigravity and Kiro](https://img.shields.io/badge/works%20with-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20Gemini%20CLI%20%C2%B7%20Devin%20%C2%B7%20Antigravity%20%C2%B7%20Kiro-111111?style=for-the-badge&color=111111)](#install)

[Website](https://wiro.ai) · [Models](https://wiro.ai/models) · [Docs](https://wiro.ai/docs/wiro-mcp-server) · [Dashboard](https://wiro.ai/panel)

</div>

This repository packages the hosted Wiro MCP server (`https://mcp.wiro.ai/v1`) as a plugin for each of these tools. Once it is installed, your assistant can use three sets of Wiro AI tools:

- **Models**: search the Wiro AI model catalog, read a model's inputs and price, run it, wait for the task and show you the output. It can also upload input files and look through your past tasks.
- **Workflows**: build workflows that chain models into one graph, run them, resume failed runs and browse the public gallery. The Workflow Agent can design or change a workflow with you in plain language.
- **Agents**: talk to Studio, Wiro's creative agent, and deploy, configure, run and message your own agents built from templates or from skills.

Your assistant can also search the Wiro AI docs, and built-in guides tell it the order of calls, what costs money and what needs your approval.

The plugin also comes with ready [slash commands](#slash-commands) for images, image edits, video, speech, music, transcripts, 3D, the model catalog, workflows, agents and tasks. Each one picks a fitting model from the catalog, tells you the price before it runs and can save the results into your project.

The plugin is free. Model runs are billed to your Wiro wallet at the model's listed price, workflow runs for their model steps, and chats with Studio or the Workflow Agent after each reply. An agent plan your assistant starts is paid from the same wallet when it starts and then every 30 days until you cancel it. A plan you pay by card in the Wiro dashboard keeps renewing on that card, and you upgrade or top it up there. Deploying an agent, moving it to a higher plan or buying extra credits shows the price and asks before charging; turning skills on or off is free.

## Sign in

There is no key to copy. The first time your assistant connects, it opens the Wiro sign-in page in your browser. Sign in or create an account, pick a project, choose how long the connection lasts and click Allow. The project you pick decides which wallet pays and which workflows and agents your assistant works with. You can see or disconnect your apps at any time under [Connected Apps](https://wiro.ai/panel/project?view=apps).

If you'd rather use an API key, add the server by hand with an `Authorization` header, as shown under [Other assistants](#other-assistants).

## Install

### Claude Code

```
/plugin marketplace add wiroai/Wiro-Plugin
/plugin install wiro-ai@wiro
```

Then open `/mcp`, select the Wiro server and choose Authenticate to sign in.

### Codex

```bash
codex plugin marketplace add wiroai/Wiro-Plugin
codex plugin add wiro-ai@wiro
```

Then run `codex mcp login wiro` to sign in. The plugin adds the Wiro MCP server, the five agent skills and the [commands](#slash-commands), which you call with `$`, for example `$wiro-ai:image`.

### Gemini CLI

```bash
gemini extensions install https://github.com/wiroai/Wiro-Plugin
```

Then run `/mcp auth wiro` in Gemini CLI to sign in.

### Devin

```bash
devin plugins install wiroai/Wiro-Plugin
```

In the Devin web app, go to Customize > Plugins > Add plugin > From repository and enter `wiroai/Wiro-Plugin`. Devin opens the Wiro sign-in page the first time it connects.

### Antigravity

```bash
agy plugin install https://github.com/wiroai/Wiro-Plugin
```

The plugin adds the Wiro MCP server, the agent skills and the slash commands. Antigravity opens the Wiro sign-in page the first time the server connects.

### Kiro

In Kiro, open the Powers panel, choose Add Custom Power > Import power from GitHub and enter `https://github.com/wiroai/Wiro-Plugin/tree/main/kiro`. The power adds the Wiro MCP server, the agent skills and the slash commands, and Kiro opens the Wiro sign-in page the first time it connects.

### Cursor

This repository is also a Cursor plugin. Until it is listed in the Cursor Marketplace, use the one-click link or add the hosted server to your MCP settings by hand:

[Add to Cursor](https://cursor.com/install-mcp?name=wiro&config=eyJ1cmwiOiJodHRwczovL21jcC53aXJvLmFpL3YxIn0=)

```json
{
  "mcpServers": {
    "wiro": {
      "url": "https://mcp.wiro.ai/v1"
    }
  }
}
```

Cursor opens the Wiro sign-in page the first time it connects.

### Other assistants

Any client that supports remote MCP servers can connect to `https://mcp.wiro.ai/v1`. Clients with MCP sign-in (OAuth) open the Wiro sign-in page. Others can send an `Authorization: Bearer <API key>` header instead; for a project that uses signature-based auth, send `API_KEY:API_SECRET` (both values joined with a colon). Create a project and its API key at [wiro.ai/panel/project/new](https://wiro.ai/panel/project/new). To run the server on your own machine instead, use the npm package [`@wiro-ai/wiro-mcp`](https://www.npmjs.com/package/@wiro-ai/wiro-mcp). Setup guides for more clients are in the [Wiro MCP docs](https://wiro.ai/docs/wiro-mcp-server).

### Agent skills

The repository also has five agent skills:

- `wiro-ai` in [`skills/wiro-ai/SKILL.md`](./skills/wiro-ai/SKILL.md) shows a coding agent how to use Wiro AI from code: find a model, check its price, run it, get the result, and call LLMs through the OpenAI-compatible endpoint.
- `wiro-realtime-voice` in [`skills/wiro-realtime-voice/SKILL.md`](./skills/wiro-realtime-voice/SKILL.md) covers live voice conversation, streaming text-to-speech and streaming speech-to-text over the Wiro WebSocket.
- `wiro-workflows` in [`skills/wiro-workflows/SKILL.md`](./skills/wiro-workflows/SKILL.md) designs, saves, runs, tests and repairs workflows, writes their graphs and drafts or edits them with the Workflow Agent.
- `wiro-agents` in [`skills/wiro-agents/SKILL.md`](./skills/wiro-agents/SKILL.md) covers agents from template to daily use: plans and prices, deploying, credentials and sign-ins, messages, scheduled tasks, plan changes and removal.
- `wiro-media-assets` in [`skills/wiro-media-assets/SKILL.md`](./skills/wiro-media-assets/SKILL.md) makes images, social cards, icons, short videos, voice-overs and 3D models for a project, sizes them and puts them where the project's framework expects them.

Claude Code, Gemini CLI, Cursor, Devin and Antigravity pick them up with the plugin, and the Kiro power and the Codex plugin carry them too. To add them to other agents that read skills, run:

```bash
npx skills add wiroai/Wiro-Plugin --skill wiro-ai --skill wiro-realtime-voice --skill wiro-workflows --skill wiro-agents --skill wiro-media-assets
```

The Wiro SDKs and packages ship their own skills: `wiro-flutter` (wiroai/Dart-QuickStart), `wiro-react-native` (wiroai/ReactNative-QuickStart), `wiro-swift` (wiroai/Swift-QuickStart), `wiro-kotlin` (wiroai/Kotlin-QuickStart), `wiro-n8n` (wiroai/n8n-nodes-wiro) and `wiro-llm` (wiroai/Wiro-LLM), which covers the LLM gateway.

For agents without this plugin, [wiroai/Wiro-Skills](https://github.com/wiroai/Wiro-Skills) has eight skills that do the jobs of the slash commands below: `wiro-image`, `wiro-edit-image`, `wiro-video`, `wiro-music`, `wiro-speech`, `wiro-transcribe`, `wiro-3d` and `wiro-models`. Add them with `npx skills add wiroai/Wiro-Skills`.

## Slash commands

Type a command, then say what you want in plain words. Options are optional, and a command asks for anything it needs that you left out.

| Command | What it does |
| --- | --- |
| `image` | Generate images from a prompt |
| `edit-image` | Edit an image: a new style, things added or removed, the background removed, or a sharper, larger version |
| `video` | Make a video from text, or animate a start image |
| `speech` | Turn text into speech or a voice-over, in the voice and language you pick |
| `music` | Make an instrumental track or a song with lyrics |
| `transcribe` | Turn audio or video into text or captions, with timestamps and speaker labels when the model has them |
| `3d` | Turn a photo or a description into a 3D model file, such as GLB |
| `models` | Search the catalog of 1,000+ models, compare them and read their inputs and prices, for free |
| `workflow` | List, run, create and edit workflows, or have the Workflow Agent draft one |
| `agent` | Ask Studio to create media, message your own agents, check on them, browse templates and deploy one |
| `task` | Check a task, wait for it, show its files and cost, or stop it |

The media commands share their options: `--model owner/slug` picks the model, `--save` or `--save <path>` downloads the results into your project, and model settings such as `--ratio 16:9`, `--duration 5`, `--voice <name>` or `--count 3` go straight to the model. Without `--model`, the command picks a fitting model from the catalog and names one or two others with their prices.

Before a paid run, every command tells you the model, the settings and the expected cost. It goes ahead when the run costs $1 or less, and asks first when it costs more, makes more than four files or is priced after the run. Searching the catalog, reading prices and checking tasks are free.

How each assistant names them:

| Assistant | Example | What ships |
| --- | --- | --- |
| Claude Code | `/wiro-ai:image` | Commands in `commands/` |
| Gemini CLI | `/wiro:image` | Commands in `commands/wiro/` |
| Cursor | `/wiro-image` | Commands in `cursor/commands/` |
| Devin | `/wiro-ai:image` | Skills you call by name, in `devin/skills/` |
| Antigravity | `/wiro-ai:image` | Skills that run only when you call them, in `antigravity/skills/` |
| Kiro | `/wiro-image` | Skills in the power, in `kiro/skills/` |
| Codex | `$wiro-ai:image` | Skills that run only when you call them, in `codex/skills/` |

Devin, Antigravity and Kiro have no command files, so the same commands ship there as skills you call with `/`. Codex gets them as skills too, and you call them with `$`. Other agents that only read skills get the five agent skills, not the commands. Any MCP client that shows MCP prompts also gets four from the server itself: `build_workflow`, `deploy_agent`, `create_with_studio` and `talk_to_my_agent`.

## Try it

These are real Claude Code sessions with the plugin, shown in a clean terminal view.

**Make an image.** `/wiro-ai:image` picks a model from the catalog, gives the price before it runs and saves the file into the project.

<img src="docs/screenshots/claude-code-image.png" alt="Claude Code running /wiro-ai:image: it searches the catalog, picks FLUX.2 Dev Turbo at $0.01, runs it and saves the PNG to public/" width="820">

<img src="docs/screenshots/image-result.jpg" alt="The image it made: a flat illustration of a steaming coffee cup on a wooden table in warm morning light" width="420">

**Animate it.** `/wiro-ai:video` uses that image as the first frame, estimates the cost and waits until the clip is ready.

<img src="docs/screenshots/claude-code-video.png" alt="Claude Code running /wiro-ai:video with a start image: it picks an image to video model, estimates about $0.11, charges $0.084 and saves the MP4 to public/videos/" width="820">

<img src="docs/screenshots/video-frame.jpg" alt="A frame from the 5 second clip, with steam rising from the cup" width="420">

**Compare models for free.** `/wiro-ai:models` reads the catalog and the prices without running anything.

<img src="docs/screenshots/claude-code-models.png" alt="Claude Code running /wiro-ai:models: it compares text to speech models that speak Turkish in a table with their prices and names the cheapest" width="820">

**Find an agent.** `/wiro-ai:agent templates` shows the agent templates that fit, with their plans, prices and what they need.

<img src="docs/screenshots/claude-code-agent.png" alt="Claude Code running /wiro-ai:agent templates: it suggests the Social Manager and Video Creator templates with their plans, prices and the accounts they need" width="820">

**Commands**

- `/wiro-ai:image a flat illustration of a steaming coffee cup, warm morning light, 16:9 --save`
- `/wiro-ai:edit-image https://example.com/mug.jpg put the mug on a marble kitchen counter`
- `/wiro-ai:video --image https://example.com/cup.png steam rising from the cup, slow push-in, 5 seconds`
- `/wiro-ai:speech "Good morning. Your coffee is ready." warm, calm voice --save public/audio/`
- `/wiro-ai:transcribe https://example.com/interview.mp3 --srt --save`
- `/wiro-ai:models cheapest text to speech model that speaks Turkish`
- `/wiro-ai:workflow create a product photo in, a 5 second ad video out`
- `/wiro-ai:agent studio three square product shots of a ceramic mug`
- `/wiro-ai:task last`

In Gemini CLI, type `/wiro:image` instead of `/wiro-ai:image`; in Cursor and Kiro, `/wiro-image`; in Codex, `$wiro-ai:image`.

**Models**

- "Generate a photorealistic image of a mountain lake at sunset"
- "What video generation models are available on Wiro?"
- "Show me the parameters for google/veo3-1"
- "Make a 5 second drone shot over mountains with Kling V3"
- "Check the status of my last task"

**Workflows**

- "Build a workflow that turns a product photo into a short ad video, then run it on this photo"
- "Ask the Workflow Agent to add an upscale step to my product ad workflow and save it"
- "Why did my last workflow run fail? Resume it if it can be resumed"

**Agents**

- "Ask Studio for three logo ideas for a coffee shop"
- "Which agent templates can manage Instagram? What does each plan cost?"
- "Deploy the Instagram Manager agent on the Starter plan and tell me what it still needs"
- "Tell my support agent to summarize today's tickets"

## What's in this repository

| File | Used by |
| --- | --- |
| `.cursor-plugin/plugin.json`, `mcp.json` | Cursor |
| `.codex-plugin/plugin.json`, `mcp.json`, `assets/logo.png` | Codex |
| `codex/skills/` | Codex, the commands as skills you call with `$` and copies of the agent skills |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code |
| `gemini-extension.json` | Gemini CLI |
| `.devin-plugin/plugin.json` | Devin |
| `.antigravity-plugin/plugin.json`, `.antigravity-plugin/README.md`, `mcp_config.json` | Antigravity |
| `kiro/plugin.json`, `kiro/mcp.json` | Kiro |
| `skills/<name>/SKILL.md` (five skills) | Claude Code, Codex, Gemini CLI, Cursor, Devin and Antigravity with the plugin, and other agents through `npx skills add` |
| `commands/*.md` | Claude Code slash commands |
| `commands/wiro/*.toml` | Gemini CLI slash commands |
| `cursor/commands/` | Cursor slash commands |
| `devin/skills/` | Devin, the commands as skills |
| `antigravity/skills/` | Antigravity, the commands as skills |
| `kiro/skills/` | Kiro, the commands and the agent skills inside the power |
| `src/commands/`, `src/partials/` | The one source every assistant's commands are built from |
| `scripts/` | `build-commands.mjs` builds the command files; `validate.mjs` and `validate-schemas.mjs` check them |
| `package.json`, `package-lock.json` | The pinned schema checker `validate-schemas.mjs` uses, installed with `npm ci` |
| `docs/screenshots/` | The screenshots in this README |

All of them connect to the same hosted server, which runs the MCP tools from the open-source [wiroai/Wiro-MCP](https://github.com/wiroai/Wiro-MCP) package.

To change a command, edit its file in `src/commands/` (or a shared part in `src/partials/`) and run `node scripts/build-commands.mjs`, which writes the files for every assistant. CI fails when they differ from the source, and it also runs the Claude Code and Gemini CLI validators and checks the manifests against the Cursor, Antigravity and Kiro schemas.

The skills in [wiroai/Wiro-Skills](https://github.com/wiroai/Wiro-Skills) are built from the same sources. After changing the image, edit-image, video, music, speech, transcribe, 3d or models command, run `node scripts/build.mjs --plugin ../Wiro-Plugin` in a checkout of Wiro-Skills next to this one; its CI fails until the skills match.

## Support, terms and privacy

Email [support@wiro.ai](mailto:support@wiro.ai) or open an issue in this repository. Use of Wiro AI through the plugin is covered by the Wiro AI [Terms of Service](https://wiro.ai/agreement/terms-of-service) and [Privacy Policy](https://wiro.ai/agreement/privacy-policy).

## More from Wiro AI

| Repository | What it is |
| --- | --- |
| [Wiro-MCP](https://github.com/wiroai/Wiro-MCP) | Official MCP server for Wiro AI, [`@wiro-ai/wiro-mcp` on npm](https://www.npmjs.com/package/@wiro-ai/wiro-mcp) |
| [Wiro-Agent-Connectors](https://github.com/wiroai/Wiro-Agent-Connectors) | MCP connectors for Gmail, Shopify, YouTube, Notion and other services without an official MCP server, [`@wiro-ai/wiro-agent-connectors` on npm](https://www.npmjs.com/package/@wiro-ai/wiro-agent-connectors) |
| [Wiro-Skills](https://github.com/wiroai/Wiro-Skills) | Agent skills for images, image edits, video, music, speech, transcripts, 3D and model search |
| [Wiro-LLM](https://github.com/wiroai/Wiro-LLM) | Vercel AI SDK provider for chat, images, speech, transcription and video, [`@wiro-ai/wiro-llm` on npm](https://www.npmjs.com/package/@wiro-ai/wiro-llm) |
| [Wiro-Chromium-Extension](https://github.com/wiroai/Wiro-Chromium-Extension) | Wiro AI extension for Chrome, Edge, Opera and Brave |
| [Wiro-Firefox-Extension](https://github.com/wiroai/Wiro-Firefox-Extension) | Wiro AI add-on for Firefox |
| [Wiro-Safari-Extension](https://github.com/wiroai/Wiro-Safari-Extension) | Wiro AI extension for Safari on the Mac |
| [Swift-QuickStart](https://github.com/wiroai/Swift-QuickStart) | WiroKit, the Wiro AI SDK for iOS |
| [Kotlin-QuickStart](https://github.com/wiroai/Kotlin-QuickStart) | WiroKit, the Wiro AI SDK for Android |
| [Dart-QuickStart](https://github.com/wiroai/Dart-QuickStart) | Wiro AI SDK for Dart and Flutter, [`wiro` on pub.dev](https://pub.dev/packages/wiro) |
| [ReactNative-QuickStart](https://github.com/wiroai/ReactNative-QuickStart) | Wiro AI SDK for React Native and Expo, [`@wiro-ai/wiro-react-native` on npm](https://www.npmjs.com/package/@wiro-ai/wiro-react-native) |
| [Swift-Realtime](https://github.com/wiroai/Swift-Realtime) | Realtime voice AI example for iOS |
| [Kotlin-Realtime](https://github.com/wiroai/Kotlin-Realtime) | Realtime voice AI example for Android |
| [Dart-Realtime](https://github.com/wiroai/Dart-Realtime) | Realtime voice AI example for Flutter |
| [ReactNative-Realtime](https://github.com/wiroai/ReactNative-Realtime) | Realtime voice AI example for React Native |
| [n8n-nodes-wiro](https://github.com/wiroai/n8n-nodes-wiro) | One Wiro AI node for n8n with a searchable model picker, [`@wiro-ai/n8n-nodes-wiro` on npm](https://www.npmjs.com/package/@wiro-ai/n8n-nodes-wiro) |
| [Wiro-Dify-Plugin](https://github.com/wiroai/Wiro-Dify-Plugin) | Wiro AI plugins for Dify: the LLM gateway as a model provider, plus image, video, speech and music tools |
| [Wiro-ComfyUI](https://github.com/wiroai/Wiro-ComfyUI) | Wiro AI nodes for ComfyUI |
| [Wiro-Hermes](https://github.com/wiroai/Wiro-Hermes) | Wiro AI plugins for Hermes Agent: image, video, audio and 3D tools, plus the LLM gateway as a model provider |
| [Wiro-Zed](https://github.com/wiroai/Wiro-Zed) | Wiro AI MCP server extension for Zed |
| [Wiro-Action](https://github.com/wiroai/Wiro-Action) | GitHub Action for Wiro AI models and the LLM gateway, [on the GitHub Marketplace](https://github.com/marketplace/actions/wiro-ai-action) |
| [Wiro-Raycast](https://github.com/wiroai/Wiro-Raycast) | Wiro AI extension for Raycast: image and video generation, LLM chat and model search |
| [Wiro-WordPress](https://github.com/wiroai/Wiro-WordPress) | Wiro AI plugin for WordPress: featured images, image edits, alt text, narration and SEO suggestions |
| [Wiro-Obsidian](https://github.com/wiroai/Wiro-Obsidian) | Wiro AI plugin for Obsidian: images, video, speech, music, transcription and text tools |
| [Wiro-Blender](https://github.com/wiroai/Wiro-Blender) | Wiro AI add-on for Blender: text to 3D, image to 3D and textures |
| [Wiro-Figma](https://github.com/wiroai/Wiro-Figma) | Wiro AI plugin for Figma: images, vectors, image edits and text |
| [Wiro-Next-Starter](https://github.com/wiroai/Wiro-Next-Starter) | Next.js starter for Wiro AI: Playground, image, video and audio tools, and LLM chat, ready for Vercel and Railway |
| [Wiro-Docs](https://github.com/wiroai/Wiro-Docs) | Source of the Wiro AI API docs |
| [wiroai.github.io](https://wiroai.github.io) | Every open-source project from Wiro AI on one page, with a page for each repository |

[Website](https://wiro.ai) · [Models](https://wiro.ai/models) · [Docs](https://wiro.ai/docs) · [X](https://x.com/wiroai)

## License

MIT, see [LICENSE](./LICENSE).
