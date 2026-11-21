# Verification

> A workbook is not finished until the thing you claim about it was checked against the file.

## Gates, in order

| Gate | Command | Passes when | If it fails |
|---|---|---|---|
| Structural | `inspect <file>` | parses, no `E_*` warning | Report the failure; do not answer from the file |
| Coverage | `verify <file> [--max-cells N]` | `cells_complete == pass` | The sheet was cut short; every count covers only the cells read, so say so |
| Integrity | `verify <file>` | no `errorLiterals`, no mismatched cache, no cycle | List the cells; fix or disclose |
| Preservation | `patch …` output | `verification.status == "pass"` | Nothing was written; fix the operation |
| Read-back | re-`inspect` or an independent reader | opens, same sheet names, same cell values | Treat as a failed write |
| Cache | `recalc` then `verify` | `cache_complete == pass` | Report which formulas stayed uncached and why |

## What each gate actually proves

- **Structural** proves the package is readable and the parts the reader needs exist. It does not prove values are right.
- **Integrity** proves each recomputed formula agrees with the stored value, that no cell holds an error literal, and that no formula depends on itself. A formula the evaluator cannot compute is `unevaluated`, never `pass`, and one cell that makes the evaluator raise does not suppress the report for the others: `unevaluated` names the cell, the formula, and the error class.
- **Preservation** proves untouched parts are byte-identical. It does not prove the changed part is what the user wanted; the report does that.
- **Read-back** proves a second parser accepts the file. Without an independent reader installed, say the check was limited.
- **Cache** proves a reader that does not calculate sees a value. It does not make the cached value authoritative; `fullCalcOnLoad` keeps Excel recomputing from source.

## Numbers in the report

Three labels, used consistently:

- `캐시 값` — read from `<v>` in the file. State the cell.
- `재계산 값` — produced by the bundled evaluator. State the formula.
- `미검증` — the evaluator does not implement the function. State the function name.

A derived number (a growth rate, a difference) shows its inputs and formula, not just the result.

## What not to claim

- Do not say "수식 검증 완료" when some formulas were unevaluated.
- Do not say "서식 유지" from a visual glance; cite the digest comparison.
- Do not say "엑셀에서 열린다" unless a real spreadsheet engine opened it on this machine.
- Do not say "값이 맞다" when the only evidence is that the formula ran without error.

## Repair loop

Verification failure gets one repair and one re-verify. If the same check fails twice for the same reason, stop and report: what failed, what was tried, what the user must decide. Never retry blindly and never weaken a check to make it pass.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Gate order (structural, integrity, preservation, read-back, cache) | this package's design; each gate is one command in `assets/tools/` |
| `cache_complete` returns `partial` while any formula lacks a value | `verify_formulas.py`, read on 2026-11-13 |
| `fullCalcOnLoad` makes Excel recompute from source on open | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.calculationproperties.fullcalconload> |
| An independent read-back is available via `uv run --with openpyxl` | run on this machine 2026-11-13; openpyxl 3.1.5 |

### Evidence grade

`LOCAL` for the gate design and the tool fields; the recalculation row is Microsoft's documentation.
