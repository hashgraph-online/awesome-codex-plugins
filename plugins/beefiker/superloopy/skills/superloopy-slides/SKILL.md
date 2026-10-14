---
name: superloopy-slides
description: >-
  Use when the user asks to create, convert, style, animate, export, share, or
  deploy HTML slide decks, presentations, pitch decks, talks, or keynotes;
  including zero-dependency or single-file output, PowerPoint/PPT/PPTX input,
  PDF export, browser delivery, visual style exploration, or "loopy slides".
  Not for general web pages or landing pages.
---

# Superloopy Slides

Create zero-dependency, animation-rich HTML presentations that run entirely in the browser.

> **Live example** — a multilingual deck built with this skill: <https://fileloom-slides.pages.dev> (English · 한국어 · 中文 · 日本語 · Español; single-file, embed-safe, on a fixed 16:9 stage).

This is a Superloopy skill: the deck is done only when a real-browser visual artifact proves it renders correctly — never when the HTML "looks complete" in source. Completion requires an artifact under the active evidence root via `SUPERLOOPY_EVIDENCE`.

## Activation

Open your reply with `SUPERLOOPY SLIDES ENABLED`. If another active Superloopy mode mandates its own first line, print that first and this marker on the next line.

The anti-slop design rules below are this skill's own instance of the `superloopy-frontend` [anti-slop contract](../superloopy-frontend/references/anti-slop.md), specialized for the fixed 1920×1080 slide stage. A presentation is campaign/editorial surface, so that contract's non-waivable core binds every deck: honest assets (no div-mock passed off as a product capture, no unauthorized marks, no invented metrics or testimonials), no shipped placeholder names/brands/filler copy, and a named authority for every kept default or waived check. Do not open a second superloopy-frontend pass on top of a deck — this skill owns the visual layer for presentations, including the evidence gate.

## Core Principles

1. **Zero Dependencies** — Single HTML files with inline CSS/JS. No npm, no build tools.
2. **Show, Don't Tell** — Generate visual previews, not abstract choices. People discover what they want by seeing it.
3. **Distinctive Design** — No generic "AI slop." Every presentation must feel custom-crafted.
4. **Progressive Disclosure** — Read lightweight style indexes first. For bold templates, use small preview cards for style previews and load the full `design.md` only after the user picks that template.
5. **Fixed 16:9 Stage (NON-NEGOTIABLE)** — Every deck uses a 1920×1080 slide canvas scaled as a whole to the viewport. Slides must stay 16:9 on every screen, including phones. Do not reflow slide content to fit the device.

## Design Aesthetics

You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight.

Focus on:

- Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.
- Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.
- Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.
- Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Avoid generic AI-generated aesthetics:

- Overused font families (Inter, Roboto, Arial, system fonts)
- Cliched color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!

## Fixed Stage Rules

These invariants apply to EVERY slide in EVERY presentation:

- Every deck has a viewport wrapper that fills the browser window.
- Every slide is authored inside a fixed 1920×1080 stage.
- The stage scales uniformly to fit the viewport. It may letterbox/pillarbox; it must not re-layout content.
- Do not use responsive breakpoints to rearrange slide content for phones.
- Use fixed internal slide measurements at the 1920×1080 design size.
- **Embed-safe + standalone-safe (NON-NEGOTIABLE)** — every deck must render correctly BOTH opened directly AND inside an iframe (Confluence "Advanced HTML & Iframe Embed" macro, Notion, etc.). Use the dual-mode scaler from `html-template.md`: detect iframes (`window.self !== window.top` in try/catch), add `.embed` to `<html>`, scale by width only in embed mode, and set `window.frameElement.style.height` in a try/catch for same-origin hosts. Never `position:fixed` for the viewport or chrome; never rely on `vh`/`%` heights in embed mode — an auto-height iframe computes them as ~0 and locks the collapsed height in.
- Keep ALL presentation chrome (controls, counter, progress, nav dots) inside `.deck-stage`, after the slides, sized for the 1920×1080 canvas — chrome outside the stage does not scale in iframes and overlaps content when the deck shrinks.
- Slide visibility must be controlled by `.active` / `.visible` using `visibility`, `opacity`, and `pointer-events` from `viewport-base.css`. Do not use `display: none` / `display: block` for slide switching; later layout classes such as `.slide-content { display: flex; }` can override them and make every slide visible at once.
- Use `clamp()` only for non-slide UI outside the stage, or for small fallback previews where a full stage is impractical.
- Include `prefers-reduced-motion` support
- Never negate CSS functions directly (`-clamp()`, `-min()`, `-max()` are silently ignored) — use `calc(-1 * clamp(...))` instead

**When generating, read `viewport-base.css` and include its full contents in every presentation.**

### Content Density Modes

Ask the user whether this is primarily a reading deck or a speaking deck, then design around that answer:

