---
name: forge
description: "Autonomous development with experimental self-correction. Iterates through quality gates until antifragile or blocked."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent, WebSearch, WebFetch
disable-model-invocation: true
kernel:
  kind: workflow
  version: 1
  side_effects: writes_remote
  confirmation: on_side_effect
---

<skill id="forge">

<purpose>
Fully autonomous. No human checkpoints. Iterate until the solution is antifragile.

The forge metaphor is literal:
  HEAT   — generate competing approaches, inject entropy
  HAMMER — iterate implementation against failing tests
  QUENCH — quality gates, adversarial review, convergence check
  TEMPER — experiment on output, discover emergent patterns, self-correct
  ANNEAL — if brittle, reheat and try a different crystalline structure

TEMPER is the evolution: the forge doesn't just build — it measures, hypothesizes,
tests, and adapts. Every cycle produces data. Every data point refines the next cycle.

Run this overnight. Come back to shipped code + experimental evidence + emergent learnings.
</purpose>

<skill_load>
always: skills/quality/SKILL.md, skills/build/reference/testing.md, skills/build/reference/git.md, skills/build/SKILL.md
on_classify:
  bug:      skills/debug/SKILL.md
  refactor: skills/build/reference/refactor.md
on_domain:
  api:      skills/architecture/reference/api.md, skills/architecture/reference/backend.md
  auth:     skills/tearitapart/reference/security.md
  frontend: skills/frontend/SKILL.md
  backend:  skills/architecture/reference/backend.md
on_tier:
  2+:       skills/orchestration/SKILL.md
</skill_load>

<on_start>
```bash
agentdb read-start
agentdb emit command "forge-start" "" '{"goal":"...","max_budget_usd":N.NN}'
```
Load ALL always-skills immediately. Load task/domain skills after classify.

**Budget preflight (mandatory before any forge cycle):**
1. Confirm `max_budget_usd` is set on the contract or the forge invocation.
2. If unset: AskUserQuestion — "Forge runs are autonomous loops. Set a cost ceiling
   (default: $5 tier 2 / $15 tier 3), or proceed unbounded?" Never proceed unbounded silently.
3. Cumulative cost tracked via agentdb emit each cycle. Hard stop at 100% of budget.
4. Hitting the cap = forge halts and reports. This is the circuit breaker working.

Why: one stuck retry at $0.40-0.60/query × 200 retries = $120 silently. The cap is the only
mechanism that prevents this — there is no in-session signal that cost is runaway.
See `skills/orchestration/SKILL.md` <max_budget_usd_invariant>.
</on_start>

<!-- ============================================ -->
<!-- THE FORGE CYCLE                              -->
<!-- ============================================ -->

