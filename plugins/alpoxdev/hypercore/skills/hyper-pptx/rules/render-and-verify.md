# Render And Verify

Use this rule file before the first render and before delivery. It owns the three commands, the report fields, the repair loop, and the closing report.

## 1. Create

```bash
bash <skill-dir>/scripts/render-deck.sh --spec <out-dir>/<slug>.deck.json --out-dir <out-dir> \
  [--name <slug>] [--formats pptx,html,png[,pdf]] [--scale 1-3] [--browser <path>] [--budget-ms <ms>] [--no-check]
```

- Defaults: `--formats pptx,html,png`, `--scale 1`, name taken from the spec file stem, `--budget-ms 30000`.
- `--browser` or `HYPER_PPTX_BROWSER` picks the renderer; `--list-browsers` prints the candidates that exist.
- Exit codes: `0` built and every check passed, `1` built but a layout check failed, `2` usage or spec error, `3` blocked (no browser, no zip, no runtime result).

Output on stdout is one JSON object:

| Field | Meaning |
|---|---|
| `status` | `pass` or `fail` |
| `slides` | slide count |
| `checks` | array of `{code, message}`; `LAYOUT_OVERFLOW` means text needs more room than its box, `LAYOUT_OUTSIDE` a shape crossing the slide edge, `LAYOUT_OVERLAP` two text blocks covering each other, `LAYOUT_SPARSE` a page using under a third of the canvas, `MOTION_INVALID` a timing tree PowerPoint would repair |
| `images` | `[{index, path}]` for the written PNGs |
| `pptx`, `html` | absolute paths, or `null` when not requested |

## 2. Inspect

```bash
bash <skill-dir>/scripts/inspect-deck.sh --file <deck.pptx> [--outline|--json] [--slide <n>] [--check]
```

Reports `slideCount`, size, fonts, and per slide: `shapes` (name, type, x, y, cx, cy, text), `notes`, `table` (2D array), `chart` (`{type, categories, series}`), and the shapes that leave the canvas.

- Run it on your own output when a check fails, and on someone else's deck before editing it.
- `--check` exits 1 when a slide has a shape outside the canvas.

## 3. Edit An Existing Deck

```bash
bash <skill-dir>/scripts/edit-deck.sh --file <in.pptx> --out <out.pptx> \
  [--replace "old=>new"]... [--set-font <name>] [--set-font-ea <name>] [--drop-slide <n>]... [--allow-miss]
```

- Only text nodes, typeface attributes, and the named slide parts change; layouts, masters, images, and custom XML from the original survive.
- A `--replace` that matches nothing is reported in `missed` and makes the run exit 1, because a phrase split across runs cannot be replaced safely. Shorten the search string and repeat, or rewrite the slide from a spec.
- `--drop-slide` removes the slide part, its relationships, its notes, its chart, the `sldId`, the relationship entry, and the content-type override, then revalidates every XML part.

## 4. The Repair Loop

Feedback is `checks` and what the PNGs show. The guard is `status: pass` plus a read of every PNG. The cap is three repair passes after the first render.

| Check code | Usual cause | Fix in the spec |
|---|---|---|
| `LAYOUT_OVERFLOW` | bullet text exceeds the box height | cut words, split the slide, or drop a bullet level |
| `LAYOUT_OUTSIDE` | a shape crosses the slide edge | reduce the row or column count |
| `LAYOUT_OVERLAP` | two text blocks cover each other | the spec put text where a caption or card already sits |
| `LAYOUT_SPARSE` | the page uses under a third of the canvas | a slide with one short line; give it a second element or merge it |
| `IMAGE_NO_ALT` | a picture has no alternative text | write `alt`; the picture is invisible without it |
| `IMAGE_REMOTE` | an image path is a URL | download the file and pass a local path |
| `IMAGE_UNREADABLE` | the pixel size cannot be read from the file | replace the file, or give a correct `aspect` |
| `MOTION_INVALID` | a slide has two timing trees, a repeated time-node id, or an animation target that names no shape on the slide | this is a writer bug unless a spec change removed a shape the animation still targets; re-render and report if it repeats |
| `RELATIONSHIP_BROKEN` | a package part is missing | this is a bug in the skill, not the spec; report it |
| `XML_INVALID` | malformed part | same as above |

