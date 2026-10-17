# Toolchain Guide

The practical reference for `renderer_agent`: what each toolchain is for, how to
detect it, the exact commands to build and verify, and what to do when nothing is
installed. The honesty contract sits on top of all of it: detection results are
reported verbatim, builds run for real, and an uninstalled tool is presented with its
install cost — never as a capability the skill already has (SKILL Iron Rule 2).

## Decision table

| The professor wants | Route | Why |
|---------------------|-------|-----|
| Editable PPTX on the institutional .potx/.pptx template | **python-pptx** (most control) or **pandoc --reference-doc** (faster, less control) | The only routes that honor a real template; Marp's PPTX export is images-on-slides, not editable |
| Fast, beautiful PDF or HTML deck; no template constraint | **Marp** | Markdown in, themed CSS, one-command build — the suite default |
| Math-heavy deck (proofs, derivations, heavy notation) | **Beamer via tectonic** | LaTeX math rendering; tectonic needs no TeX Live install |
| Interactive web deck (embedded demos, fragments, speaker view) | **reveal.js / Slidev** — note only | Supported as an export note, not a maintained route: npm project setup exceeds a per-deck build; offer if the professor already runs one |
| Editable PPTX, no template, minimal tooling | **pandoc** (plain) | `pandoc deck.md -o deck.pptx` works with zero theme work |

Tie-breakers: institutional template constraint dominates everything; otherwise prefer
the installed tool over the better tool; otherwise Marp.

## Marp CLI

- **Detect:** `marp --version`
- **Install (macOS):** `brew install marp-cli` (or `npm i -g @marp-team/marp-cli`)
- **Build:**
  ```
  marp deck.md --theme decks/theme/course.css --pdf --allow-local-files -o deck.pdf
  marp deck.md --theme decks/theme/course.css --html -o deck.html
  ```
- **Theme implementation:** a CSS file (`@theme course`) implementing the theme spec's
  tokens; layout masters become CSS classes selected per-slide via
  `<!-- _class: section -->` directives. See `ts/deck-studio/templates/theme_spec_template.md`.
- **Handout:** `marp deck.md --pdf --pdf-notes` (notes as PDF annotations), or render
  the handout variant source (one-per-page + note space) as a separate build.

| Limitation | Consequence |
|------------|-------------|
| PPTX export is rendered images per slide | Not editable in PowerPoint — never offer it as "editable PPTX" |
| No .potx template support | Institutional-template requests route elsewhere |
| LaTeX math via KaTeX/MathJax subset | Very heavy notation → consider Beamer |

## Pandoc

- **Detect:** `pandoc --version`
- **Install (macOS):** `brew install pandoc`
- **Build:**
  ```
  pandoc deck.md -o deck.pptx                                  # plain editable PPTX
  pandoc deck.md --reference-doc=institutional.pptx -o deck.pptx   # on the template
  pandoc deck.md -t beamer --pdf-engine=tectonic -o deck.pdf       # Beamer route
  ```
- **Theme implementation:** for PPTX, the theme lives in the reference doc's slide
  masters — pandoc maps content onto the template's layouts by placeholder; the theme
  spec records which master maps to which layout name. For Beamer, a small preamble
  file carries the tokens (`-H preamble.tex`).
- **Handout:** Beamer route supports `\documentclass[handout]{beamer}` + `pgfpages`
  (e.g., 2-on-1 with note space); PPTX handouts are PowerPoint's own print feature —
  say so rather than rebuilding it.

| Limitation | Consequence |
|------------|-------------|
| Reference-doc mapping is coarse (limited layout control) | Pixel-precise template compliance → python-pptx |
| Speaker notes need `::: notes` divs | deck_architect emits both notes syntaxes per the source template |
| Marp directives (`_class`) are ignored | Layout-master selection degrades to pandoc's slide-level heuristics — flag it |

## Beamer via tectonic

- **Detect:** `tectonic --version`
- **Install (macOS):** `brew install tectonic`
- **Build:** `tectonic deck.tex` (deck.tex generated from the markdown source via
  pandoc, or written directly for `poster` mode / TikZ-heavy decks)
- **Theme implementation:** a `beamercolortheme`/`beamerfontheme` pair generated from
  the theme spec tokens; 24pt floor enforced via font theme, not per-slide sizing.
- **Poster:** `beamerposter` or `tikzposter` class, A0/A1 per the venue spec.

| Limitation | Consequence |
|------------|-------------|
| Output is PDF only | "Editable by colleagues in PowerPoint" → different route |
| First tectonic run downloads packages (network) | Warn before the first build, not after it hangs |
| Beamer's own templates fight custom themes | Start from `default` theme + spec tokens, not from `Madrid` etc. |

## python-pptx

- **Detect:** `python3 -c "import pptx; print(pptx.__version__)"`
- **Install (macOS):** `pip3 install python-pptx`
- **Build:** a generated build script (`decks/build_W<N>.py`) that opens the
  institutional template, walks the deck source, and places content into the
  template's named placeholders. The script is a committed artifact — the deck is
  rebuildable and the mapping auditable.
- **Theme implementation:** the .potx/.pptx template *is* the theme; the theme spec
  records placeholder names per layout master and the token→template mapping. Spec
  tokens the template violates (e.g., 20pt body in the institutional master) are
  flagged at the theme checkpoint — institutional template vs accessibility floor is
  the professor's call to make, on the record.
- **Handout:** PowerPoint's handout printing (say so), or a generated notes-pages
  variant from the same build script.

| Limitation | Consequence |
|------------|-------------|
| No markdown rendering — the build script does the mapping | Build script complexity scales with layout variety; keep masters few |
| No math rendering | Equations become images from the figure pipeline (LaTeX→SVG/PNG) |
| Charts placed as images, not native chart objects by default | Colleagues can't re-edit chart data in PowerPoint — state it |

## Degradation ladder

When detection comes back empty, in order:

1. **Ship the source anyway** — Marp-flavored markdown per
   `ts/deck-studio/templates/deck_source_template.md`, complete with theme directives, notes, and
   figure pointers. The deck of record exists; only the binary is pending.
2. **State the exact install** for the recommended route (one command, from the
   sections above) and the one-liner build the professor runs afterward.
3. **State what the build would produce** — format, page count, theme — plainly
   marked as *expected on build*, never phrased as if it exists.
4. Figures degrade independently: no matplotlib → ship the script + `[PENDING RENDER]`
   placeholder; no mermaid CLI → ship the `.mmd` source (it renders in many viewers).

Never on the ladder: a fabricated "rendered" file, a stale artifact passed off as
current, or silence about what's missing.

## Verification commands

Run after every build (`renderer_agent` Procedure 4):

| Output | Exists / fresh | Count check | Spot check |
|--------|----------------|-------------|------------|
| `.pdf` | `ls -la deck.pdf` (size > 0, mtime after source) | `mdls -name kMDItemNumberOfPages deck.pdf` vs source slide count | `open deck.pdf` — first/middle/last slides |
| `.pptx` | `ls -la deck.pptx` | `python3 -c "from pptx import Presentation; print(len(Presentation('deck.pptx').slides))"` | `open deck.pptx` |
| `.html` | `ls -la deck.html` | `grep -c '<section' deck.html` (Marp: sections per slide) | `open deck.html` |
| figures | `ls -la decks/figures/` — every manifest entry present | manifest count vs files | thumbnail at slide scale |

Count mismatch or stale mtime → investigate and report before presenting anything.
Source slide count for the comparison: `grep -c '^---$' deck.md` minus front-matter
fences (the source template keeps this countable).