| Density mode | Best for | Design behavior |
| ------------- | -------- | --------------- |
| **Low density / speaker-led** | Public talks, keynote-style sharing, live explanation | One idea per slide, large type, strong visual hierarchy, generous negative space, 1-3 bullets max, more slides if needed |
| **High density / reading-first** | Reports, handouts, async review, detailed internal docs | More self-contained slides, structured grids/tables/annotations, 4-8 bullets or 4-6 cards when readable, tighter but still intentional spacing |

Baseline limits still apply: no scrolling, no overflow, no overlapping panels, and no text below comfortable reading size. If content exceeds the selected density mode, split it into more slides instead of shrinking until it becomes cramped.

---

## Phase 0: Detect Mode

Determine what the user wants:

- **Mode A: New Presentation** — Create from scratch. Go to Phase 1.
- **Mode B: PPT Conversion** — Convert a .pptx file. Go to Phase 4.
- **Mode C: Enhancement** — Improve an existing HTML presentation. Read it, understand it, enhance. **Follow the Mode C modification rules in [Enhancement](references/enhancement.md).**

---

## Phase 1: Content Discovery (New Presentations)

Ask the Phase 1 questions and run the Step 1.2 image evaluation exactly as [Content discovery](references/content-discovery.md) specifies.

---

## Phase 2: Style Discovery

**This is the "show, don't tell" phase.** Most people can't articulate design preferences in words.

### Step 2.0: Generate 3 Style Previews Directly

Based on purpose, audience, mood, and content density, generate 3 distinct single-slide HTML previews showing typography, colors, animation, and overall aesthetic.

Do not ask the user whether they want options or a preset picker. The default discovery experience is always visual comparison.

If the user already gave a vibe, use it. If they did not, infer the likely mood from the occasion, audience, content, and stakes. Keep the options diverse enough that the user can react visually instead of needing to articulate taste up front.

If the user explicitly names a preset or bold template, honor that as one option and generate the remaining preview slots around it.

Read [STYLE_PRESETS.md](STYLE_PRESETS.md) for safe preset candidates. If [bold-template-pack/selection-index.json](bold-template-pack/selection-index.json) exists, read that compact index too, but do not read any `design.md` files yet.

**Brand-named direction (StyleGallery):** when the user names a specific brand — directly or as a mood reference ("Stripe 느낌", "Linear처럼", "like Notion") — consult the frontend skill's brand library index at [`design/_INDEX.md`](../superloopy-frontend/references/design/_INDEX.md), pick ONE matching teardown, and derive one preview slot's tokens from it — palette, type scale and weight attitude, radius, and motion tone — translated into 1920×1080 stage proportions. Inherit that library's contract: a teardown is scoped reference input, never automatic token authority; use public brand facts only, never clone a logo or trade dress, and name the teardown file in your message (and later in `VISUAL_QA.md`) as the provenance of that direction. Without a user-named brand or mood, do not open the gallery — the preset/bold-template mix below stays the default.

Apply the mood table, preview mix rules, custom wildcard design rules, bold template selection rules, and the NON-NEGOTIABLE preview authenticity rules in [Style discovery](references/style-discovery.md) before generating any preview.

### Step 2.1: User Picks

Ask (header: "Style"):
Which style preview do you prefer? Options: Style A: [Name] / Style B: [Name] / Style C: [Name] / Mix elements

If "Mix elements", ask for specifics.

**The style choice belongs to the user — do not skip it.** The three-preview comparison is the core of this skill. If the structured question times out (the harness gives up after a short wait), do NOT proceed with a default style: re-ask the question, and if it times out again, stop and wait for the user's reply in plain text. Only pick a style yourself when the user has explicitly delegated the choice ("you pick", "surprise me") or asked for a fully unattended run.

---

## Phase 3: Generate Presentation

Generate the full deck following [Generation](references/generation.md): density application, the selected bold template or custom wildcard recipe, the supporting files to read first, and the key requirements.

---

## Phase 4: PPT Conversion

Convert PowerPoint input following the PPT conversion steps in [Generation](references/generation.md).

---

## Phase 5: Visual-QA Evidence Gate + Delivery

A deck that parses is not verified. Before declaring done, capture real-browser evidence under `.superloopy/evidence/slides/<timestamp>-<slug>/`. Create and verify that run root with the frontend skill's portable helper so path rules stay identical across skills — `node "$SKILL_DIR/../superloopy-frontend/scripts/evidence-root.mjs" create <slug> slides` to create it (`$SKILL_DIR` is this skill's base directory, announced when the skill loads, and `superloopy-frontend` is packaged as its sibling), and `... verify <root> <file...>` to prove each artifact is a non-empty regular file confined beneath it:

