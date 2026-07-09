# Screenshot Creation

Create one approved screenshot prompt per panel, then call `generate_screenshot`
once per panel. The hosted MCP instructions handle setup, billing, polling, and
review URLs.

## Inputs To Lock

- Target app identity: app name, what it does, target platform, and App Store URL
  if published.
- Audience and positioning: who should install, what pain they feel, and what
  outcome the app promises.
- Real UI references: at least one uploaded app screenshot, reference image
  showing actual UI, or imported App Store screenshot.
- Optional inspiration: public gallery screenshots from another app, used only
  for style, composition, color, typography, and pacing.

Do not generate from only an icon, brand colors, or written app description.
Apple requires screenshots to show real app usage, and invented UI risks a weak
or unusable result.

Infer facts from local files, saved app records, imported App Store metadata,
and existing media first. Ask the user when a missing detail is about intent or
taste rather than repo truth: audience, positioning, visual direction, which UI
flow matters, or whether a proposed inspiration source is acceptable.

If the user wants a small targeted change to an existing generated screenshot,
use `screenshots.revise` instead of starting a new `generate_screenshot` job.
Examples: adjust headline size, improve contrast, move the device, remove a
visual artifact, or make the current screenshot closer to an existing reference.

## Pre-Generation Checks

- Load the app with `apps.get`.
- If no real UI reference exists, search the local repo for screenshots,
  fastlane screenshots, preview images, docs images, or product mockups. Upload
  good candidates with the helper using `--kind app_screenshot`.
- If the user provides local image paths, clipboard images saved to disk, or you
  discover useful local screenshots yourself, upload them before generation. The
  image model only receives references through Shots media IDs; local file paths
  in the prompt are not enough. Use `--kind app_screenshot` for real product UI,
  `--kind reference` for product/brand assets, and `--kind inspo` for mood-only
  references.
- Before planning new English screenshots, check `screenshots.listing` for
  selected/promoted `en-US` store screenshots. Use relevant selected/promoted
  screenshots as default continuity/product references. Do not use recent
  unpromoted generations as image references unless the user selects them or
  asks to continue from them.
- If the user gives another App Store URL as inspiration, use
  `gallery.ensure_app` and `gallery.get_app`; do not import it as the user's app
  unless they explicitly say it is theirs.
- A vague request for a "new style" or "different style" is not permission to
  pick a gallery inspiration app. Define the style in the prompt, or ask for /
  get approval on the exact gallery source first.
- If the user has not described the new style, ask for preferences or present
  2-4 concrete style directions before writing the approval table.

## Strategy Snapshot

Before writing panels, summarize and save:

- one-line positioning
- target audience
- visual direction and palette
- 3-5 market-native words
- available critical screens
- mapping of uploaded media IDs to screens
- selected/promoted English campaign screenshots used for product/campaign continuity
- public gallery inspiration ids, if used

Store durable findings with `apps.update_research` so Studio and future agents
share the same context.

## Screenshot Plan

Show a table and wait for approval before generation.

```markdown
| # | Panel type | Visible text | Image/UI direction | Reference assets | Purpose |
| --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |
```

Planning rules:

- Honor an explicit screenshot count exactly.
- During first-time setup only, suggest 3 screenshots when the user wants
  screenshots but gives no count.
- Match the panel type to the app and references: text-free object hero,
  poster-style headline, device UI proof, editorial collage, feature grid,
  founder/testimonial, or full-bleed product scene.
- Headline first when the panel uses copy: 3-6 word benefit, relief, identity,
  curiosity, or transformation promise.
- No-copy panels are valid when the reference and concept are visual-first.
- Avoid feature labels like "AI Dashboard" unless the user asks for literal
  feature naming.
- Each row needs a specific UI moment, object, scene, collage, or proof point,
  not generic "show the app" direction.
- The `Reference assets` column must name the uploaded media IDs for the real UI
  reference and any style reference used by that row, plus any public inspiration
  reference. If a useful reference is still only a local file, upload it before
  approval or mark the row blocked until upload succeeds.
- If a row uses public gallery inspiration, name the inspiration app and
  screenshot explicitly. Do not hide it behind a generic "style reference" label.

If context is thin, propose 5-10 candidate panel concepts and ask which ones to
generate.

## Generate

For each approved row:

- Build a complete plain-text prompt using [prompting.md](prompting.md).
- Pass only the uploaded references that row actually needs, up to the server's
  max. `referenceMediaIds` must be Shots media IDs, not local paths or CDN URLs
  mentioned only in the prompt.
- Include `galleryInspirationScreenshotId` only when that row uses public
  gallery inspiration approved by the user. Gallery inspiration is style-only
  and still costs 3 generation credits. Keep gallery-inspiration generation on
  medium quality.
- Use selected/promoted English campaign screenshots for product and campaign
  continuity, not old copy. Avoid unpromoted generations unless the user picked
  them.

Prompt example:

```text
Create one App Store screenshot for "MyApp".

Campaign job: hero benefit for busy parents planning meals.
Visible text: "Know Dinner by 5" and smaller subtitle "Plans that adapt when life changes".

Composition: warm olive-to-cream background. Large headline at top. Center an
iPhone 16 Pro below with a weekly meal plan screen: Monday selected, three
recipe cards, pantry match badges, and a yellow Swap Dinner button. Add one
small pantry card breakout on the right reading "Use tonight" with tomato,
pasta, and basil icons.

Reference usage:
- Reference 1: real app UI layout and meal card hierarchy.
- Reference 2: existing campaign palette and typography scale.

Avoid App Store badges, fake chrome, clipped text, and fictional UI unrelated
to the references.
```

Call `generate_screenshot` with the app id, platform, this prompt text, the
approved reference ids, and the gallery inspiration id only if the panel uses
one.

After jobs complete, present screenshot ids, CDN URLs, and the returned review
URL when available. In Codex or another browser-capable client, open the review
URL automatically after all approved generation jobs complete. If the user
approves final winners for the store listing, call `screenshots.promote` once
per screenshot with only its `mediaId`. Use `screenshots.unpromote` with the
same `mediaId` to remove a promoted screenshot. Do not pass app, locale, or
platform to those commands; Shots derives the listing slot from the screenshot
media record.

If generation repeatedly produces clipped text, wrong product UI, broken layout,
or other quality issues after multiple attempts, call `feedback.report` with
`category: "quality_issue"` and include related `mediaId` or `jobId` when
available.
