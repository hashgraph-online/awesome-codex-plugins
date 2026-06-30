---
name: _critic
description: "HarnessX Critic (Tier 2.1) — adversarial review of evolved-skill proposals against trace evidence. Detects reward hacking and manifest/evidence contradictions. Out-of-band LLM counterpart to the in-loop deterministic critic in src/evolve/critic.rs."
---

# Critic — Adversarial Proposal Review

> **In-loop vs out-of-band.** epic-harness forbids external LLM calls from
> production, so the reflect loop ships a **deterministic** critic
> (`src/evolve/critic.rs`) that gates seeding when reward hacking is
> suspected. THIS skill is the **out-of-band LLM** version a meta-agent or
> human runs during `/evolve` review for the cases the deterministic check
> cannot catch (non-local effects, manifest/evidence nuance).

## When to Trigger
- During `/evolve` review of newly seeded skills
- When `reward_hacking_suspected` is true in metrics
- After a seesaw-regression round, before re-proposing

## Process

### 1. Gather the proposal + evidence
- Read the evolved skill proposal(s) from this round
- Read the EditManifest (edit_type, target, intended_effect, predicted_impact)
- Read the round's TaskDigests (outcome, failure_categories, evidence_excerpts)
- Read recent score_history dimension_averages (tool_success, output_quality, execution_cost)

### 2. Falsify the manifest (paper §4.3, Table 9)
For each proposal, ask: does the trace evidence support the `predicted_impact`?
- If the manifest claims "Lift avg_score_with" but output_quality is regressing → **Reject**
- If the manifest claims a tool fix but the implicated component shows no change → **Warn**
- If the evidence corroborates the predicted effect → **Approve**

### 3. Reward-hacking cross-check
- Is execution_cost rising while output_quality falls across the window?
- Could the skill be gaming a metric (fewer tool calls inflating cost score) rather than improving outcomes?
- If yes, the skill must NOT ship — flag for the rejected buffer.

### 4. Non-local effect scan
- Will this skill's guard rules conflict with existing skills (overlapping triggers, contradictory rules)?
- Does it interact with shared state (context, memory, control) in a way the manifest didn't account for?

## Anti-Rationalization

| Excuse | Rebuttal | Do instead |
|--------|----------|------------|
| "The score went up, so it works" | Score can rise via metric gaming | Verify the *outcome* improved, not just the score |
| "The seesaw passed, it's safe" | Seesaw is coarse; sub-threshold coupling evades it | Check dimension deltas, not just aggregate pass |
| "It's just a prompt tweak" | Prompt edits have non-local effects on shared context | Trace the effect across skills, not just the target |

## Evidence Required
- [ ] Manifest's predicted_impact checked against observed dimension deltas
- [ ] reward_hacking_suspected consulted
- [ ] No conflict with ≥1 existing skill demonstrated
- [ ] Verdict (Approve/Warn/Reject) recorded per proposal with reason

## Red Flags
- Approving a skill whose only evidence is "score went up"
- Ignoring a falling output_quality because execution_cost rose
- Shipping after a seesaw-regression round without explicit justification
- Treating the deterministic critic as sufficient for non-local effects (it is not — it only checks reward hacking + score-claim contradiction)
