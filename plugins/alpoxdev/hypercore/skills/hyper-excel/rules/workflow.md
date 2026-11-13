# Workflow

> Pick the mode from the request, inspect before acting, and report in a fixed shape.

## Mode selection

| The request mentions | Mode | First tool call |
|---|---|---|
| 무엇이 들었는지, 구조, 시트 목록, 수식 위치 | `inspect` | `inspect <file>` |
| 얼마인지, 몇 개인지, 어디가 제일 큰지 | `inspect` | `inspect <file> --rows 20` |
| 검사, 검토, 맞는지, 오류, 합계 빠짐 | `verify` | `verify <file>` |
| 바꿔, 수정, 고쳐, 값 넣어, 시트 추가 | `patch` | `inspect` then `patch` |
| 만들어, 생성, 보고서, 양식, 템플릿 | `build` | `inspect` the source data first |
| CSV·텍스트를 엑셀로 | `profile` → `build` | `profile <csv>` |
| 다른 프로그램에서 값이 안 보인다 | `recalc` | `inspect` then `verify` |

Two requests can combine: "매출 요약 만들어줘" on an existing file is `inspect` → `build` of a new sheet, not a patch of the original, unless the user named the cells.

## Step order

1. **Baseline.** `doctor` once, then `inspect` the input file. Record: sheet names, dimensions, formula count, error cells, whether a cache exists, macros, external links. Quote these facts, do not summarize them away.
2. **Scope.** State the mode and the exact cells, ranges, or sheets that will change. If the user named a cell, that cell; if they named a whole sheet, say which ranges you are touching.
3. **Work.**
   - `inspect`/`verify`: read only, no writes.
   - `patch`: one `--set-value`/`--set-formula`/`--set-format`/… per change, all in one call, with `--out` to a new path unless the user asked for in-place.
   - `build`: write a JSON spec first so the structure is reviewable, then build.
   - `recalc`: after any build that wrote formulas, so readers that do not calculate see values.
4. **Verify.** `verify` for anything with formulas; for a patch, the tool already proves untouched parts by digest and rejects on mismatch. Re-`inspect` the output.
5. **Read back.** Prefer an installed independent reader (`openpyxl` under `uv run --with openpyxl`) to confirm a third party opens the file. If no reader exists, say the read-back was limited to this toolchain's parser.
6. **Report** in the shape below.

## Report shape

```
## 결과
<한 문장: 무엇을 했고 어디에 있는지>

- 경로: /abs/path/파일명.xlsx
- 시트: <이름들>
- 바뀐 것: <셀/범위 목록 또는 "새로 만든 파일">
- 검증: <verify 요약 — 수식 n개 재계산, 불일치 m개, 미검증 k개>
- 보존: <건드리지 않은 파트 n개 다이제스트 일치 / 해당 없음>
- 확인한 것: <읽어서 본 값, 열어본 결과>
- 못 한 것: <없으면 이 줄을 빼고, 있으면 무엇을 왜 못 했는지>
```

Never write "완료했습니다" without the verification line. When a check could not run, the line says so and the heading says why.

## Numbers

- A value read from a cached cell is reported as **캐시 값**, quoting the cell address.
- A value this skill computed is reported as **재계산 값**, with the formula that produced it.
- A value the user asked for that depends on a formula the evaluator does not support is reported as **미검증** with the function name. Never fill it in from intuition.

## Ambiguity

If the target sheet or cell is ambiguous, list the candidates from the `inspect` output and ask once. Do not pick a sheet by position. If the user gave a range but the data extends past it, do the named range and mention the extra rows in the report rather than silently expanding scope.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Mode selection by request verb, and inspecting before answering | this package's design, exercised by `assets/tools/hyper_excel.py inspect` / `verify` on 2026-11-13 |
| Distinguishing a cached value from a recomputed one in a report | `verify_formulas.py` output fields `totals.uncached` and `mismatches`, read on 2026-11-13 |
| A patch leaves the original untouched when verification fails | `patch_workbook.py` `verification.status`, observed with a forced digest mismatch |

### Evidence grade

`LOCAL` — the mode table, the step order, and the report shape are this skill's chosen contract. The tool behavior rows are reproducible with the bundled scripts.
