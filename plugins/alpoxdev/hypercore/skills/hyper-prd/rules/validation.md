# Validation

Use this rule before saving and in every `review`. It owns the per-mode completion evidence, the pre-save checklist, the blocking-question handling, and the optional no-context reader test.

## 1. Completion evidence per mode

| Mode | Evidence that the run is done | What is not evidence |
|---|---|---|
| `create` | `prd.md` saved at `.hyper/prd/<slug>/prd.md`, and every pre-save checklist item passes | A chat message describing the document |
| `update` | The changed sections, a change-history row with the date and what changed, and every checklist item passing | Rewriting the whole file while claiming a section edit |
| `review` | A pass/fail table per checklist item, with the failing item named and its location | Editing the file, or a prose verdict without a table |

`review` never edits. When a review finds a fix, it names the fix and stops; applying it is an `update`.

## 2. Pre-save checklist

Run each item over the saved text, not over the intention behind it.

| # | Check | Fails when |
|---|---|---|
| 1 | Every `FR-###` maps to a goal or a `P1`/`P2`/`P3` story | A requirement cites nothing, or cites only a non-goal |
| 2 | Every metric has a target, a measurement means, and a measurement time | One of the three is missing, or the target has no unit |
| 3 | Non-goals actually cut scope | A non-goal restates a goal, or could be removed without changing what is built |
| 4 | No vague word remains | `빠르게`, `쉽게`, `적절히`, `충분히`, `사용자 친화적`, `fast`, `easy`, `appropriate`, `robust`, `seamless` appear as a requirement |
| 5 | No implementation mechanism appears | A file path, function or type name, newly chosen library, or invented schema name is named outside an existing external constraint |
| 6 | Every story has a happy path and a failure-or-edge scenario citing `FR-###` ids | One path is missing, or a scenario cites no requirement |
| 7 | Every `A-###` has an evidence grade and a consequence | An assumption sits in the body as fact, or has no "if wrong" line |
| 8 | `[확인 필요: …]` appears at most 3 times outside the release gate tables | A fourth inline marker exists in the prose sections |
| 9 | No empty or `N/A` section remains | A heading has no content, or says `N/A`/`TBD` |
| 10 | The handoff block is complete | It lacks platforms, size, P1 scope, remaining blocking questions, or next-stage inputs |
| 11 | The meta block carries status, platforms, size, and the updated date | One field is missing |
| 12 | The must-not-change behavior is stated or explicitly declared absent | The change touches an existing flow and the section is missing |
| 13 | Every `[M]` and `[M-조건]` item of each decided platform appears in that platform's release gate table with a conclusion | A decided platform's checklist has an `[M]` or `[M-조건]` item with no row, or a row with no conclusion |
| 14 | No breakpoint is named after a device | A breakpoint reads `iPhone 375px`, `iPad`, `desktop 1440`, or any other device class instead of a content width in CSS pixels |

Item 13 counts items, not rows: an `[M-조건]` item that reads "not applicable" with the condition and its reason passes, and so does an `[M]` item marked `[확인 필요: <question>]` as long as the document stays `status: draft`. Item 8 counts only the inline markers in the prose sections: a `[확인 필요: <question>]` standing as a gate row's conclusion is excluded from the cap, and the document stays `status: draft` while any gate row is `[확인 필요]`. Item 14 applies to every width the document names, in the goals, the platform block, or a requirement. A breakpoint is written as the content width in CSS pixels plus what in the content needs it, for example `640px where the metric row wraps`; a device name in a breakpoint is a defect because the device list changes while the content width does not.

Fix a failure in place and re-run only the failing item. Do not re-run the whole checklist to feel finished.

## 3. Blocking questions

- Any `Q-###` with `Blocking: yes` and no answer keeps `status: draft`.
- A `draft` document is still saved and reported; it is not withheld and not reported as complete.
- The completion report names each remaining blocking question and who must answer it.
- A document may pass every checklist item and still be `draft`; the checklist measures the text, the status measures whether a scope decision is missing.

## 4. Optional no-context reader test

Run this only when a subagent is available and the user has not forbidden it. It is never a required step, and a skipped test is stated as skipped rather than passed.

1. Write five expected questions the document must answer for a build stage: what is being built, for whom, what is out of scope, how success is measured, and what decision is still open.
2. Give a fresh subagent only the saved `prd.md` and ask those five questions.
3. Count the answers the document supports. A question the document cannot answer from its own text is a defect in that section, not in the reader.
4. Fold the defects back into the document and re-run the affected checklist items.

Record the outcome as `reader test: passed <n>/5` or `reader test: skipped (<reason>)`. Never claim a pass that was not run.

## 5. Review output shape

```text
| # | Check | Result | Location / note |
|---|---|---|---|
| 1 | FR maps to goal or story | pass | |
| 2 | Metric target and measurement | fail | Section 5, FR-007 has no target |
| 13 | Platform `[M]` items in the release gate table | fail | Android block, A9 has no row |
| 14 | Breakpoints named by content | fail | Section 9, web block says "iPhone 375px" |
```

One row per checklist item, in checklist order. After the table, one line naming the blocking questions and one line stating that no file was edited.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Independent testability as a gate on every story | [spec-kit spec-template](https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md) - "Each user story/journey must be INDEPENDENTLY TESTABLE" |
| Removing a non-applicable section instead of writing N/A | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "When a section doesn't apply, remove it entirely (don't leave as 'N/A')." |
| A clarification cap as a readiness gate | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "Maximum 3 [NEEDS CLARIFICATION] markers total" |
| A no-context reader test before other readers | [anthropics doc-coauthoring](https://github.com/anthropics/skills) - "Test the doc with a fresh Claude (no context) to catch blind spots before others read it" |
| Assumptions kept out of body fact | [phuryn create-prd](https://github.com/phuryn/pm-skills) - "Don't invent. What you don't know goes to 7.4 Assumptions and open questions, clearly marked, not into the body as fact." |
| Counter-metrics as part of a measurable goal set | [TerminalSkills prd-writing](https://github.com/TerminalSkills/skills) - "Counter-metrics: [Metrics we don't want to hurt]" |
| The implementation-mechanism audit | [ai-conductor prd](https://github.com/jstoup111/ai-conductor) - "It MUST NOT name the new internal mechanism by which this feature is built." |
| Output proportional to the problem, so the checklist stays short | [Martin Fowler, SDD tool comparison](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) - "it quickly became clear that the workflow was like using a sledgehammer to crack a nut" |
| Breakpoints chosen by content instead of device class | [Responsive web design basics](https://web.dev/articles/responsive-web-design-basics) - "Don't define breakpoints based on device classes" |
| Every mandatory store item reaching the release gate | [Play Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) - "Even developers with apps that do not collect any user data must complete this form" |

### Evidence grade

`LOCAL` - the fourteen checklist items and the review table shape are this package's design. The marker cap and the removal rule are quoted from the cited specification guidance; the reader test is quoted from the cited authoring guidance.
