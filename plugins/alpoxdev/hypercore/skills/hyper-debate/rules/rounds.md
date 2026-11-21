# Rounds

Read this before dispatching round 1 and again at each round boundary. It owns the wave discipline, the three round contracts at the procedure level, the sequential fallback, and the ledger.

## 1. Grounding Before Round 1

Restate the request in the ledger before any perspective runs:

- the user's request, quoted verbatim
- the scope and the constraints the user stated
- the observable outcome the plan must produce
- the adversarial opt-in phrase that selected this skill
- the slug, and the receipt directory `.hyper/debate/<slug>/`

Then ground read-only. A perspective that receives no grounded material invents evidence, so the lead collects the smallest useful evidence set first: the files the request names, the schema or config that bounds it, and any constraint the user stated. Record each grounded path in the ledger under `grounding`.

Grounding is not a plan. Do not decide the approach, do not sequence work, and do not pre-write the plan's todos.

## 2. Wave Discipline

One round is one wave of five perspective jobs.

1. Dispatch all five at once when the runtime supports parallel subagents. Each job carries the shared request, the grounding, its own perspective brief, the round contract, and its finding-id prefix.
2. Record every returned job identity against perspective, round, and attempt in the ledger before acting on it.
3. Advance only when the wave's pending set is empty and all five receipts are valid. A preview, a partial message, or a still-running snapshot is not a completed receipt.
4. A perspective's logical name is not a transport address. Address a running job only through the identity the runtime returned.
5. Do not launch a replacement for a job that is still running. Silence and elapsed time are not failure.
6. Replace a lane only after its job ends invalid or failed, once, carrying the exact failure context. A second failure on that lane ends the run as `blocked`.

The lead never judges a receipt by its prose alone. Validate the shape, the coverage, the citations, and the identity independently.

## 3. Round 1: Independent Findings

Each perspective reads the grounded material and returns 3-7 findings. No perspective sees another's findings.

A finding carries:

- a stable id unique across the whole run, prefixed by the perspective (`skeptic-1`, `validator-3`)
- one claim, at most three sentences
- at least one citation: `path:line`, an official URL, the user's own statement, or an explicit `no evidence found`

A finding that states a risk without a citation is rejected and returned to the same perspective for repair. A perspective that cannot produce three cited findings reports fewer with `no evidence found` on the ones it could not ground, and the lead records the shortfall rather than padding.

Round 1 produces no synthesis, no plan, and no ranking.

## 4. Round 2: Cross-Attack

Bundle all round-1 findings with their ids, perspectives, and citations. Give the identical bundle to all five perspectives.

Each perspective judges every finding of the other four perspectives, never its own:

- `ATTACK` - the finding is wrong, unsupported, over-scoped, or its consequence does not follow. The reason names the defect and the evidence that shows it.
- `STANDS` - the finding survives this perspective's scrutiny. A reason is still required; a bare `STANDS` is an empty judgment and is rejected.

Validation is a coverage check, not a schema check alone: every other-perspective finding appears exactly once, no unknown target id appears, and no perspective judges itself. The lead forwards the attacks without softening them and does not synthesize early.

## 5. Sequential Fallback

When the runtime exposes no parallel subagent capability, run the five perspectives one after another in the lead's own context.

The fallback keeps the three rounds, the receipt shapes, the ids, and the citations. What it loses is independence: the same context writes all five perspectives, so a blind spot shared by the lead's reading can survive all five. Say exactly that in the report.

Rules for the fallback:

- Write each perspective's receipt to its own file before starting the next, so the separation stays auditable.
- Keep the same finding-id prefixes and the same coverage requirements.
- In round 2, read the bundled findings from disk rather than from memory, and produce one judgment per other-perspective finding.
- Record `execution: sequential` and `reduced: true` in the ledger, with the reason.
- The terminal becomes `reduced-planned` instead of `planned`.
- Never claim five independent perspectives, cross-perspective discovery, or a complete parallel debate.

The fallback is not a smaller scope. Every perspective still runs, every round still completes, and the approval point still holds.

## 6. Round 3: Defend, Refine, Concede

Group round-2 judgments by their target finding. Give each perspective only its own findings and every judgment against them, with the attacker's identity attached.

Each perspective returns one response per own finding:

- `DEFEND` - rebut every attack with specific evidence, and keep the claim. Evidence is mandatory.
- `REFINE` - state the stronger, narrower claim that survives, say what changed, and cite the evidence that supports the narrowed version. The refined claim is a new claim and must carry its own citation.
- `CONCEDE` - the claim is wrong or unsupported. No surviving claim.

A perspective must address every attack against the finding, not only the easy one. An unanswered attack is recorded as unresolved, and the finding does not count as defended.

## 7. The Lead's Independent Judgment

A `DEFEND` is a claim by an interested party, not proof. For every defended or refined finding the lead re-reads the cited evidence and decides:

- keep it when the citation actually supports the surviving claim
- downgrade it to an open question when the citation is weaker than the claim
- drop it when the citation does not support the claim at all

Record the decision and its reason per finding in the ledger. The lead never keeps a claim because a perspective sounded confident.

## 8. Ledger

`.hyper/debate/<slug>/ledger.json` is the run's durable record. It holds:

- `request` - the user's request verbatim and the quoted opt-in phrase
- `slug`, `mode`, `execution` (`parallel` or `sequential`), `reduced` (boolean) and `reducedReason`
- `grounding` - the paths and commands read before round 1
- `waves` - per round, the perspective ids, their job identities, their attempt numbers, and their receipt paths
- `findings` - every finding with its id, perspective, claim, citations, round-2 judgments, round-3 response, and the lead's keep/refine/drop decision
- `surviving` and `dropped` counts per perspective
- `openQuestions` - every disagreement the evidence did not settle
- `approval` - the request, its timestamp, and the decision verbatim
- `terminal` - one of `planned`, `awaiting-approval`, `reduced-planned`, `declined`, `blocked`
- `notes` - capability gaps, replaced lanes, and shortfalls

Write each entry when it is decided. A later turn or a compacted context resumes from this file, never from memory.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| Wave discipline, the rule that in-flight work is not replaced, and the exact coverage check | `dbc-hbin/omp-ulw@74df40f hyperplan/references/rounds.md` (mechanism reference, re-authored) |
| The rounds 1-3 procedure and the verdict vocabulary | `dbc-hbin/omp-ulw@74df40f hyperplan/SKILL.md`, `hyperplan/references/rounds.md` (mechanism reference, re-authored) |
| The sequential fallback and the reduced-report rule | this package's design, 2026-11-10 (issue #26) |
| The ledger fields and the write-as-you-decide rule | this package's design, 2026-11-10 (issue #26) |

### Evidence grade

`LOCAL` - the procedure was re-authored from a repository without a license, and no text or code was copied. The sequential fallback and the ledger are this package's design.
