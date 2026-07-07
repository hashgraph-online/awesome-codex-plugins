---
name: reality-check
description: 'Mid-epic drift audit: code is ground truth'
---
# $reality-check — Mid-epic strategic drift audit

> **Purpose:** at a wave boundary, force the agent who has been deep in the
> implementation to articulate implemented-reality against claimed-vision, name
> every gap with evidence, and route the bridge into the planning stack. The
> canonical failure this catches: **72% of beads done, 0% of the value
> proposition working end-to-end.** Tracker arithmetic measures motion; this
> skill measures whether the motion still points at the promise.

**Use when:** a wave boundary lands mid-epic; the operator asks "where are we
really"; tracker counts look healthy but nobody can demo the headline feature;
or the next wave is about to be planned and needs steering input.

(`user-invocable: false` is interim — promotion to invocable needs catalog +
dispositions rows, a separate one-line change outside this skill's directory.)

## ⚠️ Critical Constraints

- **Code is ground truth; docs are the measuring stick.** When README/PRODUCT.md/plan disagree with the implementation, the code tells you where you ARE and the docs tell you where you promised to BE — the gap between them is the deliverable. **Why:** because "fixing" the doc to match the code mid-epic silently shrinks the vision, and "trusting" the doc inflates the status report.
- **Audit-only: never patch code, edit beads, or rewrite vision docs inline.** **Why:** because the value is an honest steering signal; the moment the auditor starts fixing, it starts grading its own work.
- **Route every bridge through `$discovery` → `$beads-br` — never through an idea-generation ceremony and never straight to code.** **Why:** because gaps need decomposition into evidence-bearing units with dependencies before any agent touches the implementation, or the next wave drifts exactly like the last one.
- **Fires mid-epic at wave boundaries, not at close-out.** **Why:** because after the epic ends it is a post-mortem; the point here is steering while course-correction is still cheap.
- **Tracker percentages are evidence about effort, never the verdict.** **Why:** because beads cluster where work was tracked, and the worst gaps are vision goals no bead ever covered — completion math cannot see them.
- **Every gap row carries a file-level citation or a command output.** **Why:** because an uncited "feature X is missing" claim is an opinion, and downstream discovery will re-litigate it instead of planning against it.

## Boundaries — what this is NOT

| Neighbor | Its question | This skill's question |
|---|---|---|
| `$status` | What do the tracker counts and recent activity say? | Do those counts correspond to shipped value? Status reads the tracker; reality-check reads the code *against the promise*. |
| `$validate` | Does this one artifact (plan, PR, gate) pass? | Does the *aggregate* of all merged artifacts deliver the vision? Artifact-level verdicts can all be PASS while the epic drifts. |
| `$post-mortem` | What did we learn after the work finished? | What do we steer *now*, mid-epic, while waves remain? |
| `/review` | Is this diff well-built (bugs, risk, quality)? | Is the well-built code the *right* code for the claimed value proposition? |

Non-goals: stub-hunting for its own sake (that is an input, not the output),
re-scoping the vision, and generating new product ideas.

## Execution Steps

### Step 1: Extract the claimed vision

Read README.md, PRODUCT.md, and any plan/spec docs for the epic. Distill them
into a numbered list of concrete, falsifiable promises — each one something a
user could try and watch succeed or fail. Record the source line for each.

**Checkpoint:** every promise is testable as written. If a promise is too vague
to falsify ("great DX"), note it as a vision defect and move on — do not
invent a testable version on the docs' behalf.

### Step 2: Establish implemented reality

For each promise, find the code that supposedly delivers it and read it. Build
a code map: real / partial / stub / absent, with file paths. Run the tests and,
where feasible, the software itself — a wired-up command that exits 0 without
doing the work counts as a stub, because the decision here is behavioral, not
structural. Then pull tracker state (`br list`, `bv --robot-insights`) as a
*secondary* signal: which promises do open beads actually cover?

**Checkpoint:** for each promise you can answer "what happens today if a user
tries this?" with observed evidence, not inference from file names.

### Step 3: Emit the gap list

Produce one row per promise: status (`working` / `partial` / `stub` / `absent`),
evidence citation, whether any open bead covers the remainder
(`covered` / `uncovered`), and severity against the value proposition. Lead the
report with the one-sentence drift verdict: how much of the *value proposition*
works, versus how much of the *tracker* is green.

**Checkpoint:** confirm the uncovered gaps are flagged loudest — those are the
ones no amount of cranking the existing queue will close.

### Step 4: Route the bridge

Hand the gap list to `$discovery` to sharpen each uncovered gap into planned,
evidence-bearing work, then `$beads-br` to land it on the tracker with
dependencies sequenced into the remaining waves. The next action after this
skill is always a discovery invocation or an explicit operator decision to
accept the drift — never an inline fix.

## Worked Example

Fixture project in [fixtures/sample-readme.md](fixtures/sample-readme.md)
(README promising 3 features) and
[fixtures/code-map.md](fixtures/code-map.md) (what is actually on disk).
Tracker shows 13/18 beads closed (72%). Running Steps 1-3 yields:

```markdown
# Reality check — relaymail, wave 2 boundary (2026-06-12)

Drift verdict: 72% of beads are closed; 1 of 3 promised features works.
The product's pitch (cross-host inbox sync) is 0% functional end-to-end.

| # | Promise (source) | Status | Evidence | Bead coverage | Severity |
|---|---|---|---|---|---|
| 1 | send: durable at-least-once delivery (README #1) | working | src/send.rs real impl, 14 tests incl. crash-recovery | covered (closed) | — |
| 2 | sync: cross-host inbox replication (README #2) | stub | src/sync.rs is todo!() behind a flag that exits 0 | UNCOVERED — no open bead mentions replication | critical |
| 3 | dlq: dead-letter triage (README #3) | absent | no file; dlq not in CLI dispatch table | UNCOVERED | high |

Route: $discovery on gaps #2 and #3 → $beads-br into wave 3.
```

The steering insight the tracker could never produce: all 13 closed beads
cluster on feature #1's internals. Cranking the remaining 5 closes nothing a
user was promised in #2 or #3.

## Output Specification

**Format:** markdown gap report (drift verdict + gap table + routing line), as
in the worked example above.
**Filename:** written to `.agents/reality-check/YYYY-MM-DD-<epic-slug>.md`;
also summarize the drift verdict and top uncovered gaps inline to the operator.
**Next action:** named explicitly at the end of the report — a `$discovery`
invocation over the uncovered gaps, or an operator-accepted drift note.

## Quality Rubric

- [ ] Every promise extracted from docs is falsifiable and source-cited
- [ ] Every gap row cites a file path, test result, or command output
- [ ] Bead coverage was cross-checked per promise, not inferred from completion %
- [ ] The drift verdict contrasts tracker % with value-proposition %
- [ ] No code, bead, or vision doc was modified by this skill
- [ ] The bridge routes through discovery → beads-br, not straight to implementation

## See Also

- [discovery](../discovery/SKILL.md) — downstream: sharpens uncovered gaps into plans
- [beads-br](../beads-br/SKILL.md) — downstream: lands the bridge plan as sequenced beads
- [post-mortem](../post-mortem/SKILL.md) — the after-the-fact sibling of this mid-epic check
- [validate](../validate/SKILL.md) — artifact-level verdicts; compose per-gap when evidence needs a judge
