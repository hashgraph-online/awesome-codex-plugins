---
name: ingest
description: "Entry point for new or resumed work. Researches and scopes new tasks; validates and resumes handoff/checkpoint manifests. Triggers: start, begin, do, implement, build, fix, create, resume, continue."
user-invocable: true
allowed-tools: Read, Bash, Grep, Glob, Task, WebSearch, WebFetch
kernel:
  kind: workflow
  version: 1
  side_effects: writes_repo
  confirmation: none
  consumes:
    - kernel.handoff/v1
    - kernel.checkpoint/v1
---

<skill id="ingest">

<purpose>
Unified entry for new and resumed work.
New task:  READ → CLASSIFY → RESEARCH → SCOPE → TESTS → EXECUTE → LEARN (human confirms each phase).
Resume:    DISCOVER → VALIDATE → DIVERGENCE → COMPILE (bounded context + receipt) → RESUME AT PHASE.
For autonomous loop: /kernel:forge

Authority order (highest wins) — a manifest is a map, not the territory:
1. live verified repository state
2. explicit current user instruction
3. handoff or checkpoint manifest
4. chronicle
5. inferred conversation history
</purpose>

<skill_load>
always: skills/debug/SKILL.md
on_classify:
  bug:      skills/debug/SKILL.md
  feature:  skills/build/SKILL.md, skills/architecture/SKILL.md
  refactor: skills/architecture/SKILL.md
  review:   skills/review/SKILL.md
on_domain:
  frontend: skills/frontend/SKILL.md
  app:      skills/app-dev/SKILL.md
on_tier:
  2+:       skills/orchestration/SKILL.md
reference: skills/build/reference/build-research.md
</skill_load>

<on_start>
```bash
agentdb read-start
ls _meta/research/  # check prior work
```

Load /kernel:quality, /kernel:testing, /kernel:git immediately.
After classify: load task-specific skills above. Do NOT proceed without loading them.
After scope: if tier 2+, load /kernel:orchestration.
If any domain detected (API, auth, frontend, backend): load domain skills.
</on_start>

<step id="1_classify">
task: what user wants (one sentence)
type: bug|feature|refactor|question|verify|resume|review
familiar: yes|no

Search before asking: Glob, Grep, common paths.

<ask_user>
  Use AskUserQuestion when: classification is ambiguous (could be bug or feature, refactor or rewrite)
  Ask: "This looks like {type_A} but could be {type_B}. Which framing fits your intent?"
  Options: type_A, type_B, or clarify
</ask_user>

After classify: load matching workflow from workflows/{type}.md if it exists.
Workflow steps guide the phase sequence. Human confirms at each step (ingest mode).
</step>

<branch after="classify">
  IF type == resume (or a manifest path was supplied) → go to MANIFEST RESUME (below)
  IF familiar AND tier_likely_1 → skip to step 3 (scope), mark research="skipped (familiar)"
  IF unfamiliar OR complex → proceed to step 2 (research)
  ALWAYS: check _meta/research/ cache regardless (cache != full research)
</branch>

