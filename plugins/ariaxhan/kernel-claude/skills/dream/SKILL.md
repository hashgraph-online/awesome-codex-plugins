---
name: dream
description: "Deep creative exploration engine. Competing perspectives, stress-tested by a 4-persona council, scored by integrity. The approach that survives attack wins — not the one that sounds best."
user-invocable: true
allowed-tools: Agent, Bash, Read, Write, Grep, Glob, WebSearch
kernel:
  kind: workflow
  version: 1
  side_effects: writes_meta
  confirmation: none
---

<skill id="dream">

<purpose>
Expand the solution space BEFORE committing.

Not "give me 3 options" — structured divergence:
competing value systems + adversarial stress test + integrity scoring.

The winning approach is the one that SURVIVES attack, not the one that sounds best.

Use before any non-trivial decision. Use when the obvious answer feels too easy.
</purpose>

<on_start>
agentdb read-start   # prior dreams + learnings seed the perspectives; don't re-explore killed approaches
</on_start>

<skill_load>
always: skills/quality/SKILL.md, skills/architecture/SKILL.md
on_domain:
  api:      skills/architecture/reference/api.md, skills/architecture/reference/backend.md
  frontend: skills/frontend/SKILL.md
  backend:  skills/architecture/reference/backend.md
  security: skills/tearitapart/reference/security.md
</skill_load>

<!-- ============================================ -->
<!-- THE DREAM CYCLE                              -->
<!-- ============================================ -->

<phase id="0_ground" name="Ground in Reality">
  Before dreaming, understand what exists:
  1. Glob/Grep affected areas in the codebase
  2. Check _meta/research/ for prior work
  3. Check agentdb for related learnings/failures
  4. Map existing patterns, conventions, constraints

  Dreams that ignore the codebase are fantasies, not proposals.
</phase>

<phase id="1_diverge" name="Generate Competing Perspectives">

  <perspective id="minimalist" voice="terse, provocative, reductive">
    Goal: the SMALLEST possible solution. Question the premise itself.
    - Can we delete our way to the answer?
    - Does an existing tool/library already do this?
    - What if we just... don't build this?
    - What's the 20-line version?

    Target: 90% code reduction. Must reference actual files that could be deleted.
    Format: 3-8 lines. Effort estimate. Coverage percentage.
  </perspective>

  <perspective id="maximalist" voice="expansive, visionary, system-thinking">
    Goal: the version you'd be PROUD of in 6 months.
    - What does the ideal architecture look like?
    - What does this unlock beyond the immediate need?
    - What edge cases should be handled from day 1?

    Target: complete solution. Must sketch actual architecture, not hand-wave.
    Format: full description with component diagram. Effort estimate.
  </perspective>

  <perspective id="pragmatist" voice="balanced, explicit about tradeoffs, deadline-aware">
    Goal: the 80/20 point. Ship this week.
    - What's the minimum that solves the real problem?
    - What can we defer without paying interest?
    - What's the upgrade path when we need more?

    Target: 80% solution with clear upgrade path.
    Must explicitly state what's deferred and the cost of deferral.
    Format: concrete plan. Effort estimate. Tradeoff table.
  </perspective>

  Tier 1: generate all 3 inline.
  Tier 2+: spawn dreamer agent for codebase-grounded perspectives.
</phase>

<phase id="2_stress_test" name="4-Persona Council — Find What Breaks">
  For EACH perspective, run through the council. Not voting — adversarial probing.

  <council>
    <persona id="architect" concern="fragility, scale, tech debt">
      Probes structural integrity. Coupling, single points of failure, migration nightmares.
      Breaks things by asking "what happens when..."
    </persona>

    <persona id="user" concern="usability, complexity, does it solve MY problem?">
      Cuts through elegance. "Does it work for the person using this every day?"
    </persona>

    <persona id="adversary" concern="what breaks, worst case, what was missed">
      Pure attack mode. Edge cases, race conditions, security holes, wrong assumptions.
      If they can't find a flaw, the approach is strong.
    </persona>

    <persona id="operator" concern="can we ship it, can we maintain it, blast radius">
      Operational reality. Deployment, monitoring, rollback, on-call burden.
      Beautiful code that's hell to operate fails.
    </persona>
  </council>

  Each persona: 2-3 lines per perspective. Specific concerns, not essays.

  <ask_user>
    Use AskUserQuestion when: perspectives generated, before running council
    Ask: "Three perspectives ready. Which resonates, or run all through stress test?"
    Options: stress test all, lean toward {minimalist|maximalist|pragmatist}, rethink framing
  </ask_user>
</phase>

<phase id="3_measure" name="Integrity Scoring">
  For each perspective, score integrity based on council feedback:

  - How many council members raised critical (not fixable) concerns?
  - Did the perspective already account for the concerns?
  - Are the flaws structural or cosmetic?

  >= 0.8: ANTIFRAGILE — stronger because of the attacks.
  >= 0.6: VIABLE — survives with minor fixes.
  < 0.6: SHATTERED — fundamental flaws. Don't pursue.

  Rank surviving perspectives by score.
  If ALL shatter: the problem needs reframing (thermal shock).
</phase>

<phase id="4_present" name="Present Results">
  <output_format>
  # Dream: {topic}

  ## Context
  {codebase state, constraints, existing patterns}

  ## Perspectives (ranked by integrity)

  ### {emoji} {name} — integrity: {score}
  {perspective content}
  **Effort:** {estimate}
  **Council verdict:** {1-line summary per persona}
  **Survived because:** {why it's robust}
  — {perspective name}

  {repeat for each surviving perspective}

  ### Shattered
  {any that didn't survive, with reason}

  ---
  ## Recommendation
  {highest integrity + why. hybrid options if scores are close.}

  **Next:** /kernel:forge {approach} or /kernel:ingest for guided execution.
  </output_format>

  <ask_user>
    Use AskUserQuestion when: results presented with ranked perspectives
    Ask: "Proceed with {winner}, hybrid approach, or rethink the problem?"
    Options: proceed with winner, hybrid of top 2, rethink
  </ask_user>
</phase>

<phase id="thermal_shock" name="All Perspectives Shattered" trigger="all_shatter">
  Every approach failed the stress test. The problem needs reframing.

  1. Record why each shattered (agentdb learn failure)
  2. Ask: is the problem statement wrong? Solving the right thing?
  3. Generate 1-2 reframings of the original problem
  4. Return to diverge phase with reframed problem (max 1 reframe)
  5. If still shatters: STOP. "This needs human decomposition."
</phase>

<github_integration>
  If gh authenticated and profile is github-oss or github-production:
    Post dream to GitHub Discussions (Decisions category).
  Otherwise:
    Write to _meta/dreams/{topic}.md only.
</github_integration>

<telemetry>
agentdb emit command "dream" "" '{"topic":"X","perspectives":3,"survived":N,"chosen":"pragmatist","integrity":0.85}'
</telemetry>

</skill>