<cycle id="forge" max_iterations="10">

  <phase id="heat" name="HEAT — Generate Competing Approaches">
    Raise the temperature. Don't commit to the first idea.

    **RULE: Research without verification is theory fiction.** (LRN-F11)
    Never generate approaches from research alone. Each candidate must have a verification path
    (test, prototype, visual proof) defined upfront. If you can't verify it, don't propose it.

    **RULE: Avoid specific multiplier claims.** (H104 graduated meta-rule)
    Approaches that promise "3-5x improvement" or "always better" have a 71% refutation rate.
    Frame as directional: "reduces X" not "reduces X by 80%." Measure after, not before.

    1. Read agentdb context + _meta/research/ for prior work.
    1b. Measure entropy: check agentdb learning count in domain, test coverage, recent failures.
        Low entropy → generate 1 approach (streamlined). High entropy → generate 3 approaches (full exploration).
    2. Classify task: type, tier, domain.
    3. Generate 2-3 candidate approaches (not variations — genuinely different strategies).
    4. For each: files affected, tests needed, effort estimate, known risks, **verification method**.
    5. For each: **hypothesis** — what testable claim does this approach make?

    Tier 1: generate inline.
    Tier 2+: spawn parallel surgeon agents, one per approach.
    Tier 3: spawn full council (researcher + scout in parallel → dreamer → surgeons).

    ```bash
    agentdb emit command "forge-heat" "" '{"approaches":N,"tier":N,"hypotheses":["H-FORGE-1","H-FORGE-2"]}'
    ```
  </phase>

  <phase id="hammer" name="HAMMER — Red-Green-Refactor Until Solid">
    Select the strongest approach. Beat it into shape.

    1. Write failing tests FIRST (red). Edge cases before happy paths.
    2. Implement minimal code to pass (green).
    3. Refactor while green.
    4. Run full suite: tests + lint + types.
    5. **Measure**: record metrics that will feed TEMPER phase (tokens, time, error count, coverage).

    Inner loop (max 5 strikes per approach):
      - failing → fix implementation, not tests
      - passing → proceed to quench
      - **stuck after 3 strikes → [D1 — non-repair classifier] CLASSIFY before re-trying:**
        - **APPROACH-GAP** (the strategy is wrong, but the correct behavior is knowable) →
          switch to next candidate approach from heat phase (existing behavior).
        - **CONTRACT-GAP** (the spec is genuinely ambiguous / the correct behavior is
          undeterminable, OR the same failure survives a tactic that should have fixed it —
          the model cannot conceptually repair it) → **STOP. Do NOT burn anneals.** Escalate:
          name the exact ambiguous/un-fixable criterion and hand to the human (or flag the
          contract for redesign). Switching approaches cannot fix a contract/concept gap.
        Why: detection ≠ repair (Ayoob, n=30 — a gate detected every failure but retries kept
        the wrong action when the model couldn't grasp the distinction). Re-annealing a
        contract-gap wastes 3 full cycles on something no approach repairs.

    ```bash
    agentdb emit command "forge-hammer" "" '{"approach":"X","strikes":N,"tests_passing":N,"metrics":{}}'
    ```
  </phase>

  <phase id="quench" name="QUENCH — Rapid Cooling Under Pressure">
    Harden the solution. Adversarial entropy injection.

    <entropy_injection>
      Spawn adversary (or self-adversary for tier 1). Their mandate:
      DON'T ask "is this valid?" ASK "can I destroy this?"

      **Coordination checks FIRST** (H093 — 4.3x more impactful than code quality):
      - Did agents touch overlapping files?
      - Did agents claim completion without evidence?
      - Did scope drift beyond contract?
      - Is there duplicate work across branches?

      Then code quality attack vectors:
      - What input breaks this?
      - What race condition exists?
      - What happens at 10x scale?
      - What edge case was missed?
      - What assumption is wrong?
      - What security hole exists?

      The adversary writes a SPECIFIC failing test or proof, not a vague concern.
    </entropy_injection>

    <integrity_measure>
      Score: 0.0 (shattered) to 1.0 (antifragile).
      - >= 0.8: SURVIVED. Proceed to TEMPER.
      - >= 0.6: CRACKED. Fixable flaws. Back to hammer with adversary feedback.
      - < 0.6: SHATTERED. Approach is fundamentally flawed. Anneal.
    </integrity_measure>

    ```bash
    agentdb emit command "forge-quench" "" '{"integrity":0.X,"verdict":"survived|cracked|shattered"}'
    ```
  </phase>

  <phase id="temper" name="TEMPER — Experiment on Output" trigger="quench.survived">
    The forge's emergent intelligence. Don't just ship — learn.

    After quench survives, run experiments on the forged output:

    1. **Measure what changed**: diff size, token impact, test count, coverage delta.
    2. **Test the hypothesis from HEAT**: does the measured outcome match the predicted outcome?
       If yes → record as supporting evidence. If no → record what actually happened.
    3. **Cross-reference with AgentDB**: does this change interact with known patterns or failures?
       Query: `SELECT insight FROM learnings WHERE domain = '{task_domain}' AND type = 'failure'`
       Any match = potential regression risk. Investigate before shipping.
    4. **Discover emergent patterns**: what surprised you? What worked that shouldn't have?
       What failed that should have worked? These are the seeds of new hypotheses.
    5. **Self-correct**: if temper reveals a problem quench missed, go back to hammer.
       If temper reveals an opportunity, seed a hypothesis for the next forge cycle.

    <emergence>
    The temper phase is where the forge develops intelligence across runs:
    - Cycle 1: baseline measurements, hypothesis formation
    - Cycle 2: compare against cycle 1 measurements, detect trends
    - Cycle 3+: patterns emerge — the forge knows which approaches work for which problems
    - Cross-session: temper learnings feed into HEAT phase of future forge runs
    </emergence>

    ```bash
    # Record measurements
    agentdb learn pattern "forge-temper: {what worked and why}" "{metrics}"
    
    # Seed hypothesis if emergent pattern found
    agentdb learn pattern "forge-hypothesis: {testable claim}" "{evidence from this cycle}"
    
    # Record cycle metrics for cross-session learning
    agentdb emit command "forge-temper" "" '{"cycle":N,"hypothesis_confirmed":true|false,"emergent":["..."],"metrics":{}}'
    ```

    If temper passes → proceed to SHIP.
    If temper reveals issue → back to HAMMER with temper feedback.
  </phase>

  <phase id="anneal" name="ANNEAL — Reheat and Restructure" trigger="quench.shattered">
    The current crystalline structure is brittle. Don't patch — remelt.

    1. Record WHY it shattered: agentdb learn failure "approach X failed because Y"
    2. Penalize this approach: mark as explored-and-failed.
    3. **Experiment on the failure**: WHY did this approach shatter? Is it a pattern?
       Check: does this shatter reason match any prior forge failures?
       If pattern found → skip entire class of approaches, not just this variant.
    4. Return to HEAT with the shatter reason + pattern analysis as new constraints.
    5. The next approach MUST be structurally different.

    This prevents hammering a fundamentally flawed approach into submission.
    Sometimes the metal needs a different alloy, not more force.

    Max anneals: 3. After 3 structural failures → STOP.
    "Tried 3 distinct approaches. All shattered. Here's why. Human decision needed."

    ```bash
    agentdb learn failure "forge-shatter: approach X because Y" "{diff, test output, adversary verdict}"
    agentdb emit command "forge-anneal" "" '{"reason":"X","approaches_exhausted":N,"pattern_match":"..."}'
    ```
  </phase>

  <phase id="ship" name="SHIP — Release the Forged Artifact" trigger="temper.passed">
    Solution survived entropy AND experimentation. Ship it.

    Profile-gated:
    - local: commit to main
    - github: commit + push
    - github-oss: feature branch → PR → self-review via /kernel:review
    - github-production: feature branch → PR → request review

    ```bash
    agentdb learn pattern "forge-shipped: {approach}, integrity {score}, {key metric}" "{evidence}"
    agentdb emit command "forge-ship" "" '{"iterations":N,"integrity":0.X,"approach":"X","temper_findings":[]}'
    agentdb write-end '{"command":"forge","iterations":N,"tests":N,"integrity":0.X,"shipped":true,"emergent_hypotheses":N}'
    ```
  </phase>

</cycle>

<council note="tier 3 only">
  For tier 3 tasks, spawn a full agent council:
  - researcher + scout: parallel reconnaissance
  - dreamer: 3 competing approaches (after recon)
  - surgeon: implement winning approach
  - adversary: coordination + entropy testing (quench phase)

  Council communicates via agentdb. Each reads prior agents' output.
  You orchestrate the sequence and handle annealing.
</council>

<loop_control>
  continue_if: progress (tests improving, integrity increasing, temper passing)
  anneal_if: integrity < 0.6
  temper_back_to_hammer_if: temper reveals missed issue
  stop_if: 3 anneals OR 10 iterations OR scope creep
  on_stop: audit trail (approaches+scores, shatter reasons, temper findings, emergent hypotheses, learnings)
</loop_control>

<experimental_behavior>
  The forge is not just a build tool — it's a learning system.

  **Within a single run:**
  - Each cycle generates data (metrics, failures, successes)
  - TEMPER phase analyzes that data and forms hypotheses
  - Subsequent cycles test those hypotheses
  - Emergent patterns are captured as learnings

  **Across runs:**
  - HEAT reads prior forge learnings (forge-temper, forge-shatter, forge-shipped)
  - Approaches that worked before are preferred (but not blindly repeated)
  - Shatter patterns are avoided (but not blindly excluded — context matters)
  - The forge gets smarter with each use, not just from code but from self-measurement

  **What makes this different from plain iteration:**
  - Plain iteration: try → fail → try again
  - Forge with temper: try → measure → hypothesize → test hypothesis → learn → try smarter
  - The difference is the hypothesis step: the forge doesn't just retry, it asks WHY
</experimental_behavior>

</skill>