<step id="1b_manifest_resume" trigger="classify.type == resume">
  Resume from a kernel.handoff/v1 or kernel.checkpoint/v1 manifest. The runtime CLI:
  `KM="${CLAUDE_PLUGIN_ROOT:-.}/orchestration/manifest/kernel-manifest"`

  1. **Discover**: explicit path if the user gave one, else:
     ```bash
     "$KM" latest        # newest across _meta/checkpoints/ + _meta/handoffs/
     ```
     Legacy markdown handoffs (_meta/handoffs/*.md) remain readable this release:
     parse goal/decisions/next-steps from prose, note "legacy handoff (deprecated,
     no validation/divergence/budget)" and suggest regenerating as JSON. Removal
     path: docs/MIGRATION-8.md.

  2. **Validate** — a manifest that does not validate is not resumed:
     ```bash
     "$KM" validate <manifest>     # exit 2 (no parser) on a sealed manifest = STOP
     ```

  3. **Divergence** — live state wins over manifest claims:
     ```bash
     "$KM" divergence <manifest> --json
     ```
     Typed divergence events apply `workflow.invalidation_rules[].when` and return
     recalculated phase statuses. Never trust an inherited phase whose inputs changed.

  4. **Preflight**: run `"$KM" preflight <manifest>`. Canonical state permits only typed
     current-branch, path-exists, and allowlisted argv checks; raw shell is invalid.

  5. **Compile bounded context** — read the bundle, not the raw tree:
     ```bash
     "$KM" compile <manifest> --bundle-out /tmp/resume-bundle.md --receipt-out _meta/reports/receipt-{date}.json
     ```
     The receipt (kernel.context-receipt/v1) reports estimated tokens per layer and
     status: within_budget → proceed · target_exceeded → drop optional selectors,
     proceed with a note · maximum_exceeded (exit 3) → STOP, report the receipt,
     ask before loading anything.

  6. **Activate** the policy (arms the guard-context hook for sealed/bounded):
     ```bash
     "$KM" activate <manifest>
     ```
     sealed: forbidden globs are hook-BLOCKED; do not fight the hook — amend the
     manifest if access is genuinely needed. bounded: extra loads are allowed but
     ledgered; justify each in the receipt's loads_beyond_manifest.

  7. **Resume at the declared position**:
     ```bash
     "$KM" resume <manifest>    # entry_phase / entrypoint / next_operation
     ```
     Skip inherited phases (already verified by divergence), execute required ones.
     Honor execution.stop_conditions and emit checkpoints at execution.checkpoints.

  8. **Complete**: when outputs.required are verified,
     ```bash
     "$KM" deactivate --receipt _meta/reports/receipt-{date}.json
     ```
     Deactivate projects the receipt into AgentDB's observational context graph (shadow
     telemetry). Then outputs.completion (usually agentdb write-end), which records session
     outcome on that graph row when `did`/`blocked` are present.

  Optional advisory (never auto-loads):
     ```bash
     agentdb graph-suggest {task_type}
     ```

  Output: "Resuming {manifest}: {goal}. Entry: {entry_phase}. Receipt: {total_estimated_tokens} tokens ({status})."
</step>

<step id="2_research" mandatory="true">
**RULE: Research without verification is theory fiction.** Every research finding must be verified
with a minimal test, prototype, or proof before it drives implementation. 8 research agents and
6 docs mean nothing if nobody built a test to prove the approach works. (LRN-F11)

<substeps>
1. Check existing: ls _meta/research/, agentdb query
2. anti_patterns FIRST: "{tech} not working", "{tech} gotchas"
3. Solutions: official docs, GitHub issues, Stack Overflow
4. Built-in check: framework > stdlib > npm package
5. **Verify**: build minimal proof (test screen, script, unit test) before committing to approach
6. Write to: _meta/research/{topic}.md (include verification result)
</substeps>

<format>
# {Topic} Research
## Anti-Patterns
1. {pattern}: {why} → {fix}
## Proven Solution
- package: {name}@{version}
## Sources
- {urls}
</format>

tier 2+: spawn kernel:researcher

<ask_user>
  Use AskUserQuestion when: research reveals multiple viable approaches or unknown risks
  Ask: "Research found {N} approaches. Proceed with {recommended}, or explore alternatives?"
  Options: proceed, explore alternatives, skip research
</ask_user>
</step>

<step id="3_scope">
files:
  1: {path} - {what changes}
count: N
tier: 1|2|3

<tiers>
1: reversible + loud if wrong → execute inline
2: persistent or moderately quiet → plan, execute inline; delegate a surgeon only for heavy file-disjoint work; verify
3: hard to undo, quiet if wrong, or wide blast radius → contract + surgeon + adversary
ambiguous: assume higher. File count is only a weak hint, never the trigger.
</tiers>

<ask_user>
  Use AskUserQuestion when: tier classification is borderline (e.g., 2-3 files but complex coupling)
  Ask: "Scoped to {N} files — tier {X}. Confirm tier, or should I treat as tier {X+1}?"
  Options: confirm tier {X}, bump to tier {X+1}

  When the request itself is underspecified (any GOAL/CONSTRAINTS/INPUTS/OUTPUTS/DONE-WHEN
  field unknowable), run the structured interview from skills/build/SKILL.md "The
  interview" BEFORE scoping: batched AskUserQuestion rounds over intent, implementation
  forks, veto-risk UX, edge behavior, and tradeoffs. Bounded choices only; open-ended
  direction stays prose. Answers are quoted into the spec/commission so each decision
  carries its authority.
</ask_user>
</step>

<branch after="scope">
  IF scope reveals unknowns not covered by research → loop to step 2 with narrowed query
  IF scope is clear → proceed to step 4
</branch>

<step id="4_tests" mandatory="true">
<rule>Define success before coding. Tests first.</rule>
skill_ref: skills/build/reference/testing.md

done_when:
  - observable outcome 1
  - edge case handled

evals:
  code_grader: PASS/FAIL command
  regression: existing tests pass

<principles>
mock_boundaries_only: external APIs, DBs
edge_cases_first: null, empty, boundary, timeout
strong_assertions: specific values
</principles>
</step>

<step id="4b_spec_completeness" mandatory="true">
<rule>Spec framing > contract framing. Execution-ready, not goal-shaped.</rule>

Specification prompts with exact code achieve 100% success across all scopes (modelmind H002/H003,
0.95 confidence). Contract framing ("achieve X under constraint Y") leaves interpretation gaps
that agents fill incorrectly.

Before handing to surgeon (tier 2+) or starting execution (tier 1), the spec must answer:
- **Exact file paths**: every file that will change, by absolute path
- **Exact symbols**: every function/class/type to add/modify/remove, by name
- **Exact code snippets** for non-trivial logic (not pseudocode, not "implement X")
- **Exact configs/SQL/schemas**: if the change touches them, paste the literal block
- **Exact verification commands**: how a fresh agent confirms success without asking

Litmus test: **could a fresh agent in a new session execute this spec with zero follow-up
questions?** If no, the spec is incomplete. Return to step 3 (scope) or step 4 (tests) and fill
the gap before proceeding.

Anti-pattern: shipping a contract that says "the surgeon will figure out X." The surgeon will
figure out X by guessing, and the guess will be wrong.

<ask_user>
  Use AskUserQuestion when: the spec has a known gap and you need the user to decide which
  exact path to take (rather than letting the surgeon guess).
  Ask: "Spec gap at {location}: option A = {exact}, option B = {exact}. Which?"
  Options: option A, option B, other
</ask_user>
</step>

<step id="5_execute">
<tier_1>
1. Reference research doc
2. Write failing tests (edge cases!)
3. Implement proven pattern
4. Check Big 5: skills/quality/SKILL.md
5. Run evals → /kernel:validate before commit
6. Commit when done_when satisfied
</tier_1>

<tier_2_plus>
rule: you do NOT write code
1. /kernel:tearitapart — review plan before implementation
2. agentdb contract '{"goal":"X","files":["Y"],"tier":N}'
2b. If non-local profile: _gh_create_issue with contract goal + tier label
3. git checkout -b {type}/{name}
4. Spawn surgeon
5. Wait for checkpoint
6. (tier 3) spawn adversary
7. /kernel:validate → verify evals
8. /kernel:review — self-review before PR
</tier_2_plus>
</step>

<branch after="execute">
  IF adversary rejects (tier 3) → return to execute with adversary feedback, max 3 retries
  IF tests fail → /kernel:diagnose, fix, re-execute
  IF blocked → checkpoint and STOP, ask human
</branch>

<step id="6_learn" mandatory="true">
<rule>Every task teaches. Capture or lose.</rule>

agentdb learn pattern "{what worked}" "{evidence}"
agentdb learn failure "{what broke}" "{evidence}"
Update _meta/research/ if new findings.
Suggest /kernel:retrospective if 5+ learnings accumulated since last synthesis.
Long task still running? Emit /kernel:checkpoint at natural boundaries instead of letting context accumulate (EXP-L21).

<checkpoint>
agentdb write-end '{"task":"X","tier":N,"learned":["Z"]}'
MUST run before session ends.
</checkpoint>
</step>

<output_format>
task: one sentence | type: bug|feature|refactor | tier: 1|2|3 | status: researching|scoping|testing|executing|complete
</output_format>

<hard_stops>
ask_file_location→search | code_without_research→step2 | code_without_tests→step4 | code_tier2+→surgeon | skip_agentdb→go_back
</hard_stops>

</skill>
