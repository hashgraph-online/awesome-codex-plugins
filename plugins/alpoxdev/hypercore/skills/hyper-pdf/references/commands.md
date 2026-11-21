# Command reference

> Every command prints exactly one JSON object on stdout. Nothing human-readable is printed, so a caller parses, never greps.

```
osascript -l JavaScript <skill>/assets/runtime/engine.js <command> [inputs] [flags]
```

## Table of Contents

1. [Exit codes and status](#1-exit-codes-and-status)
2. [Reading](#2-reading)
3. [Structure](#3-structure)
4. [Security and forms](#4-security-and-forms)
5. [Generation](#5-generation)
6. [Inspecting](#6-inspecting)
7. [Invariants that apply to every command](#7-invariants-that-apply-to-every-command)

## 1. Exit codes and status

| Exit | `status` | Meaning |
|---|---|---|
| 0 | `ok` | The operation completed and nothing needs attention |
| 0 | `caveated` | The file was produced, but the `issues` array lists real defects (missing tree, unembedded font, `missing` form fields) |
| 1 | `blocked` | The operation could not proceed and produced nothing: `NO_PDF_FRAMEWORK`, `NO_HTML_RENDERER`, `ENCRYPTED`, `BAD_PASSWORD` |
| 1 | `error` | Bad arguments or a runtime failure: `ARGS`, `NO_INPUT`, `UNKNOWN_COMMAND`, `RUNTIME` |

The exit code answers one question: was a file produced. The engine runs under `osascript`, which reports only 0 or 1 and has no `exit`, so read the `status` field to tell `ok` from `caveated` and `blocked` from `error`. Both still print one JSON object on stdout, and the failing case also writes to stderr.

`caveated` is not success. A report that says "done" on a `caveated` result while an `issues` entry stands is a false report.

## 2. Reading

### `info <pdf>`

| Field | Content |
|---|---|
| `pages` | Page count |
| `encrypted` | Locked now, or `/Encrypt` present |
| `metadata` | `title`, `author`, `subject`, `keywords`, `creator`, `producer`, creation and modification dates |
| `raw` | The full byte scan (see §6) |
| `pageDetails[]` | Per page: `page`, `width`, `height` in points, `rotation`, `textChars`, `annotations` |

### `text <pdf> [--pages SPEC] [--runs]`

`--pages` takes `1-3,7,10-` (omitted bound means first or last page).

| Field | Content |
|---|---|
| `content[]` | Per page: `page`, `text`; with `--runs` also `lines[]` of `{y, runs:[{text, x, width, font, size}]}` |
| `characters` | Total extracted characters |
| `scanned` | `true` when no character was extracted at all |

### `tables <pdf> [--pages SPEC]`

| Field | Content |
|---|---|
| `tables[]` | Per page: `page`, `columns`, `rows[][]` of cell strings |
| `limitation` | Always present; states how boundaries were inferred |

Row boundaries come from baseline alignment, cell boundaries from horizontal gaps. A ruled table with wrapped cells, or a borderless table with uneven spacing, needs a manual read. Do not present the grid as exact.

### `images <pdf> --out-dir DIR`

Renders each page to PNG at 2×. `images[]` gives `page`, `raster` path, `width`, `height`. Embedded image objects keep their own resolution and are not resampled.

### `render <pdf> --out-dir DIR [--scale N] [--pages SPEC]`

Writes `page-<n>.png` per page at `--scale` (default 2). This is the command that proves what the page looks like; use it after every generation.

### `fonts`

Lists installed font files available to `resolveFont`. No arguments.

## 3. Structure

### `merge --out OUT.pdf <a.pdf> <b.pdf> ...`

| Field | Content |
|---|---|
| `pages` | Total pages in the output |
| `sources[]` | Per input: `path`, `pages`, `locked` |

An encrypted input that cannot be unlocked blocks the merge; it does not silently drop pages.

### `split <pdf> --out-dir DIR (--pages SPEC | --every N)`

| Field | Content |
|---|---|
| `sourcePages` | Page count of the input |
| `parts[]` | Per output: `from`, `to`, `out` path, `pages` |

Files are named `pages-<from>-<to>.pdf`. `--every 5` gives chunks of five.

### `rotate <pdf> --out OUT.pdf [--angle 90] [--pages SPEC]`

`--angle` must be a multiple of 90 (negative accepted). Reports `pagesRotated` and the applied `angle`. Rotation is cumulative with the page's existing rotation.

### `watermark <pdf> --out OUT.pdf --text TEXT [--opacity 0.3] [--size 48] [--angle 45] [--pages SPEC] [--font PATH]`

Draws diagonal text over each page by replaying the page into a new context. Reports `pages` and `watermarked` (the count that received the mark). The text is drawn, not added as an annotation, so it cannot be toggled off and it appears in extraction.

### `stamp <pdf> --out OUT.pdf --text TEXT [--page 1] [--x] [--y] [--width 240] [--height 60] [--size 24] [--opacity 0.5] [--font PATH]`

Adds a FreeText annotation with a red default colour. Unlike `watermark` this stays an annotation, so `flatten` is what bakes it into the page.

### `metadata <pdf> [--set "key=value;key=value"] [--out OUT.pdf | --in-place]`

Without `--set` it only reads. With `--set` it applies the named attributes; keys are `title`, `author`, `subject`, `keywords`, `creator`. It writes to `--out` when given, to the source only with `--in-place`, and to nothing otherwise. Reports `before`, `after`, `applied`.

## 4. Security and forms

### `encrypt <pdf> --out OUT.pdf --user-password PW [--owner-password PW]`

Reports `locked` after reopening the result. The note is part of the answer: PDFKit applies RC4 128-bit passwords and offers no AES-256 and no permission bit set. A request that needs AES or per-operation permissions cannot be met by this command, and that must be said rather than implied.

### `decrypt <pdf> --out OUT.pdf [--password PW]`

`blocked BAD_PASSWORD` when the password does not unlock. It never guesses.

### `form <pdf>`

Reads fields: `fields[]` with `page`, `name`, `type`, `value`, `rect`; `fillable` boolean.

### `form <pdf> --fill "name=value;name=value" --out OUT.pdf`

| Field | Content |
|---|---|
| `applied[]` | Per field: `field`, `value`, `widgets` (how many widgets took it) |
| `missing[]` | Field names with no matching widget — these make the status `caveated` |

Field values are split on `;` and `=`, so a value containing either needs a different route (write a small spec-driven document instead).

### `flatten <pdf> --out OUT.pdf`

Replays each page and draws its annotations into the content. Reports `pages` and `remainingFormFields`. Interactive widgets are dropped by design: the output is print-only, and a form that must stay fillable must not be flattened.

## 5. Generation

### `build --spec SPEC.json --out OUT.pdf`

| Field | Content |
|---|---|
| `pages`, `blocks` | What was produced |
| `language` | `{injected, language, catalog}` from the `/Lang` incremental write |
| `issues[]` | `FONT_NOT_EMBEDDED`, `TYPE3_GLYPHS`, `NO_LANGUAGE_TAG`, `NO_STRUCTURE_TREE`, `LANGUAGE_TAG_FAILED` |

### `html <input.html> --out OUT.pdf [--renderer PATH] [--untagged] [--timeout-ms 8000]`

| Field | Content |
|---|---|
| `renderer` | Path of the binary used |
| `taggedRequested` | Whether tagging was asked for (`--untagged` turns it off) |
| `raw` | Byte scan of the output |
| `issues[]` | Same code set as `build` |

`--renderer` overrides discovery. `blocked NO_HTML_RENDERER` lists what was searched.

### `ocr <pdf> --out OUT.pdf [--langs ko-KR,en-US] [--pages SPEC] [--work-dir DIR]`

| Field | Content |
|---|---|
| `languages` | The recognition languages used |
| `textCharacters` | Characters now extractable from the output |
| `pages_ocred` | How many pages received a layer |
| `perPage[]` | `page`, `observations` (recognized lines) |

The recognized text is drawn in invisible render mode over the untouched page image, so the visual is preserved and selection works. Coordinates come from Vision normalized boxes, converted per page.

## 6. Inspecting

### `check <pdf> [--scan-threshold 0.02]`

| Field | Content |
|---|---|
| `raw` | The byte scan |
| `pageChecks[]` | Per page: `textChars`, `inkRatio`, `likelyScan` |
| `issues[]` | `{code, page?, detail}` |
| `verdict` | `attn` when any page is blank or needs OCR, else `ok` |

Issue codes and their consequences are in `rules/accessibility.md`. `raw` holds the counts the codes derive from:

`bytes`, `version`, `encrypted`, `objectStreams`, `crossReferenceStreams`, `fontFile2`, `fontFile3`, `type0`, `type3`, `structureTree`, `markInfo`, `language`, `images`, `acroForm`, `linearized`, `javascript`, `launch`, `embeddedFiles`, `attachments`

## 7. Invariants that apply to every command

| Invariant | Consequence |
|---|---|
| One JSON object on stdout, nothing else | Wrap the call and parse; never parse a log line |
| All numbers are real numbers | ObjC-bridged values are coerced through `int`/`num`; a string where a number belongs is a bug in a caller's assumption |
| Inputs are never modified | Every writing command takes `--out`; only `metadata --in-place` touches the source |
| A locked input blocks, never guesses | `ENCRYPTED` without `--password`, `BAD_PASSWORD` with a wrong one |
| Paths are resolved to absolute form | A relative path resolves against the working directory at call time |

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| PDF permission and encryption handling | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§7.6) |
| FreeText annotation behaviour | <https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf> (§12.5.6.6) |
| Vision text recognition coordinate convention | <https://developer.apple.com/documentation/vision/vnrecognizedtextobservation> |
| PDFKit password options | <https://developer.apple.com/documentation/pdfkit/pdfdocument> |

### Evidence grade

`LOCAL` throughout: every command, flag, exit code, and output field in this file was read from the implementation and executed on this machine. No field is documented from intent.