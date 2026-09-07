---
name: experiment
description: "Experiment engine for development rules. Treats rules as hypotheses, designs falsifiable tests, updates confidence, and graduates or kills rules. Triggers: experiment, hypothesis, prove, test rule, validate methodology, scientific, evidence."
user-invocable: true
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent, WebSearch, WebFetch
kernel:
  kind: workflow
  version: 1
  side_effects: writes_meta
  confirmation: on_side_effect
---

<skill id="experiment">

<purpose>
Rules without evidence are superstitions. One invocation, no subcommands: the engine
figures out what the hypothesis system needs — seeds, tests, graduates, or kills.

  - No hypotheses? Seeds them from CLAUDE.md.
  - Hypotheses exist? Picks the most uncertain, designs an experiment, runs it.
  - Evidence accumulating? Graduates proven rules, kills disproven ones.
  - Everything tested? Reports and stops.

Rules that survive become convictions. Rules that fail become learnings.
</purpose>

<reference>
Deep patterns, SQL schema, domain design templates, confidence-scoring examples:
skills/experiment/reference/experiment-research.md
</reference>

<skill_load>
always: skills/quality/SKILL.md, skills/build/reference/testing.md
</skill_load>

<on_start>
```bash
agentdb read-start
agentdb emit command "experiment-start" "" '{}'
```
</on_start>

<cycle id="experiment" max_iterations="20">

  <phase id="sense" name="SENSE — Read the State">
    Autonomous entry point. Determine what the system needs.

    ```bash
    agentdb hypothesis list 2>/dev/null
    ```

    Decision tree (no human input needed):
    1. No hypotheses table or empty? → go to SEED phase.
    2. Hypotheses exist but all are unproven? → go to PICK phase.
    3. Mix of tested/untested? → go to PICK phase (prioritize untested).
    4. All have >= 3 experiments? → go to JUDGE phase.
    5. Graduation/kill candidates exist? → go to EVOLVE phase.
  </phase>

  <phase id="seed" name="SEED — Extract Rules as Hypotheses" trigger="sense.no_hypotheses">
    Scan every CLAUDE.md in the project hierarchy + rules/*.md + skills/*/SKILL.md.

    Parse rule-like patterns:
    - Imperative: "Always X", "Never Y", "Prefer Z", "Must W"
    - Anti-patterns: block actions, "Don't", "Forbidden"
    - Assertions: "X before Y", "X is better than Y"
    - Quantitative claims: "reduces by X%", "takes N minutes"
    - Conditional: "If X then Y", "When X, do Y"

    For each rule:
    ```bash
    agentdb hypothesis add "<statement>" --domain <auto-classify> --source "<file:line>"
    ```

    Domain auto-classification by keyword:
    - research, anti-pattern, prior work → methodology
    - parallel, agent, spawn, tier → coordination
    - test, coverage, edge case, mock → testing
    - commit, branch, merge, PR → git
    - secret, validation, auth, injection → security
    - measure, optimize, latency, profile → performance
    - Big 5, review, quality → quality
    - module, interface, coupling → architecture

    Deduplicate: skip if near-identical statement already exists.
    Log count, then immediately proceed to PICK. No pause.

    ```bash
    agentdb emit command "experiment-seed" "" '{"seeded":N}'
    ```
  </phase>

  <phase id="pick" name="PICK — Select Next Hypothesis">
    Choose the hypothesis that will produce the most information.

    Priority order:
    1. **Most uncertain**: confidence closest to 0.5 (maximum ignorance — any experiment is maximally informative)
    2. **Least tested**: fewest total experiments (break ties)
    3. **Highest impact domain**: methodology > coordination > security > testing > quality > git > architecture > performance

    ```sql
    SELECT id, statement, domain, confidence, evidence_for + evidence_against as total_evidence
    FROM hypotheses
    WHERE status NOT IN ('graduated', 'refuted')
    ORDER BY ABS(confidence - 0.5) ASC, total_evidence ASC
    LIMIT 1;
    ```
  </phase>

  <phase id="design" name="DESIGN — Create the Experiment">
    Autonomously design the minimum viable experiment.

    **Falsifiability gate: if no possible outcome could refute the hypothesis, redesign.**
    Every experiment defines BEFORE running: method, quantitative measurement, control
    condition (what happens WITHOUT the rule), pass_criteria, fail_criteria.

    Choose the LIGHTEST experiment type that produces signal:

    1. **HISTORICAL** (cheapest — query existing data):
       Query agentdb learnings, session outcomes, error patterns for evidence.
       Use when: agentdb has >= 10 sessions or >= 20 learnings in the domain.
    2. **COMPARATIVE** (medium — run a real task two ways):
       Execute WITH the rule applied, then WITHOUT (or find prior without-cases).
       Measure: time, error count, rework, quality.
    3. **ABLATION** (medium — remove the rule, observe):
       Temporarily ignore the rule during a real task. Record what breaks.
    4. **OBSERVATIONAL** (passive — tag next N tasks):
       Flag the hypothesis; future relevant tasks collect evidence passively.
       Use when: active experimentation would be disruptive.

    Minimum sample sizes: methodology/coordination/git/quality >= 3 comparisons;
    testing >= 5 tasks per condition; security >= 50 fuzz inputs.

    ```bash
    agentdb experiment add <H_ID> "<method>" "<measurement>" --pass-criteria "<criteria>"
    ```
  </phase>

  <phase id="run" name="RUN — Execute and Observe">
    Run the designed experiment. Record everything.

    **Gate: the control condition was actually tested, not just assumed.**

    - HISTORICAL: query agentdb with specific SQL; evidence = query result + interpretation.
    - COMPARATIVE: execute the task (spawn agents if needed); evidence = measured delta.
    - ABLATION: execute with the rule explicitly ignored; evidence = observed difference.
    - OBSERVATIONAL: record the flag; skip to next hypothesis (no blocking).
  </phase>

  <phase id="conclude" name="CONCLUDE — Verdict and Confidence Update">
    Compare observations against pass/fail criteria. Issue verdict honestly:
    **supports** | **refutes** | **inconclusive**.

    ```bash
    agentdb experiment verdict <EXP_ID> <supports|refutes|inconclusive> "<evidence summary>"
    ```

    Confidence update (Bayesian, applied automatically by CLI):
    - supports:     confidence += (1 - confidence) * 0.25
    - refutes:      confidence -= confidence * 0.3
    - inconclusive: no change

    Evidence strings must be specific and measurable, never narrative.

    Lifecycle transitions:
    - unproven → testing: first experiment registered
    - testing → supported: confidence >= 0.8 AND evidence_for >= 3 AND ratio >= 3:1
    - testing → refuted: confidence < 0.2 AND evidence_against >= 2
    - supported → graduated: human approval after sustained confidence
    - refuted → killed: human approval to remove from rules
    - any → unproven: rule is modified (resets all evidence)

    ```bash
    agentdb learn pattern|failure "<what we learned>" "<evidence>"
    agentdb emit command "experiment-conclude" "" '{"H":"ID","EXP":"ID","verdict":"X","confidence":0.XX}'
    ```

    Loop back to PICK for next hypothesis.
  </phase>

  <phase id="judge" name="JUDGE — Review All Evidence" trigger="sense.sufficient_evidence">
    For each hypothesis with >= 3 experiments: summarize evidence, calculate final
    confidence, classify graduated | refuted | needs-more-evidence | inconclusive.

    ```bash
    agentdb hypothesis export
    ```
    Write detailed report to _meta/research/experiment-report.md. Proceed to EVOLVE.
  </phase>

  <phase id="evolve" name="EVOLVE — Self-Reconfigure">
    The emergent part. The system reconfigures based on evidence.

    **Graduate** (confidence >= 0.8, evidence_for >= 3, ratio >= 3:1):
    promote via the artifact ladder with human approval — hook if enforceable, agent if
    a role, skill if methodology; CLAUDE.md prose only as last resort.

    **Kill** (confidence < 0.2, evidence_against >= 2):
    propose rule removal from CLAUDE.md (present to human).

    **Mutate** (inconclusive after 5+ experiments):
    the hypothesis may be poorly stated; propose a refined version as a NEW hypothesis,
    linked to the original (evolution chain).

    <ask_user>
      Use AskUserQuestion ONCE at the end of the evolve phase:
      Ask: "{graduated} rules proven, {killed} rules disproven, {mutated} rules refined. Apply changes?"
      Options: apply all, review individually, skip for now
    </ask_user>

    ```bash
    agentdb emit command "experiment-evolve" "" '{"graduated":N,"killed":N,"mutated":N}'
    ```
  </phase>

