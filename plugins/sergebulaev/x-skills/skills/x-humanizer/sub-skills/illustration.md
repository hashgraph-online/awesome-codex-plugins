# Sub-skill: Generate an illustration for a X (Twitter) post

Adds an optional image to a draft (feed image, square art, or quote-card) and
attaches it on publish. Uses the Pixfaro image layer through `lib.illustrate`,
which returns a hosted URL that flows straight into Publora media. Runs on any
agent (Claude Code, Codex, OpenClaw).

## When this runs

- User says "add an image", "make an illustration", "make a quote-card", or
  "make a image" for a X (Twitter) post.
- Offer it once after a draft is approved, when a visual would lift reach.

## Backends (mirrors the publish layer)

- **pixfaro** - `PIXFARO_TOKEN` (`pf_live_...`) set: image generated + attached
  automatically.
- **manual** - no token: the skill drafts the image prompt and asks the user to
  generate it and paste the URL. Never blocks a draft.

`lib.image_backend()` reports which is active.

## Steps

1. **Pick the kind.** Default for X (Twitter) is `square` (aspect 1:1). Override
   with `aspect_ratio="w:h"` when needed. Other kinds: thumbnail 16:9, carousel/
   quote/portrait 4:5, story/cover 9:16, wide/link 1200:628, square 1:1.
2. **Craft the prompt.** Describe subject, composition, style, palette. Default
   to a clean professional look unless Voice & Brand Profile §6 sets a visual
   style. Do NOT bake the post's words into the art (use overlay).
3. **Apply brand overlay (if profile has it).** Read `../../references/voice-profile.md`
   §6. If a handle, brand color, or logo is set, pass an `overlay` so text/logo is
   composited pixel-exact (crisp even on a cheap model):
   ```python
   from lib import illustrate
   r = illustrate("<scene prompt>", kind="square",
                  overlay={"text": "@handle", "position": "bottom-right", "color": "#RRGGBB"})
   ```
   For a **quote-card**, put the pulled hook line in overlay `text` (not the prompt),
   `kind="quote"`.
4. **Model choice.** Default `gemini-flash-lite`. The overlay handles text, so a cheap base
   model is fine; only reach for gemini-pro-image on premium art. Never silently
   upgrade the tier.
5. **Show + confirm.** Present the returned `url` and `cost`. On approval, attach
   via `media_urls=[r["url"]]` when publishing.
6. **Manual mode.** If `r["backend"] == "manual"`, show `r["message"]` and ask for
   a pasted URL.

## Refine instead of regenerating

When the user wants a tweak ("make the sky darker", "swap the headline", "more
whitespace"), do NOT regenerate from scratch. Keep the `id` from the previous
result and edit it:

```python
from lib import illustrate, refine
first = illustrate("<scene>", kind="wide")     # -> {"id": "img_...", "url": ...}
fixed = refine(first["id"], "make the background darker and increase contrast")
```

`refine` edits by `img_...` id (not URL), inherits the source shape/tier when you
omit `aspect_ratio`/`resolution`, and is cheaper + more consistent than a fresh
generation. Chain it as many times as needed.

## Cost-guard

- Each result carries `cost` and `balance_after`; if `low_balance` is True, tell
  the user the Pixfaro balance is low before generating more.
- Default to `nano-banana-2` + 1K. The premium models (`gemini-pro-image`,
  `gpt-5-image`) bill several times more - only use them when the user asks by
  name; `illustrate`/`refine` never upgrade on their own.
  A result's `premium`
  flag is True when a premium-priced model was used - confirm that was intended.
- `lib.available_models()` returns live pricing/latency when you need to show it.

## Hard rules

- One image per request (`n>1` unsupported); generate carousel slides one at a time.
- Keep real words in the `overlay`, not baked into the prompt art.
- Default to the cheap model + 1K resolution unless the user asks for premium.
- Never attach an image the user has not seen and approved.
