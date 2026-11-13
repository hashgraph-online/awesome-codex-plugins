# rhwp command map

## 1. Why this map exists

Every command below was run against the rhwp v0.9.0 macOS aarch64 release binary. The flags, JSON keys, and exit codes are transcribed from those runs, not from the project's prose. When rhwp changes, rerun the command and trust the run over this file; `rhwp capabilities` prints the binary's own machine-readable contract and is the authority when the two disagree.

Read only the section for the command you are about to run.

## 2. The command set

| Command | Purpose | Notes |
|---|---|---|
| `info FILE` | file size, HWP version, compression, encryption, 배포용 flag | human text only, no JSON |
| `explain FILE --json` | format, page count, paragraph and footnote counts, tables, encryption | the fastest "what is this" answer |
| `digest FILE --json` | `excerpt`, `pageCount`, `format`, outline | for reporting, not for editing |
| `export-text FILE --json` | page text under `pages[].text` | `--json` does not write files; without it, `-o DIR` receives one TXT per page (default `output/`) |
| `export-structure FILE --json` | outline tree with section and paragraph indices | the indices you feed to edits |
| `export-tables FILE --json` | `tables[].cells[]` with `row`, `col`, `text` | table index is the order they appear |
| `table-to-csv FILE -o OUT.csv --json` | every table flattened to CSV | one file per table when several exist |
| `fields FILE --json` | named form fields with current values | the only source of legal field names |
| `form-value FILE --section N --para N --ctrl N --json` | one form control's value | needs the three coordinates, not a field name; `fields --json` is the way to read a 누름틀 value back |
| `search FILE "text" --json` | `matchCount` and match locations | argument order is file then text |
| `word-count FILE --json` | character and word totals | useful for a length constraint |
| `scaffold spec.json --format hwpx -o OUT` | build a document from a JSON spec | `--format hwpx` is the only accepted value (§5) |
| `convert IN OUT.hwp --verify --json` | **always writes HWP5**, and the output path must end in `.hwp`; a `.hwpx` target is refused with a pointer to `export-hwpx` | also strips the 배포용 read-only flag, which is its stated purpose |
| `export-hwpx IN OUT.hwpx --verify` | HWP or HWPX to HWPX | the only HWP-to-HWPX path; `--verify-pages` compares rendered page counts instead and exits 4 on mismatch |
| `edit <sub> IN -o OUT --json` | all mutations | without `-o` writes `<name>_<sub>.<ext>` beside the source |
| `run plan.json --json` | a list of edit steps from one file | the step schema is narrow; see §6 |
| `csv-to-table FILE --csv IN.csv --table N -o OUT` | replace a table's contents from CSV | the CSV shape must match the table's row and column count |
| `import-pdf IN.pdf OUT.hwpx --json` | PDF to HWPX, either `fidelity` (positioned text boxes, the default) or `editable` (reflowed paragraphs) | v0.9.0 feature; report `pageCount` and the `execution` block, and note that allocation limits are unproven (`addressSpaceLimitEnforced: false` on macOS) |
| `verify FILE --expect-*` | assertions over the output | exit codes in §7 |
| `hwpx-roundtrip FILE` | parse, serialize, reparse, compare | the HWPX fidelity gate |
| `hwp5-roundtrip FILE` | same for HWP5 | fails on an HWP3 or HWPX input |
| `layout-anomaly FILE --json` | overflow, off-canvas, overlap, and empty-page counters | compare counts against the input |
| `threat-scan FILE --json` | known malicious-pattern scan | run before editing untrusted files |
| `armor FILE --json` | injection-signal scan of document text | `clean` and the signals it found |
| `inspect <axis> FILE --json` | `hidden-text`, `unicode`, `watermark`, `injection` | one axis per call |
| `scan DIR --json` | batch format probe of a directory | reports extension versus magic mismatches |
| `batch --kind <kind> --json` | run one command over newline-delimited paths | stdin is the path list |
| `export-pdf`, `export-svg`, `export-png` | visual output | needs the Skia build and the webfont cache |
| `capabilities` | the binary's own command contract as JSON | the version check the probe uses |
| `mcp-serve` | stdio MCP server exposing the same surface | for a host that speaks MCP, not for a shell task |