1. **Screenshot representative slides** — title slide, one content-heavy slide, and any slide with a complex layout (grid, table, image composition), rendered headless at 1280×720. Also capture one narrow viewport (e.g. 390×844) to prove the stage letterboxes instead of reflowing.
2. **Prove embed mode** — write a throwaway harness page with the deck in an iframe at a collapsed initial height (e.g. `width="900" height="60"`), serve the directory over local HTTP (`python3 -m http.server`; `file://` iframes are opaque-origin and skip the same-origin resize path), and screenshot it: the deck must grow the iframe to 16:9 of its width with no overlap and with chrome scaled. Delete the harness after capture or keep it in the evidence directory.
3. **Inspect every screenshot** — no text overflow, no overlapping panels, stage stays 16:9, fonts actually loaded (not fallback serif). `scrollHeight` checks alone are not enough; grid panels can visually cover each other.
4. **Write `VISUAL_QA.md`** in the evidence directory listing each screenshot, what it proves, and any finding fixed. An open finding is a FAIL — fix and re-capture. Also record the non-waivable core check (assets honest, no placeholder names/brands/filler copy shipped) and, when a StyleGallery teardown informed the style, name that teardown file as provenance.
5. **Record the evidence** — end completed deck work with a Superloopy record, e.g. `superloopy loop evidence --status pass --artifact .superloopy/evidence/slides/<slug>/VISUAL_QA.md --notes "<deck, style, slide count>"`, and end the reply with `SUPERLOOPY_EVIDENCE: <that path>`.

Then deliver:

1. **Clean up** — Delete `.slides/previews/` if it exists
2. **Open** — Use `open [filename].html` to launch in browser
3. **Summarize** — Tell the user:
   - File location, style name, slide count
   - Navigation: Arrow keys, Space, swipe/tap if enabled
   - The deck is embed-safe: paste it into Confluence's "Advanced HTML & Iframe Embed" macro (width Wide/Full, height ≈ width × 0.5625, verify on the published page) or any iframe. If a macro blocks `<script>`, host the file (attachment URL, internal static hosting, or Vercel) and embed by URL: `<iframe src="…" style="width:100%;aspect-ratio:16/9;border:0" allowfullscreen>`
   - How to customize: `:root` CSS variables for colors, font link for typography, `.reveal` class for animations
   - Inline text editing is available: Hover top-left corner or press E to enter edit mode, click any text to edit, Ctrl+S to save
   - Offer the natural post-draft actions: ask for revisions, edit text directly in the browser, or export/share

---

## Phase 6: Share & Export (Optional)

After delivery, offer sharing and follow [Share and export](references/share-export.md) for the Vercel deploy and PDF export procedures and their gotchas.

---

## Supporting Files

| File                                               | Purpose                                                              | When to Read              |
| -------------------------------------------------- | -------------------------------------------------------------------- | ------------------------- |
| [references/enhancement.md](references/enhancement.md) | Mode C modification rules for enhancing an existing deck | Phase 0, Mode C |
| [references/content-discovery.md](references/content-discovery.md) | Phase 1 questions and the Step 1.2 image evaluation, which classifies asset authority the way [`image-first.md`](../superloopy-frontend/references/image-first.md) does | Phase 1 (new presentations) |
| [references/style-discovery.md](references/style-discovery.md) | Mood table, preview mix, custom wildcard, bold template selection, and preview authenticity rules | Phase 2, before generating previews |
| [references/generation.md](references/generation.md) | Density application, template or wildcard recipe, required supporting files, key requirements, and PPT conversion | Phase 3 (generation) and Phase 4 (conversion) |
| [references/share-export.md](references/share-export.md) | Vercel deploy and PDF export procedures and gotchas | Phase 6 (sharing) |
| [STYLE_PRESETS.md](STYLE_PRESETS.md)               | 12 curated visual presets with colors, fonts, and signature elements | Phase 2 (style selection) |
| [bold-template-pack/selection-index.json](bold-template-pack/selection-index.json) | Compact bold template metadata for candidate selection | Phase 2 (style selection) |
| [bold-template-pack/templates/*/preview.md](bold-template-pack/templates/) | Lightweight style cards for shortlisted bold title previews | Phase 2 after shortlisting |
| [bold-template-pack/templates/*/design.md](bold-template-pack/templates/) | Detailed design-system docs for the selected bold template only | Phase 3 after user selection |
| [viewport-base.css](viewport-base.css)             | Mandatory fixed-stage CSS — copy into every presentation             | Phase 3 (generation)      |
| [html-template.md](html-template.md)               | HTML structure, JS features, code quality standards                  | Phase 3 (generation)      |
| [animation-patterns.md](animation-patterns.md)     | CSS/JS animation snippets and effect-to-feeling guide; follows the shared motion floor ([`motion-core.md`](../superloopy-frontend/references/motion-core.md)) | Phase 3 (generation)      |
| [scripts/extract-pptx.py](scripts/extract-pptx.py) | Python script for PPT content extraction                             | Phase 4 (conversion)      |
| [scripts/deploy.sh](scripts/deploy.sh)             | Deploy slides to Vercel for instant sharing                          | Phase 6 (sharing)         |
| [scripts/export-pdf.sh](scripts/export-pdf.sh)     | Export slides to PDF                                                 | Phase 6 (sharing)         |

---

Adapted from [frontend-slides](https://github.com/zarazhangrui/frontend-slides) by Zara Zhang (MIT, see [LICENSE](LICENSE)); Superloopy evidence-spine integration added.
