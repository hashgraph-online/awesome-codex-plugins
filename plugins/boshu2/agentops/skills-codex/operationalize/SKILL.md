---
name: operationalize
description: Distill context (research, recon, learnings)
---
# $operationalize — Distill + Route Bridge

> **Loop position:** move 7 (capture + ratchet) of the [operating loop](../../docs/architecture/operating-loop.md) — routes promoted learnings to their weakest durable enforcement (skill, gate, or bead).

Rich context dies in the artifact that gathered it. A deep-research report, a
codebase-recon sweep, or a painful learning is read once, agreed with, and
never changes behavior again. This skill is the bridge: distill the artifact
into a handful of evidence-anchored rules, then route each rule to the
automation shape that will actually fire next time — skill, workflow, hook,
gate, beads, or playbook.

**Use when:** "I gathered rich context — operationalize it." The input is a
finished artifact; the output is rules with anchors and a handoff per rule.

## ⚠️ Critical Constraints

- **Sources stay in place** — to prevent a corpus-curation detour. Name the
  source artifacts by path; never copy them into a corpus directory. The
  artifact you were handed IS the evidence base.
- **Every rule cites a source anchor,** because an unanchored rule is an
  opinion wearing a rule's clothes — it cannot be audited, challenged, or
  retired when the source is superseded.
- **Disagreement is marked DISPUTED, never averaged,** because splitting the
  difference between conflicting sources produces a rule nobody measured.
  A DISPUTED entry routes to investigation (beads), not to automation.
- **Shape is decided by routing, not by vibe** — to prevent everything
  becoming a skill. Compose [$automation-shape-routing](../automation-shape-routing/SKILL.md)
  for the shape decision; this skill only extends its target list.
- **Gates start warn-only,** because a fresh rule promoted straight to a
  blocking gate ships its false positives as outages. Promotion to blocking
  comes after the gate has run quietly on real traffic.
- **No rule survives without a counter-example check,** because the cheapest
  time to find the case where the rule is wrong is before it is wired into
  anything (see Step 5).

## Execution

### Step 1: Intake

Name the source artifacts in place — absolute or repo-relative paths plus a
one-line provenance note each (who produced it, when, method). Confirm each
source has citable anchors (section IDs, finding IDs, line ranges); if not, add
anchor IDs to your *notes about* the source, never by editing the source.

**Checkpoint:** every source is a named path with a provenance line. No corpus
dirs were created.

### Step 2: Distill

Extract candidate rules in the canonical form — **"When X, do Y because Z"** —
where Z cites at least one anchor. Work source by source, then reconcile:

- Multiple sources agree → one rule citing all supporting anchors.
- Sources conflict → one **DISPUTED** entry naming both sides' anchors and
  what evidence would settle it. Do not synthesize a compromise rule.
- A finding with no behavioral consequence → drop it (context, not a rule).

**Checkpoint:** every rule line carries ≥1 anchor; every conflict became a
DISPUTED entry, not a blended rule.

### Step 3: Route

Hand each rule to [$automation-shape-routing](../automation-shape-routing/SKILL.md)
and extend its decision with this target table:

| Route | Pick when the rule… | Emit target |
|---|---|---|
| **skill** | needs judgment at execution time | [$skill-builder](../skill-builder/SKILL.md) |
| **workflow** | is a deterministic multi-step sequence | [$workflow-builder](../workflow-builder/SKILL.md) |
| **hook** | must fire mechanically on a runtime event | [$cc-hooks](../cc-hooks/SKILL.md) |
| **gate** | should *check* outputs — start **warn-only** | a validation gate spec (warn-only first) |
| **beads** | is unsettled work or a DISPUTED investigation | [$beads-workflow](../beads-workflow/SKILL.md) |
| **playbook** | guides a human/operator decision, not an agent | `.agents/playbooks/` entry |

**Checkpoint:** every rule has exactly one route; every DISPUTED entry routed
to beads.

### Step 4: Emit

Write the rule packet (Output Specification below), then create one handoff
stub per routed rule: the rule text, its anchors, the chosen route, and the
target skill invocation. The downstream builder owns the artifact; this skill
owns the rule and its evidence trail.

### Step 5: Validate

For each rule, run the counter-example check: actively search the sources (and
your own experience) for one case where following the rule would be wrong. A
found counter-example narrows the rule's "When X" or demotes it to DISPUTED.
Then request a [$validate](../validate/SKILL.md) verdict on the packet before
handing off — verify before any downstream builder consumes it.

## Worked example (golden fixture)

Input: [fixtures/research-excerpt.md](fixtures/research-excerpt.md) — a fake
deep-research excerpt on worker-lane retry behavior, anchors RX-1…RX-5.

Distilled packet:

1. **When a lane receives a rate-limit response, wait the full advertised
   cooldown before any same-account retry,** because burst retries extend the
   penalty window (RX-1) and sub-30-second retries re-failed in 84% of logged
   events (RX-2). → route: **hook** (mechanical, event-triggered).
2. **When one same-account retry has already failed, rotate accounts before
   the next attempt — capped at three accounts per hour,** because
   post-failure rotation succeeded on the next call in 91% of cases (RX-2)
   while sustained cycling beyond three accounts/hour risks account review
   (RX-5). → route: **skill** (judgment about when the cap binds).
3. **DISPUTED — rotate unconditionally on the first rate-limit response.**
   RX-4 (operator interview) asserts it; RX-5 flags rotation frequency itself
   as a risk, and RX-2 only measured rotation *after* a failed retry. Settling
   evidence: telemetry comparing first-response rotation vs post-failure
   rotation. → route: **beads** (investigation), not automation.

Note what did NOT happen: rules 1–3 were not averaged into "rotate fairly
quickly"; RX-3 (re-dispatch to a warm lane) was held back at Step 5 because
its own source records a 9% duplicate-work counter-example.

## Output Specification

**Format:** markdown rule packet — sources-in-place list, numbered rules in
"When X, do Y because Z" form with anchors, DISPUTED section, route table, and
the validate verdict reference.
**Path:** written to `.agents/operationalize/YYYY-MM-DD-<slug>.md`; handoff
stubs accompany it as a `## Handoffs` section (one block per routed rule).
**Exit signal:** packet path + per-rule route summary reported to the caller.

## Quality Rubric

- [ ] Every rule cites at least one stable source anchor
- [ ] Zero blended rules: every source conflict appears under DISPUTED
- [ ] Every rule has exactly one route, chosen via automation-shape-routing
- [ ] Any gate route is explicitly marked warn-only
- [ ] Counter-example check ran per rule and is recorded in the packet
- [ ] No source artifact was copied or moved; no corpus directory exists

## See Also

- [automation-shape-routing](../automation-shape-routing/SKILL.md) — the shape decision this skill composes
- [skill-builder](../skill-builder/SKILL.md), [workflow-builder](../workflow-builder/SKILL.md), [cc-hooks](../cc-hooks/SKILL.md), [beads-workflow](../beads-workflow/SKILL.md) — emit targets
- [validate](../validate/SKILL.md) — the packet verdict before handoff
- [research](../research/SKILL.md) — typical upstream producer of the input artifact
