# Approval And Plan

Read this when round 3 is validated, and again immediately before writing the plan. It owns the insight bundle, the single approval point, and the plan-writing hand-off.

## 1. Distillation

Judge every round-3 response before writing anything.

Keep:

- a finding nobody contested, with its citation intact
- a `DEFEND` whose citation the lead re-read and confirmed
- a `REFINE` whose narrowed claim the citation actually supports

Drop:

- a `CONCEDE`
- an unanswered attack's target finding, until the lead can settle it with evidence of its own
- a defended or refined claim whose citation is weaker than the claim

A dropped claim never reappears in the bundle. If a fragment of it is still true, it enters as a separate finding with its own citation and its own scrutiny.

## 2. The Insight Bundle

`.hyper/debate/<slug>/insight-bundle.md` is planner input, not a plan. It has exactly these six sections, in this order:

```markdown
# <slug> - Insight Bundle
## Original request
## Hard constraints
## Decisions
## Risks and mitigations
## Open questions
## Adversarial provenance
```

| Section | Content |
|---|---|
| Original request | The user's request, verbatim, with the quoted adversarial opt-in |
| Hard constraints | Each invariant that survived, its original finding id, and why it survived |
| Decisions | Each decision the debate settled: the proposal, the attacks against it, the defense or refinement, and the reasoning trail with ids |
| Risks and mitigations | Each surviving risk with its mitigation tied to evidence and finding ids |
| Open questions | Every disagreement the evidence did not settle, with why it stayed open |
| Adversarial provenance | Per perspective: how many findings survived and how many were dropped or conceded |

The bundle states decisions and constraints. It does not contain waves, todo numbers, file-by-file write scopes, or acceptance commands. Sequencing belongs to the plan.

An open question is a gate, never a silent assumption. If it changes the shape of the work, the plan names it as a gate on the todos that depend on it.

## 3. The Single Approval Point

There is exactly one approval request in a run, and it happens after the bundle exists.

Present, in Korean and in plain prose:

- the decisions that survived, one line each
- the risks with their mitigations
- the open questions that still need the user's call
- what the plan will and will not cover

Then ask for the decision to write the plan. Record the request and its timestamp in the ledger.

Approval is explicit. Silence, a dismissed question, a timed-out question, an empty reply, an unavailable question mechanism, or a tool's own suggestion to continue is not approval. Without approval the run stops at `awaiting-approval` with the bundle on disk and nothing under `.hyper/plans/`.

When the user forbids the plan ("계획은 아직 쓰지 마", "bundle only"), the terminal is `declined` and the bundle is the deliverable.

When the user approves, record the decision verbatim and continue to §4.

Approval covers the plan file only. It never authorizes implementation, commits, pushes, deployment, or destructive commands.

## 4. Writing The Plan

The plan lives at `.hyper/plans/<slug>.md` and uses the plan shape the rest of this package executes, restated in `references/plan-shape.md`. Copy that grammar exactly: the header order, the `IS-`/`GAP-` rows, the nine nested todo fields, the `F1`-`F4` wave, the success-criteria table, and the handoff fields.

The plan is written by this skill, in this context, from the bundle. It is not handed to a separate planning stage and it does not name one; the artifact itself is what the execution stage consumes.

Rules for the plan:

- Every hard constraint from the bundle becomes a `Must have` line and, where it implies work, a todo that satisfies it.
- Every mitigation appears in the todo that could violate it.
- Every open question gates its dependent todos: the todo is written but its acceptance names the gate, or it is listed as blocked with `Unmet:`.
- The `Must NOT have` section carries the additions the debate rejected, so an executor cannot quietly reintroduce them.
- The `TL;DR` carries `Decisions made for you` from the surviving decisions and their reversibility.
- The provenance of the debate is named in the `TL;DR` risk line and in the handoff, not turned into todos.

The plan is written once and then edited in place. Its headers never change order or wording.

## 5. Terminals

| Terminal | Meaning |
|---|---|
| `planned` | Approval was explicit and `.hyper/plans/<slug>.md` exists and was read back |
| `reduced-planned` | Same as `planned`, but the debate ran sequentially and the report says so |
| `awaiting-approval` | The bundle exists and no explicit approval has arrived |
| `declined` | The user forbade the plan; the bundle is the deliverable |
| `blocked` | A lane failed twice, a receipt could not be validated, or a required capability is missing |

A run ends at exactly one terminal, recorded in the ledger, and the report names it.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The insight bundle sections and writing the plan after approval | `dbc-hbin/omp-ulw@74df40f hyperplan/SKILL.md` (mechanism reference, re-authored) |
| The plan title, `IS-`/`GAP-` items, the nine todo fields, `F1`-`F4`, the success criteria, and the handoff fields | this package's plan grammar, restated in `references/plan-shape.md` |
| Approval covers the plan file only and grants no implementation, commit, or deploy | this package's design, 2026-11-10 (issue #26) |
| An open question gates the todo that depends on it | this package's design, 2026-11-10 (issue #26) |

### Evidence grade

`LOCAL` - the bundle and the approval procedure were re-authored as a mechanism from a repository without a license, with no text copied. The gate rule and the terminal states are this package's design.