## 3. Character and paragraph formatting

`apply-char-format` and `apply-para-format` take a `--props` JSON object. Unlike `set-cell-props`, these **reject unknown keys**: an unrecognised property exits 2 with `--props 에서 적용할 글자 서식 키를 찾지 못했습니다 (키 이름 확인)`. So the key set is discoverable by trying, and it is short.

| Key | Type | Verified |
|---|---|---|
| `bold`, `italic`, `underline` | boolean | accepted, exit 0, `hwpx-roundtrip` PASS |
| `fontSize` | integer (HWPUNIT-like size value) | accepted |
| `fontId` | integer, index into the document's font table | accepted, **no bounds check**: `{"fontId":999}` exits 0 on a document with three fonts |
| `baseSize`, `textColor`, `shadeColor`, `strikeout` | see `CharShape` in `rhwp export-ir-schema` | the IR schema defines them; `color` and `strike` as key names are rejected |

Addressing is `--section`, `--para`, `--offset`, `--count` with `--count` omitted meaning "to the end of the paragraph". `apply-para-format` addresses with `--section`/`--para` and a `--props` such as `{"alignment":"center"}`.

**There is no command that lists the font table.** `{"fontId":3}` is accepted whether or not font 3 exists, so a guessed font id silently produces a document that references a font the reader has to substitute. When the user asks for a specific typeface, say this: the CLI can apply a font by index, it cannot tell you which index is 함초롬돋움. Setting a body's typeface by name therefore stays out of this skill, and the request is reported as a limit rather than attempted.

## 4. JSON keys you will actually read

| Command | Keys |
|---|---|
| `explain` | `format`, `pageCount`, `paragraphCount`, `footnoteCount`, `endnoteCount`, `encrypted`, `tables[]`, `fields`, `summary` |
| `digest` | `excerpt`, `pageCount`, `paraCount`, `format`, `outline`, `nextStep`, `truncated` |
| `export-text` | `pages[].text`, `pageCount`, `omittedCount`, `truncated` |
| `export-structure` | `mode`, `nodeCount`, `structure` |
| `search` | `matchCount`, `totalMatchCount`, `matches[]`, `omittedCount`, `truncated` |
| `fields` | `fieldCount`, `fields[].name`, `fields[].value`, `textSecurity` |
| `export-tables` | `tableCount`, `tables[].index`, `.rows`, `.cols`, `.cells[].row`, `.col`, `.text`, `.rowSpan`, `.colSpan` |
| `word-count` | `charCount`, `wordCount`, `paragraphCount`, `sectionCount`, `pageCount` |
| `edit replace-text` | `replacedCount`, `changedPages`, `occurrence`, `find`, `replace`, `untrustedFields` |
| `edit set-cell` | `changedPages`, `table`, `row`, `col`, `outputFormat` |
| `edit fill-fields` | `filledCount`, `filled[]`, `notFound[]`, `ambiguous[]`, `confusable[]`, `changedPages` |
| `edit insert-*` | `changedPages`, `section`, `paragraph`, `control` |
| `convert` | `format`, `output`, `bytes`, `verify.identical`, `verify.diffCount` |
| `run` | `steps[]` with per-step results, `invalid[]`, `inputSha256`, `outputSha256`, `assertions`, `changedPages` |
| `hwpx-roundtrip`, `hwp5-roundtrip` | exit code only; human text names the first difference |
| `layout-anomaly` | `hasSignal` plus `overflowCount`, `offCanvasCount`, `overlapCount`, `textOverlapCount`, `storedLineEscapeCount`, `emptyPageCount` |
| `armor` | `clean`, `armoredText`, `injectionSignals`, `signalCount`, `safety` |
| `threat-scan` | `clean`, `findingCount`, `findings[]`, `highestSeverity`, `notes` |
| `inspect hidden-text` | `clean`, `hiddenCharCount`, `hiddenText[]`, `thresholdPt` |
| `inspect unicode` | `clean`, `findingCount`, `findings[]`, `kindCounts`, `severityCounts` |
| `verify` | exit code only |
| any command | `schemaVersion`, `source`, `untrustedContent`, `untrustedFields` are added to every envelope |

