---
name: api2course
description: Use when creating course handouts, lecture notes, workshops, tutorials, PPT-like course slides, visual lecture materials, or course PDF decks from a topic, outline, handout, or existing course package, using the OpenAI API with gpt-image-2 for slide images.
---

# Api2Course

## Overview

Create a course package from a topic or outline: detailed teaching handouts first, then slide units, then one OpenAI API generated image per slide with `gpt-image-2`, then a PDF assembled from those images. The core rule is that slides are generated image pages, not `.pptx`, HTML, Markdown, SVG, canvas, screenshot, or locally rendered pages.

**REQUIRED IMAGE ROUTE:** Use `scripts/generate_openai_image.py` for every generated slide page, cover image, visual metaphor, diagram-like bitmap, or style variant. The script reads the API key from `OPENAI_API_KEY` and defaults to `gpt-image-2`.

## Non-Negotiable Output Routing

When this skill is active, the OpenAI Image API is the only route for producing slide visuals.

Allowed local scripts:
- `scripts/split_handout.py` may derive `slide-units/` from `handout.md`.
- `scripts/generate_openai_image.py` may call the OpenAI API and save final slide images.
- `scripts/images2pdf.py` may assemble existing `slides/*` image files into a PDF.

Forbidden substitutes for slide image generation:
- Creating `.pptx` decks with PowerPoint, LibreOffice, Keynote, or `python-pptx`
- Rendering Marp, reveal.js, HTML/CSS, Markdown, SVG, canvas, screenshots, browser pages, or notebook output into slide images
- Drawing slide pages with Pillow, matplotlib, reportlab, Mermaid, Graphviz, or other deterministic local renderers
- Using Codex/Claude built-in image tools instead of the OpenAI API path
- Generating placeholders, templates, or code-native diagrams instead of final API-generated slide images

If `OPENAI_API_KEY` is missing, the API is unavailable, or the model cannot generate the requested image, stop and report the blocker. Do not silently fall back to local PPT/rendering workflows unless the user explicitly changes the requirement to an editable `.pptx` or a deterministic locally rendered deck.

## When to Use

Use this skill for:
- Course handouts, lecture notes, tutorials, workshops, training materials
- Turning an outline into teachable content and visual slide pages
- Producing "PPT" as page images combined into a PDF
- Regenerating individual unsatisfactory pages from revised slide units
- Any course deck request where the user asks to use OpenAI API image generation instead of Codex imagegen

Do not use this skill when the user specifically needs editable `.pptx`; use `pptx` instead.

If the user says "PPT", "slides", "deck", or "课件" without explicitly asking for an editable `.pptx` file, treat the request as an image-page course deck and follow this skill's OpenAI API path.

## Workflow

Each stage below is independently invocable. Inspect what artifacts already exist (`outline.md`, `handout.md`, `slide-units/`, `slides/`) and start at the next missing stage. Do not redo work the user already approved.

All output (handout text, on-slide text, image text) must match the language of the user's input.

1. **Identify entry point, confirm input state, and preflight Git ownership.** Accept a course topic, rough outline, existing handout, finalized slide units, or a generated deck that needs targeted regeneration. If writing or extending `outline.md`, gather missing metadata up front: instructor, institution, target audience, course goal, and art style preference. If the output directory is inside a Git repository, inspect target paths before writing. Do not overwrite pre-existing content by default.
2. **Generate or refine the outline.** Use the Outline Template section below: `## Course Info`, `## Outline`, and `## Image Generation Settings`. Ask for confirmation before writing full content unless the user asked for a full draft in one pass.
3. **Write the handout.** Produce knowledge-point explanations detailed enough for learning but not a word-for-word script.
4. **STOP for human revision.** Output the handout and explicitly ask the user to review and approve it. Do not proceed to slide units until the user confirms.
5. **Annotate handout with slide markers, then materialize slide units.** Insert `<!-- slide: 标题 -->` markers at slide boundaries, present the resulting slide list for review, then run:

   ```bash
   python scripts/split_handout.py course/handout.md
   ```

   The script is the single way to produce `slide-units/`; never hand-author or hand-edit those files.

