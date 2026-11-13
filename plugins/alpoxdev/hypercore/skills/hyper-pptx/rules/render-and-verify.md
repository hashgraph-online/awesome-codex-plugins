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
| `checks` | array of `{code, message}`; `LAYOUT_OVERFLOW` means text needs more room than its box, `OUTSIDE` means a shape crosses the slide edge |
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
| `OUTSIDE` | a shape crosses the slide edge | reduce the row or column count |
| `RELATIONSHIP_BROKEN` | a package part is missing | this is a bug in the skill, not the spec; report it |
| `XML_INVALID` | malformed part | same as above |

A pass that raises the check count is reverted. When three passes are spent, deliver nothing and report the remaining defects.

## 5. What A PNG Proves

The PNG is rendered by this package's own viewer at 1/9525 scale, from the same resolved JSON that produced the `.pptx`. It proves the geometry and the text fit. It does not prove the reader's PowerPoint will show the same font, and it does not prove a chart's axes match PowerPoint's renderer. State that limit when the deck matters.

## 6. Before Delivery

- `status: pass`, and the PNG of every slide was opened and read.
- `inspect-deck.sh --check` on the delivered file, with exit 0.
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