`untrustedContent` and `untrustedFields` are not decoration: the tool marks which returned strings it considers attacker-controlled (document text, and `oldText` from a `set_cell` result). When you paste a field from a response into a later command, check whether it was listed there first.

## 5. Scaffold spec

`scaffold` accepts only `--format hwpx`; every other value is rejected with `지원하는 --format 은 hwpx 뿐입니다`. To get an HWP5 file, scaffold HWPX and then `convert IN OUT.hwp`.

The spec is deserialized strictly: an unknown field fails the whole run with ``unknown field `bold`, expected one of `type`, `level`, `text`, `rows`, `cell_align` ``. That error is the schema documentation, so read it rather than deleting keys until the run passes.

| Field | Meaning |
|---|---|
| `version` | spec version string, `"1"` |
| `title` | document title, used as the first paragraph |
| `font` | base font family name |
| `page_size` | `width_mm`, `height_mm` (A4 is 210 × 297) |
| `outline_numbering` | array of up to seven `{text, num_format}` entries, one per heading level |
| `blocks[]` | `{"type": "heading", "level": 1..7, "text": "..."}` |
| | `{"type": "paragraph", "text": "..."}`, newlines inside `text` split into runs |
| | `{"type": "table", "rows": [[...]], "cell_align": "left"}` or a per-cell alignment array |

`num_format` values: `digit` (1, 2, 3), `hangul_syllable` (가, 나, 다), `circled_digit` (①, ②, ③). Verified output for the seven levels with `digit`, `hangul_syllable`, `digit`, `hangul_syllable`, `digit`, `hangul_syllable`, `circled_digit` and the texts `^1.`, `^2.`, `^3)`, `^4)`, `(^5)`, `(^6)`, `^7`:

```
1.갑
가.을
1)병
가)정
(1)무
(가)기
①경
```

The `text` field is the literal prefix before each number, so a trailing space in the spec is a trailing space in the document. Omit the space to match the packed form governments usually type.

## 6. What `run` can and cannot do

`run` executes a plan file with `planVersion`, `input`, `output`, and `steps[]`. `planVersion` must be the string `"1.0"` - `"1"` fails with `planVersion "1.0" 이 필요합니다` and exit 2. Each step's `action` is a tagged union of exactly eight values, published by `rhwp export-plan-schema`:

| `action` | Required step fields |
|---|---|
| `replace_text` | `find`, `replace`, optional `occurrence`, `caseSensitive` |
| `set_cell` | `table`, `row`, `col`, `text`, optional `keepStyle` |
| `fill_fields` | a field-name to value map |
| `set_checkbox` | the checkbox target |
| `fill_template`, `repeat_and_fill_paragraph_block`, `repeat_and_fill_table_rows`, `import_paragraph_block` | single-step templates; they cannot be combined with other steps |

Every step also accepts an `if` condition. An unknown `action` is **not** a schema error at the top level: it lands in the response's `invalid[]` array with the reason `알 수 없는 action`, and the command exits 2 without writing the output file. Read `invalid[]`, not just the exit code.

A successful run reports per-step results plus `inputSha256` and `outputSha256`, so a run can be proven to have produced a specific file from a specific input.

Prefer individual `edit` calls when a step fails: the failure names the subcommand and its options, which the plan schema does not.

## 7. Exit codes