6. **Prepare API prompt snippets.** Create `prompt-snippets/course-prefix.md` from `outline.md`'s `## Image Generation Settings` and keep it unchanged for every image call. Create `prompt-snippets/000-cover.md` from the course title and `## Course Info`. Create `prompt-snippets/zzz-ending.md` from the configured ending text, defaulting to "谢谢 / Q&A" in the course language. Content slides use their `slide-units/NNN-slug.md` files directly as payloads.
7. **Generate slide images with the OpenAI API only.** Use `scripts/generate_openai_image.py` once per final slide image. Generate three groups in this order:
   - **Cover** -> `slides/000-cover.png`: `course-prefix.md` + `000-cover.md`.
   - **Content** -> `slides/NNN-slug.png`, mirroring `slide-units/` filenames 1:1: `course-prefix.md` + the slide-unit file.
   - **Ending** -> `slides/zzz-ending.png`: `course-prefix.md` + `zzz-ending.md`.

   Example commands:

   ```bash
   python scripts/generate_openai_image.py \
     --prompt-file course/prompt-snippets/course-prefix.md \
     --prompt-file course/prompt-snippets/000-cover.md \
     --out course/slides/000-cover.png \
     --size 1536x864 --quality high

   python scripts/generate_openai_image.py \
     --prompt-file course/prompt-snippets/course-prefix.md \
     --prompt-file course/slide-units/001-topic.md \
     --out course/slides/001-topic.png \
     --size 1536x864 --quality high
   ```

   The script accepts these environment overrides: `OPENAI_API_KEY` (required), `OPENAI_IMAGE_MODEL` (default `gpt-image-2`), `OPENAI_IMAGE_SIZE` (default `1536x864`), `OPENAI_IMAGE_QUALITY` (default `high`), `OPENAI_IMAGE_FORMAT` (default `png`), `OPENAI_IMAGE_BACKGROUND` (default `auto`), `OPENAI_IMAGE_TIMEOUT` (default `180`), `OPENAI_BASE_URL`, `OPENAI_ORG_ID` / `OPENAI_ORGANIZATION`, and `OPENAI_PROJECT_ID` / `OPENAI_PROJECT`.

   If the full deck has more than 10 images (cover + content + ending), use the Sequential Batch protocol below for content slides. Generate cover and ending separately because their layouts intentionally differ from normal content slides.

8. **Run a generated-image consistency audit before review or PDF assembly.** Inspect every generated image and compare it against its payload source. For content slides, compare `slides/NNN-slug.png` with `slide-units/NNN-slug.md`; for the cover, compare `slides/000-cover.png` with the H1 and `## Course Info`; for the ending, compare `slides/zzz-ending.png` with the configured ending text. Check that visible title, topic, core terms, examples, code/domain objects, and visual metaphor match the source.

   If any generated image is semantically inconsistent with its payload, treat it as a generation failure: immediately regenerate only that image with the same course-level prefix and same original payload, plus a short correction note via `--prompt "Correction note: ..."`. Replace the same `slides/` filename, then re-inspect it.

9. **Batch review, then targeted regeneration.** After all slides pass the consistency audit, present the deck to the user for review in one pass. Regenerate only the specific slides the user names, using the same prefix + payload plus the user's revision note. If feedback changes content rather than visuals, edit `handout.md` and rerun the split script first; for cover/ending content fixes, edit `outline.md` and refresh the prompt snippet.
10. **Assemble PDF from API-generated outputs.** Run:

    ```bash
    python scripts/images2pdf.py course/slides
    ```

    The script sorts images alphabetically (`000-cover.png` -> content slides -> `zzz-ending.png`). Requires Pillow (`pip install Pillow`). When the output path is omitted, the script reads the H1 of `<slides-dir>/../outline.md` and writes `<slides-dir>/../<course title>.pdf`.

## Output Structure

Prefer this structure unless the user provides another destination:

```text
course/
├── outline.md
├── handout.md
├── prompt-snippets/    # API prompt snippets; derived from outline.md
│   ├── course-prefix.md
│   ├── 000-cover.md
│   └── zzz-ending.md
├── slide-units/        # DERIVED from handout.md by scripts/split_handout.py
│   ├── 001-title.md
│   ├── 002-topic.md
│   └── ...
├── slides/             # OpenAI API-created cover + content + ending
│   ├── 000-cover.png
│   ├── 001-title.png
│   ├── 002-topic.png
│   └── zzz-ending.png
└── <course-title>.pdf
```

## Repository Hygiene

When generating a course package inside any Git repository, keep only Api2Course-created intermediate artifacts local. Commit the final PDF deliverable and any `.gitignore` change needed to hide generated intermediates. Never hide unrelated files that were already part of the target repository.

Api2Course-generated intermediates include paths created by this skill during the current run, or paths the user explicitly identifies as prior Api2Course output: `outline.md`, `handout.md`, `prompt-snippets/`, `slide-units/`, and `slides/`.

Before adding ignore rules, check candidate paths with Git and the filesystem, for example `git ls-files -- <path>` plus a normal existence check. Add ignore rules only for exact generated paths this skill created or owns. Do not ignore the final assembled PDF.

