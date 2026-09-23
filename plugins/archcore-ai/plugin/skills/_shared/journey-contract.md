# Journey Content Contract

Plugin runtime asset. Loaded by skills creating journeys: `plan` (the intent
instrument at `sdd.require`); no `document` mode produces a journey. Companion to `skills/_shared/scenario-contract.md`,
`skills/_shared/prd-contract.md`, and `skills/_shared/precision-rules.md`. Engine
gate: `skills/_shared/actor-subject-compatibility.md`.

## What a journey is

The record of **the intended path of one user type through the system**, before a
`spec` covers that interaction. A journey says "we want the user to be able to…":
the actor is the subject of every step, there is no data, and there is no modal.
It is the vision half of the pair; a `scenario` is the record it becomes once a
`spec` exists, the way an `idea` becomes a `prd`.

**Routing gate:** no `spec` covers the interaction → `journey`. A covering `spec`
exists → `scenario` (`skills/_shared/scenario-contract.md`). Tense test: a journey
reads "we want the user to be able to…"; a scenario reads "the user does… and
sees…" with data in its examples.

## When NOT to write a journey

- Concrete examples with data, or a flow anchored to code → `scenario`
- A wanted outcome with a metric → `prd`
- A concept and the opportunity it opens → `idea`
- A rule or an obligation → `spec`
- A persona and usability requirement on the Sources track → `urd`

## Mandatory sections

1. **Intent** — one header, goal first: `In order to <goal> / As a <actor> / I want
   <outcome>`, followed by a short narrative of two to four sentences.
2. **Actors** — a table with the columns `Actor`, `Who they are`, `What they want`.
3. **Journeys** — one `###` subsection per actor: numbered steps in the actor's
   words, no data, no UI mechanics; alternative paths as an `Extensions` list.
4. **Open Questions** — the red cards: what the team does not know.

A journey MAY add `## Clarifications`. It carries no other section.

## Notation

Line format F6, actor-subject step, as in the scenario contract:

- Action: `<Actor> <action>; <system> <observable response>.`
- Observation: `Given|When|Then|And|But <observation>.`

Rules:

1. Every step under Journeys opens with the actor's name exactly as the Actors table
   spells it — no leading article: `Beginner starts…`, not `The beginner starts…`.
2. One step carries one action or one observation, and holds 20 words or fewer.
3. A step MUST NOT carry a BCP 14 modal.
4. A step carries no data value; a value belongs in a scenario example.
5. The Intent header names the goal before the actor; a journey with no goal is a
   task list, not a journey.

## Body cap

**≤ 120 lines**, counted as the `spec` cap is counted. The Archcore CLI reports the
same cap in `@templates/precision.go` (`MaxBodyLines`).

### Over the cap — split by actor, never compress

WHEN a draft exceeds the cap, the composing skill MUST apply the first remedy the
evidence supports:

1. Route foreign content to its owner — a rule to a future `spec`, a wanted outcome
   to the `prd`, a data-bearing example to a `scenario`. A journey over the cap is a
   signal that the narrative has taken on rules or data; try this remedy first.
2. Split by the **actor**: one journey per user type (`filename=<subject-slug>-<actor-slug>`),
   each with its own Intent. Evaluate links between the parts through
   `skills/_shared/relation-authoring.md`; splitting alone creates no edge.
3. IF no boundary is unambiguous, THEN keep the document whole and report the excess.
4. The skill MUST NOT delete a journey step to fit the cap.

## Status

Created with `status: draft`. `accepted` means the team agreed this is the wanted
interaction. `rejected` means the interaction was abandoned. WHEN a `scenario` takes
over a journey's flow, the composing skill edits the journey down to intent in the
same gate close (ownership rule 2 in `skills/_shared/prd-contract.md`).

## Relations and tags

- `journey related prd`, `journey related idea` — peers on vision.
- `scenario implements journey` — added by the scenario, never by the journey.
- Tags: `actor:<type>`, `component:<name>`, `nfr:<concern>`.

## Forbidden in the body

- A `Requirements` heading → the `prd`.
- A `Surface`, `Normative Behavior`, or `Failure Behavior` heading → the `spec`.
- A Given/When/Then example with data → a `scenario`.
- A section enumerating other `.archcore/` documents (`skills/_shared/precision-rules.md` Rule 5).

## Enforcement

The Archcore CLI reports the mechanical part in the post-tool-use hook: the
mandatory sections, a step over 20 words, a modal in a step, a step opening with
neither an Actors-table actor nor an observation keyword, a foreign heading, and
the body cap. Whether the interaction is the wanted one is the team's judgement at
`closeout.accept`.

## Rationale

Smart's three-layer model names the middle layer directly: the Business Flow layer
is "the user's journey through the system". User stories are transitory planning
artifacts and belong to the `plan`; the durable narrative is the journey. Keeping
data out of it is what keeps the routing test against `scenario` decidable from
the graph rather than from a judgement about text.

## Examples

### Good

```markdown
## Intent
In order to practice English without a tutor / As a beginner / I want short
conversations that correct me gently.
A beginner opens the tutor a few minutes a day and leaves each session knowing
one thing they said wrong and how to say it.

## Actors
| Actor | Who they are | What they want |
|---|---|---|
| Beginner | A2 level, no tutor | daily practice with gentle correction |

## Journeys
### Beginner
1. Beginner starts a session; the tutor greets them and proposes a topic.
2. Beginner answers in their own words; the tutor replies and marks one error.
Extensions: 2a. Beginner asks for the rule; the tutor explains it in one line.

## Open Questions
- How many errors per session before the beginner disengages?
```

### Bad

```markdown
## Journeys
### Beginner
1. Given the beginner said "I goed home", When the tutor replies, Then it shows "went".
2. The tutor MUST correct every past-tense error.
```

(Line 1 carries data — a scenario example. Line 2 is a rule with a modal — a
`spec` clause. A journey holds neither.)
