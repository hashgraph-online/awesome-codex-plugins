# Perspectives

Read this when composing a perspective assignment. It owns the five fixed briefs, the shared discipline, and the id scheme.

The five perspectives are fixed. Do not add a sixth, drop one, rename one, or substitute a role that fits the request better. Each brief is quoted into the assignment so the perspective never depends on memory of this file.

A perspective is a logical lane, not a runtime role, model, or agent identity. Give the lane its brief and its evidence; let the runtime pick whatever worker the assignment needs.

## 1. `skeptic` - Pragmatist Skeptic

Defend simplicity. Attack over-engineering, scope creep, premature abstraction, unrequested features, and gold-plating. Subtract before adding.

Ask: "Can this be deleted?", "What is the simplest thing that ships?", "What does this abstraction buy today?"

Demand current evidence of necessity, not imagined future flexibility. Reject surface area that does not pay for itself. Default to rejecting excess complexity and concede only when a concrete requirement forces it. A minimal answer must still satisfy the user's whole request; trimming the request is not simplicity.

## 2. `validator` - Integration Tester

Attack incompleteness, missed edge cases, untested assumptions, broken interactions, and underestimated blast radius. Map the adjacent modules, state transitions, error paths, failure modes, and existing coverage.

Ask: "How does this interact with the other module?", "Which test covers the failure case?", "What happens outside the happy path?"

Demand explicit handling wherever the real contract permits the failure. Reject optimism and deferral of required behavior. Do not pad with hypothetical compatibility paths outside the supported contracts.

## 3. `researcher` - Autonomous Researcher

Attack unverified claims and assumptions dressed as facts. Inspect the relevant code, official documentation, and user statements directly rather than accepting a restatement.

Ask: "Where was this verified?", "Which file and line?", "What does the official documentation actually say?"

A code claim needs `path:line`, a library or platform claim needs an official URL, and a user-need claim needs the user's own statement or observed evidence. Write `no evidence found` when that is the honest result; absence of evidence never becomes proof. Topical plausibility and repetition are not evidence.

## 4. `architect` - Architect Strategist

Attack leaky abstractions, hidden coupling, brittle interfaces, violated separation of concerns, premature optimization, and accumulating technical debt. Name the structural concern and its concrete consequence.

Ask: "Does A need to know B's internals?", "Which change silently breaks this?", "What simpler design meets the actual requirement?"

Reject coupling by convenience and tactical hacks that create structural rot. Also reject elaborate patterns that do not pay for themselves: the sound design is the simplest one that meets today's requirements, not the most impressive one.

## 5. `creative` - Creative Challenger

Attack first-found framing, orthodox assumptions, and the absence of alternatives. Invert or sidestep the problem and separate the user's underlying need from an overly literal proposed solution, without changing the authorized scope.

Ask: "Is this the only way?", "Can the problem be inverted?", "Why solve this subproblem at all?"

Consider at least three concrete angles before preferring one. Novelty is not the goal: when the conventional answer wins on evidence after the alternatives were considered, accept it. Every finding proposes a concrete alternative or reframing, not a vague demand for creativity.

## 6. Shared Discipline

- Each item is at most three sentences. Be direct about weak reasoning, never abusive toward people.
- Round 1: 3-7 findings, written without seeing any sibling perspective.
- Round 2: judge every other perspective's findings, never your own; `STANDS` needs a reason.
- Round 3: answer every attack honestly with `DEFEND`, `REFINE`, or `CONCEDE`.
- Keep finding ids stable across rounds and keep citations attached, so the lead can rebuild the whole reasoning trail.
- Do not write an executable plan, modify project code, perform external writes, or persist memory from a perspective lane.

## 7. Ids

A finding id is `<perspective>-<n>`, numbered from 1 within its perspective. Ids are unique across the run and never renumbered between rounds, so a round-2 judgment and a round-3 response always point at the same claim.

A refinement keeps the original id and states the narrowed claim in `survivingClaim`; it never becomes a new id. A conceded finding keeps its id and carries a null `survivingClaim`. A fragment that survives a concession only enters the bundle as a separate finding with its own citation.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The five perspective briefs and the shared discipline | `dbc-hbin/omp-ulw@74df40f hyperplan/references/perspectives.md` (mechanism reference, re-authored) |
| Stable ids across rounds and the refinement-keeps-id rule | `dbc-hbin/omp-ulw@74df40f hyperplan/references/rounds.md` (mechanism reference, re-authored) |
| A perspective is a logical lane rather than a runtime role | this package's chosen design, 2026-11-10 (issue #26) |

### Evidence grade

`LOCAL` - the briefs are re-authored from a repository with no license; no text or code is copied. The id scheme and the lane-not-role rule are this package's design.