A spec error is different from a check failure: an unknown transition, an unknown effect or trigger, a malformed gradient, or an animation target that matches nothing stops the run before anything is written, with exit 2 and the error code as the message (`TRANSITION_UNKNOWN`, `ANIMATION_EFFECT_UNKNOWN`, `ANIMATION_TRIGGER_UNKNOWN`, `ANIMATION_DIRECTION_UNKNOWN`, `ANIMATION_TARGET_EMPTY`, `GRADIENT_INVALID`, `PROCESS_TOO_FEW`, `PROCESS_TOO_MANY`). Each names the value it rejected, so the fix is to use one of the listed names rather than to weaken the check.

Motion is checked by reading the written XML, not the spec: `pp_check_motion` re-opens every `ppt/slides/slideN.xml` and counts `p:timing` trees, time-node ids, and `p:spTgt` targets. That is the only way to catch the failure mode where the writer and the layout disagree, because that produces a file that opens with a repair prompt rather than a file that fails here.

A pass that raises the check count is reverted. When three passes are spent, deliver nothing and report the remaining defects.

## 5. What A PNG Proves

The PNG is rendered by this package's own viewer at 1/9525 scale, from the same resolved JSON that produced the `.pptx`. It proves the geometry and the text fit. It does not prove the reader's PowerPoint will show the same font, and it does not prove a chart's axes match PowerPoint's renderer. State that limit when the deck matters.

Motion is not in the PNG. The preview shows the final state of each slide; a transition and an entrance leave no trace in a still image, so "the PNG looks right" says nothing about the animation. What was verified for motion is the XML and the three `MOTION_INVALID` conditions. Playback is unverified, and a deck with motion should be opened in PowerPoint before it is presented.

Charts and pictures are where this matters most: a combo's secondary axis, a scatter's x placement, and a `srcRect` crop are all drawn twice — once in the package, once in the preview. When the two disagree, the package is what the reader opens and the preview is what the author approved. Compare them on any slide where a chart or a picture carries the argument.

Looking at every PNG is not a formality. Three defects fixed while building this package passed every automated check and were visible only in the image: a combo that drew no bars, a scatter plotted as a diagonal, and an area chart filled with an opaque block that hid the grid.

## 5a. Determinism

Two renders of one spec must produce byte-identical `.pptx` files. Every part is stamped `1980-01-01 00:00`, the member list is sorted, and `zip -X` strips extra attributes. To confirm, render twice into different directories and compare `shasum -a 256`; the hashes must match. A mismatch means something reads the clock or the filesystem order, and a diff of two decks would show changes that are not changes.

## 6. Before Delivery

- `status: pass`, and the PNG of every slide was opened and read.
- `inspect-deck.sh --check` on the delivered file, with exit 0.
- Every slide and chart part validated against the ECMA-376 schema; `xmllint --schema` is the gate, not "PowerPoint opened it". Filter the `failed to load` import warnings out of the output before reading a result.
- Two renders of the spec hash identically.
- On a deck with motion: every `p:spTgt` names a shape on its slide, and the deck was opened once in PowerPoint. If PowerPoint is not available, say so in the report; do not claim the animation plays.
- Compare the deck against the spec's `slides` count and against the request: the same number of slides, the same claims, nothing invented.
- Report absolute paths for the `.pptx` (and the HTML and PNGs when written), the slide count, the palette and fonts, the checks that ran, and any limit that applies.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Presentation part structure and slide ordering | <https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document> |
| Notes and relationship parts | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-notes-slides> |
| Chart cached values | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-charts> |
| Deterministic zip output (fixed timestamps, `-X`) | <https://linux.die.net/man/1/zip> |

### Evidence grade

`LOCAL` — the exit codes, report fields, and check codes are read from the three scripts in this package and were exercised end to end on 2026-11-13, including a deliberate overflow and a repaired re-render.
