---
name: revid-blog-to-avatar-video
description: Turn a blog post URL into a talking-head avatar video — the avatar reads a summarized script of the post against a clean background. Use when the user wants a personal/expert delivery vs an edited promo. Calls the Revid MCP server (render_video → get_project_status).
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

# Blog post → talking-head avatar video

> Calls the **Revid MCP server** (`https://www.revid.ai/api/mcp`). Install once — see [`revid-api-foundations`](../revid-api-foundations/SKILL.md#install-the-revid-mcp-server).

Take any blog/article URL and produce a vertical (or square) talking-head video
with a chosen avatar reading a summarized version of the post.

## When to use this skill

- Source is a blog post / opinion piece / explainer with substantial body text.
- Output should feel like a *person delivering the take*, not an edited promo
  with stock b-roll.
- An avatar (image URL or `characterId`) is available, or the user accepts the
  default avatar.
- For an edited short with stock visuals, use
  [`revid-article-to-short`](../revid-article-to-short/SKILL.md) instead.

## Inputs

| Field | Required | Notes |
|---|---|---|
| `url` | yes | Blog post URL |
| `avatar.url` *or* `characterIds[]` | yes | The face. Either an image URL or a saved consistent character ID (see [character mgmt](#consistent-characters)). |
| `aspectRatio` | no | Default `9:16`. Use `1:1` for LinkedIn. |
| `voiceId` | no | Match it to the avatar's tone if known. |
| `targetDuration` | no | Default 60 (s) — talking heads can run longer. |

## Step-by-step

1. Validate the URL.
2. If the user gave an avatar image URL, set `avatar.url`. If they gave a saved
   character ID, set `characterIds: [id]` (and leave `avatar` omitted).
3. Call MCP tool `render_video` with the payload below — returns `data.pid`.
   Then poll MCP tool `get_project_status` with that `pid` every 5–8 s until
   `data.status === "ready"`. Optionally call `export_video` for a freshly
   named mp4.
4. Return `videoUrl`.

## `render_video` arguments

```json
{
  "workflow": "article-to-video",
  "source": {
    "url": "{BLOG_URL}",
    "scrapingPrompt": "Extract the article body. Skip header, navigation, related posts, and footer."
  },
  "aspectRatio": "9:16",
  "avatar": {
    "enabled": true,
    "url": "{AVATAR_IMAGE_URL}",
    "removeBackground": true,
    "imageModel": "good"
  },
  "voice": {
    "enabled": true,
    "voiceId": "aria-en-us",
    "stability": 0.65,
    "speed": 1.0,
    "language": "en-US",
    "enhanceAudio": true
  },
  "captions": { "enabled": true, "position": "bottom", "autoCrop": true },
  "music":    { "enabled": false },
  "media": {
    "type": "moving-image",
    "density": "low",
    "animation": "soft",
    "placeAvatarInContext": true
  },
  "options": {
    "targetDuration": 60,
    "summarizationPreference": "summarize",
    "hasToGenerateCover": true
  },
  "render": { "resolution": "1080p", "frameRate": 30 }
}
```

Notes:

- `placeAvatarInContext: true` composites the avatar over a relevant background
  (vs a plain green-screen feel).
- `media.density: "low"` keeps cuts minimal so the talking head can carry the
  video.
- `music.enabled: false` is the default — voice-driven content reads better
  without competing audio.

## Consistent characters

If the user wants the **same face** across many posts, create a character once
and reuse the ID:

1. Call `create_character` once:
   ```json
   { "name": "Maya", "description": "Friendly host in her thirties, short dark hair", "imageUrl": "https://cdn.example.com/maya.jpg" }
   ```
   It returns the character `id`.
2. Pass it in every `render_video` call:
   ```json
   { "characterIds": ["<id>"], "avatar": { "enabled": true } }
   ```

List existing characters with `list_characters`.

## Examples

- [`examples/blog-to-avatar.json`](examples/blog-to-avatar.json) — copy-paste
  body for `render_video` *(also a valid POST body for the direct HTTPS
  fallback)*.
- [`examples/run.sh`](examples/run.sh) — bash smoke test using the **direct
  HTTPS fallback** (`POST /api/public/v3/render` → `GET /status`). Useful when
  you don't have an MCP client at hand.

## Polling

Call `get_project_status` with the `pid` returned by `render_video`. Stop when
`data.status === "ready"`; fail when `data.status === "failed"`. Cadence: 5 s,
then 8 s once `progress > 30`. Full pseudocode:
[`revid-api-foundations` § Polling](../revid-api-foundations/SKILL.md#polling).

## Failure modes

| Symptom | Fix |
|---|---|
| Avatar lip-sync drifts on long copy | Lower `targetDuration` to 45 s, or switch `summarizationPreference: "summarize"` (already on). |
| Avatar background bleeds into video | Set `avatar.removeBackground: true` (default). For stubborn cases, pre-process the avatar image to a transparent PNG. |
| Background visuals distract from face | `media.density: "low"` and `media.animation: "soft"` (already on). For pure plain background, set `media.type: "custom"` + `media.useOnlyProvided: true` with a single neutral asset. |
| Voice doesn't match the avatar | Set `voice.voiceId` explicitly. The default voice is gendered female English — always override for other languages or personas. |
| `scrape failed` | Same as in [`revid-article-to-short`](../revid-article-to-short/SKILL.md): pre-scrape the post and switch to `script-to-video` with the avatar block intact. |
| `ok: false`, `error: "insufficient_credits"` | Drop `media.quality` to `"standard"` or `render.resolution` to `"720p"`, or call `buy_credit_pack`. |

## See also

- [`revid-article-to-short`](../revid-article-to-short/SKILL.md) — same input,
  edited-short output.
- [`revid-tweet-to-talking-head`](../revid-tweet-to-talking-head/SKILL.md) —
  shorter form of the same talking-head pattern.
- [`revid-api-foundations`](../revid-api-foundations/SKILL.md).
