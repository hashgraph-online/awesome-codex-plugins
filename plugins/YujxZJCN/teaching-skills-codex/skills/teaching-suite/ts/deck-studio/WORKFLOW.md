---
name: deck-studio
description: "Slide deck production for university professors. 4-agent team turning slide outlines and lecture notes into actually rendered deck files — Marp, Pandoc, Beamer via tectonic, or python-pptx — with a course-wide visual theme, code-generated figures, student handouts, and academic posters. Detects installed toolchains honestly; enforces accessibility minimums. Triggers on: make slides, PPT, PowerPoint, slide deck, beamer, presentation, lecture slides, poster, render my slides, slide theme, 做PPT, 幻灯片, 课件制作, 讲义, 海报, 演示文稿."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 2
  related_skills:
    - lesson-builder
    - course-publisher
    - teaching-pipeline
---

# Deck Studio — Slide Production Team

Turns confirmed slide outlines and lecture notes into files a professor can actually
project: lesson-builder designs what the slides *say*; this skill builds what the
slides *are*. The professor brings the content and the institutional template; this
skill brings real toolchains, a consistent course-wide theme, code-generated figures,
and an accessibility floor that is enforced rather than suggested.

> **Prime rule:** never fake a render. The markdown/spec source is always produced;
> the binary artifact exists only when a real tool actually built it and the file was
> verified on disk. "Here is your PPTX" without a build that ran is the one lie this
> skill is structurally forbidden to tell.

## Quick Start

```
Turn my Week 5 slide outline into a PowerPoint deck
帮我把这份讲稿做成幻灯片，用学校的模板
Build a visual theme for my whole course — institutional blue, big fonts
Make a figure: cache hit rate vs cache size, three eviction policies
My old deck is a wall of text — audit and rebuild it
I need an A0 poster for the teaching innovation showcase
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `deck` | "Make/render slides from…" with an outline or notes | Markdown deck source + rendered file (PDF/PPTX/HTML) through the chosen toolchain |
| `theme` | "Build a theme / make my decks consistent" — once per course | Theme spec (`ts/deck-studio/templates/theme_spec_template.md`) + Marp CSS or pptx template notes: typography, colors, title/section/content masters |
| `figure` | "Make a diagram/chart of…" — one graphic from a description | Code-rendered figure (matplotlib / mermaid / TikZ), colorblind-safe, with generating code and alt text |
| `handout` | "Student handout version" of a deck | One-slide-per-page with note space, or condensed notes pages, rendered |
| `restyle` | Existing deck + dissatisfaction ("too dense", "ugly", "inconsistent") | Audit against `ts/deck-studio/references/slide_design_rules.md` (R-check report) → rebuilt deck on the course theme |
| `poster` | "Make a poster for…" — conference, showcase, course advertisement | Single large-canvas poster source + rendered file |

**Mode dispatch rule:** "make slides" with no existing outline → check for a
lesson-builder `W<N>_slides_outline.md` artifact first; none found → offer
`lesson-builder` `slides-outline` for content design, or run `deck` with direct intake
if the professor already has notes. `theme` runs once and every later mode consumes
its spec. Detect intent in any language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Deciding what the slides should *say* — content, sequencing, assertion titles from scratch | `lesson-builder` (`slides-outline` mode) |
| Lesson plans, activities, lecture notes for the meeting | `lesson-builder` |
| Publishing the course site / LMS package the decks live on | `course-publisher` |
| Full design → materials → assessment run across stages | `teaching-pipeline` |

(The boundary in one line: slide *content* is lesson-builder's; slide *files* are ours.
An outline arriving from `slide_outliner_agent` is consumed as confirmed content —
deck_architect restructures its packaging, never its claims.)

## Agent Team (4)

| Agent | Role |
|-------|------|
| `deck_architect_agent` | Maps the outline to a slide sequence: one idea per slide, assertion titles preserved or derived (flagged), section dividers, builds, speaker notes, length sanity; routes paragraph walls back to lesson-builder |
| `visual_designer_agent` | Builds the course theme: typography scale (24pt body floor), contrast-checked color tokens, colorblind-safe palette, layout masters, Marp CSS / pptx implementation — the contract other agents consume |
| `figure_maker_agent` | Renders every figure spec as a real graphic via code (matplotlib / mermaid / TikZ), theme-aligned, alt-texted; generating code stored alongside; refuses decorative clip-art |
| `renderer_agent` | Detects installed toolchains, runs the actual build commands, verifies output exists and matches the source, reports build failures verbatim; never edits content during render |

## Workflow (`deck` mode)

```
Phase 0  LOAD        — read the slide outline: lesson-builder artifact
                       (lessons/W<N>_slides_outline.md) preferred, else direct intake
                       (notes/outline from the professor). Load theme spec if one
                       exists; none → offer `theme` mode first or one-deck defaults.
