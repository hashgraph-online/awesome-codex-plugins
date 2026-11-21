# Requirements Writing

Use this rule when writing the scope, requirements, scenario, and metric sections. It owns the id formats, the EARS sentence forms, the scenario shape, the metric set, the inline markers, assumptions, open questions, the must-not-change behavior, and the implementation-mechanism ban.

## Contents

- Ids and priority
- EARS sentence forms
- Verification method
- Scenarios
- Metrics
- Inline markers
- Assumptions
- Open questions
- Must-not-change behavior
- Forbidden content
- Empty sections

## Ids and priority

| Id | Meaning | Format |
|---|---|---|
| `FR-###` | Functional requirement | `FR-001`, zero-padded, unique in the document, never renumbered after a revision |
| `A-###` | Assumption | `A-001`, referenced from the sentence that depends on it |
| `Q-###` | Open question | `Q-001`, referenced from the sentence or section it blocks |
| `P0`/`P1`/`P2` | Requirement priority | `P0` without it the goal fails; `P1` first shippable scope; `P2` later |
| `P1`/`P2`/`P3` | Story priority | Story priority and requirement priority are separate scales; a story says which of its requirements are `P0` |

A story carries a priority reason ("why now, and what breaks if it slips") and an independent test ("how this story alone is proven, without the later stories").

## EARS sentence forms

Every `FR-###` uses exactly one of these five forms. Pick the form that matches the requirement, not the one that is easiest to write.

| Form | Shape | Use for |
|---|---|---|
| Ubiquitous | `The <system> SHALL <response>.` | A rule that holds always |
| Event | `WHEN <trigger>, the <system> SHALL <response>.` | A response to an event |
| State | `WHILE <state>, the <system> SHALL <response>.` | Behavior that lasts as long as a state holds |
| Unwanted event | `IF <condition>, THEN the <system> SHALL <response>.` | Error and failure paths |
| Optional feature | `WHERE <feature is included>, the <system> SHALL <response>.` | Behavior that exists only in some configurations |

Write one response per sentence. A sentence with "and" joining two behaviors becomes two requirements. The system name is the product or surface, not a component, module, or class.

## Verification method

Every `FR-###` carries one line starting `Verification:` that names an observable check: a measurement, an inspection, a test scenario, or a demonstration. It says what a reviewer does and what they see.

- Good: `Verification: enter an expired code at sign-in; the screen shows the retry message and no session is created.`
- Not verification: `Verification: works correctly.` / `Verification: tested by QA.`

## Scenarios

Write Given/When/Then scenarios per story, not per requirement. Each story gets one happy path and one failure-or-edge path. Each scenario cites the `FR-###` ids it exercises.

```text
Scenario: <name> (FR-003, FR-004)
Given <a concrete starting state with real values>
When <one action>
Then <one observable outcome>
```

A scenario without a cited `FR-###` is a story description, not an acceptance scenario. A scenario whose `Then` cannot be observed is not acceptance.

## Metrics

Each goal has one primary metric, optionally secondary metrics, and at least one counter-metric per document.

| Part | Required fields |
|---|---|
| Primary | Name, target value with a unit, measurement means, measurement time |
| Secondary | Same four fields, supporting the primary |
| Counter | The metric that must not get worse, its floor, measurement means, measurement time |

- A target is a number with a unit and a direction, or a bounded range. "Better" is not a target.
- A measurement means names where the number comes from: an existing report, an event count, a manual sample with its size.
- A measurement time names the window: "first 14 days after release", "weekly for the first month".
- A counter-metric protects what the change could damage: latency, support contacts, cancellation rate, battery, cost.

## Inline markers

Two markers, placed in the sentence where the gap is, never collected only at the end:

| Marker | Meaning | Limit |
|---|---|---|
| `[가정: <statement>]` | Plausible but unverified; the document proceeds on it | No fixed limit, but each one that changes scope gets an `A-###` entry |
| `[확인 필요: <question>]` | Unknown; someone must answer before the statement is final | At most 3 inline markers in the prose sections |

A `[확인 필요: …]` over the limit means the document is not ready: either resolve the extra one, convert it to an assumption with an owner, or leave `status: draft` and report it. A `[확인 필요: <question>]` that stands as a release gate row's conclusion is excluded from the cap, and the document stays `status: draft` while any gate row is `[확인 필요]`.

## Assumptions

Every assumption that changes scope appears as `A-###`:

