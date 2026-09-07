# Root Cause Claim Contract

## Principle

Debugging stops too early not because the agent is lazy, but because the stop
condition is a self-judged, non-falsifiable claim. The moment an agent decides
"no deeper why remains" is the moment it has selected itself as the authority
on absence. That is structurally biased toward premature closure.

This document defines the **Pre-Claim Gate**: a small set of mechanical,
falsifiable checks an agent must satisfy *before* it is allowed to claim a root
cause and enter Phase 4 (Implementation). It also defines the **Causal
Topology Gate**, which replaces the implicit "single-root" default with an
explicit topology classification — because some bugs have more than one root,
and some roots form a cluster rather than a chain.

The gate is **advisory method-pack discipline**. It is not a `GateDecision`, a
`PolicySnapshot`, evidence sufficiency authority, or completion authority.

## When to Use

Run the Pre-Claim Gate when **any** of these is true:

- the candidate fix matches a Patch-Shape Triage signal (H1 / H3 / H8 / H10 /
  H11 / H13) — i.e. the fix is a guard, fallback, consumer/caller patch,
  artifact/cache patch, or sample-only naming
- the diagnosis crosses a component or system boundary (L3 and above)
- the user has pushed back on a previous root-cause claim ("is that really the
  root?", "you stopped too early")
- a fix was attempted and the symptom persisted or shifted

Do **not** run it for the quick bug lane when the fix is at the canonical owner
of a single-component, single-owner bug and no patch-shape signal fires. Keep
simple tasks cheap.

## Deeper Cause Challenge

Before any non-trivial root claim, account for the mechanism that can regenerate
the failure. A locally effective intervention proves that the selected point is
causal; it does not prove that the point is the recurrence generator.

Run the full challenge when an upstream producer, configuration, default,
contract, policy, or specification dependency has not been excluded. Record:

```text
Deeper Cause Challenge:
- Claimed cause:
- Causal status: root | proximate | contributing | deepest-confirmed-root-unknown | external-terminal
- Upstream generator:
- Recurrence path:
- Counterfactual intervention:
- Plausible deeper candidate:
- Rejection evidence:
- Recurrence status: closed | open
- Topology / anti-disguise proof:
```

The causal statuses mean:

- `root`: the recurrence generator is accounted for and closed;
- `proximate`: the mechanism directly produces the symptom but can be regenerated upstream;
- `contributing`: the mechanism changes likelihood or severity without independently generating the bug class;
- `deepest-confirmed-root-unknown`: evidence confirms the deepest observed mechanism but ends before root closure;
- `external-terminal`: the actionable chain ends at a proven T-class boundary.

A `root` claim requires all of these: the upstream generator is accounted for,
the recurrence path is closed, the counterfactual eliminates the relevant bug
class rather than one sample, at least one plausible deeper candidate is
rejected with evidence, and the topology / anti-disguise proof passes. If any
item remains open, use `proximate`, `contributing`, or
`deepest-confirmed-root-unknown`; never promote the deepest observed mechanism
to root by default.

### Quick Exit Proof

The quick bug lane may skip the full challenge only with explicit negative
proof:

```text
Quick Exit Proof:
- Canonical local owner:
- Origin and termination: bad value/state originates and terminates here
- Upstream producer/config/default/contract/policy/spec: excluded with evidence
- History and same-pattern searches: negative
- Variant counterfactual: eliminates the bug class
- Causal status: root
```

If any quick-exit field is unknown or positive, leave the quick lane and run the
full challenge. A familiar file, canonical owner, or green local test is not a
substitute for this proof.

## The Five Gate Checks

A root-cause claim passes only when all five are satisfied. Each turns a
subjective judgment into a mechanical, checkable condition.

### Gate 1 — Causal Closure

Every causal edge from symptom back to claimed root has an evidence anchor
(file:line, test, log, reproduction). A link that is "probably" or "I think"
breaks the chain. The chain is closed or it is not — there is no partial pass.

### Gate 2 — Falsifier Checked

The claim must state: "If X were *not* the root cause, then observable F would
appear." Then F must have been checked and found absent. No falsifier, or a
falsifier that was never checked, blocks the claim.

This converts "X is the root" from an assertion into a proposition that could
have been wrong.

### Gate 3 — Adversarial Self-Refutation

Before claiming, generate the strongest single argument for why this root cause
is wrong, and show why it does not hold. Self-refutation activates a different
reasoning path than self-confirmation and is the cheapest known correction for
the selection bias at the stop point.

### Gate 4 — Causal Topology Gate (see below)

The claim must carry an explicit topology classification, not an implicit
"single-root" default.

### Gate 5 — Layer Ceiling Proof

If the claimed root sits at layer L?, the agent must show why L?+1 is *not*
reachable — with a concrete constraint, not "I didn't go there." Reaching L7
(Spec Gap) or a T-class terminal counts as a valid ceiling; stopping at L2 with
"looks deep enough" does not.

```text
Pre-Claim Gate Pass:
Topology: <single-root | single-root-multi-symptom | chain | independent-compound | conjunctive-cluster | disjunctive-or>
CausalClosure: <closed | open-edge: <edge>>
Falsifier: <if not-X then F; F checked: yes/no>
SelfRefutation: <strongest objection> -> <why it does not hold>
LayerCeiling: <L?> -> <why L?+1 unreachable>
Verdict: pass | fail-<which-gate>
```

This card is an advisory readback. It is not a `GateDecision`,
`PolicySnapshot`, or completion authority.

## Causal Topology Gate

Bugs have one of six causal topologies. Diagnostic layers (L1-L7) are
observation altitudes, not causal shapes: any topology can occur at any stop
layer. These topologies assume convergence on discrete mechanisms within an
acyclic incident graph; when member-by-member repair keeps regenerating the
symptom, treat that as Architecture Escalation evidence rather than adding
another cluster member. The topology is not optional metadata
— it determines the correct stop condition and the correct repair shape. The
default is `unknown`; an agent must actively exclude the multi-root topologies
before it may collapse to a single-root claim.

| Topology | Structure | Stop condition | Repair shape |
| --- | --- | --- | --- |
| `single-root` | A → symptom | Layer Ceiling Proof at A | fix A |
| `single-root-multi-symptom` | A → B, C, D | Layer Ceiling Proof at A | fix A, symptoms self-resolve |
| `chain` | A → B → C → symptom | Layer Ceiling Proof at A | drill to A, fix A |
| `independent-compound` | A and Y are both active in the same incident; each independently produces an anchored manifestation; A ⊥ Y | prove same-incident activity, each root's Gate 1/2/5, and no shared upstream | fix **all active roots**; missing one leaves its causal path |
| `conjunctive-cluster` | A ∧ B ∧ C → symptom (each necessary, none sufficient) | enumerate members, necessity test each, sufficiency test the set, anti-disguise check | fix **all** members; missing one leaves symptom |
| `disjunctive-or` | A ∨ B can cause symptom; current evidence shows one or an unknown active disjunct | identify the incident's active root and enumerate alternatives | fix the observed active root; enumerate alternatives for defense-in-depth |

Classification boundary: `independent-compound` requires evidence that two or
more causally independent roots are active in the same observed incident. If
evidence identifies one active root while other roots are alternative sufficient
mechanisms, classify `disjunctive-or`; if activity is unresolved, keep topology
`unknown`. Alternative mechanisms alone do not prove simultaneous activity.

```text
ClassificationRules:
- independent-compound: multiple active roots in same incident
- disjunctive-or: one active root plus alternative sufficient roots
```

### Topology-specific member proof

#### Conjunctive cluster proof

For `conjunctive-cluster`, each member must pass a **necessity test**: with all
other claimed members present, conceptually remove this member. If the symptom
still occurs, the member is not necessary for that cluster. The full set must
also pass a **sufficiency test** by explaining every observed manifestation,
not only the headline failure.

#### Independent compound proof

For `independent-compound`, do not reuse the conjunctive removal test. Prove
that every claimed root is active in the same incident and independently passes
Gates 1, 2, and 5: under evidence excluding the other roots, it can produce its
anchored manifestation. Removing it must eliminate its own causal path, although
the overall symptom may persist through another independent root. Also prove no
shared upstream and enumerate conditions/manifestations assigned to every root.

```text
TopologyEvidence:
- Candidate: independent-compound | disjunctive-or | unknown
- Same-incident active roots:
- Alternative sufficient roots:
- Shared upstream: none | found | unknown
- Repair obligation:
```

These are **conceptual proofs**, not empirical removals. Complete topology proof
may require runtime coverage that a method pack cannot grant; state that ceiling
honestly when member completeness remains uncertain.

### Anti-disguise check (the step most often skipped)

A claimed cluster may actually be a chain or single-root-multi-symptom in
disguise. Before accepting `conjunctive-cluster`, ask:

> Do members X and Y share a deeper common cause Z, such that X and Y are
> merely two manifestations of Z?

If yes, the topology is not a cluster — it is `single-root-multi-symptom` or
`chain`, and Z is the true root. Drill to Z. This single check is what
prevents an agent from stopping at a "two causes" story when one deeper cause
explains both.

The same check in reverse protects `independent-compound`: if two divergent
chains share an upstream Z, they are not independent, and the root is Z.

## Real Example: Excel-to-Word Conversion Produced a 10-Row Artifact

This is a replay of a real two-turn debugging session, used here to show the
gate catching both a premature L4 stop and a hidden second root.

**Symptom:** a downloadable Word file generated from an attached 363-row Excel
contained only the first 10 rows.

**First-turn stop (would be caught):** the agent stopped at L4 — "scope and
intention signals exist but were not upgraded into a full-document conversion
contract" — and presented this as the root cause.

Running the Pre-Claim Gate against that stop:

- **Gate 1 Causal Closure:** open edge. No evidence linked the "missing
  contract" to the specific 10-row cutoff in the projection layer.
- **Gate 2 Falsifier:** none stated. No claim of the form "if this were not
  the cause, F would appear."
- **Gate 4 Topology:** implicit `single-root`, but the projection layer's use
  of visible-answer text as artifact source was an independent causal path —
  topology had not been classified, let alone reduced to single-root.
- **Gate 5 Layer Ceiling:** no proof that L5+ was unreachable.

Verdict: `fail-open-edge / fail-topology / fail-layer-ceiling`. The agent may
not claim root cause. It must drill upward.

**Second-turn stop (also caught, for a different reason):** drilling deeper,
the agent found that the typed workflow contract compiler recognized only four
regulated families and mapped "convert Excel to Word" into a generic drafting
family with no row-completeness obligation. It presented this L6 gap as the
root.

Running the Topology Gate against that stop:

- The agent had **two** causal paths to the 10-row symptom: (A) no
  full-document conversion family, and (B) the artifact projection sourced
  content from the visible answer text rather than the parsed rows.
- Independent proof for A: with B excluded (projection reads parsed rows), the
  missing full-document contract still produces the incomplete-row symptom.
- Independent proof for B: with A excluded (the contract requires all rows),
  visible-answer projection still produces the incomplete-row symptom.
- Fixing only A or B leaves the other causal path active. This is an
  `independent-compound` candidate {A, B} — **not** a single root.
- **Anti-disguise check:** do A and B share a deeper cause? Yes. Neither
  exists because the system never defined "whole-file artifact generation" as
  a first-class workflow with a completeness obligation — an L7 Spec Gap. A
  and B are two manifestations of that single deeper cause.

Final classification: topology collapses from `independent-compound` to
`single-root-multi-symptom` rooted at the L7 Spec Gap, with two ripple paths
(A, B) that must both be repaired when the spec gap is addressed.

```text
ExampleTopologyEvidence:
- Candidate: independent-compound
- Same-incident active roots: A, B
- Anti-disguise result: shared upstream L7 Spec Gap
- Final: single-root-multi-symptom
```

Without the gate, the first turn would have shipped an L4 non-root as a root,
and the second turn would have shipped an L6 half-root and silently dropped
the projection-layer second member.

## Key Principle

The stop condition must be something the agent has to *buy*, not something it
*defaults to*. Five mechanical checks plus an explicit topology turn "I think
this is deep enough" into "here is the evidence chain, the falsifier I checked,
the objection I survived, the topology I proved, and the ceiling I reached."
That is a claim worth acting on.
