# Prompt crafting reference

Read this whenever a request needs a category, an output format, or the text-render protocol.

Classify the request into one category, read only that category's row, and compose the brief. This file covers category routing, format selection, cut splitting, and the text-render protocol. Vocabulary choice and deadword reduction live in `visual-direction.md`.

## Request categories

Read the request's signal words and pick exactly one category from the table. When two categories overlap, apply the boundary rule; after classification, load only that category's row. The canvas column is a ratio description only — actual ratio and size travel in the `canvas` optional key, never inside the prompt string.

| Category | Cut types | Default canvas | Required details | Signal words | Boundary |
| --- | --- | --- | --- | --- | --- |
| poster | full-frame single cut | portrait | headline wording, date and venue, subject object | poster, show, exhibition, event | single medium beats campaign |
| product | hero cut, detail cut | square or portrait | product form, material, surface reflection, background separation | product, package, merchandise, shot | skin expression as main goal routes to beauty |
| campaign | key visual, variation cuts | landscape | campaign message, target situation, brand motif | campaign, ad, promotion | multi-medium rollout beats poster |
| card news | card face, sequential cards | square | card order, per-card message, reading order | card news, SNS card | presentation use routes to slide |
| infographic | single chart cut | portrait | figures and item list, chart type, comparison axis | infographic, graph, chart, statistics | print or posting use beats slide |
| key art | main visual cut | landscape or portrait | world setting, protagonist placement, mood lighting | key art, main visual | world-building as main goal beats poster |
| editorial | figure cut, mood cut | portrait | model pose, garment texture, lighting concept | editorial, fashion cut | close-up skin or makeup routes to beauty |
| comic | panel cut, cover cut | portrait | line style, speech bubble or not, panel division | comic, webtoon, manga | plain illustration routes to its own category |
| slide | title cut, body cut | landscape | slide purpose, step count, text volume | slide, presentation, deck | on-screen presentation beats card news |
| branding | logo cut, application cut | square | brand character, symbol direction, applied media | branding, logo, identity | symbol rather than package beats product |
| 3d icon | single object cut | square | object form, material (matte or glossy), background | 3d icon, icon, rendered object | rendered object rather than photo beats product |
| beauty | close-up cut, texture cut | portrait | skin grain, makeup texture, lighting angle | beauty, makeup, cosmetics, skin | face or skin expression as main goal beats editorial |

## Edit categories

When the request edits a supplied image, pick exactly one edit category instead of a generation row. Every edit brief states `change only <X>; keep <Y> unchanged` and the preserve list from `rules/prompt-compilation.md`.

| Edit category | Change only | Always preserve |
| --- | --- | --- |
| text localization | the in-image wording | layout, typography, spacing, hierarchy; no reflow unless the new text needs it |
| identity preserve | the named clothing, setting, or prop | face, body, pose, hair, expression; matched light and shadow |
| precise object edit | the one named element removed or replaced | surrounding texture and lighting, everything else |
| lighting and weather | time of day, season, atmosphere, precipitation | geometry, framing, subject identity |
| background extraction | the background, cut to real transparency | a crisp silhouette with no halo, label text exactly, no restyling |
| style transfer | the subject or scene, rendered in the reference style | the named style cues (palette, texture, brushwork); no extra elements |
| compositing | the element moved from one indexed image into another | base framing; matched light, perspective, and scale |
| sketch to render | the medium, from line art to finished render | layout, proportions, perspective; no new elements |

## Format selection

- Format A (default): a simple request gets a natural prose brief. No labels.
- Format B (optional): named sections are allowed only for complex structured requests that stack text, charts, and objects in one frame (card news, infographic, poster).
- Format B rules: the allowed labels are exactly `subject`, `context`, `composition`, `lighting`, `style`, `text`. Each label appears exactly once, starts its line as `label:`, and no report prose (delivery notes, capability observations, paths) appears outside the labels or at the end of the brief.
- Either way, the compiled result is one ready-to-use brief.

## One row, one cut, one call

One request row is one cut and one generation call. Splitting several cuts onto one canvas (grid, artboard) is not the standard path. When several cuts are needed, split them into separate briefs and repeat the shared invariants (palette, lighting, type treatment, motif) in every brief.

## Canvas

State the requested shape as a ratio description and pass actual ratio and size only through the runtime's structured fields, never in the prompt string. When the runtime exposes no size field, say so in the report instead of inventing one. An edit normally keeps the source's ratio; when several images are supplied, name which one sets the output ratio, because some runtimes follow the last input. A runtime may return a different count or size than requested; report what came back.

## Text rendering

Rendered characters are quote-pinned inside the brief. The string inside quotes is exact: no translation, normalization, abbreviation, or added words.

- Area naming: divide the canvas into a 3×3 grid (top-middle-bottom × left-center-right) and place text by naming the area, e.g. "headline in the top-center area".
- Role labels: every rendered string gets a role — `headline`, `subhead`, `callout`, `caption`.
- Free-writing zone: scene description outside the quotes is free prose. Do not put non-rendered words inside quotes.
- Density lever: as text volume grows, prefer a portrait canvas orientation; for dense work consider the 2048 long side (carried via the `canvas` optional key).
- Chart breakthrough: for complex charts, try coordinate placement (assign each element a 3×3 area), arrow verbalization ("arrow from A to B"), and dual anchoring (position plus role), and retry in that order on failure.
- Post-generation lettering edits are forbidden. If a character is wrong, fix the brief and regenerate — no compositing or patching.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The eight edit categories and their change-only and preserve pairs | OpenAI `imagegen` skill, <https://github.com/openai/skills> (commit `e6afb0d`, file `.system/imagegen/references/prompting.md`) |
| An edit keeps the input ratio and follows the last image with several inputs | Google Developers Blog, 2025-08-28, <https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/> |
| The exact output count is not guaranteed | Gemini API image generation docs, <https://ai.google.dev/gemini-api/docs/image-generation> |
| The generation categories, format selection, and text-render protocol | this package's own rules |