```text
- A-001: <the assumed statement>
  - Evidence grade: repo fact | convention default | guess
  - Basis: <path, quote, or the convention relied on>
  - If wrong: <the section, requirement, or scope that changes>
```

Evidence grades are exactly these three: a fact read from the repository, a convention default taken without evidence, or a guess. A guess that would change the P1 scope belongs in open questions with a blocking flag instead.

## Open questions

```text
- Q-001: <the question>
  - Answerer: <role or person>
  - Blocking: yes | no
  - History: Q: <question as asked> → A: <answer, or "unanswered">
```

A `Blocking: yes` question that is unanswered keeps `status: draft`. When it is answered, append the answer to the history line rather than deleting the question. Never invent an answer to close a question.

## Must-not-change behavior

State the behavior that must survive the change, using `SHALL CONTINUE TO`:

```text
FR-010 WHEN a saved draft is reopened, the editor SHALL CONTINUE TO restore the last cursor position.
```

Use it wherever a change touches an existing flow, a data contract, or a permission. A document with no such behavior says so in one line instead of omitting the section silently.

## Forbidden content

A requirement never states an implementation mechanism:

- file paths, module names, function names, type names, class names
- a newly chosen library, framework, database, or service
- schema names, table names, column names, event names invented by this document
- a task list, an estimate, or a staffing plan

Existing external constraints are the only exception, and they are quoted as constraints: a mandated third-party API, an offline requirement, a store rule, a legal obligation. Write the constraint and its source; do not derive an internal design from it. A store-rule value or a file or format name a store or OS mandates is an external constraint, not an invented mechanism: a target API level, `.aab` as the uploaded artifact, and a privacy manifest file name are quoted with the rule that requires them.

Also forbidden: vague quality words with no observable meaning - `빠르게`, `쉽게`, `적절히`, `충분히`, `사용자 친화적`, `fast`, `easy`, `appropriate`, `robust`, `seamless`. Replace each with a number, a state, or a check.

## Empty sections

Delete a section that does not apply. Do not leave a heading with no content, do not write `N/A`, `TBD`, or `-`. A deleted section is invisible in the document; a section kept empty claims content that does not exist.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Numbered requirements with MUST/SHALL and independent tests | [spec-kit spec-template](https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md) - "Each user story/journey must be INDEPENDENTLY TESTABLE" |
| The WHEN/SHALL shape for feature requirements | [Kiro feature specs](https://kiro.dev/docs/specs/feature-specs.md) - "WHEN [condition/event] THE SYSTEM SHALL [expected behavior]" |
| The full five-form EARS set, including state and unwanted-event requirements | [EARS](https://alistairmavin.com/ears/) |
| `SHALL CONTINUE TO` for behavior that must not change | [Kiro bugfix specs](https://kiro.dev/docs/specs/bugfix-specs.md) - "WHEN [condition] THEN the system SHALL CONTINUE TO [existing behavior]" |
| Inline gap markers at the point of the gap | [deanpeters prd-development](https://github.com/deanpeters/Product-Manager-Skills) - "Tag inline where the gap appears, not just at the end." |
| A clarification-marker cap | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "Maximum 3 [NEEDS CLARIFICATION] markers total" |
| Assumptions separated from body fact | [phuryn create-prd](https://github.com/phuryn/pm-skills) - "Don't invent. What you don't know goes to 7.4 Assumptions and open questions, clearly marked, not into the body as fact." |
| Naming who answers an open question | [anthropics write-spec](https://github.com/anthropics/knowledge-work-plugins) - "Tag each with who should answer (engineering, design, legal, data, stakeholder)" |
| Counter-metrics beside the primary metric | [TerminalSkills prd-writing](https://github.com/TerminalSkills/skills) - "Counter-metrics: [Metrics we don't want to hurt]" |
| Not naming the internal mechanism | [ai-conductor prd](https://github.com/jstoup111/ai-conductor) - "It MUST NOT name the new internal mechanism by which this feature is built." |
| Removing a non-applicable section instead of writing N/A | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "When a section doesn't apply, remove it entirely (don't leave as 'N/A')." |

### Evidence grade

`LOCAL` - the id scheme, the marker limits, and the assumption fields are this package's design assembled from the sources above. The EARS forms are quoted from the EARS reference; the `SHALL CONTINUE TO` form is quoted from the Kiro bugfix documentation.
