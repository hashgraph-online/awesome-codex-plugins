---
name: codex2course
description: Use when creating course handouts, lecture notes, workshops, tutorials, PPT-like course slides, visual lecture materials, or course PDF decks from a topic, outline, handout, or existing course package.
---

# Codex2Course

## Overview

Create a course package from a topic or outline: detailed teaching handouts first, then slide units, then one Imagegen-generated raster image per slide, then a PDF assembled from those images. The core rule is that slides are generated image pages, not `.pptx`, HTML, Markdown, SVG, canvas, screenshot, or locally rendered pages.

**REQUIRED SUB-SKILL:** Use `imagegen` for every generated slide page, cover image, visual metaphor, diagram-like bitmap, or style variant.

## Non-Negotiable Output Routing

When this skill is active, `imagegen` is the only route for producing slide visuals.

Allowed local scripts:
- `scripts/split_handout.py` may derive `slide-units/` from `handout.md`.
- `scripts/images2pdf.py` may assemble existing `slides/*.png` files into a PDF.

Forbidden substitutes for slide image generation:
- Creating `.pptx` decks with PowerPoint, LibreOffice, Keynote, or `python-pptx`
- Rendering Marp, reveal.js, HTML/CSS, Markdown, SVG, canvas, screenshots, browser pages, or notebook output into slide images
- Drawing slide pages with Pillow, matplotlib, reportlab, Mermaid, Graphviz, or other deterministic local renderers
- Generating placeholders, templates, or code-native diagrams instead of final Imagegen slide images

If `imagegen` is unavailable, blocked, or unsuitable for a requested slide deck, stop and tell the user that this skill cannot produce the visual deck through its required path. Do not silently fall back to local PPT/rendering workflows unless the user explicitly changes the requirement to an editable `.pptx` or a deterministic locally rendered deck.

## When to Use

Use this skill for:
- Course handouts, lecture notes, tutorials, workshops, training materials
- Turning an outline into teachable content and visual slide pages
- Producing "PPT" as page images combined into a PDF
- Regenerating individual unsatisfactory pages from revised slide units

Do not use this skill when the user specifically needs editable `.pptx`; use `pptx` instead.

If the user says "PPT", "slides", "deck", or "课件" without explicitly asking for an editable `.pptx` file, treat the request as an image-page course deck and follow this skill's Imagegen path.

## Workflow

Each stage below is independently invocable. Inspect what artifacts already exist (`outline.md`, `handout.md`, `slide-units/`, `slides/`) and start at the next missing stage — do not redo work the user already approved.

All output (handout text, on-slide text, image text) must match the language of the user's input.

