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

## Completion decision

- `pass`: all applicable critical guards passed and no user decision remains.
- `review_required`: safe work is complete but a context-dependent or review-only decision remains.
- `blocked`: required evidence, authority, capability, or a critical guard is missing.

A caveated result is valid only when limitations are explicit and no hidden critical failure is presented as passed.

## Sources

> Checked 2026-11-07. No external source was used in this file.

The verification order, claim rules, and report sections are this package's own. The required Korean headings match the package's report template and its report validator.
