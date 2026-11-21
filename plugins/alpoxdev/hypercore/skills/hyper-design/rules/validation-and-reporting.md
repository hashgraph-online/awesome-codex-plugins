# Validation and Reporting

Read before writing the report. This file owns the verification order, the report sections, and what each claim must cite.

## Verification order

1. Re-run `scripts/detect-slop.sh` against the same target and compare rule IDs, severity counts, engine and evidence fields, and the baseline delta when used. Save the before and after JSON under `.hyper/design/<slug>/`.
2. Run the craft-floor checklist (`rules/craft-floor.md` §9) for every changed screen.
3. Run the smallest project build, typecheck, lint, and test commands that cover changed files; inspect failures rather than suppressing them.
4. When rendering is available, inspect the checked widths and the states the surface exposes; otherwise mark rendered items `static_only` or `unavailable`.
5. Check keyboard focus, semantics, contrast where measurable, reduced motion, and responsive overflow affected by the change.
6. Exercise directly affected behavior and preserve copy, routes, form contracts, state transitions, and analytics hooks.
7. Run the independent review (`rules/independent-review.md`) and answer its findings.
8. Validate the saved report with `scripts/validate-report.sh --report .hyper/design/<slug>/report.md` and record residual risk.

## Claim rules

- Do not report “no issues” unless the detector or equivalent static inspection actually ran.
- Do not report a visual pass without rendered inspection.
- Do not report an accessibility pass from a screenshot or CSS source alone.
- Do not turn a context-dependent or review-only heuristic into a confirmed defect.
- Do not call `generic-output risk` an AI-authorship result.
- Do not treat a candidate exception or baseline as suppression or a remediation pass.
- Do not invent product metrics, brand claims, testimonials, users, or source provenance.
- Record every unrun check and why it was unavailable or out of scope.

## Required report sections

Use `assets/report-template.ko.md` by default for every mode except `brief-only`. The report heading is fixed by the validator and reads the same in every mode. Preserve these headings so the validator can inspect the result:

- `# AI Design Slop 정리 결과`
- `## 처리 요약`
- `## Brief inference`
- `## 발견 사항`
- `## 적용한 변경`
- `## 검증`
- `## 남은 위험`

The summary also records the mode, the `brief.md` path or `해당 없음`, detector version and engines, generic-output risk, baseline delta, candidate or persisted waivers with reason, `complete | static_only | unavailable` rendered-evidence status, the craft-floor result, and the review mode (`subagent | self (degraded) | user | 미실행`).

`audit` may state that no changes were applied. `verify` must identify the change or finding set it checked. `design`, `restyle`, and `mockup` list the tokens and files they created or changed. Empty sections are invalid; use an explicit `없음` or `미검증` with a reason.

### WCAG table

A passing report whose render verification is `complete`, and any report carrying a WCAG heading, also carries the WCAG 2.2 table in `assets/report-template.md` (`## Processing summary` copy). The table has one row per listed success criterion (1.4.3, 1.4.11, 2.4.7, 2.4.11, 2.5.8, 2.1.1, 2.1.2, 1.4.10, 1.4.12, 2.5.7, 3.3.8, 3.2.6, 3.3.7); each row is `PASS`, `FAIL`, or `N/A` with a reason and the browser evidence used. A `PASS` without browser evidence is not a pass. The report validator enforces the table structurally. A report with final status `pass` whose render verification is `complete` must carry the full 13-row table, and so must any report carrying a WCAG heading. Each criterion must appear as a pipe-delimited table row with a verdict (`PASS`, `FAIL`, or `N/A`), a reason, and evidence. The row is parsed into cells: the criterion cell holds exactly one SC id (a token match, so `1.4.30` is not `1.4.3`), the verdict cell is exactly `PASS`, `FAIL`, or `N/A` (backticks allowed, case-insensitive), and the reason and evidence cells are both non-empty. A row holding more than one SC id is incomplete, never valid for either; a structurally broken row is rejected with `WCAG_ROW_INCOMPLETE` and a missing row with `WCAG_TABLE_MISSING`; a criterion that appears only in a list, without a table row, is rejected with `WCAG_TABLE_MISSING`. Reports that do neither (a passing `static_only` report with no WCAG heading) are unconstrained by the table, so the legacy valid fixture stays valid.

## Completion decision

- `pass`: all applicable critical guards passed and no user decision remains.
- `review_required`: safe work is complete but a context-dependent or review-only decision remains.
- `blocked`: required evidence, authority, capability, or a critical guard is missing.

A caveated result is valid only when limitations are explicit and no hidden critical failure is presented as passed.

## Sources

> Checked 2026-11-09.

The verification order, claim rules, and report sections are this package's own. The required Korean headings match the package's report template and its report validator.

| Claim | Source |
|---|---|
| The WCAG 2.2 per-criterion table shape and the need for browser evidence per criterion | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |
| The 13 success criteria and their pass conditions | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> |

### Evidence grade

The per-criterion table is this package's contract; each criterion's pass/fail rule is WCAG 2.2 as cited. A `PASS` is only as strong as the browser evidence recorded for that row.
