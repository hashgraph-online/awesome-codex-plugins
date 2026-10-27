# Root Cause Claim Contract

## Principle

Debugging stops too early not because the agent is lazy, but because the stop
condition is a self-judged, non-falsifiable claim. The moment an agent decides
"no deeper why remains" is the moment it has selected itself as the authority
on absence. That is structurally biased toward premature closure.

This document defines the **Pre-Claim Gate**: a bounded set of evidence-backed,
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

The quick bug lane may use its compact proof instead of the full card only
after evidence establishes locality and excludes relevant other paths. The
causal standard applies to every repair; a small diff is not locality evidence.

## Deeper Cause Challenge

Before any root claim, account for the mechanism that can regenerate the
failure. A controlled intervention can support a causal relationship; it
does not prove that the point is the recurrence generator. Uncontrolled
changes or a passing sample alone do not establish causality.

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

A root-cause claim requires all five checks within an explicit version, input
and environment scope. These are evidence-backed judgments, not mechanical
certification: a filled card proves neither completeness nor correctness.

### Gate 1 — Causal Closure

Trace actual data, control and state from inputs through decisions and effects
to the observed outcome. Explain key intermediate observations and derive
coverage from relevant upstream, downstream, shared-source, bypass, timing and
feedback influences. Each causal relation needs evidence (code, log, experiment
or execution semantics); a list of inspected modules is not coverage.

For each relevant path or interaction, record confirmation, evidence-backed
exclusion, bounded influence, or an unresolved question. Missing observations
exclude a mechanism only when observation coverage is established. Check
independent and joint causes, including paths masked by an earlier failure.
A scoped model is closed only when no unresolved question could change the
cause, intervention or sufficiency judgment. Explain why the investigated
paths cover the outcome; do not claim absence of all unknowns or enumerate all
technical dependencies. An assumption limiting the claim cannot exclude the
conditions of the reported failure.

### Gate 2 — Falsifier Checked

Identify an observation that would refute the proposed explanation or
distinguish it from a plausible alternative, then obtain that evidence.
Control other causes when testing a member: an independent path can preserve
the overall failure after that member is removed. Neither disappearance nor
persistence alone proves the complete topology. Diagnostic instrumentation and
reversible experiments may precede closure; they are not retained repairs.

### Gate 3 — Adversarial Self-Refutation

Before claiming, generate the strongest single argument for why this root cause
is wrong, and test it against evidence. Revise the explanation when it survives;
do not manufacture a rejected alternative merely to complete the card.

### Gate 4 — Causal Topology Gate (see below)

The claim must carry an explicit topology classification, not an implicit
"single-root" default.

### Gate 5 — Layer Ceiling Proof

Justify the investigation boundary with evidence about mechanisms that could
change the conclusion, not a layer number or "I did not go there." A spec-gap
label is not automatic closure. An external terminal limits the claim; it does
not prove the user outcome repaired. Deeper inquiry may stop when exclusions
and coverage support the scoped intervention, without inventing higher-layer
defects.

```text
Pre-Claim Gate Pass:
Topology: <single-root | single-root-multi-symptom | chain | independent-compound | conjunctive-cluster | disjunctive-or>
CausalClosure: <closed | open-edge: <edge>>
Falsifier: <discriminating observation; evidence checked: yes/no>
SelfRefutation: <strongest objection> -> <why it does not hold>
LayerCeiling: <scope and conditions> -> <coverage and exclusion evidence>
Verdict: pass | fail-<which-gate>
```

This card is an advisory readback. It is not a `GateDecision`,
`PolicySnapshot`, or completion authority.

## Causal Topology Gate

The six classifications below describe bounded acyclic cases, not every
possible failure. Inspect feedback and timing explicitly; do not force them
into an acyclic classification. Diagnostic layers (L1-L7) are
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
| `single-root-multi-symptom` | A → B, C, D | Layer Ceiling Proof at A | repair A and propagate required implementation changes; verify each affected outcome |
| `chain` | A → B → C → symptom | Layer Ceiling Proof at A | drill to A, fix A |
| `independent-compound` | A and Y are both active in the same incident; each independently produces an anchored manifestation; A ⊥ Y | prove same-incident activity, each root's Gate 1/2/5, and no shared upstream | fix **all active roots**; missing one leaves its causal path |
| `conjunctive-cluster` | A ∧ B ∧ C → symptom (each necessary, none sufficient) | enumerate members, necessity test each, sufficiency test the set, anti-disguise check | break the conjunction at the correct defective owner; removing any necessary condition stops this path |
| `disjunctive-or` | A ∨ B can cause symptom; current evidence shows one or an unknown active disjunct | identify the active root and check other paths within the claimed repair scope | cover every in-scope sufficient failure path or exclude it with evidence; an earlier abort can mask a later one |

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

Necessary conditions are not necessarily defects: ordinary traffic or a
required cache may enable the incident without needing removal. Choose the
smallest owner-correct repair that breaks the conjunction while preserving
required behavior. Repair additional defective members only when their own
correctness obligations justify it; do not infer an all-members repair from
AND causality. Verify with the other enabling conditions still present.

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

Use execution semantics or controlled experiments as evidence for member
claims; conceptual removal alone is a hypothesis. Separate cause confirmation,
scoped causal closure and verified repair. Verify the original end-to-end
outcome, relevant interactions and counterexamples, and preserved behavior.
Reopen diagnosis when the error changes without the goal being achieved.
A method pack cannot certify runtime coverage; state remaining limits honestly.

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
- **Gate 2 Falsifier:** no discriminating observation was stated or checked.
- **Gate 4 Topology:** implicit `single-root`, but the projection layer's use
  of visible-answer text as artifact source was an independent causal path —
  topology had not been classified, let alone reduced to single-root.
- **Gate 5 Layer Ceiling:** relevant upstream influences remained unexcluded.

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

This collapse requires evidence that the shared specification gap generates
both paths; a common architectural label alone is insufficient. Without that
evidence, keep the shared upstream and final classification unknown. When
that evidence exists, the final classification collapses from `independent-compound` to
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

A closure claim needs a bounded explanation, coverage and exclusion evidence,
and checked counterexamples. The retained intervention must cover relevant
failure paths and preserve required behavior. A method-pack card is a review
aid, not certification; unresolved consequential unknowns block a repair claim,
not diagnostic experiments.