The binary publishes its own table; `rhwp capabilities --json | jq .exitCodes` prints this one.

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | runtime failure: read, parse, render, or write |
| 2 | usage error: missing argument, unknown option or command, page range exceeded |
| 3 | a verification assertion failed: `convert`/`export-hwpx --verify` IR difference, the three `edit ... --verify` write-back mismatches, `run` plan assertions unmet, `render-diff --json` visual regression, `layout-anomaly --strict` confirmed signal |
| 4 | `--verify-pages` page-count mismatch |

Two practical consequences. A failed assertion is exit 3 and not 1, so a script that only fails on non-zero is safe but a script that logs "exit 1 = parse error" is not. A plain `rhwp verify FILE` with no expectation exits 2. Password-protected input without `--password` exits non-zero with a parse error naming the encryption.

## 8. Formats and what each one allows

| Input | Read | Edit | Write back as |
|---|---|---|---|
| HWPX | yes | yes | HWPX (native) |
| HWP 5.x | yes | yes | HWP5 (native) |
| HWP 3.x | yes | yes | **HWP5** - the 3.x writer does not exist, so the result is a format upgrade |
| HML | yes when non-empty and valid | limited | HML only when the source was HML; otherwise `HML_SOURCE_REQUIRED` |
| Encrypted HWPX | only with `--password` | same | same format |
| PDF | through `import-pdf` into HWPX or HWP | the import is a reconstruction, not an edit | HWPX by default |
| DOCX, XLSX, PPTX, ODT | no | no | - |

Rendering (`export-pdf`, `export-svg`, `export-png`) needs `--features native-skia` in the build and downloads a Korean webfont into `~/.cache/rhwp/webfonts` on first use. Without network access and without that cache, rendering fails while text, table, and edit commands keep working.

## 9. Table surgery

Structure edits exist and they work; what they do not do is validate your intent.

| Need | Command | Notes |
|---|---|---|
| change a cell's text | `edit set-cell --table N --row R --col C` | text only; coordinates from `export-tables` |
| change one column's widths | `edit set-column-widths --table N --widths "12000,24000"` | HWPUNIT, and the count must equal the column count or the run fails with `열 폭 개수 … 와 다릅니다` |
| merge a rectangle | `edit merge-cells --table N --row R --col C --end-row R2 --end-col C2` | inclusive corners |
| split one merged cell | `edit split-cell --table N --row R --col C` | |
| add or remove a row or column | `edit insert-row`, `insert-col`, `delete-row`, `delete-col` | `--below` on row insert, `--right` on column insert |
| resize by dragging metaphor | `edit resize-table --row R --col C [--vertical]` | height or width of one cell, optionally propagated |
| set table or cell properties | `edit set-table-props --props '<json>'`, `set-cell-props --table N --row R --col C --props '<json>'` | **properties are not schema-checked**: an unknown key is accepted, reported as a successful change, and writes a file that differs from the input in ways no counter tells you about |
| reshape a whole table | `edit fit-table`, `move-table`, `merge-table` | |

Two consequences for how you work:

- After any structural edit the table index and the cell coordinates can move. Re-read `export-tables` before the next coordinate edit ([edit-safety.md](edit-safety.md) §3).
- Because `set-cell-props` accepts junk silently, verify a property change by the thing you actually wanted (re-read the widths, re-render the page) rather than by the command's exit code.

## 10. Things the CLI does not do

- `insert-table` takes `--rows`, `--cols`, `--section`, `--para`, `--offset` and no cell text; fill cells with `set-cell` afterwards.
- `csv-to-table` needs an existing table whose shape matches the CSV; it does not append rows.
- HML saving is refused unless the source was HML.
- `set-cell-props` and `set-table-props` take an untyped JSON bag; the tool does not reject keys it does not know.
- There is no way to ask the parser for the Hangul application's own rendering; `export-pdf` renders with rhwp's engine and can differ in line breaks from Hangul.

## 11. Verified runs

Every claim about a command in this file comes from a run, not from reading the project's description. Two rounds were executed on 2026-11-13 and 2026-11-14 against the release binary.

