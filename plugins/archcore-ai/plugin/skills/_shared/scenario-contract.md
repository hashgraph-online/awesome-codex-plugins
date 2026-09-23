# Scenario Content Contract

Plugin runtime asset. Loaded by skills creating scenarios: `plan` (the illustrate
instrument at `sdd.illustrate`) and `document` (the describe track). Companion to
`skills/_shared/spec-contract.md`, `skills/_shared/journey-contract.md`, and
`skills/_shared/precision-rules.md`. Engine gate: `skills/_shared/actor-subject-compatibility.md`.

## What a scenario is

The record of **how a user or an external actor moves through a system**, and the
concrete examples that illustrate the clauses of one `spec`. A scenario takes the
actor as the subject of every step and carries no modal; the rules stay in the
`spec` it illustrates. It exists so a reader sees the realized path — who does
what, and what the system shows — beside the contract that governs it.

**Routing gate:** the subject of the line decides. A line that obligates the
component with a modal (`WHEN the user requests a refund, the service MUST approve
it`) is a `spec` clause. A line that takes the actor as its subject and carries no
modal (`Anna requests a refund on 10 Sep; she sees the refund approved`) is a
scenario step. Between the pair: a covering `spec` exists → `scenario`; none exists
→ `journey` (`skills/_shared/journey-contract.md`).

## When NOT to write a scenario

- A rule or an obligation → `spec`
- The intended path before any `spec` covers the interaction → `journey`
- A wanted outcome or a metric → `prd`
- A delivery task → `plan`
- A stakeholder need on the Sources or ISO tracks → `urd` User Journeys, `strs` Operational Scenarios
- An executable feature file → the test tree (`features/*.feature`), cited by `@path`, never copied into `.archcore/`

## Mandatory sections

1. **Subject** — the system and the `spec` clauses this document illustrates, by
   clause number; who depends on the illustration.
2. **Actors** — a table with the columns `Actor`, `Who they are`, `What they want`.
   The first column is the actor list every step opens with.
3. **Flows** — one `###` subsection per actor. Each subsection opens with an
   `Anchors:` line of `@path` references to the code and test files the flow walks,
   then numbered steps, then an `Extensions` list for alternative and failure paths.
4. **Examples** — a `Background` block for context shared by every example, then
   one titled example per case: a title naming what is special, an `Illustrates:`
   line with the clause number, and unfenced Given/When/Then lines. Several cases of
   one shape go in an `Examples` table with a `notes` column.
5. **Open Questions** — what the team does not know.

A scenario MAY add `## Clarifications`. It carries no other section.

## Notation

Line format F6, actor-subject step:

- Action: `<Actor> <action>; <system> <observable response>.`
- Observation: `Given|When|Then|And|But <observation>.`

Rules:

1. Every step under Flows opens with the actor's name exactly as the Actors table
   spells it — no leading article: `Anna opens…`, not `The buyer opens…`.
2. One step carries one action or one observation, and holds 20 words or fewer.
3. A step MUST NOT carry a BCP 14 modal; an obligation belongs in the linked `spec`.
4. `Given` states preconditions in the past tense; one action per `When`; no UI
   mechanics ("clicks the third button") — state what the actor does and sees.
5. Examples carry no dependency on one another; each runs from its Background alone.
6. A title names an activity the actor performs, not the outcome.

## Body cap

**≤ 120 lines**, counted as the `spec` cap is counted — headings and blank lines
included. The Archcore CLI reports the same cap in `@templates/precision.go`
(`MaxBodyLines`), so the contract and the hook agree.

### Over the cap — split by actor, never compress

WHEN a draft exceeds the cap, the composing skill MUST apply the first remedy the
evidence supports:

1. Reference, do not reproduce — an `Anchors:` line cites files; an utterance,
   payload, or screen longer than one example row cites its fixture by `@path`.
2. Route foreign content to its owner — a rule to the `spec`, a wanted outcome to the
   `prd`, a delivery task to the `plan`, a stakeholder need to the `urd`.
