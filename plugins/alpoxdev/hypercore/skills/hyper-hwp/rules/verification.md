# verification

## 1. What counts as proof

A claim about a document is proved by a command whose output you can quote. Four kinds exist, cheapest first:

| Level | Claim | Command |
|---|---|---|
| Identified | this file is HWPX, 4 pages, not encrypted | `rhwp explain FILE --json` |
| Changed | the edit reported the pages it touched | the edit's own JSON: `changedPages`, `replacedCount`, `filledCount` |
| Parsed | the output still parses to the same intermediate representation | `rhwp hwpx-roundtrip OUT` or `rhwp hwp5-roundtrip OUT` (check for `PASS`, not just exit 0), or a conversion with `--verify` |
| Correct | the change is what the user asked for | `rhwp export-text OUT --json`, then read the text; `rhwp verify OUT --expect-contains "..."` |

Level two without level four is the common failure: a `replacedCount` of 1 proves something matched, not that the right thing matched. Level three without level four proves the file is intact, not that it is right.

## 2. Report shape

Write `.hyper/hwp/[slug]/report.md` when the job has more than one step or produces more than one artifact. Keep it short:

```markdown
# [작업 이름]

## 입력
- 경로, 형식, 쪽 수, 암호·배포용 여부 (`explain` 출력에서)

## 실행
| 순서 | 명령 | 핵심 결과 |
|---|---|---|
| 1 | `rhwp edit replace-text ...` | replacedCount=2, changedPages=[0] |
| 2 | `rhwp export-text ...` | 새 문자열 확인 |

## 검증
- 왕복: `hwpx-roundtrip` 종료 0
- 조판: 발견 0건 (입력 0건)
- 재확인: `verify --expect-contains` 종료 0

## 산출물
- 절대 경로, 형식, 쪽 수, 바이트

## 하지 못한 것
- 요청 중 도구가 만족하지 못한 부분과 그 이유

Result: done - [한 줄 요약]
```

A one-step job needs no report file: put the same facts in the chat answer and end with the `Result:` line there.

## 3. The verification ladder

Run the checks the change actually threatens, in this order, and stop at the first failure to diagnose.

1. **Read-back.** Export text and confirm the new string is present and the old one absent. This catches a wrong occurrence, a wrong table index, and a no-op edit.
2. **Structural gate.** `hwpx-roundtrip` for HWPX, `hwp5-roundtrip` for HWP5. Both parse, serialize, and reparse; a diff means the edit broke something the read-back cannot see.

   **Read the status word, not only the exit code.** The gate prints `[PASS]`, `[FAIL]`, or `[FORMAT_SKIP]`, and `FORMAT_SKIP` exits **0**. Handing an HWP5 file to `hwpx-roundtrip` (or an HWPX file to `hwp5-roundtrip`, or an HWP3 file to either) therefore looks like a pass while nothing was checked. The line names the real format: `확장자 위장: 실체 HWP3 — HWPX 게이트 범위 밖`. A script that trusts `$?` here records a false pass; grep for `[PASS]`.
3. **Layout gate.** `layout-anomaly OUT --json` and compare each count (`overflowCount`, `offCanvasCount`, `overlapCount`, `textOverlapCount`, `storedLineEscapeCount`, `emptyPageCount`) and `hasSignal` with the input's. A count that grew after an edit is a regression the roundtrip check will not catch. `--strict` turns a confirmed signal into exit 3.
4. **Assertion gate.** `rhwp verify OUT --expect-pages N --expect-contains "문자열" --expect-min-chars N --expect-format hwpx` for the facts the user stated (page count, required text).
5. **Roundtrip writes files.** Both roundtrip commands write a reassembled document and an `inventory.tsv` under `output/poc/task1315/` (HWPX) or `output/poc/task1552/` (HWP5), relative to the working directory, unless `-o` names a folder. Point `-o` at a scratch directory so the artifacts do not land inside the user's document folder.

6. **Visual gate, only when asked.** `export-pdf` or `export-png`, then look at the page. This is the only way to see a line break that moved. It needs the Skia build and the webfont cache; when they are absent, say so instead of claiming the layout is fine.

## 4. Terminals

| Terminal | When |
|---|---|
| `done` | artifact exists, the checks the change threatens passed, and the answer states what changed |
| `prerequisite_missing` | the probe reports `rhwp_not_found` or `version_too_old`; name the install or upgrade path and stop |
| `awaiting_input` | the target text, field name, or output path was not given and cannot be inferred from the file |
| `blocked` | a check failed after two repair attempts, or the file cannot be parsed at all |

A `blocked` report carries the failing command, its exit code, and the first line of its error. Never report `done` for a run whose last check failed.

## 5. What must not be claimed

- That a document opens correctly in the Hangul application. It is not installed here and no command proves it.
- That a converted HWP3 file is still HWP3.
- That the layout matches Hangul's own pagination. rhwp renders with its own engine; line breaks can differ.
- That an edit is safe because the roundtrip passed; the roundtrip proves the format, not the intent.
- That the roundtrip passed when its output says `[FORMAT_SKIP]`. That word means the file was the wrong format for that gate and nothing was verified.
- That a table extraction is complete when `export-tables` returned fewer tables than the document shows; nested or text-box tables are the usual gap, and it is reported as a gap.

## Sources

> Checked 2026-11-13 by running each gate against scaffolded, converted, and edited documents with rhwp v0.9.0 on this machine.

- Exit codes and flags observed: `verify` returns 0 pass, 3 mismatch, 1 read failure, 2 usage error; `hwpx-roundtrip` and `hwp5-roundtrip` return 0 or non-zero with a named first difference; `layout-anomaly --strict` returns non-zero when it finds anything
- `layout-anomaly` JSON carries `hasSignal` and six counters; a scaffolded one-page document returns `hasSignal: false` with every counter at 0, and `--strict` exits 0
- `convert --verify` reports `verify.identical` and `verify.diffCount`; a HWPX→HWP5 conversion of a scaffolded table document returns `identical: true`
- rhwp repository: <https://github.com/edwardkim/rhwp>