Table surgery (§9), on a scaffolded two-column, two-row HWPX, each output passing `hwpx-roundtrip`:

| Run | Result |
|---|---|
| `edit set-column-widths --table 0 --widths "12000,24000"` | exit 0, `widths: [12000, 24000]` |
| `edit set-column-widths --table 0 --widths "12000"` (one for a two-column table) | exit 1, `열 폭 개수 1 가 표의 열 수 2 와 다릅니다` |
| `edit merge-cells --table 0 --row 0 --col 0 --end-row 0 --end-col 1` | exit 0, `endRow: 0, endCol: 1` |
| `edit insert-row --table 0 --row 1 --below` | exit 0, `below: true` |
| `edit set-cell-props --row 1 --col 1 --props '{"bogus":1}'` | exit 0, file written, byte-identical to the same call with a valid property |
| `edit set-cell-props --row 9 --col 9` on a 2×2 table | exit 2, `좌표가 격자를 벗어났습니다` |

Behaviour that changed how this file describes the tool:

| Run | Result | What it forced |
|---|---|---|
| `hwpx-roundtrip legacy.hwp` (an HWP3 file) | `[FORMAT_SKIP]`, **exit 0** | §2 and `verification.md` now say to read the status word; a skip is a silent false pass |
| `hwp5-roundtrip plan.hwpx` (an HWPX file) | `[FORMAT_SKIP]`, exit 0 | same |
| `convert a.hwpx out.hwpx` | exit 1, `convert 출력 경로는 .hwp 확장자여야 합니다` | `convert` is HWP5-only; HWP to HWPX is `export-hwpx` |
| `run` with `planVersion: "1"` | exit 2, `planVersion "1.0" 이 필요합니다` | §6 pins the version string |
| `run` with `action: "insert_text"` | exit 2, `invalid[]` names `알 수 없는 action` | §6 lists the eight real actions and says to read `invalid[]` |
| `edit fill-fields --data '{"myMsg01":"홍길동"}'` on the form sample | exit 0, `filledCount: 1`, read back as `myMsg01=홍길동` | `fill-fields` takes `--data`, not `--set` |
| `form-value --name myMsg01` | exit 2, unknown option | form value needs `--section/--para/--ctrl`; fields are read back with `fields --json` |
| `edit replace-text --find 추진 --occurrence 0` | `replacedCount: 1` and exit 0; `--occurrence 1` gave 0 and wrote no file | `--occurrence` is zero-based |
| `import-pdf out2.pdf imp.hwpx` | exit 0, `pageCount: 1`, `execution.filesystemNetworkSandbox: false` | PDF import works but its isolation is not what the flag names suggest; reported as such |
| `export-hml a.hwpx -o x.hml` | exit 1, `HML_SOURCE_REQUIRED` | HML output is source-locked |
| `edit replace-text pw.hwpx --password 123456 -o out.hwpx` | exit 0, `replacedCount: 42`; `info out.hwpx` reports `암호화: 아니오` | an edit of an encrypted document is a declassification, so `edit-safety.md` §2 states it and §6 refuses without consent |
| `convert pw.hwpx out.hwp --password 123456` | exit 0, `passwordProtected: false`, `wasDistribution: false` | conversion drops the password too, and the boolean in the JSON is the cheap way to report it |

## Sources

> Checked 2026-11-13 against the rhwp v0.9.0 macOS aarch64 release binary (`~/.cargo/bin/rhwp` held an older 0.7.15 build that lacks `edit`, `scaffold`, and `convert`, so the release tarball was used).

- rhwp repository and release assets: <https://github.com/edwardkim/rhwp>
- Scaffold schema: `src/scaffold/schema.rs` in that repository; `rhwp export-plan-schema` prints the plan schema the binary enforces
- Project agent guides: `mydocs/manual/rhwp_cli_skill_guide.md`, `mydocs/manual/agent_toolkit_cli.md`
- crates.io metadata (0.9.0 published 2026-11-08): <https://crates.io/crates/rhwp>
