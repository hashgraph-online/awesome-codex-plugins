---
name: revid-prompt-to-video
description: Turn a one-line idea into a full short video — Revid writes the script, picks visuals, and assembles the cut. Use when the user has a topic but no script. Calls the Revid MCP server (render_video → get_project_status).
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# Idea prompt → video

The lowest-input skill. The user types one line ("Why honey never spoils") and
Revid handles everything: script, visuals, voice, music, cuts.

> Calls the **Revid MCP server** (`https://www.revid.ai/api/mcp`).
> Install once — see [`revid-api-foundations`](../revid-api-foundations/SKILL.md#install-the-revid-mcp-server).

## When to use this skill

- Source is a topic, question, or one-line concept — *no script*.
- The user is OK letting the AI choose the angle and structure.
- For a known script, use [`revid-script-to-video`](../revid-script-to-video/SKILL.md).
- For an idea + brand voice, use
  [`revid-product-description-to-ad`](../revid-product-description-to-ad/SKILL.md).

## Inputs

| Field | Required | Notes |
|---|---|---|
| `prompt` | yes | The idea (one or two sentences) |
| `stylePrompt` | no | Optional tone notes (angle, opener, CTA) |
| `durationSeconds` | no | Default 35 (s) |
| `aspectRatio` | no | Default `9:16` |

## Step-by-step

1. Validate `prompt` is non-empty.
2. Call MCP tool `render_video` with the payload below — it returns `data.pid`.
3. Poll MCP tool `get_project_status` with that `pid` every 5–8 s until
   `data.status === "ready"` (then read `data.videoUrl`).
4. *(Optional)* Call `export_video` with `{ pid, fileName }` if you need a
   freshly named mp4 export.

## `render_video` arguments

```json
{
  "workflow": "prompt-to-video",
  "source": {
    "prompt":          "{ONE_LINE_IDEA}",
    "stylePrompt":     "{OPTIONAL_TONE_NOTES}",
    "durationSeconds": 35
  },
  "aspectRatio": "9:16",
  "voice":    { "enabled": true, "stability": 0.6, "speed": 1.0, "language": "en-US" },
  "captions": { "enabled": true, "position": "middle", "autoCrop": true },
  "music":    { "enabled": true, "syncWith": "beats" },
  "media": {
    "type": "stock-video",
    "density": "medium",
    "animation": "soft",
    "quality": "pro",
    "videoModel": "pro",
    "imageModel": "good"
  },
  "options": {
    "promptTargetDuration": 35,
    "summarizationPreference": "summarizeIfLong",
    "soundEffects": true,
    "hasToGenerateCover": true
  },
  "render": { "resolution": "1080p", "frameRate": 30 }
}
```

## Polling

Call `get_project_status` with the `pid` returned by `render_video`. Stop when
`data.status === "ready"`; fail when `data.status === "failed"`. Cadence:
5 s, then 8 s once `progress > 30`. Full pseudocode:
[`revid-api-foundations` § Polling](../revid-api-foundations/SKILL.md#polling).

## Examples

- [`examples/honey-prompt.json`](examples/honey-prompt.json) — copy-paste body
  for `render_video` *(also a valid POST body for the direct HTTPS fallback)*.
- [`examples/run.sh`](examples/run.sh) — bash smoke test using the direct HTTPS
  fallback (`POST /api/public/v3/render` → `GET /status`). Useful when you don't
  have an MCP client at hand.

## Failure modes

| Symptom | Fix |
|---|---|
| Script angle is generic ("Did you know…") | Add `source.stylePrompt` with a specific angle: `"Open with a contrarian claim. End with a question that invites comments."` |
| Off-niche visuals | Mention concrete subjects in the prompt: `"Why honey never spoils — show beehives, ancient Egyptian jars, microscope close-ups of crystallized honey."` |
| Too long / too short | Set `source.durationSeconds` AND `options.promptTargetDuration` together (some legacy paths only read one). |
| `ok: false`, `error: "insufficient_credits"` | Drop `media.quality` to `"standard"` or `render.resolution` to `"720p"`, or call `buy_credit_pack`. |

## See also

- [`revid-api-foundations`](../revid-api-foundations/SKILL.md) — auth, MCP install, response envelope.
- [`revid-script-to-video`](../revid-script-to-video/SKILL.md) when you have the words.
- [`revid-product-description-to-ad`](../revid-product-description-to-ad/SKILL.md) for ads.
