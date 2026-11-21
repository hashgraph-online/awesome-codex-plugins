---
name: preflight
description: "Use before starting delivery work. Pre-implementation validation checklist to ensure readiness."
metadata:
  instruction_budget: "45"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Preflight Skill

Pre-delivery validation checklist. Run before every implementation task.

## Checklist

### Constraints (ALWAYS FIRST)

Before scoping any delivery work, establish constraints. Do not propose a plan before knowing the budget.

- [ ] **Time budget**: "How much time do you have for this?" (hours, days, sprint length)
- [ ] **Resource constraints**: Solo? Team? What skills are available?
- [ ] **Fidelity**: Demo/prototype vs. production? Who is the audience?
- [ ] **Dependencies**: Waiting on anything external?

If time budget < 8 hours, scope aggressively — one vertical slice, no polish. If the initial plan exceeds the time budget, cut scope before presenting it to the user.

**Re-forecast trigger (audit-triggered / emergent work).** Work that opens as "just address the recommendations", "quick fix", or any audit/assessment follow-up still gets a constraint pass — set an explicit estimate even when no one asked for one. Then, mid-session, **re-forecast when the work crosses ~2× the estimate or when no estimate was ever set**: stop, state actual-so-far vs estimate, and re-scope or re-confirm the budget before continuing. The failure this catches: emergent cycles that bypass preflight and balloon silently (dogfood `cycle-history.yml` — a "~2h" audit cycle ran ~9h; a "session-scope" one ran ~14h). The re-forecast becomes the `calibration.effort_accuracy` data point at `/retrospective`.

*Source: Hoskins transcript (2026-04-25) — agent proposed 20-hour plan before learning user had 8 hours. Goldratt (Theory of Constraints — identify the constraint before optimizing). Corrections.md: "Over-scope before constraints." Re-forecast trigger from the 2026-06-15 `/framework-health` effort-calibration finding (audit-triggered cycles balloon past estimate).*

### Context
- [ ] corrections.md reviewed for relevant past mistakes
- [ ] patterns.md reviewed for applicable patterns
- [ ] Current diamond phase is Develop or Deliver
- [ ] Acceptance criteria are clear and measurable
- [ ] Scenarios linked: `.claude/canvas/scenarios.yml` has scenarios for this solution, and acceptance criteria trace back to scenario success/failure states (Hoskins)

### Scope
- [ ] Scope fits within the time budget declared above
- [ ] This is the smallest vertical slice that delivers value
- [ ] Scope is explicitly bounded (what is NOT included)
- [ ] No speculative features (YAGNI check)
- [ ] Dependencies identified and available

### Technical / Production Readiness
**Software/AI tool:**
- [ ] Tech stack detected and understood
- [ ] Build/test/lint commands confirmed working
- [ ] Development environment functional
- [ ] Existing code patterns reviewed

**Content:**
- [ ] Production tools ready (editor, recording, hosting)
- [ ] Style guide / editorial standards available
- [ ] Existing content patterns reviewed

**Service:**
- [ ] Delivery tools ready (templates, scheduling, communication)
- [ ] Existing service patterns reviewed

### Security (software, ai_tool, service with digital infra)
- [ ] Data classification understood for this feature
- [ ] Security requirements identified (auth, input validation, etc.)
- [ ] No secrets will be hardcoded
- [ ] Dependencies checked for known vulnerabilities

### Accessibility
**Software:**
- [ ] Accessibility requirements identified
- [ ] Semantic HTML approach planned
- [ ] Keyboard interaction model defined
- [ ] Color contrast requirements noted

**Content:**
- [ ] Captions/transcripts planned for audio/video
- [ ] Alt text planned for images
- [ ] Readable typography confirmed

### Validation Strategy
**Software:** Test approach defined (unit, integration, e2e), edge cases and error scenarios identified.
**Content:** Review process defined (SME, self-checklist, fact-check), learning objectives mapped.
**AI tool:** Eval test cases defined, red-team scenarios planned, bias testing approach chosen.
**Service:** Walkthrough planned, client feedback mechanism defined.

### Success Criteria (G-V11)
- [ ] Declare what will be true after this delivery increment (1-3 measurable statements)
- [ ] Declare how each criterion will be verified (test, manual check, metric)
- [ ] Record criteria in .claude/harness/decision-log.md alongside the delivery decision

Example:
```
Success criteria:
1. "Users can complete onboarding in < 5 min" — verified by usability test
2. "API responds in < 200ms at p95" — verified by load test
3. "No new lint or type errors introduced" — verified by CI
```

### Definition of Done
- [ ] DoD criteria reviewed and understood
- [ ] All criteria are achievable within this task

## Before anything meets real people (v0.246.0)

A pilot is real people. Before the increment is deployed, published or sent to anyone, an exposure record on the diamond carrying it covers it, with **Security, Privacy and Service Quality passed** for that exposure (since v0.306.0 there is no fallback to the diamond's phase): `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --exposure-state`. If it prints what is missing, that is the next step, before any "pull and restart" instruction to the user. The exposure gate blocks the deploys the agent runs; this line is the guard on the ones the user runs.

**And record who it reaches** (v0.294.0): an entry in the carrying diamond's `exposures`, with the
audience, channel, data class, end date, consent and the gates passed for it. `python3
"${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --exposures` says what is missing. Report only until
stage 2 of the phase migration moves the release gate onto these records.

## If Every Item Passes: offer the L4 cycle (v0.243.0)

A passing preflight means **an increment is ready to build, which is L4's event**. L4 recurs per
increment, not on a pile, so it has no catalogue door; **this offer is its entrance**
(`engine/leaf-lifecycle.md` Phase 8: "Delivery diamond spawned (L3 spawns L4)"). If no L4 diamond is
open on this increment, ask whether to open an L4 Delivery diamond on it (`object_ref`: the L3's
front runner and the increment, e.g. "sol-003, swap request + single approval"; since v0.300.0 the L4 lock
reads that solution's verdicts alone), or record in one line why not:
"increment not opened". **Every product has some kind of delivery**, and its shape follows the
product type: tested code for software, reviewed and accessible content, passing evals for an AI
tool, a documented and repeatable step for a service. Offer it only when the L4 entry lock holds
(`engine/diamond-rules.md`, Entry locks, v0.245.0): the L3 it delivers, named as the L4's `parent`, at
medium confidence or higher (`data-supported`, `test-validated` or `launch-validated`; Gilad,
*Evidence-Guided* p158-159: most ideas reach medium-high before delivery, bigger or riskier ones go
further). Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --can-open L4 --parent <l3-id>`. A passing checklist on an L3 still at `anecdotal` is an
increment ready to build TO LEARN, which stays in the L3: when its test needs real use, the L3 takes
it to its own Deliver with an exposure record (`exposures[]`: audience, until, channel) recorded (v0.257.0,
`engine/diamond-rules.md`), and the verdict is what opens the L4. Before v0.243.0 nothing opened an L4: the Four Risks verdict was described as its
"entry permit" and no skill consumed it.

## If Any Item Fails

Do not proceed to implementation. Instead:
1. Document what is missing.
2. Determine the fastest path to readiness.
3. Address the gap before starting delivery work.

## Theory Citations
- Smart: BVSSH (Sooner -- avoid rework by preparing)
- Forsgren: Accelerate (reduce lead time by removing blockers early)