1. **Identify entry point, confirm input state, and preflight Git ownership.** Accept a course topic, rough outline, existing handout, finalized slide units, or a generated deck that needs targeted regeneration. If you will need to write or extend `outline.md`, also gather any missing metadata up front: instructor, institution, target audience, course goal, art style preference (ask the user for whatever is missing). If the output directory is inside a Git repository, inspect the target paths before writing (`outline.md`, `handout.md`, `slide-units/`, `slides/`, final PDF path). Treat files or directories that already exist or are already tracked as pre-existing repository content unless the user explicitly says Codex2Course owns them. Do not overwrite, hide, or add ignore rules for pre-existing content by default; choose a fresh course subdirectory or ask the user how to proceed if there is a collision.
2. **Generate or refine the outline.** Use the structured template in the Outline Template section below — three required sections: `## Course Info` (cover-slide source), `## Outline` (drives handout writing), `## Image Generation Settings` (imagegen prefix source). Organize the outline body by dependency, teaching rhythm, and difficulty. Ask for confirmation before writing full content unless the user asked for a full draft in one pass.
3. **Write the handout.** Produce knowledge-point explanations that are detailed enough for learning but not a word-for-word script. Prioritize logic, terminology, examples, and order.
4. **STOP for human revision.** Output the handout and explicitly ask the user to review and approve it. Do not proceed to slide units until the user confirms. Encourage edits to content logic, terminology, emphasis, and teaching sequence.
5. **Annotate handout with slide markers, then materialize slide units.** Insert `<!-- slide: 标题 -->` markers at the points in `handout.md` where each slide should begin (see Slide Marker Convention below). This is the key human decision in this stage — present the resulting slide list to the user for review before moving on. Then run `python scripts/split_handout.py course/handout.md` to mechanically materialize `course/slide-units/NNN-slug.md`. The script is the single way to produce slide-units; never hand-author or hand-edit those files. If `handout.md` is later edited, rerun the script to refresh `slide-units/` before regenerating any image.
6. **Generate slide images with `imagegen` only.** Before generating the first slide image, load the `imagegen` skill and use its built-in tool path unless the user explicitly selected its CLI fallback. Reuse the course-level prefix from `outline.md`'s `## Image Generation Settings` verbatim for every imagegen call. Do not create a local-rendered intermediate deck or screenshot source. Generate three groups in this order:
   - **Cover** → `slides/000-cover.png`. Content payload built from `## Course Info` (course title from `outline.md`'s H1, instructor, institution, target audience as a tone cue), with an explicit instruction that this is the deck's cover.
   - **Content** → `slides/NNN-slug.png`, mirroring `slide-units/` filenames 1:1. For each slide-unit file, payload is the file's verbatim content.
   - **Ending** → `slides/zzz-ending.png`. Short closing slide (e.g., "谢谢 / Q&A" in the course language). Custom ending text can be added by the user in `## Image Generation Settings`.
   - If the full deck has more than 10 images (cover + content + ending), use the Sequential Sub-Agent Batching protocol below for content slides. Generate cover and ending slides separately because their layouts intentionally differ from normal content slides.
7. **Run a generated-image consistency audit before review or PDF assembly.** After all slides (cover + content + ending) exist, inspect every generated image and compare it against its payload source. For content slides, compare `slides/NNN-slug.png` with `slide-units/NNN-slug.md`; for the cover, compare `slides/000-cover.png` with the H1 and `## Course Info`; for the ending, compare `slides/zzz-ending.png` with the configured ending text. Check that the visible title, topic, core terms, examples, code/domain objects, and visual metaphor match the source. Also check that the slide has not drifted into an unrelated topic, reused a previous deck's content, or mixed in foreign examples such as scheduling, algorithms, business charts, or unrelated activities.

   If any generated image is semantically inconsistent with its payload, treat it as a generation failure, not as user review feedback: immediately regenerate only that image with `imagegen`, using the same course-level prefix and the same original payload, plus a short correction note that names the mismatch to avoid. Replace the same `slides/` filename, then re-inspect it. Do not assemble the PDF until this audit passes. If the slide is visually acceptable but has small text inaccuracies that do not change the lesson meaning, note the residual issue for user review rather than silently rewriting source content.

8. **Batch review, then targeted regeneration.** After all slides (cover + content + ending) are generated and have passed the consistency audit, present the deck to the user for review in one pass. The user identifies which specific slides need changes and provides per-slide revision feedback. Regenerate only those slides, one at a time, by re-running `imagegen` with the same prefix + payload plus the user's revision note appended. Overwrite the same `slides/` filename so PDF assembly picks up the latest version. Never regenerate a slide without an explicit per-slide instruction from the user, except for self-correcting failed images during the consistency audit in step 7. If the user's feedback is actually about content (not visuals) for a content slide, edit `handout.md` and rerun the split script first; for cover/ending content fixes, edit `outline.md`.
9. **Assemble PDF from Imagegen outputs and keep only the PDF commit-ready.** Run `scripts/images2pdf.py` to combine the existing Imagegen-created slide images in filename order into a single PDF. This script is only an assembler; it must not replace or create slide visuals:

   ```bash
   python scripts/images2pdf.py course/slides
   ```

   The script sorts images alphabetically (`000-cover.png` → content slides → `zzz-ending.png`), so page order is always correct. Requires Pillow (`pip install Pillow`). When the output path is omitted, the script reads the H1 of `<slides-dir>/../outline.md` (stripping a leading `课程标题:` / `Course:` prefix) and writes `<slides-dir>/../<course title>.pdf`; it falls back to `course-deck.pdf` only when no usable title is found. Pass an explicit second argument to override.

   If the course package lives inside a Git repository, update that repository's `.gitignore` using the Repository Hygiene rules below before committing or publishing anything. Verify that generated intermediates are ignored and the final PDF is still visible to Git.

## Output Structure

Prefer this structure unless the user provides another destination:

```text
course/
├── outline.md          # 3 sections: Course Info, Outline, Image Generation Settings
├── handout.md          # source of truth, contains <!-- slide: ... --> markers
├── slide-units/        # DERIVED from handout.md by scripts/split_handout.py — never hand-edit
│   ├── 001-title.md
│   ├── 002-topic.md
│   └── ...
├── slides/             # Imagegen-created cover + content (mirrors slide-units/ 1:1) + ending
│   ├── 000-cover.png
│   ├── 001-title.png
│   ├── 002-topic.png
│   ├── ...
│   └── zzz-ending.png
└── <course-title>.pdf   # filename derived from outline.md's H1
```

## Repository Hygiene

When generating a course package inside any Git repository, keep only Codex2Course-created intermediate artifacts local. Commit the final PDF deliverable and any `.gitignore` change needed to hide those generated intermediates. Never hide unrelated files that were already part of the target repository.

Definition:

- A Codex2Course-generated intermediate is a path this skill created during the current run, or a path the user explicitly identifies as prior Codex2Course output.
- Pre-existing repository content includes anything that existed before the current run or is already tracked by Git, even if its name is `outline.md`, `handout.md`, `slide-units/`, or `slides/`.

Rules:

- Update the `.gitignore` in the target repository where the course content is being generated. Do not modify this skills repository's `.gitignore` unless it is actually the target output repo.
- Before adding ignore rules, check candidate paths with Git and the filesystem, for example `git ls-files -- <path>` plus a normal existence check. If a candidate path already existed or is tracked, do not ignore it unless the user explicitly confirms it is Codex2Course output that should stay local.
- Add ignore rules only for the exact generated intermediate paths that Codex2Course created or owns. Do not blindly ignore every `outline.md`, `handout.md`, `slide-units/`, or `slides/` path just because those names appear in the output structure.
- Use path-scoped ignore rules for the actual generated paths. Do not add broad rules like `**/slides/` or `**/outline.md` unless the user explicitly wants those ignored across the whole repo.
- Do not ignore the final assembled PDF in the course directory. If an existing ignore rule hides PDFs or the course directory, add the necessary negation rules so the final PDF remains trackable.
- If the intended course output directory contains unrelated pre-existing content, prefer a fresh dedicated subdirectory for the Codex2Course package instead of mixing generated intermediates into that directory.
- If the user explicitly asks to preserve source files in Git, narrow or skip the ignore block to match that request.

Build the ignore block from the generated-path inventory. Example only when all four paths are newly created or explicitly owned by Codex2Course:

```gitignore
# Codex2Course generated intermediates for <course-dir>/
<course-dir>/outline.md
<course-dir>/handout.md
<course-dir>/slide-units/
<course-dir>/slides/
```

If only some intermediates were generated, include only those lines. Before final handoff, check the target repo state. `git status --short -- <course-dir>` should show the final PDF and should not hide pre-existing repository content. If the final PDF is missing because it is ignored, inspect with `git check-ignore -v <course-dir>/<course-title>.pdf` and adjust `.gitignore` with path-specific `!` rules until the PDF is trackable.

## Outline Template

`outline.md` has three required sections. Section names matter — downstream steps and the imagegen call all reference them by exact heading.

```markdown
# 课程标题: <Course Title>

## Course Info

- **Instructor:** <name>
- **Institution:** <institution / 单位>
- **Target audience:** <e.g., 工作 1-3 年的后端工程师，没有 LLM 使用经验>
- **Course goal:** <one line: what learners walk away with>
- **Duration:** <e.g., 一天 / 6 hours>

## Outline

1. Module 1: ...
   - Topic 1.1
   - Topic 1.2
2. Module 2: ...

## Image Generation Settings

- **Course brief:** <one-paragraph summary used as imagegen prefix; can be derived from Course Info + Course goal>
- **Art style:** <one shared style line, e.g., modern educational slide, soft pastel palette, clean sans-serif, generous whitespace>
- **Resolution:** <e.g., 1920×1080 (16:9)>
- **Language:** <e.g., Chinese>
- **Ending text (optional):** <override the default "谢谢 / Q&A" closing>
```

If any field in `Course Info` or `Image Generation Settings` is missing in step 1's input, ask the user before drafting the outline. Do not invent an instructor, institution, or audience.

## Slide Marker Convention

`handout.md` is the single source of truth. It is organized for teaching/reading — heading hierarchy follows pedagogical logic, not slide structure. Slide boundaries are an orthogonal annotation layer added in step 5 using HTML comments (invisible in rendered markdown):

```markdown
<!-- slide: 什么是 prompt engineering -->

它是一种通过设计输入来引导模型行为的实践……

## 三个核心原则

<!-- slide: 原则一：明确意图 -->

模型不会读心。明确意图意味着……
```

Rules:

- Every `<!-- slide: 标题 -->` marker opens a new slide. Slide content is everything from that marker up to the next marker (or end of file).
- Slide numbering is implicit (sequential by appearance order). Reordering slides means moving markers, not renumbering.
- The title in the marker becomes the slide filename suffix (slugified) and the slide-unit file's H1 heading.
- A heading like `## 三个核心原则` between markers belongs to whichever slide's range it falls into — handout structure and slide structure are decoupled.

## Slide Unit File Format (derived)

`scripts/split_handout.py` mechanically generates `slide-units/NNN-slug.md` from `handout.md`. Each file looks like:

```markdown
# Slide 003: Short Title

<verbatim handout content between this slide's marker and the next>
```

These files are **derived artifacts** — never hand-author or hand-edit them. To change slide content or boundaries, edit `handout.md` and rerun the script.

Run the script:

```bash
python scripts/split_handout.py course/handout.md
# defaults --out to course/slide-units
```

It clears stale `NNN-*.md` files in the output directory and rewrites all slides, so removing a marker correctly removes its slide.

## Imagegen Call Pattern

Before the first call, read and follow the `imagegen` skill. In ordinary use, this means the built-in `image_gen` tool, one call per final slide image, then move/copy the selected output into `slides/` using the exact filename below. The prompt payload is not a recipe for local rendering.

Each `imagegen` call has two parts in this order:

1. **Course-level prefix** — pulled verbatim from `outline.md`'s `## Image Generation Settings` (course brief, art style, resolution, language). Reused unchanged across every slide (cover, content, ending). Do not re-derive per call.
2. **Per-slide payload** — depends on slide kind:

| Slide kind | Payload source |
|---|---|
| Cover (`000-cover.png`) | An explicit cover-instruction line + the H1 course title + `## Course Info` fields (instructor, institution, target audience as tone cue) |
| Content (`NNN-slug.png`) | The slide-unit file's verbatim contents |
| Ending (`zzz-ending.png`) | An explicit ending-instruction line + the optional ending text from `## Image Generation Settings`, defaulting to "谢谢 / Q&A" in the course language |

Do not over-structure the prompt — `gpt-image-2` handles composition, layout, and visual metaphor on its own. Do not translate this prompt into HTML, PPT, SVG, chart code, or any other local renderer. When regenerating a single slide in step 7, append the user's per-slide revision note after the payload. Keep the prefix unchanged.

## Sequential Sub-Agent Batching

Large decks can stall or degrade when one conversation accumulates many image-generation calls and generated-image artifacts. When the deck needs more than 10 images total, keep the main agent as the orchestrator and delegate content-slide image generation to one sub-agent at a time.

Rules:

- Use this protocol only when sub-agents are available. If they are not available, continue in the main thread but pause every 5 images to summarize progress, check saved files, and keep the prompt context tight.
- Do not launch all image-generation sub-agents at once. Start exactly one batch worker, wait for it to finish and report saved file paths, verify the expected files exist, then start the next batch.
- Batch size is 5 images by default. Use smaller batches for very dense slides or if imagegen responses become slow; do not exceed 5 unless the user explicitly asks.
- The main agent owns course structure, cover generation, ending generation, source files, batch planning, review, and PDF assembly. Batch workers only generate assigned content-slide images, save them into `slides/`, and report paths plus any failures.
- Batch workers must use the `imagegen` skill for every assigned slide image. They must not edit `outline.md`, `handout.md`, `slide-units/`, or unrelated generated slides.
- Keep sub-agent context minimal. Do not fork the entire conversation unless necessary. Give each worker only the style contract, the exact course-level prefix, the assigned slide payloads or readable file paths, and the required output filenames.
- Starting with content batch 2, give each worker the last successfully generated content slide from the immediately previous content batch as a visual style anchor. The worker must inspect that image before its first imagegen call and use it only to match style, typography feel, palette, density, and aspect ratio; it must not copy the previous slide's content or layout literally.
- Do not use the cover image as an anchor for content slides, and do not use a content slide as an anchor for the ending slide. Cover and ending slides have intentionally different layouts from content pages.
- If a prior approved cover image for the same course family exists, use it as the cover's visual style anchor. If a prior approved ending image exists, use it as the ending's visual style anchor. If no corresponding anchor exists, generate the cover or ending from the course-level prefix and payload only.

Batch order:

1. Generate `slides/000-cover.png` separately in the main agent. Use a prior approved cover image as a visual anchor only when one exists.
2. Build the ordered content-image manifest from `slide-units/*.md` in filename order, mapped to matching `slides/*.png` filenames. Do not include `000-cover.png` or `zzz-ending.png` in this manifest.
3. Split the content manifest into contiguous groups of up to 5 images.
4. Start the first content worker with batch 1 only.
5. After the worker finishes, verify all assigned output files exist under `slides/` and look plausibly current.
6. For the next content worker, include the previous content batch's final output image path as `Visual style anchor`.
7. Repeat until all content batches are complete.
8. If a worker fails or produces missing files, retry only that content batch before moving forward.
9. Generate `slides/zzz-ending.png` separately in the main agent. Use a prior approved ending image as a visual anchor only when one exists.

Every worker prompt must include a compact style contract before the per-slide assignments:

```text
You are generating slide images for one course deck. Use the imagegen skill.

Style contract:
- Reuse this course-level prefix verbatim for every assigned imagegen call:
  <paste the exact ## Image Generation Settings content from outline.md>
- Keep all pages visually consistent: same art style, typography feel, color palette, spacing density, visual metaphor level, aspect ratio, and language.
- Do not invent a new brand, logo, mascot, decorative system, or page template.
- Save each final selected image to the exact output path listed for that assignment.

Visual style anchor:
- Batch 1: none.
- Content batch 2 or later: inspect this previous content batch's final generated content slide before generating anything: course/slides/005-topic.png
- Use the anchor only for visual continuity. Do not reuse its content, title, diagram, or exact composition unless the assigned payload calls for it.

Assigned images:
1. Output: course/slides/001-topic.png
   Payload source: course/slide-units/001-topic.md
   Payload: <paste content or instruct the worker to read this exact file>
...

Return only:
- generated output paths
- any failed assignment and the reason
```

For content slides, use each slide-unit file's verbatim content as the payload. The style contract exists to preserve consistency across batches; it does not replace the course-level prefix.

Cover and ending slides are generated outside the content-worker batches. For cover and ending slides, include the same payload rules from the Imagegen Call Pattern table. Use a corresponding visual anchor only from the same slide kind: cover-to-cover or ending-to-ending. If there is no corresponding approved anchor, use no visual anchor.

For targeted regeneration handled by a sub-agent, use a visual anchor from the same slide kind. For content-slide regeneration, include the nearest already-approved neighboring content slide when one exists; prefer the preceding approved content slide, or use the following approved content slide if needed. For cover or ending regeneration, use only a prior approved cover or ending image respectively; if none exists, use no visual anchor. The anchor should stabilize visual style only, not content.

## Quality Bar

| Area | Check |
|---|---|
| Handout | Correct terms, coherent order, teachable examples, no unsupported claims |
| Slide units | One file per slide, filename mirrors `slides/` 1:1, body is verbatim handout content |
| Image pages | Text is readable, layout is not crowded, visual metaphor matches content |
| Consistency audit | Every generated image has been inspected against its payload source; title, topic, key terms, examples, code/domain objects, and visual metaphor match; mismatched slides are regenerated before PDF assembly |
| Cover/Ending | Cover shows title + instructor + institution clearly; ending is simple and uncluttered; both share style with content slides |
| PDF | Cover first, ending last, content in order, consistent aspect ratio, no missing or stale regenerated pages |
| Large-deck batching | More than 10 images use separately generated cover/ending slides plus sequential content batches of up to 5, each content batch after the first receives the previous content batch's final content slide as a visual style anchor, each batch saves exact filenames, and the main agent verifies files before continuing |

## Common Mistakes

- **Generating `.pptx` by habit.** This workflow produces image pages plus PDF unless the user explicitly asks for editable `.pptx`.
- **Using local rendering because it feels more deterministic.** Local HTML/PPT/SVG/canvas/render-to-PNG workflows violate this skill's visual-generation contract. Use `imagegen`, or stop and ask the user to approve a different deliverable.
- **Skipping the handout review.** Slide units should reflect the reviewed teaching logic. Step 4 is a hard stop.
- **Drifting from the confirmed outline** when writing the handout or slicing slide units.
- **Over-structuring the imagegen prompt.** Passing only the course-level prefix + the verbatim slide-unit content beats elaborate prompt scaffolds.
- **Re-deriving the course brief per slide.** Generate it once in step 2, store it in `outline.md`'s `## Image Generation Settings`, reuse verbatim.
- **Hand-editing files in `slide-units/`.** Those are derived from `handout.md` — edit handout and rerun `scripts/split_handout.py` instead. Hand-edits get wiped on the next run.
- **Forgetting to rerun the split script after editing `handout.md`.** Stale `slide-units/` will produce slides that no longer match the source.
- **Using placeholders instead of imagegen.** If the deliverable needs a slide page image, use `imagegen`.
- **Skipping the consistency audit.** Imagegen can occasionally produce a polished slide for the wrong topic or reuse unrelated deck content. Inspect every generated image against its source payload before review and before PDF assembly.
- **Launching many image-generation sub-agents at once.** For large decks, run one batch worker at a time so context, file writes, and failures stay controlled.
- **Giving batch workers the whole conversation.** Pass only the style contract, course-level prefix, assigned payloads/paths, and output filenames.
- **Skipping the visual anchor after content batch 1.** Later content batch workers should inspect the previous content batch's final approved content slide image before generating their own slides.
- **Mixing slide-kind anchors.** Do not anchor content slides on the cover, and do not anchor the ending slide on a content page. Use cover-to-cover, content-to-content, and ending-to-ending anchors only.
- **Regenerating slides without explicit per-slide feedback** from the user, or regenerating the whole deck when only a few pages need fixes.
- **Restarting the workflow from step 1** when a reviewed handout or slide-unit file already exists. Pick up at the next missing stage.
- **Inventing instructor/institution/audience** when `outline.md` doesn't specify them. Ask the user.
- **Skipping cover or ending slides.** Every deck has both, named `000-cover.png` and `zzz-ending.png` so PDF assembly orders them by alphabetical glob.
