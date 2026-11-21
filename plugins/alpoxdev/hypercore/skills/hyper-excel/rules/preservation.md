# Preservation

> An edit to an existing workbook is a surgical change, not a rewrite.

## The contract

Only the parts named by an operation may change. Everything else in the zip stays byte-identical. `patch_workbook.py` enforces this: after writing, it re-opens the result, digests every part, and refuses the output if a part it did not touch changed. Nothing replaces the original unless that check passes.

What this protects, in the order users notice its loss:

| Part | Lost by | Kept by |
|---|---|---|
| charts | most library round-trips, some chart types silently drop | untouched part copy |
| images and logos | libraries that rebuild `drawings/` | untouched part copy |
| cell styles, theme colors | rebuilding `styles.xml` with a different theme | append-only style table |
| conditional formats | writers that emit `dxfId` without a `dxfs` entry | registered `dxfs` entry |
| data validation dropdowns | writers that skip `dataValidations` | node insertion |
| pivots and pivot cache | any re-save that does not understand pivots | untouched part copy |
| VBA | writers that strip `vbaProject.bin` | untouched part copy |
| comments, hyperlinks, defined names | partial writers | untouched part copy |
| print areas, headers, page setup | partial writers | untouched part copy |

## Rules

1. **Default to patch.** If the user says 수정, 바꿔, 고쳐, or names a cell, patch. Rebuilding loses parts even when the visible result looks right.
2. **Never overwrite in place without a passing check.** Use `--out` when the destination differs; use `--in-place` only when the user wants the same file, and then the tool verifies before replacing.
3. **A rebuild is a different request.** If patch cannot express the change (a new pivot, a restructured sheet), say what a rebuild would lose, then rebuild only with the user's agreement.
4. **Macros are never executed.** A `.xlsm` patch copies `vbaProject.bin` through untouched. Do not strip it, do not edit its bytes, do not claim to have tested it.
5. **Styles are appended, never renumbered.** A new number format takes an id above the existing custom range, and a new `cellXfs` entry is appended. Renumbering breaks every cell that referenced the old index.
6. **Shared strings are left alone.** Written strings use `inlineStr`, so `sharedStrings.xml` is not modified and no index in any other cell moves.
7. **A formula written by patch has no cache.** Say so, or run `recalc` so non-calculating readers see a value.
8. **The stale calculation chain goes.** After an edit, `calcChain.xml` describes positions that may no longer exist; `--strip-calc-chain` removes it and Excel rebuilds it.

## When the file is locked or open

A workbook open in Excel cannot be replaced on macOS in the same path by some writers. Write to `--out`, verify, then tell the user the new path. Do not retry a locked write in a loop.

## Reporting preservation

Name the parts. "건드리지 않은 파트 23개 다이제스트 일치" is evidence; "서식 유지됨" is a claim. List `touchedParts` from the tool output verbatim.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| `patch_workbook.py` proves untouched parts by SHA-256 and refuses a changed part | run on 2026-11-13; `untouchedPartsPreserved: true` on a 19-part file with an injected pivot cache |
| openpyxl drops an unmodelled pivot part and its rels on load/save | measured 2026-11-13 with openpyxl 3.1.5 under `uv run --with openpyxl` |
| openpyxl strips `xl/vbaProject.bin` unless `keep_vba=True` | measured 2026-11-13; bytes identical with the flag |
| `calcChain.xml` describes positions that may no longer exist after an edit | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.calculationchain> |

### Evidence grade

`LOCAL` for every measured row; the `calcChain.xml` row is Microsoft's file-format documentation.