3. Split by the **actor**: Flows is already sectioned per actor, so the document
   becomes one scenario per actor (`filename=<subject-slug>-<actor-slug>`), each with
   its own Subject, and each still `depends_on` the one `spec` it illustrates.
   Evaluate links between the parts through
   `skills/_shared/relation-authoring.md`; splitting alone creates no edge.
4. WHEN the actor is one and the cap still exceeds, split by the `spec` clause set:
   a `spec` split by sub-surface takes its scenarios with it, one per part.
5. IF no boundary is unambiguous, THEN keep the document whole and report the excess.
6. The skill MUST NOT delete an example or a flow to fit the cap.

## Status

Created with `status: draft`. `accepted` means a reader confirmed the examples
against the running system, by a test run or by hand, and the `closeout.accept`
gate names that readiness result in its offer. `rejected` means the examples no
longer hold and no replacement was written. Archcore executes no scenario; the
status is the word of whoever confirmed it.

## Relations and tags

- `scenario depends_on spec` — the one `spec` this document illustrates; the edge the
  engine's cascade notice reads, so a `spec` edit reaches its scenarios.
- `scenario implements journey` — when a `journey` on the topic exists.
- `scenario related scenario` — between the parts of a split.
- No edge from `spec` to `scenario`; a behavior change enters `/archcore:plan` as a
  `modifies` delta with a verdict.
- Tags carry what Gherkin carries as `@tags`: `actor:<type>`, `component:<name>`,
  `nfr:<concern>`. A `plan` task or a backlog item is a tag, never an edge.

## Forbidden in the body

- A `Surface`, `Normative Behavior`, or `Failure Behavior` heading → the `spec`.
- A `Requirements` heading → the `prd`.
- A fenced feature file or a fenced example block: Examples hold unfenced lines.
- A section enumerating other `.archcore/` documents (`skills/_shared/precision-rules.md` Rule 5).
- A prescribed test runner, discovery technique, or feature-file layout.

## Enforcement

The Archcore CLI reports the mechanical part in the post-tool-use hook: the
mandatory sections, a step over 20 words, a modal in a step, a Flows subsection
without an `Anchors:` line, a step opening with neither an Actors-table actor nor
an observation keyword, a foreign heading, and the body cap. Whether the examples
hold against the running system is not decidable there; that judgement stays with
the reader at `closeout.accept`.

## Rationale

Every practice in the territory — BDD, Specification by Example, use cases,
Example Mapping — separates the rule from the example and takes the actor as the
subject of the example. The `spec` owns rules; this type owns the flow and the
examples; the subject of the line is the boundary. The `Anchors:` line is the
price of staying alive: it is what gives a scenario staleness detection and
edit-time injection.

## Examples

### Good

```markdown
## Subject
Refund approval in the orders service; illustrates clauses 2 and 4 of the
refund-policy spec. Support and the checkout UI depend on it.

## Actors
| Actor | Who they are | What they want |
|---|---|---|
| Anna | a buyer within the 14-day window | her money back without a call |

## Flows
### Anna
Anchors: @internal/orders/refund.go, @features/refund.feature
1. Anna opens the order; the page shows a Refund action.
2. Anna requests the refund; the service approves it and shows the credit date.
Extensions: 2a. Outside the window, the page shows the policy and no action.

## Examples
Background: Anna bought a book on 1 Sep.
### Refund inside the window
Illustrates: clause 2.
Given Anna bought the book on 1 Sep.
When she requests a refund on 10 Sep.
Then she sees the refund approved with a credit date of 12 Sep.
```

### Bad

```markdown
## Flows
### Buyer
1. WHEN the user requests a refund, the service MUST approve it within 200 ms.
2. Click the third button in the header, then scroll to the bottom.
```

(Line 1 is a `spec` clause: component subject with a modal. Line 2 is UI
mechanics with no actor and no observable response. Neither is a step.)