Phase 1  TOOLCHAIN   — renderer detects what is installed (marp, pandoc, tectonic,
                       python-pptx) and reports plainly: available routes, what each
                       produces, what is missing + install command.
         🧑 checkpoint: toolchain + target format confirmed. Default: Marp markdown
            → PDF/HTML. Institutional .potx/.pptx template supplied → python-pptx or
            pandoc --reference-doc route. Nothing installed → professor chooses:
            install, or ship source-only (degradation ladder).
Phase 2  ARCHITECT   — deck_architect maps the outline to a slide sequence with theme
                       tokens: splits/merges to one idea per slide, dividers, builds,
                       speaker notes carried into the source, slide-count sanity
Phase 3  FIGURES     — figure_maker renders every figure spec as an actual image file
                       + generating code + alt text; [NEEDS PROFESSOR INPUT] figures
                       (own data, lab photos) left as labeled placeholders
Phase 4  RENDER      — renderer builds the deck for real, verifies the output file
                       exists, slide count matches source, and opens it for the
                       professor; then the accessibility pass per
                       references/slide_design_rules.md (font floor, contrast,
                       palette, alt text) — violations flagged, never silently fixed
         🧑 checkpoint: rendered artifact path + accessibility findings + every
            decision made (splits, derived titles, figure choices). Confirmed →
            passport week artifact_refs updated.
```

`handout`, `restyle`, and `poster` re-enter this workflow at the phase they need:
`handout` is Phase 4 with a layout variant; `restyle` runs the R-check audit first,
then Phases 2–4 on the existing content; `poster` swaps the slide sequence for a
single-canvas layout but keeps figure and render discipline unchanged.

## Iron rules

1. **Source of truth is the source.** The markdown/spec file is the deck of record;
   the PDF/PPTX is a build product, rebuildable from source at any time. Edits go into
   the source and re-render — never into the binary alone.
2. **Never fake a render.** No installed tool for the chosen route → deliver the
   source, the exact install command, and a plain statement of what the build would
   produce. A claimed render with no verified file on disk is a defect, not a draft.
3. **Accessibility minimums are enforced, not advisory** (Quality Gate U1 made
   executable): 24pt body-text floor for projection, contrast-checked text/background
   pairs, colorblind-safe palette wherever color carries meaning, alt text in the
   source for every figure. Violations are flagged with slide numbers; the professor
   may override with a logged reason — silence is not an option.
4. **Theme consistency.** Every deck in a course renders against the confirmed theme
   spec. A deck drifting from it (ad-hoc colors, off-scale fonts) is flagged at the
   render checkpoint, not quietly normalized and not quietly shipped.
5. **Figures are code.** Every generated figure ships with the script that drew it,
   stored alongside the image — rebuildable when the data changes, editable when the
   professor disagrees. Pasted unreproducible images are for professor-supplied
   material only.
6. **Content fidelity.** The deck says what the outline/notes say — this skill adds
   zero new domain claims at any phase. Where the outline is silent, the slide carries
   `[NEEDS CONTENT: <what>]`, never plausible filler; inherited `[VERIFY]` markers
   survive into the source untouched.

## Outputs

- `decks/W<N>_deck.md` — deck source, from `ts/deck-studio/templates/deck_source_template.md`
- `decks/W<N>_deck.pdf` / `.pptx` / `.html` — the verified build product
- `decks/figures/W<N>_fig<k>.(png|svg|pdf)` + `decks/figures/src/W<N>_fig<k>.(py|mmd|tex)`
- (`theme` mode) `decks/theme/theme_spec.md` + `decks/theme/course.css` or pptx template notes
- (`handout` mode) `decks/W<N>_handout.pdf`
- (`restyle` mode) `decks/restyle_audit.md` (R-check report) + rebuilt deck
- (`poster` mode) `decks/poster_<name>.md` + rendered poster file
- Updated `course_passport.yaml` week `artifact_refs[]` (after confirmation)

## References

- `ts/deck-studio/references/slide_design_rules.md` — the enforced rulebook: assertion-evidence,
  density ceilings, legibility table, palette, R-check audit ids
- `ts/deck-studio/references/toolchain_guide.md` — toolchain decision table, install/build/verify
  commands, degradation ladder
- `ts/deck-studio/templates/theme_spec_template.md`
- `ts/deck-studio/templates/deck_source_template.md`
- Shared: `ts/shared/pedagogy_foundations.md` (§7, §9), `ts/shared/course_passport_schema.md`,
  `ts/shared/checkpoint_protocol.md`, `ts/shared/quality_gate_protocol.md`