Example only when all paths are newly created or explicitly owned by Api2Course:

```gitignore
# Api2Course generated intermediates for <course-dir>/
<course-dir>/outline.md
<course-dir>/handout.md
<course-dir>/prompt-snippets/
<course-dir>/slide-units/
<course-dir>/slides/
```

## Outline Template

`outline.md` has three required sections. Section names matter because downstream steps reference them exactly.

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

- **Course brief:** <one-paragraph summary used as the API prompt prefix>
- **Art style:** <one shared style line>
- **Resolution:** <e.g., 1536x864 or 2048x1152, 16:9, both edges multiples of 16>
- **Quality:** <low / medium / high>
- **Language:** <e.g., Chinese>
- **Ending text (optional):** <override the default "谢谢 / Q&A" closing>
```

Ask the user before drafting the outline if instructor, institution, target audience, or required visual style is missing.

## Slide Marker Convention

`handout.md` is the single source of truth. Slide boundaries are HTML comments:

```markdown
<!-- slide: 什么是 prompt engineering -->

它是一种通过设计输入来引导模型行为的实践……

## 三个核心原则

<!-- slide: 原则一：明确意图 -->

模型不会读心。明确意图意味着……
```

Rules:
- Every `<!-- slide: 标题 -->` marker opens a new slide.
- Slide numbering is implicit by marker order.
- The marker title becomes the slide filename suffix and the slide-unit H1.
- To change slide content or boundaries, edit `handout.md` and rerun `scripts/split_handout.py`.

## OpenAI API Call Pattern

Each API call has two prompt parts in this order:

1. **Course-level prefix** from `prompt-snippets/course-prefix.md`, derived verbatim from `## Image Generation Settings`.
2. **Per-slide payload**:

| Slide kind | Payload source |
|---|---|
| Cover (`000-cover.png`) | `prompt-snippets/000-cover.md` |
| Content (`NNN-slug.png`) | Matching `slide-units/NNN-slug.md` |
| Ending (`zzz-ending.png`) | `prompt-snippets/zzz-ending.md` |

Do not translate the prompt into HTML, PPT, SVG, chart code, or any other local renderer. Let `gpt-image-2` handle composition, layout, and visual metaphor.

For style anchors or targeted regeneration, pass one or more `--reference-image <path>` arguments. This uses the OpenAI image edits endpoint with reference images. Reference images stabilize visual style only; they must not replace the current slide payload.

## Sequential Batch Protocol

Large decks can stall or become harder to audit when one pass accumulates many generated images. When the deck needs more than 10 images total, keep the main agent as orchestrator and process content slides in contiguous batches of up to 5.

Rules:
- Generate `slides/000-cover.png` separately first.
- Build the ordered content manifest from `slide-units/*.md`, mapped to matching `slides/*.png`.
- Process batches in order, up to 5 slides at a time.
- After each batch, verify all assigned output files exist and inspect them against their payloads.
- Starting with content batch 2, use the previous content batch's final generated content slide as a style anchor with `--reference-image`.
- Do not use the cover image as a content-slide anchor, and do not use a content slide as the ending-slide anchor.
- Generate `slides/zzz-ending.png` separately last.

Example batch-2 content command:

```bash
python scripts/generate_openai_image.py \
  --prompt-file course/prompt-snippets/course-prefix.md \
  --prompt-file course/slide-units/006-topic.md \
  --reference-image course/slides/005-topic.png \
  --out course/slides/006-topic.png
```

## Quality Bar

| Area | Check |
|---|---|
| Handout | Correct terms, coherent order, teachable examples, no unsupported claims |
| Slide units | One file per slide, filename mirrors `slides/` 1:1, body is verbatim handout content |
| API images | Text is readable, layout is not crowded, visual metaphor matches content |
| Consistency audit | Every generated image has been inspected against its payload source |
| Cover/Ending | Cover shows title + instructor + institution clearly; ending is simple and uncluttered |
| PDF | Cover first, ending last, content in order, consistent aspect ratio, no missing pages |

## Common Mistakes

- Generating `.pptx` by habit.
- Using Codex/Claude image tools instead of the OpenAI API script.
- Using local HTML/PPT/SVG/canvas/render-to-PNG workflows as a shortcut.
- Forgetting to set `OPENAI_API_KEY`.
- Choosing a slide size whose edges are not multiples of 16.
- Skipping the handout review.
- Hand-editing files in `slide-units/`.
- Forgetting to rerun the split script after editing `handout.md`.
- Skipping the consistency audit.
- Reusing a reference image as content instead of only as a style anchor.
- Regenerating the whole deck when only a few pages need fixes.