</cycle>

<loop_control>
  continue_if: untested hypotheses remain OR new evidence changes confidence significantly
  pause_at:    EVOLVE phase (only human checkpoint — graduation/kill decisions)
  stop_if:     all hypotheses have >= 3 experiments AND no graduation/kill candidates
  on_stop:     write final report to _meta/research/experiment-report.md, agentdb write-end
  Iteration budget: max 20 cycles per invocation.
</loop_control>

<anti_patterns>
  <never>Confirm a hypothesis without running a real experiment.</never>
  <never>Use a single data point to graduate a hypothesis.</never>
  <never>Ignore refuting evidence because the rule "feels right".</never>
  <never>Test a hypothesis with a method that can only confirm (design for falsifiability).</never>
  <never>Modify the hypothesis after seeing results (that is a new hypothesis).</never>
</anti_patterns>

<hard_stops>
  - NEVER modify CLAUDE.md autonomously. Present changes at EVOLVE, human decides.
  - NEVER delete hypotheses. Mark as refuted. Audit trail is sacred.
  - NEVER fabricate evidence. If experiment can't run, mark inconclusive with reason.
  - NEVER run destructive experiments without explicit approval.
  - ALWAYS record evidence, even for inconclusive results.
</hard_stops>

<on_end>
```bash
agentdb write-end '{"skill":"experiment","cycles":N,"experiments_run":N,"graduated":N,"refuted":N,"mutated":N}'
```
</on_end>

</skill>
