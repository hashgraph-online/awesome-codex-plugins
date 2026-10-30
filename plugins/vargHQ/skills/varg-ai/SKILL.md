---
name: varg-ai
description: >-
  Generate AI videos, images, voiceovers and music with one varg API key.
  Text- and image-to-video on Seedance 2.5, Kling 4, Veo 3.1 and Wan 3;
  images and edits on Nano Banana 2.1, GPT Image 2.5 and Flux 3; lip sync
  and talking avatars; ElevenLabs v4 voices; Lyria and Mureka music;
  captions and multi-scene renders to MP4. Use when someone asks to make or
  render a video, animate a photo, generate an image, create a UGC ad,
  product video, slideshow or talking head, add voiceover (text to speech),
  music, lip sync or captions, or mentions varg. Cloud mode needs only curl;
  local mode runs on bun + ffmpeg.
license: MIT
metadata:
  author: vargHQ
  version: "2.2.0"
  openclaw:
    requires:
      env:
        - VARG_API_KEY
      anyBins:
        - curl
        - bun
    primaryEnv: VARG_API_KEY
    homepage: https://varg.ai
compatibility: >-
  Requires VARG_API_KEY (get at https://varg.ai/dashboard/api).
  Cloud mode: curl only (zero dependencies).
  Local mode: bun runtime + ffmpeg.
allowed-tools: Bash(bun:*) Bash(bunx:*) Bash(npx:*) Bash(curl:*) Bash(mkdir:*) Bash(echo:*) Bash(chmod:*) Bash(grep:*) Bash(head:*) Bash(cut:*) Bash(tr:*) Bash(printf:*) Read Write Edit
---

## TSX/JSX videos are deprecated

varg's TSX/JSX composition (`vargai/react`: `<Render>`, `<Clip>`, `Video({...})`) is deprecated and gets no new features. The `vargai` CLI no longer renders it: `vargai render`, `preview`, `frame`, `storyboard`, `studio` and `hello` were removed from vargai 0.4.0-alpha125 and from the standalone binary (0.17.1).

- **New videos**: make each clip with the generate tools (`vargai generate_video`, `generate_image`, `generate_speech`, `generate_music`, or the varg MCP / `POST /v2/{video,image,speech,music}`), then cut, join, mix and caption them with the ffmpeg tool (`vargai get_tool ffmpeg`, `vargai call_tool '{"tool":"ffmpeg","input":<its input>}'`, or `POST /v2/ffmpeg`).
- **Existing TSX** still renders: cloud via `POST /v2/render`, local via the pinned `bunx vargai@0.4.0-alpha124 render` (the last release with the command). Use the TSX sections below only for that.

## Version Check (run once per session)

This skill is version **2.2.0**. Before first use each session, check for updates:

```bash
curl -sf https://raw.githubusercontent.com/vargHQ/skills/main/varg-ai/SKILL.md | grep 'version:' | head -1
```

If the remote version is newer than 2.2.0, update and re-read this file:

```bash
npx -y skills update
```

## Setup (REQUIRED before first use)

Before generating anything, find an API key and determine rendering mode.
**Do NOT run interactive CLI tools** (like `bunx vargai init` or `bunx vargai login`) -- they require stdin which agents cannot provide. CLI email (OTP) login is also disabled server-side: `/api/auth/cli/send-otp` returns 403, so don't call it.

### 1. Find an API key (before asking the user anything)

Most users already have a key somewhere. Look for it yourself first -- this checks the environment, then `~/.varg/credentials`, then the project's `.env` / `.env.local`, and loads the first key it finds into `$VARG_API_KEY` without printing it:

```bash
[ -n "${VARG_API_KEY:-}" ] || VARG_API_KEY=$(grep -o '"api_key"[^,}]*' ~/.varg/credentials 2>/dev/null | head -1 | cut -d'"' -f4)
[ -n "${VARG_API_KEY:-}" ] || VARG_API_KEY=$(grep -hE '^(export )?VARG_API_KEY=' .env .env.local 2>/dev/null | head -1 | cut -d= -f2- | tr -d "\"' \r")
export VARG_API_KEY
if [ -n "$VARG_API_KEY" ]; then
  curl -s -o /dev/null -w "key found -- HTTP %{http_code} (200 = valid, 401 = invalid)\n" -H "Authorization: Bearer $VARG_API_KEY" https://api.varg.ai/v2/billing/balance
else
  echo "no key found"
fi
```

- **200** -- the key works. Save it (step 1b) and continue to the balance check.
- **401** -- the key was revoked or mistyped. Tell the user, then do step 1a.
- **no key found** -- do step 1a.

Some agent shells don't keep variables between commands. If `$VARG_API_KEY` is empty in a later command, start that command with:

```bash
[ -n "${VARG_API_KEY:-}" ] || export VARG_API_KEY=$(grep -o '"api_key"[^,}]*' ~/.varg/credentials 2>/dev/null | head -1 | cut -d'"' -f4)
```

### 1a. No key: one message to the user

Ask once, with everything in a single message -- don't first ask whether they have a key, the steps are the same either way. Send them:

> To generate with varg I need an API key:
> 1. Open **https://varg.ai/dashboard/api** and sign in (or create an account).
> 2. Generate an API key and copy it.
> 3. Run this in your terminal and paste the key when prompted -- it stays out of this chat and your shell history:
>    ```bash
>    mkdir -p ~/.varg && printf 'varg API key: ' && read -rs K && echo && (umask 077 && printf '{"api_key":"%s"}\n' "$K" > ~/.varg/credentials) && unset K
>    ```
> Tell me when it's done.

When they reply, re-run the step 1 block. Do NOT ask the user to paste the raw key into the chat, and don't ask them to `export` it -- an `export` in their terminal doesn't reach your already-running shell, but the credentials file does.

### 1b. Save the key for next time

If the key came from the environment or `.env`, save it to `~/.varg/credentials` so future sessions find it (skipped if the file already exists). Always reference `$VARG_API_KEY` -- never the raw value:

```bash
[ -f ~/.varg/credentials ] || (mkdir -p ~/.varg && umask 077 && printf '{"api_key":"%s"}\n' "$VARG_API_KEY" > ~/.varg/credentials)
```

For local render (bun auto-loads `.env`), also add it to the project `.env` -- only if that file exists, is gitignored, and has no key yet:

```bash
[ -f .env ] && git check-ignore -q .env 2>/dev/null && ! grep -q '^VARG_API_KEY=' .env && echo "VARG_API_KEY=$VARG_API_KEY" >> .env
```

**Check balance and add credits**

```bash
curl -s -H "Authorization: Bearer $VARG_API_KEY" https://api.varg.ai/v2/billing/balance
```

You should get `{"available": ..., "total_balance": ..., ...}` (values in credits). If `available` is 0 (or too low for the user's task), the user needs credits before generating anything. A typical short video costs 200-500 credits.

Available packages:

| Package ID | Credits |
|---|---|
| `credits-2000` | 2,000 |
| `credits-5000` | 5,000 |
| `credits-10000` | 10,000 (recommended) |
| `credits-20000` | 20,000 |
| `credits-50000` | 50,000 |
| `credits-100000` | 100,000 |

Direct the user to **https://varg.ai/devs/billing** to buy credits, then re-check the balance. Quote amounts in credits only: what a credit costs depends on the user's plan, so never convert credits to money.

### 2. Determine rendering mode

| bun | ffmpeg | Mode |
|-----|--------|------|
| No  | No     | **Cloud Render** -- read [cloud-render.md](references/cloud-render.md) |
| Yes | No     | **Cloud Render** -- read [cloud-render.md](references/cloud-render.md) |
| Yes | Yes    | **Local Render** (recommended) -- read [local-render.md](references/local-render.md) |

## Critical Rules

Everything you know about varg is likely outdated. Always verify against this skill and its references before writing code.

1. **Never guess model IDs** -- consult [models.md](references/models.md) for current models, pricing, and constraints. If the user names a model that is not there, read `https://varg.ai/models/llms.txt`, then that model's spec at `https://varg.ai/models/<id>.md`. `sora_2*` is discontinued.
2. **Function calls for media, JSX for composition** -- `Image({...})` creates media, `<Clip>` composes timeline. Never write `<Image prompt="..." />`.
3. **Cache is sacred** -- identical prompt + params = instant cache hit that costs 0 credits. When iterating, keep unchanged prompts EXACTLY the same. Never clear cache.
4. **Images in Video** -- ONE image in `Video({ prompt: { images: [img] } })` is the first frame (image-to-video). Several images are *references*, and only models that take references accept them (`seedance_2_5`, `wan_3`, `kling_v4`, `omni_flash_1_1`, `grok_imagine_1_5`, `minimax_h3_max`). Other models fail.
5. **Duration constraints differ by model** -- seedance_2_5: integer 4-30s. wan_3: 2-30s. kling_v4: 3-30s. veo_3_1: only 4, 6 or 8. kling_v2_5: ONLY 5 or 10. Check [models.md](references/models.md).
6. **Native audio = `audio: "native"`** on `Video()`. Provider options must be **namespaced by provider**: `providerOptions: { varg: { fal: { ... } } }`. A flat `providerOptions: { varg: { generate_audio: true } }` is silently dropped by the API, and you get a silent video.
7. **Renders cost credits** -- a typical 3-clip video costs ~300-800 credits depending on the video model (wan_3 vs seedance_2_5). Iterate with `--preview` (local), cheap draft models (`minimax_h3_max_turbo`, `grok_imagine_1_5_lite`) and 720p. Render 1080p only for the final.
8. **API key hygiene** -- Never write a raw API key value into a bash command. Load keys into `$VARG_API_KEY` with the setup snippets (from env, `~/.varg/credentials`, or `.env`) and use `$VARG_API_KEY` in all subsequent commands -- never `echo` or `cat` the key itself. This prevents keys from leaking into conversation context and terminal history.

### Default Models (October 2026)

Ranks are from the Artificial Analysis arenas. Details and alternatives: [models.md](references/models.md).

| Need | Use | ~Credits |
|---|---|---|
| Video, hero shots (T2V/I2V, refs, 4-30s, native audio) | `seedance_2_5` | 210 per 5s 720p |
| Video, best value (#1 T2V, 2-30s) | `wan_3` | 53 per 5s 720p |
| Video, long multi-shot (up to 30s) | `kling_v4` | 82 per 5s 720p |
| Video drafts | `minimax_h3_max_turbo` | 42 per 5s |
| Image, generation and editing / character consistency | `nano_banana_2_1` | 8 |
| Image, top quality / dense text | `gpt_image_2_5` | 11-23 |
| Speech | `eleven_v4` (or `eleven_v4_turbo`, #1 and half price) | 84 / 42 |
| Background music (instrumental) | `mureka_9_5` | 25 |
| Song with vocals | `lyria_3_5` | 11 |
| Talking head (image + audio) | `veed_fabric_1_0` | 160-470 |

## Quick Start

### Cloud Render (no bun/ffmpeg needed)

```bash
# Submit TSX code to the render service — returns a job: {"id": "job_xxx", "status": "queued", ...}
curl -s -X POST https://api.varg.ai/v2/render \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"code": "const img = Image({ model: varg.imageModel(\"nano_banana_2_1\"), prompt: \"a cabin in mountains at sunset\", aspectRatio: \"16:9\" });\nexport default (<Render width={1920} height={1080}><Clip duration={3}>{img}</Clip></Render>);"}'

# Poll for result (repeat until "completed" or "failed"; video at output.outputs[0].url)
curl -s https://api.varg.ai/v2/jobs/JOB_ID \
  -H "Authorization: Bearer $VARG_API_KEY"
```

Full details: [cloud-render.md](references/cloud-render.md)

### Local Render (bun + ffmpeg)

```tsx
/** @jsxImportSource vargai */
import { Render, Clip, Image } from "vargai/react"
import { createVarg } from "vargai/ai"

const varg = createVarg({ apiKey: process.env.VARG_API_KEY! })

const img = Image({
  model: varg.imageModel("nano_banana_2_1"),
  prompt: "a cabin in mountains at sunset",
  aspectRatio: "16:9"
})

export default (
  <Render width={1920} height={1080}>
    <Clip duration={3}>{img}</Clip>
  </Render>
)
```

```bash
bunx vargai@0.4.0-alpha124 render video.tsx --preview   # free preview
bunx vargai@0.4.0-alpha124 render video.tsx --verbose   # full render (costs credits)
```

Full details: [local-render.md](references/local-render.md)

### Single Asset (no video composition)

For one-off images, videos, speech, or music without building a multi-clip template:

```bash
curl -X POST https://api.varg.ai/v2/image \
  -H "Authorization: Bearer $VARG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "nano_banana_2_1", "prompt": "a sunset over mountains"}'
```

Full API reference: [gateway-api.md](references/gateway-api.md)

## How to Write Video Code

Video code has two layers: **media generation** (function calls) and **composition** (JSX).

```tsx
// 1. GENERATE media via function calls
const img = Image({ model: ..., prompt: "..." })
const vid = Video({ model: ..., prompt: { text: "...", images: [img] }, duration: 5 })
const voice = Speech({ model: ..., voice: "rachel", children: "Hello!" })

// 2. COMPOSE via JSX tree
export default (
  <Render width={1080} height={1920}>
    <Music model={...} prompt="upbeat electronic" duration={10} volume={0.3} />
    <Clip duration={5}>
      {vid}
      <Title position="bottom">Welcome</Title>
    </Clip>
    <Captions src={voice} style="tiktok" withAudio />
  </Render>
)
```

### Component Summary

| Component | Type | Purpose |
|-----------|------|---------|
| `Image()` | Function call | Generate still image |
| `Video()` | Function call | Generate video (text-to-video or image-to-video) |
| `Speech()` | Function call | Text-to-speech audio |
| `<Render>` | JSX | Root container -- sets width, height, fps |
| `<Clip>` | JSX | Timeline segment -- duration, transitions |
| `<Music>` | JSX | Background audio (always set `duration`!) |
| `<Captions>` | JSX | Subtitle track from Speech |
| `<Title>` | JSX | Text overlay |
| `<Overlay>` | JSX | Positioned layer |
| `<Split>` / `<Grid>` | JSX | Layout helpers |

Full props: [components.md](references/components.md)

### Provider Differences (Cloud vs Local)

Both modes use `varg.*` for all models. The only difference is imports:

| Cloud Render | Local Render |
|---|---|
| No imports needed (globals are auto-injected) | `import { ... } from "vargai/react"` + `import { createVarg } from "vargai/ai"` |
| `varg.imageModel("nano_banana_2_1")` | `varg.imageModel("nano_banana_2_1")` |
| `varg.videoModel("seedance_2_5")` | `varg.videoModel("seedance_2_5")` |
| `varg.speechModel("eleven_v4")` | `varg.speechModel("eleven_v4")` |

**Always use `varg.*Model()`** with `VARG_API_KEY`. It handles routing, caching, billing, and works with a single key. BYOK via the API is not available in v2 — see [byok.md](references/byok.md) for what works (local-render direct provider modules only).

## Cost & Iteration

- **Prices are in credits.** Typical prices: nano_banana_2_1 image ≈ 8, gpt_image_2_5 (high) ≈ 23, seedance_2_5 5s 720p ≈ 210, wan_3 5s 720p ≈ 53, eleven_v4 line ≈ 84, mureka_9_5 track ≈ 25. Live catalog: `GET https://api.varg.ai/v2/pricing` (no auth). Every model spec: `https://varg.ai/models/llms.txt`. Estimate any request: `POST /v2/estimate`.
- **Cache saves credits.** Keep unchanged prompts character-for-character identical across iterations.
- **Preview first** (local mode only): `--preview` generates free placeholders to validate structure.
- Full pricing: [models.md](references/models.md)

## References

Load these on demand based on what you need:

| Need | Reference | When to load |
|------|-----------|-------------|
| Render via API | [cloud-render.md](references/cloud-render.md) | No bun/ffmpeg, or user wants cloud rendering |
| Render locally | [local-render.md](references/local-render.md) | bun + ffmpeg available |
| Patterns & workflows | [recipes.md](references/recipes.md) | Talking head, character consistency, slideshow, lipsync |
| Model selection | [models.md](references/models.md) | Choosing models, checking prices, duration constraints |
| Component props | [components.md](references/components.md) | Need detailed props for any component |
| Better prompts | [prompting.md](references/prompting.md) | User wants cinematic / high-quality results |
| REST API | [gateway-api.md](references/gateway-api.md) | Single-asset generation or Render API details |
| Debugging | [common-errors.md](references/common-errors.md) | Something failed or produced unexpected results |
| Full examples | [templates.md](references/templates.md) | Need complete copy-paste-ready templates |
| BYOK keys | [byok.md](references/byok.md) | Own provider API keys (BYOK): not available in v2 |
