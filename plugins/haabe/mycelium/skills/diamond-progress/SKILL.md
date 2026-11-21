---
name: diamond-progress
description: "Record a diamond's next decision (set_target; start_experiment and commit_to_build; release; close; an L0's state_purpose or review). Runs the theory gates each decision needs, validates evidence, and at close runs the executable Definition of Done checklist."
metadata:
  instruction_budget: "205"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Diamond Progress Skill

Record a diamond's decisions, each through the theory gates it needs. Where a diamond is, is read from its decisions ("target set", "committed to build", "released", "closed"; discovery until `commit_to_build`, delivery after; DL-1368, DL-1372). At `close`, runs an executable checklist that GATES it.

## Preflight: Read target canvas file(s) before any Write/Edit

**Hard rule.** Before issuing `Write` or `Edit` against any `.claude/canvas/*.yml`, use the **Read tool** on that file in this session. Claude Code's Read-before-Write check requires the `Read` tool specifically — `cat`/`head`/`grep` via Bash do NOT satisfy it.

## Preflight: Read-before-Recommend (gate-narration discipline)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 graduation v0.39.16). Every gate-status narration, blocker statement, hold claim, theory-gate verdict, or transition-blocked finding this skill emits MUST cite the canvas file + field path of the source evidence. Adjacent-surface inference (different opportunity, different ht, different topic) MUST be tagged as inference, not asserted as gate state. Companion to the Read-before-Write rule above: that one protects what gets WRITTEN to canvas; this one protects what gets CLAIMED about canvas state in the skill's narration.

**Edit vs Write — different cost profiles** (verified 2026-05-14):
- **`Edit`** (exact-string replacement): `Read` with `limit: 1` satisfies the check at ~50 tokens. State-tracking is per-file, not per-byte — subsequent `Edit` calls work anywhere in the file. Use this for partial updates against large canvas files (e.g., `purpose.yml` at 800+ lines).
- **`Write`** (full replacement): do a **full Read** first. Write obliterates the file; you should see what you're about to replace. The `limit:1` shortcut is *not* appropriate here.

**ID-bearing entries — scan the ID space before assigning** (added 2026-05-15, v0.23.19): When adding a new component, opportunity, solution, or any other ID-bearing entry to a canvas file, run a Bash grep first to confirm the next ID in your prefix sequence is actually free:

```
grep -o "<prefix>-[0-9][0-9]*" .claude/canvas/<file>.yml | sort -u -t- -k2 -n | tail -3
```

Replace `<prefix>` with the canvas's ID prefix (`comp` for landscape, `opp` for opportunities, `sol` for solutions, `ht` for human-tasks, etc.). Then pick the next free integer, **matching the zero-padding already used in that file**. The sort is NUMERIC (`-t- -k2 -n`) rather than lexical, and that is not pedantry: a plain `sort -u` orders `ht-1` after `ht-080`, so on a canvas with inconsistent padding it reports the wrong maximum and the next ID collides. Verified on the dogfood repo 2026-08-13, where lexical sort returned `ht-1` as the highest human-task ID against an actual `ht-080`. `grep -o` is also deliberate: it matches IDs wherever they appear, including cross-references and prose, so an ID that was promised somewhere but not yet defined is not handed out twice. `validate_canvas.py` has a per-file duplicate-ID check (it reports `duplicate id '<id>'`) that catches the failure on CI, but a duplicate can persist in the working tree for days if CI isn't run between edit and discovery; that happened on 2026-05-15, when a duplicate ID was created in `landscape.yml`.

Original failure mode: anti-pattern #7 instance #5, 2026-05-09 — agent conflated Bash `head` with the Read tool, lost ~14k tokens to a Write-fail → remedial-full-Read → re-Write loop. The `limit:1` discipline (graduated 2026-05-14, v0.23.18) prevents the second-order cost where the agent *correctly* follows the rule but full-Reads every time. The ID-scan discipline (graduated 2026-05-15, v0.23.19) prevents the related class where the agent reads enough of the file to satisfy the Edit check but not enough to see existing ID assignments — kin to anti-pattern #8 (Stale State Read).

If this skill writes to multiple canvas files, register each one first (limit:1 for Edit-only paths; full Read for Write paths) AND ID-scan any prefix you intend to assign.

See `${CLAUDE_PLUGIN_ROOT}/engine/agent-operating-contract.md` *Canvas writes — Read before Write* for the canonical rule.

## Workflow

1. **Identify the decision**: where the diamond is (`scale_locks.position`, e.g. "target set
   (discovery)") and the decision to record next at [scale]: `set_target`; `start_experiment` and
   `commit_to_build`, recorded together to commit to build; `release`; `close`. An L0 records
   `state_purpose`, then `review`. To iterate, append (DL-1373, step 8).

1b. **Cognitive Forcing (before gate evaluation)**:

   Before running gates, ask the human for their unprimed judgment:

   > "Before I check the gates — do you think we're ready to record [decision]? What's your gut say?"

   Wait for the response. Record it. Then run the gates. After presenting results, compare:

   > "You said [X]. The gates say [Y]. Where do we differ?"

   **The turn that asks this question ends with a `Next:` line, like every turn in which a skill ran** (contract rule 12). The question is the next action: `Next: say whether you think we're ready to record [decision] (per: diamond-progress step 1b)`. Without that line the Stop hook `hooks/next-action-check.sh` blocks the turn, and Claude Code shows the block to the person as "Stop hook error" under a question they have not answered yet. The same pause in diamond-assess step 0 caused 3 of that hook's first 5 blocks on the dogfood project.

   The human's instinct often catches risks the gates miss. If the human says "not ready" but gates pass, investigate — the human may be sensing something the evidence hasn't captured yet.

   *Source: Buçinca, Malaya & Gajos (Cognitive Forcing Functions, Harvard CHI/CSCW 2021). Applied after Hoskins transcript analysis — Drew's product judgment consistently outperformed the agent's gate-based assessment.*

   **Autonomous mode** (per `${CLAUDE_PLUGIN_ROOT}/engine/autonomous-mode.md`): rung (b) — record the declared persona's gut call BEFORE running gates, tag `internal_simulated`, ledger it. The compare-after step still runs.

1c. **At an L1 or L2 `set_target`: the opposite question (a prompt, not a block)**:

   When the decision is `set_target` on an L1 (the outcome it sets) or an L2 (the opportunity it targets), ask the same one-line question `/mycelium:define-done` step 1 asks of an outcome, about the target being set:

   > "Write the opposite of this outcome. Would anyone choose it?"

   Ask it in the same turn as step 1b's question, so the run pauses once. A target whose opposite is absurd on its face makes no choice: it rules out no work, and every later diamond can be argued to serve it. If the opposite is absurd, offer to narrow one part (who, what changes, how) until the opposite is something a reasonable builder might pick; what the person decides is written as any choice is (step 8, "A choice is written when it is made"), and the decision-log entry keeps both wordings, the first and the narrowed one. This is a prompt, never a block: the person judges whether the opposite is absurd, a target that already rules something out passes as written, and no gate reads the answer. The source is cited in `/mycelium:define-done` step 1.

2. **Run all required theory gates** (per ${CLAUDE_PLUGIN_ROOT}/engine/theory-gates.md Decision Matrix, one column per decision; a move needs the gates of every decision it records):
   - For each gate:
     a. State the gate name and source theory.
     b. **Surface the suggested skill**: "Run `/skill-name` to satisfy this gate."
     c. Evaluate pass criteria against available evidence.
     d. Record Pass / Fail / Insufficient Evidence **in `theory_gates_status` on the diamond, on
        every outcome, not only when it progresses** (`pass`, `fail`, or `pending` with what is
        missing in `progression_blockers`). Added v0.278.0: E2E rung L4-define ran this skill on an
        L4, ruled needs-evidence, and wrote no gate result, since the only instruction to record
        gates sat under the phase move. The next session read "no gate results are recorded" as a
        blocker, the closing path read the empty field as every gate passing, and the L4 sat in
        discover. A gate evaluated and not written is a gate the next assessment re-derives from
        nothing.
     e. If Fail: document what is missing, recommend the skill to run, and do NOT proceed.

   **CRITICAL — Perspective conflict check (do this BEFORE evaluating any other gate)**:
   Before checking any gate status, read `.claude/canvas/opportunities.yml` and inspect the Four Risks risk LEVELS for the active solution. Do NOT rely on `theory_gates_status.four_risks` in active.yml — that only records whether risks are documented, not whether they conflict. You must read the actual `value.level`, `usability.level`, `feasibility.level`, `viability.level` values.

   If TWO OR MORE risk dimensions are rated HIGH, or if perspectives directly contradict each other (e.g., value says "build it" but usability/feasibility say "don't"), this is a **perspective conflict** — not a simple gate failure. STOP evaluating other gates and jump to step 2b immediately. This takes priority over all other gate checks.

2b. **Resolve perspective conflict** (if detected in step 2):
   Do NOT continue to steps 3-6. A perspective conflict must be resolved before any other gate evaluation matters. Follow this procedure:

   1. **Name the conflict explicitly** in the decision log: "Perspective conflict: [type]" — use the vocabulary from `${CLAUDE_PLUGIN_ROOT}/engine/perspective-resolution.md` (value-vs-feasibility, usability-vs-feasibility, value-vs-viability, usability-vs-viability, three-way).
   2. **Classify the conflict type** per the resolution framework.
   3. **State each perspective's position**:
      - Product perspective: what does the value evidence say?
      - Design perspective: what does the usability evidence say?
      - Engineering perspective: what does the feasibility evidence say?
   4. **Apply the resolution methods in order of preference**:
      - Constraint-based: Can all three perspectives be satisfied within acceptable thresholds?
      - Phased: Can we deliver in stages? (Phase 1 = MVP addressing highest risk, Phase 2 = polish)
      - Evidence-based: Can we test the disputed dimension? (Run `/mycelium:assumption-test` on the riskiest assumption)
      - Scope reduction: Can we remove features until all perspectives align?
   5. **Log the resolution** in .claude/harness/decision-log.md with: the conflict type, each perspective's position, the resolution method chosen, and why.
   6. **Block progression**: Report "Progression blocked: perspective conflict ([type]). Recommended resolution: [method]."
   7. Do NOT proceed to step 3 or beyond. The conflict must be resolved first.

   The perspective resolution framework (`${CLAUDE_PLUGIN_ROOT}/engine/perspective-resolution.md`) is the authoritative reference. The anti-pattern to avoid is Perspective Suppression — resolving a conflict by ignoring one perspective.

2b-2. **Four Risks: a blind pass runs before the gate is recorded as passed** (2026-11-12; at `commit_to_build` and `release`, L1-L4, wherever this run is about to write `four_risks` as `pass` or `pass-with-risk`):

   Before you write the pass, run `/mycelium:devils-advocate` Technique 7, the blind adversarial pass, on the Four Risks assessment, as that section describes: hand each reader the chosen solution's `four_risks` block from `opportunities.yml` (the four assessments and the evidence each cites) plus one line on how it was assessed, and nothing else; ask for the single most likely way it is wrong; permit "NO OBJECTION". It runs by default. The person can decline it; record the decline as below.

   **It can only raise concerns. It never passes anything.** A "NO OBJECTION" is not evidence for the gate and is never cited as a reason the gate passed: the gate passes on its own pass criteria (`${CLAUDE_PLUGIN_ROOT}/engine/theory-gates.md`, Four Risks gate). Verify each concern against the canvas yourself. A concern that holds is a gate finding like any other: `four_risks` is `fail` or `pending`, and the concern goes in `progression_blockers` with `gate: four_risks`. A concern that does not hold is recorded with the reason it was ruled out.

   **Record the result on the gate.** In the decision entry whose gates include `four_risks` (the `commit_to_build` or `release` entry in `decisions`), add one line to its `note`: `blind pass on four_risks: <n> reader(s); <each concern and what was done with it>`, or `blind pass on four_risks: no objection`, or `blind pass on four_risks: not run: <why>`. The decision-log entry carries the same line. When the ruling is not `progressed` and no decision entry is written, the line goes in the decision-log entry, and a concern that held is already in `progression_blockers`.

   **If no subagent can be spawned** (Technique 7's prerequisite), say so, offer to run it if the person permits one subagent, and record `not run: <why>`. The pass not running does not fail the gate: a step that can only raise concerns cannot block by being absent. In autonomous mode, run it, and never record a decline on the person's behalf.

   Why this is a default step: the Four Risks are otherwise assessed and judged by the agent that wrote them, and a solo builder has no second person to challenge them. A blind reader stands in for that person's judgement, never for their stake (devils-advocate, Technique 7, "What it stands in for").

2c. **Build-to-learn awareness NUDGE** (at `commit_to_build` only):
   When the diamond commits to build, surface this prompt to the human:
   > "Are you building to learn or building to earn right now? Discovery work (prototypes, spikes, experiments) can use lighter gates. Delivery work (shipping to users) must meet full DoD."
   This is awareness only — it does not change gate requirements or routing. The human's answer is informational context, not a gate input.
   *Source: Cagan (SVPG), Patton (build to learn vs build to earn). Added as NUDGE per risk analysis — conceptual awareness, not process gate.*

2c-2. **An L4's `commit_to_build` says where the work may write** (v0.324.0, enforced by
   `hooks/scope-gate.sh`). In the same edit that records `commit_to_build` on a delivery cycle
   (an L4), write `in_scope_paths` on that cycle: the folders, files or globs the work will
   touch, project-relative.

   ```yaml
   in_scope_paths: [app/billing/, tests/billing/**]   # the agent is held to these
   in_scope_paths: []                                  # no hold for this one, said on purpose
   ```

   **Propose the list from the plan; the person decides it.** Say which folders you propose and
   why, in one line, before the edit. The edit is put to the person by the gate (an ask), because
   where the agent may write is theirs to say; where nobody can be asked it is refused, and the
   person makes the change themselves. An empty list is a real answer ("no hold for this one")
   and is asked about the same way. Do not write an empty list to get past the question: propose
   the folders, and let the person say "no hold" if that is what they want.

   **A commitment to build with nothing said is refused.** The gate reads the edit, and an L4
   that would end up committed with no `in_scope_paths` at all does not land.

   **While the cycle is open the agent is held to the list.** A write under `.claude/` is never
   held. A write outside the list is put to the person with the file named; a yes lets that one
   write through. If the work turns out to need another folder, propose adding it to the list
   (that edit is asked about too) instead of asking write by write. The hold ends when the
   cycle's `close` is recorded: nothing has to be taken away.

   **What the hold cannot see:** a command that writes files itself (a scaffolder, a clone). Say
   so if you run one during delivery, and name what it wrote. A shell command that changes
   `in_scope_paths`, or since 0.325.0 anything else in the diamonds file, is undone afterwards
   (the whole file is put back) and the person is told: change it with Edit or Write, never
   from the shell.

   **A cycle that committed before 0.324.0** carries no list and is not held; session start names
   it. Offer the person the two choices above for it once, and do not add either unasked.

   **An old `.claude/state/active-execution.json`** is no longer read. While it exists, product
   writes are refused: tell the person to move its folders to the cycle as above and to delete the
   file themselves (it is one of the files that are theirs to write).

   Why this is a step here and not a file the agent is told to write: until 0.324.0 the folders
   lived in that state file, no skill wrote it, and the hold was never on in a plugin install
   (a blind reader of the installed plugin, dogfood 2026-10-11).

2d. **L3 `start_experiment`: the lightest test is named first** (v0.253.0, enforced by the
   scale-lock gate). Before an L3 builds, run `/mycelium:assumption-test` on the riskiest assumption of the
   solution it builds and record, on that solution in `opportunities.yml`,
   `riskiest_assumption: {statement, cheapest_test}` (or `test_design`), a sentence, not a label.
   Offer the light options first: concierge (a person does by hand what the product would do),
   Wizard of Oz (a real-looking front, a person behind it), a few early adopters. They need no
   production infrastructure and still give test-validated evidence. A real hosted pilot is allowed;
   name it here as the test, so building infrastructure is a choice and not the default. E2E runs
   19 to 23 each built a server, an SMS provider, a domain and a security review inside the L3, and
   each stalled there.
   **A test that needs real use runs after the L3's own `release`** (v0.257.0). Record on the L3 an
   exposure record (`exposures[]`: `audience`, `until`, `channel`): a named, opted-in audience, an
   end date, and the channel that fits the product type (web software: infrastructure as code for an environment that
   can be torn down; courseware: a pilot cohort on an existing platform; service: by hand). Record
   the L3's `release` through Security, Privacy and Service Quality, run the test, and record the
   verdict on the riskiest assumption; that verdict is the medium-confidence evidence the L4 opens
   on. The L4 then builds to earn, for everyone. Production for everyone is never an L3's.
   **The L3 builds only what its test needs to run** (v0.273.0). Not a finished product: the
   smallest thing that lets the named, opted-in audience take part and the test read out. A question
   the build raises that the test does not need (a refund edge case, a full export pipeline, terms
   for a stranger) is recorded, not answered now: as a next assumption on the solution
   (`assumptions:` in opportunities.yml), to be tested in turn, or as L4 work. The test lands, and
   its verdict may call for a new test; that is the opportunity solution tree working, not a gap in
   this one. E2E service world run 3 grew 8,500 words of client documents for a two-month, hand-run
   pilot with three existing clients, and the pilot never started.
   **The exposure record is the learning delivery** (v0.294.0, v0.296.0; since v0.307.0 the only
   record of it). An entry in the diamond's `exposures`: `recorded_at`, `audience`, `channel` (a
   moderated session, a link, a device), `data_class` (`none`, `synthetic`, `personal`,
   `sensitive`), `until`, `consent` (how consent was given) and the `gates` passed for this
   exposure; `started`, `changes` and `ended: {how, on, l4, note}` go on it too. Recording it is
   not the start; `started` is. Draft it; if the data is personal or sensitive the write asks the
   person, who confirms it (founder ruling g). An exposure already live before this was recorded
   gets `reconstructed: true` (ruling h). `scale_locks.py --exposures` reports what is missing, and
   the release gate refuses a release no current exposure record covers.
   **A team-only exposure is its own trial** (founder ruling 2026-11-12). An L3's Evidence gate at
   `release` asks that what reaches people has had one trial outside the team first
   (`engine/theory-gates.md`, gate 1). When the exposure's only audience is the builder or the
   team, write its `audience` starting with the token `team-only` (`team-only: the builder, in
   their own sessions`): the release is then the trial, and record the Evidence gate at `release`
   as `n/a` with the reason "team-only exposure: the release is the trial". Do not use the token
   for anyone outside the team, however close (a friend, a pilot client, one tester). Before the
   work reaches anyone outside the team, the outside trial is still required: the release gate
   reads the audience from each exposure record, and an L3's Evidence `n/a` does not count while
   any of them names an audience outside the team. Widening a team-only exposure to outsiders is
   a `widened` change, and it needs the Evidence gate passed by a trial outside the team.
   **A service check scoped to one exposure lands on the exposure** (founder ruling 2026-11-12).
   When `/mycelium:service-check` is run for one exposure, its 15 principles go in that
   exposure's `gates_basis.service_quality` with a decision-log line, and `services.yml` stays the
   product-wide record. The release gate reads the exposure's own record first.
   **Something already live with no record** (v0.322.0). When the repository shows the project
   deploys and no diamond carries an exposure record, the next item `already-live` asks the
   person whether something from it is already in front of real people, and names this skill
   for a yes. That run records no decision and needs no gate passed: write the exposure record
   on the diamond that carries the live work, with `reconstructed: true`, `data_class` and
   `consent` only as the person states them, and no gate marked passed. Then run Security and
   Privacy for it; until they pass, `--exposures` lists it, which is the point of recording
   it. If no open diamond carries that work, say so and do not put the record on a diamond it
   does not belong to: it waits on one being opened, `/mycelium:security-review` and
   `/mycelium:privacy-check` can look at what is live now, and their yes is kept meanwhile with
   `advisory_ledger.py rule --id already-live --ruling snooze --until asked --note "yes: <who it
   reaches>; record it when its diamond opens"`. A no is the person's answer, recorded with
   `--ruling drop`. The question never blocks.
   **The harms check is a step here, and it never blocks** (v0.321.0). When you draft or change
   an exposure record, ask the two things no record carries: does this work have sign-up,
   retention, cancellation, consent or pricing flows, and does it reach people who are vulnerable
   (children, patients, people at financial or other risk)? If either is yes, run
   /mycelium:harms-check before the release is recorded, while the design can still change, and
   write its result on the exposure: `harms_check: {on, verdict, note}`, with `verdict` one of
   `net-positive`, `happier-negative`, `not-applicable`. If both are no, write `not-applicable`
   and the reason in `note`; do not write it without asking the two questions. It is not one of
   the exposure's `gates`. A `happier-negative` verdict does not stop the release: tell the person
   what was found and let them decide whether the work goes out as it is. Until a verdict is on
   the record, `scale_locks.py --exposure-state`, `--exposures` and the release gate each say so
   in one advisory line. Why this is a step and not a suggestion in a list: in 175 end-to-end runs
   the harms check was mentioned in 1, against 33 for the privacy check, whose record the release
   gate requires. A diamond that still
   carries the old `learning_delivery` field is not read by any rule since v0.307.0: the next item
   offers `scripts/migrate_phase.py`, which moves it into an exposure record. Do not write it.
   **The test starts, on the record** (v0.274.0). Record `exposures[].started` with the day
   the first person in the audience took part. An L3 that has released with no start date is offered the
   start at every session; once that is overdue, stop extending the build, name only what blocks
   the start, and send the rest to the tree or to L4. E2E service world run 4 grew its client pack
   from 4,100 to 7,100 words in Deliver while nobody was served.
   **Once the L3 has released, its audience changes on the record, and the delivery ends when the
   L3 closes** (v0.267.0, v0.268.0). The audience is identifiable and opted in: a named list, a
   cohort, a pre-release channel. Record each change in `exposures[].changes` as `{on,
   audience_was, kind, why}`: `narrowed` or `reworded` (a learner left, a typo, a translation);
   `widened`, a bigger test audience that is still identifiable and opted in (a second beta wave, a
   larger cohort), with `reassessed: [security, privacy, service_quality]` re-run for it; or
   `everyone`, a release to all, which is the L4's: open the L4 on this L3 first and deliver
   through it. When the L3 records `close`, record `exposures[].ended: {how, on, l4, note}`: `how`
   is `withdrawn` (taken down, devices collected back, the cohort or engagement over) or
   `handed_to_l4` with the L4's id in `l4`; `note` is free text in any language. E2E rung L4-open
   made a web page public under its L3 on reviews scoped to five testers; the same rules hold a
   course pilot, a concierge service, a hardware loan or a staged app beta.

3. **Judge confidence, then compare it to the effective threshold**:
   - **Confidence is a judgement, and you are the one making it.** The `scoring` block in
     `${CLAUDE_PLUGIN_ROOT}/engine/confidence-thresholds.yml` (evidence 0.4, theory gates 0.3,
     validation 0.2, peer review 0.1, and the six `evidence_values`) is guidance for that
     judgement: evidence counts most, then the gates, then validation, then a second reader. No
     code computes confidence from those weights and nothing checks a number against them, so do
     not present the result as calculated. Two runs on the same record have scored the same
     diamond 0.60 and 0.35 (dogfood, 2026-09-22). Write the number with the reasons that set it:
     which evidence, which gates, and what would move it, so the next reader can disagree with
     the judgement instead of re-deriving it. Founder ruling 2026-11-12.
   - Look up `project_type` and `dogfood` from `.claude/diamonds/active.yml`.
   - **If `project_type` is empty or absent, ask before ruling (v0.328.0):**
     "Before I rule: is this a solo hobby, a solo product, or a team product?"
     Map and write the answer as the interview's scope step does (`solo_hobby`, `solo_product`,
     `team_startup`, `team_enterprise`), then compute. Never apply the base threshold silently because
     nobody asked. If the person declines, rule at the base and say in the ruling that the bar is unadapted because the scope is unknown. Until 0.328.0 an
     L0 gate on a hobby project noted "project_type unset, so no adaptation" and held it to 0.9 instead
     of 0.63, nine days after a brief that never asked.
   - Apply `project_type_adaptations` from ${CLAUDE_PLUGIN_ROOT}/engine/confidence-thresholds.yml:
     - `effective_threshold = base_threshold * threshold_multiplier`
     - If `dogfood: true`: `effective_threshold *= dogfood_modifier.additional_threshold_multiplier`
     - `effective_min_sources = ceil(base_min_sources * min_sources_multiplier)`
   - Compare confidence to the **effective** threshold (not the base), **at the decisions where it
     applies**: if the scale lists `threshold_applies_at` (decision names since v0.308.1), only at
     those. At the others, report the confidence, check the evidence each decision the move records
     names in `evidence_by_decision` (keyed by `product_type` where the evidence differs, `software`
     the fallback: v0.269.0), and do not
     hold the move on the number (v0.259.0). The L3's threshold is its exit bar: an L3 sets its
     target on a real problem, commits to build once its lightest test is named, and releases once
     the prototype has met users. E2E runs 42-43 held an L3 in discover for three in-world months, 0.6 against 0.64,
     asking for the evidence its own build and learning delivery exist to produce.
   - Report both: "Confidence: 0.55. Effective threshold: 0.57 (base 0.85, adapted for solo_product). Needs: one more evidence source to cross."

4. **Check human approval requirement**:
   - Per ${CLAUDE_PLUGIN_ROOT}/engine/confidence-thresholds.yml, is human approval required/recommended/optional?
   - `human_approval` is keyed by decision (since v0.308.1): a move needs the approval its strictest decision asks. **Apply `human_approval_override` from the project_type — EXCEPT at L5 `release` and `close`, which are NO_REDUCTION and stay `required` whatever the override says** (added 0.237.0). These are the two decisions that reach people outside the team, and an override cannot make a launch self-approvable. A solo hobbyist launching to the public still reaches the public. If an override would have lowered one of these, say so out loud rather than silently applying the floor: *"project_type <x> would set this to optional; L5 `release` and `close` are NO_REDUCTION, so approval is still required."*
   - If required: present assessment and wait for approval.
   - **When asking for approval, include the interaction convention explicitly in the prompt** — do not leave it implicit. Use this template (or paraphrase faithfully):
     > "Reply **yes** to advance, **no** to stay. Re-invoking `/mycelium:diamond-progress` is also treated as approval (shortcut). Type **evaluate again** to re-run gates from scratch."
   - This makes the implicit-shortcut convention visible. If the user re-invokes `/mycelium:diamond-progress` while a previous invocation is awaiting approval, that re-invocation IS treated as approval — but only because the convention has been surfaced in the prompt above. Without the prompt-line, the behavior is a footgun (corrections.md 2026-05-06 — `/mycelium:diamond-progress` re-invocation interpreted as approval).
   - **Autonomous mode** (per `${CLAUDE_PLUGIN_ROOT}/engine/autonomous-mode.md`): where `human_approval` is **required**, this is a HARD GATE — rung (c): do not advance, ledger the block, surface it for the next human session. Where it is **recommended/optional**, autonomous advance is permitted ONLY if every gate passes on evidence that does not depend on `internal_simulated` entries; ledger + decision-log entry mandatory. The re-invocation-as-approval shortcut does NOT apply in autonomous runs — an agent re-invoking the skill must never count as its own approval.

5. **Run bias check**: Execute bias-check for the current stage.

6. **Run corrections check**: Review corrections.md for relevant entries.

6b. **Check trio perspective coverage** (Torres Product Trio):
   - For each gate evaluated in step 2, verify all three perspectives (product/design/engineering) are documented.
   - Each perspective must have evidence or an explicit "N/A: [reason]" justification.
   - Missing perspectives without justification = **GATE FAILED** (Perspective Skip anti-pattern).
   - See `${CLAUDE_PLUGIN_ROOT}/engine/theory-gates.md` §Trio Perspective Requirement for per-scale guidance.
   - Note: Perspective CONFLICTS (2+ HIGH risk dimensions) are caught in step 2b, not here. This step checks for missing perspectives, not conflicting ones.

7. **If the decision is `close`: RUN EXECUTABLE DoD CHECKLIST** (see below)

8. **Decision**:
   - All gates pass + confidence met + approval (if needed) + DoD pass (if delivery) = **PROGRESS**
   - Any REVIEW item fails = **blocked** (list specific blockers with suggested skills)
   - Confidence below threshold = **NEEDS EVIDENCE** (list what would help)

   **Write the ruling to the diamond — MANDATORY, on ALL THREE outcomes, added v0.92.0.**
   Immediately after deciding, set these fields on the assessed diamond in
   `.claude/diamonds/active.yml`:

   ```yaml
   progression_ruling: progressed | blocked | needs-evidence   # one of exactly these
   progression_ruled_at: <YYYY-MM-DD>
   last_progressed: <YYYY-MM-DD>       # ONLY when ruling is `progressed` — see below
   progression_blockers:                # REQUIRED when ruling is blocked or needs-evidence;
     - gate: <which gate or threshold>  # omit entirely when progressed
       reason: <why it did not clear, in your own words>
       unblocked_by: <the skill or evidence that would clear it>
   decisions:                           # APPEND the decisions, when progressed (v0.305.0)
     - decision: start_experiment       # one entry per decision recorded (see below)
       'on': <YYYY-MM-DD>               # quoted: a bare `on` is a YAML 1.1 boolean
       gates: {evidence: pass, cynefin: pass, ...}   # this decision's gates (scale_locks.DECISIONS)
       ruling: progressed
       note: <for a repeated start_experiment: the test and the result it expects (DL-1373)>
   ```

   **Name the decisions (v0.298.0).** Each level runs a learning loop: set the target
   (`set_target`); start an experiment and commit to build (`start_experiment` and
   `commit_to_build`, recorded together); release (`release`); close (`close`). Each gate belongs to
   the decision it guards, and a move needs the gates of every decision it records.

   **The decisions are the record, and where a diamond is, is read from them (v0.305.0, v0.306.0;
   DL-1368).** Append one `decisions` entry for each decision, with its gates and the date.
   `scale_locks.position` reads them: "committed to build" needs both `start_experiment` and
   `commit_to_build`. `phase` is not read, and may stay as a label for people reading the file.
   **An L0 does not move** (DL-1368 S2): when its purpose has been revisited (a re-derived
   `purpose_properties`, a changed `why`, the bar's own review date), record `review` with the L0
   gates, and the ruling. A project whose diamonds still carry only a phase is offered
   `scripts/migrate_phase.py` by the next item.

   **A choice is written when it is made; its decision when its gates pass (v0.313.0).** Two
   fields hold a choice that a decision later records, and the choice is written when the person
   makes it, whatever this run rules: an L2's `target` (`{opportunity, chosen_on, compared, why}`),
   whose decision is `set_target`, and an L3's `front_runner`, whose decision is `commit_to_build`.
   On `needs-evidence` or `blocked`, write the choice and record no decision entry. The entry locks
   read the choice and its evidence, never the parent's decisions (ENTRY and SPEED are separate
   questions; `engine/diamond-rules.md`, Entry locks), so a withheld choice closes the door below
   it and makes the next item ask for a choice already made. Found on the dogfood L2 2026-10-04:
   the founder chose a target, `set_target` was ruled needs-evidence, `target` was withheld as if
   it were the decision, and the next item asked for the comparison every session. Every scale's
   `object_ref`, the outcome an L1 sets (`desired_outcomes[].set_by`) and an L0's purpose fields
   are choices of the same kind, written when made; none of them waits on a decision.

   **A loop iterates by appending, never by editing (DL-1373).** When a test reads inconclusive or
   the front runner fails, append the decision the iteration makes: a new experiment is another
   `start_experiment`, its `note` naming the test and the result it expects (and the test recorded
   on the solution, as in step 2d); a re-chosen front runner is another `commit_to_build`, with
   `front_runner` set to it. The
   position stays where it is, and the earlier experiment and its verdict stay on the record. Never
   remove or rewrite a recorded decision to move a diamond back: since v0.309.1 the scale-lock gate
   refuses a write that removes a recorded decision or changes its name or date (DL-1374; a note,
   the gates and the ruling stay editable). A repeated decision is not judged, so nothing checks
   that the new experiment names its test: this step is that check.

   **Record the decisions and their gates IN THE SAME WRITE (v0.248.0).** The scale-lock gate
   refuses a write that records a decision unless its gates are passed in `theory_gates_status`
   (Security and Privacy backed by a threat model and a privacy assessment on the canvas). E2E runs
   12, 14 and 16 moved diamonds forward leaving no record of how; run 14 moved one to develop with
   its evidence gate still pending. `progression_history` is not required since v0.307.8: the
   decisions are the record of the move, and entries already there stay as history. Parking,
   killing and archiving are not judged.

   **`last_progressed` HAS NO OTHER WRITER, AND A THEORY GATE READS IT (added 2026-09-20).** Set it
   whenever the ruling is `progressed`. Until now nothing in the plugin wrote this field — it
   appeared only in the schema (not required), in `diamond-render`, and in `engine/theory-gates.md`,
   where the **competitive gate compares it against the landscape's newest entry.** Measured in the
   dogfood repo 2026-09-20: stale on four of five diamonds, by up to 3.5 months, while every one of
   those diamonds was being actively edited.

   **Work the direction through, because it is the dangerous part.** That gate FAILS when the
   landscape entry predates `last_progressed` by more than the staleness window. As the field decays
   backwards relative to real work, the threshold moves further into the past, the failure condition
   gets harder to satisfy, and **the gate gets EASIER to pass the longer nobody maintains the
   field** — a staleness check whose own staleness silently loosens it.

   **This is the third instance of one defect class in this file's own history**: `progression_ruling`
   was read by a consumer and written by no skill (fixed 2026-08-05), `completed_diamonds` is read by
   `check_scale_occupancy.py` and written by nothing, and this. **A gate may not read a field that
   nothing writes.**

   **Why this is mandatory rather than nice-to-have.** The verdict was previously
   narrated to the user and written as prose to the decision log, and nowhere else.
   Nothing downstream could tell a refusal from a narration ABOUT refusal — the only
   available check was grepping the log for words like "block", "gate" and
   "insufficient", which any paragraph explaining the framework's philosophy satisfies
   without a single gate having fired. Discovered 2026-08-05: `progression_ruling` was
   read by a consumer and written by no skill, so the rigorous path was dead code and
   every check silently fell through to the prose grep.

   Write it on a PASS too. A field that only appears on failure cannot distinguish
   "this diamond was assessed and cleared" from "this diamond was never assessed" —
   which is the same absent-vs-negative confusion that made `confidence` required on
   the diamond schema in this release. The ruling records that a judgement happened;
   its value records which way it went.

9. **If progressing**:
   - **At `commit_to_build` with a product-leaf solution chosen**: open a cycle record in `.claude/canvas/cycle-history.yml` with `cycle_class: product-leaf` and **copy the solution's `ice_score` from `opportunities.yml` into `predicted.ice_score`** (the three factors and their product, as written; a total of 0 with its factors recorded is a score, since 0.319.0). If the solution has no ICE score, STOP — return "Cannot open product-leaf cycle without ICE. Run `/mycelium:ice-score` on the chosen solution first." This is the gate that prevents permanent dark cells in calibration. See `${CLAUDE_PLUGIN_ROOT}/engine/cycle-learning.md#cycle-class`.
   - **Framework-self-development or observation decisions** (no OST solution leaf chosen — e.g., L2 strategy adjustment, cohort-log capture, validator-check ship): open the cycle record with `cycle_class: meta-dogfood` or `cycle_class: observation` as appropriate. `ice_score` may be zero with a `notes:` line stating why. These cycles are excluded from ICE-calibration aggregates by design.
   - Update diamond state in `.claude/diamonds/active.yml`.
   - **At `close`: stamp `completed_at`** on the diamond (ISO-8601 — the true ship timestamp; no other diamond field records completion). This times the outcome→discovery loop: `/metrics-pull` Step 8b (DoD outcome-check) and the `session-start` overdue nudge both read `completed_at` to know when a shipped diamond's outcome is due for verification. Without it, the back half of the loop can't fire.
   - **At `close`: MOVE the diamond into `completed_diamonds` and write its `dod_verdict`** (v0.230.0). Not `archived_diamonds` — see 9b.

9b. **Completing a diamond — the state that had a reader and no writer.**

   Move the diamond out of `active_diamonds` into **`completed_diamonds`** in
   `.claude/diamonds/active.yml`, carrying its fields and adding:

   ```yaml
   completed_at: <YYYY-MM-DD>
   dod_verdict:
     signal_observed: <what you actually SAW, in your own words>
     verified_by: <metric snapshot | named person | test | link | self-assessed>
     threshold_met: <the DoD threshold's real value, where it declared one>   # optional
     shortfall: <where the outcome fell short but you completed anyway>        # optional
   ```

   **`signal_observed` may not restate the DoD's `signal`.** If the only sentence you can write
   is the target back again, you did not observe it — that is the DoD un-met, and this is a
   `blocked` ruling, not a completion. The schema requires `signal_observed` and `verified_by`,
   so an unevidenced completion is rejected by `validate_canvas.py` rather than accepted quietly.

   **`shortfall` exists so the bar does not have to be rounded up.** Completing with a stated
   shortfall is honest and permitted; completing by quietly reinterpreting the DoD is the failure
   this field removes the incentive for.

   **WHY THIS IS A SEPARATE STATE FROM `archived`.** `engine/diamond-rules.md` defined archived as
   *"Completed or deliberately paused"* — one bucket for two opposite outcomes. With those merged,
   no reader can distinguish work that MET its bar from work that merely STOPPED, so **compliance
   with completion was unverifiable by construction**: the count of finished cycles and the count
   of abandoned ones were the same number. Archived now means stopped-without-meeting-the-bar;
   completed means the bar was met and here is the evidence. Killed is unchanged.

   **FOURTH INSTANCE OF THE READER-WITH-NO-WRITER CLASS, and the one that sat longest.**
   `check_scale_occupancy.py` has read `completed_diamonds` since it shipped — it is in that
   script's key list, counting toward "ever opened" at each scale. **No schema defined the key and
   no skill wrote it**, so every occupancy report counted zero completed cycles at every scale
   regardless of how much work had finished, and its "intake and no outlet" finding could never be
   retired by finishing anything. See `progression_ruling` (fixed 2026-08-05), `last_progressed`
   (fixed 2026-09-20, above) and the competitive gate in `docs/errata.md`.
   **A gate may not read a field that nothing writes — and a state nothing can enter is not a state.**
   - **Render the updated journey map**: Follow `${CLAUDE_PLUGIN_ROOT}/engine/wayfinding.md` to show the user where the diamond now is. This makes the decision visible — the user sees the position change on the map.
   - Log the decision in `.claude/harness/decision-log.md`. If threshold was adapted, include: "Threshold adapted from [base] to [effective] because project_type=[type]. Would increase with [action]."
   - Update `.claude/memory/product-journal.md`.
   - **Offer the child cycle this decision makes possible** (v0.243.0; replaces "identify if child diamonds should be spawned", which fired in no run). When an **L0 records `state_purpose`**, strategic questions follow: ask whether to open an L1 Strategy diamond on the first strategic decision, or record "no strategic decision open". When an **L3 records `commit_to_build`** (Four Risks cleared), direct to `/mycelium:preflight`, which offers the L4 on the increment. When an **L4 records `release`** (it has shipped), direct to `/mycelium:launch-tier`: record its launch data and categorise the release; a first release to the market opens an L5 (v0.254.0). Every scale must be enterable, and each opens only on what its parent has established (`engine/diamond-rules.md`, Entry locks, v0.245.0): run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --can-open <scale>` before the offer, and if the lock does not hold, offer the step that produces what is missing instead. Where the parent is, is not the lock; its artefact is. **For each child diamond spawned, run `/mycelium:define-done` before it goes live** — pin its outcome `definition_of_done` and set `rolls_up_to` naming which parent outcome it serves (contribution-not-summation). A child born without a done-bar inherits the implicit-harshest-bar problem.
   - **Capture learnings** (see Learning Capture section below)

10. **If blocked or needs evidence**:
    - Report in plain language: "Can't mark this done yet because [reason]."
    - List each failed item with its suggested skill
    - Record no decision; the diamond stays where it is.
    - At **L0 / L1 / L2 / L5** diamonds, if the Evidence gate is "Insufficient Evidence" and `.claude/jit-tooling/active-metrics.yml` is configured, suggest `/mycelium:metrics-pull` as one route to strengthen external signal. If `.claude/jit-tooling/active-metrics.yml` is missing, suggest `/mycelium:metrics-detect` first. (v0.14: `external_data` from snapshots satisfies the Evidence gate's behavioral-data criterion but does NOT replace `external_human` requirements at an L2's `release`.)

    **Technical-discovery shape detection (sol-007a, v0.39.6)**: when Evidence/Bias/Feasibility gates are blocking AND the agent observes any of the following technical-shape signals in canvas state, **name the dimension explicitly as "technical discovery" in the verdict and recommend `/mycelium:assumption-test` with read-docs / pull-real-payload framing — NOT `/mycelium:user-interview`** (interviewing a domain user does not validate an unread API contract):
    - Any `constraints.*` entry with `validated: false` that names an external API, contract, schema, data model, or third-party integration
    - Develop_intent or develop_summary referencing a specific external API/service version without an evidence source
    - Recent code change touching an external client/SDK while the contract is unread (look for client/SDK imports in src/ adjacent to the active diamond's scope)

    Verdict-line template when triggered: *"Blocked — **technical discovery** incomplete. The [API contract / data model / architecture decision] for [name] is unverified. **Feasibility** evidence missing: [the specific assumption flagged]. Recommended next: `/mycelium:assumption-test` against the unread contract — read the current docs, pull a real payload, validate the assumption against observed data before building the dependent component."*

    Why this routing-branch (rationale captured 2026-06-03 — roadmap brownfield-iteration eval, sw-tech-discovery dogfood pass 6/7 with `decision_log_contains` failing): the framework's existing gates correctly BLOCK the bad-progression behavior (5+ of 7 measurable dimensions pass on the failing-first dogfood) — the structural gating is healthy. The gap was purely vocabulary + routing: the verdict didn't NAME the dimension as technical-discovery and recommended `/user-interview` where `read-docs / pull-payload` was the correct surface. Sol-007a closes both gaps without adding a new gate, scale, or skill. See opp-007 in mycelium-roadmap canvas.

11. **Always communicate in plain language**:
    - Use ${CLAUDE_PLUGIN_ROOT}/engine/status-translations.md for all state descriptions
    - Include contextual confidence explanation
    - Suggest specific skills for any gaps

---

## Executable Definition of Done (at `close` ONLY)

When recording `close`, run this checklist. Items marked `REVIEW` block progression. Items marked `PROMPTED` are asked but don't block.

**Two rules before any item (v0.210.0, dogfood `l2-framework-reliability` 2026-09-02, where both fired on one transition).**
- **WAIVED is a verdict.** A required field that is legitimately empty carries a sibling `<field>_absent_reason` or `<field>_applicability` with a substantive reason (the contract `check_instrument_contract.py` already reads). An item whose field is waived reports **WAIVED — not a pass and not a defect**, printed in the checklist output so the exemption is seen, and does not fail the gate. The dogfood canvas carried `accuracy_score_applicability: n/a-until-n10` beside a null score for nine days while this checklist read GATE FAILED against it; the checklist and a recorded founder decision disagreed, and the skill had no third verdict.
- **The build-shaped items apply to builds.** Tests, type-check, lint and eval scores are keyed to `product_type`, never to what the diamond's own `definition_of_done` asks for. When the diamond's `definition_of_done.outcome` names no build (a recorded verdict, a ruling, an archived leaf) or its cycle class is `meta-dogfood` or `observation`, skip those items and say so in one line; a gate a correct diamond cannot satisfy enforces nothing and teaches its reader to route around it. Observed on one transition; a second verdict-shaped done-bar would confirm the shape.

### Auto-Checked (Machine Verifiable)

Check `product_type` from `.claude/diamonds/active.yml` to determine which auto-checks apply.

**For software and ai_tool (code components):**

**Testing (G-V7 REVIEW)**:
- Check: Do test files exist? (glob for *.test.*, *.spec.*, Tests/*, __tests__/*)
- If no tests AND project has source files: **GATE FAILED**
- Message: "No tests found. Tests must exist before marking delivery complete. Run /mycelium:reflexion to add tests."
- If tests exist: run them and verify they pass

**Type Safety (REVIEW for typed languages)**:
- Check: If tsconfig.json, *.swift, *.cs, go.mod, Cargo.toml detected: run type checker
- If type errors: **GATE FAILED**

**Linting (REVIEW if linter detected)**:
- Check: If linter config exists (.eslintrc, biome.json, .swiftlint.yml, ruff.toml): run it
- If lint errors: **GATE FAILED**

**For content products (content_course, content_publication, content_media):**

**Content Quality (REVIEW)**:
- Check: Are `content-metrics.yml#quality_review` flags all true? (sme_reviewed, accessibility_checked, fact_checked, style_consistent, learning_objectives_met)
- If any flag is false: **GATE FAILED** -- "Content quality review incomplete. Set the relevant flags in content-metrics.yml after completing review."
- Fallback: If content-metrics.yml doesn't exist yet, ask: "Has content been reviewed? Create content-metrics.yml and mark quality_review flags."

**For ai_tool:**

**Eval & Safety (REVIEW)**:
- Check: Are `ai-tool-metrics.yml#prompt_quality` fields populated (not null)? Specifically: accuracy_score, consistency_score, safety_score.
- If any are null: **GATE FAILED** -- "Prompt/model must be evaluated. Populate accuracy_score, consistency_score, and safety_score in ai-tool-metrics.yml."
- Check: Is `ai-tool-metrics.yml#prompt_quality.last_evaluated` set?
- If null: **GATE FAILED** -- "No evaluation timestamp. Run eval and record the date."

**For all product types:**

**Secrets (G-S1 BLOCK)**:
- Check: no secret in what git tracks. Where gitleaks is installed, run `gitleaks git --redact --no-banner` over the repository; otherwise run Mycelium's own short list over tracked files (`git grep -nE` with each pattern in `scripts/_secret_patterns.sh`). An ignored env file is not a finding (since 0.323.0 the hooks stop a secret at the commit and the push, not at the write)
- If secrets found: **GATE FAILED**

### Delivery-Type Dependent (from ${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml)

**For user_facing work (G-V2, G-V8, G-V9 REVIEW)**:
- Check: Has services.yml been assessed? (count of "not-assessed" < 15)
- If all 15 are "not-assessed": **GATE FAILED** -- "Run /mycelium:service-check before completing."
- Check: Has accessibility been considered? (any evidence of a11y work)
- If no evidence: **GATE FAILED** -- "Run /mycelium:a11y-check for user-facing work."
- Check: Has usability been evaluated? (Nielsen's 10 heuristics via /mycelium:usability-check)
- If no evidence: **GATE FAILED** -- "Run /mycelium:usability-check for user-facing interfaces." (G-V10)

**For api_service or permission_requiring work (G-S2 REVIEW)**:
- Check: Does threat-model.yml have components listed?
- If empty: **GATE FAILED** -- "Run /mycelium:threat-model for work that handles data or requires permissions."

**For data-handling work (G-S3 REVIEW)**:
- Check: Does privacy-assessment.yml have principles assessed?
- If all "not-assessed" and product handles user data: **GATE FAILED** -- "Run /mycelium:privacy-check."

### Always Required (REVIEW)

**Outcome Definition of Done met (REVIEW)**:
- Read `.claude/diamonds/active.yml` for this diamond's `definition_of_done` (the outcome bar, distinct from the quality checklist below — set at birth via `/mycelium:define-done`).
- If the field is **absent**: **GATE FAILED** — "This diamond has no outcome Definition of Done. Run `/mycelium:define-done` to pin what behaviour-change marks it done before completing." (Do not silent-fill — the question is what produces a real bar.)
- If present: the gate passes only when **either** the `signal` is met with evidence (cite the canvas/decision-log source), **OR** the `kill_criterion` (state+date) has fired with evidence — done-by-invalidation, which must route through `/mycelium:diamond-progress kill` + `dogfood-mode`, not be declared here. If neither holds: **GATE FAILED** — report which (signal unmet / kill-date not reached) and record no `close`: the diamond stays released.
- **Child diamonds**: also verify the outcome `rolls_up_to` the parent — the parent outcome moved or the parent assumption validated. A child that shipped but did not move the parent is not done (contribution-not-summation).
- **Recording the result of this gate (v0.225.0):** whatever you learn here about the bar (the signal was checked and not met, the kill criterion was scored, the founder ruled) is appended to `definition_of_done.log[]` as `{date, text}`. Do not add a dated key to the Definition of Done and do not lengthen `kill_criterion.state` with the history of its own scoring: the bar has to stay statable from memory, and `check_dod_shape.py` reports when it has not.
- This is the diamond-level outcome gate; the items below are per-feature quality. Both must pass.

**Success criteria declared (G-V11 REVIEW)**:
- Check: Does .claude/harness/decision-log.md have success criteria recorded for this delivery (from `/mycelium:preflight`)?
- If no success criteria found: **GATE FAILED** -- "No success criteria declared. Run `/mycelium:preflight` and declare what will be true after delivery and how to verify it."
- If criteria exist: verify each criterion is satisfied. Report pass/fail per criterion.
- This catches the denominator problem: without declared criteria, "done" = "whatever we built."

**Decision log (G-P4)**:
- Check: Does .claude/harness/decision-log.md have an entry for this delivery?
- If no entry since diamond was created: **GATE FAILED** -- "Log the delivery decision."

**BVSSH Quick-Check (Smart -- Fix 6)**:
- Prompt the user/agent with product-type-appropriate questions:

  Happier covers four stakeholders (Smart): **customers, colleagues, citizens, and climate**.

  **Software:**
  - "Better: Did code quality improve or degrade?"
  - "Value: Did we deliver measurable user value?"
  - "Sooner: Was deployment flow efficient? Any unnecessary delays?"
  - "Safer: Did we maintain security, reliability, and trust?"
  - "Happier: How is developer/team satisfaction? User advocacy? Was compute usage proportionate to value delivered?"

  **Content (course, publication, media):**
  - "Better: Did content quality and learning outcomes improve?"
  - "Value: Will this content help the audience accomplish their goal?"
  - "Sooner: Was production cadence maintained? Any bottlenecks?"
  - "Safer: Is the content accurate, accessible, and free from harm?"
  - "Happier: How is creator satisfaction? Audience sentiment? Positive societal contribution?"

  **AI tool:**
  - "Better: Did eval scores improve? Is output quality higher?"
  - "Value: Does the tool reliably help users accomplish their task?"
  - "Sooner: Was the prompt/model iteration cycle efficient?"
  - "Safer: Are safety scores acceptable? Bias assessed? Regulatory status current?"
  - "Happier: How is the builder's satisfaction? User feedback positive? Token/compute usage proportionate (not brute-force waste)?"

  **Service offering:**
  - "Better: Did delivery quality improve? Client satisfaction up?"
  - "Value: Did the client get measurable value from the engagement?"
  - "Sooner: Was delivery lead time acceptable? Any waiting waste?"
  - "Safer: Were commitments met? Trust maintained? No scope creep harm?"
  - "Happier: How is your satisfaction as a service provider? Client sentiment? Sustainable resource usage?"
- Record in bvssh-health.yml assessment_history
- **REVIEW**: Must answer all 5 (even briefly) before completing

### Prompted (Not Blocking)

**Delivery journal (PROMPTED)**:
- "What was built? What technical decisions were made? What surprised you?"
- Auto-draft entry from canvas diff if possible
- Present to user for confirmation

**Patterns (PROMPTED)**:
- "Did you discover any reusable patterns? I'll draft for patterns.md."
- Check corrections.md for entries logged during this diamond -- suggest generalizing any

**Retrospective (PROMPTED)**:
- "What went well? What didn't? What to change next time?"
- Suggest /mycelium:retrospective for deeper review

---

## Non-Progression Paths: Pivot, Park, Kill

Not every diamond makes forward progress. Sometimes the right move is to reframe, pause, or abandon. `/mycelium:diamond-progress` handles these paths too, via subcommands:

- `/mycelium:diamond-progress pivot` — reframe the diamond's scope, audience, or JTBD with new evidence
- `/mycelium:diamond-progress park` — mark the diamond as inactive-pending-conditions
- `/mycelium:diamond-progress kill` — abandon with a documented reason

All three are **sanctioned exits** from a stuck diamond. They are not failure modes — they are the system working correctly when evidence tells you the current direction is wrong.

Addresses dogfood report finding T5: "Stop-the-diamond pattern has no escape valve."

### Pivot (reframe with new evidence)

Use when evidence invalidates the current framing but the underlying need is still valid. Example: macos-fileviewer pivoted from "replace QuickLook for all devs" to "serve terminal-resistant devs specifically" after mocked-persona findings.

**Workflow**:
1. State the invalidating evidence (what did we learn that broke the old framing?)
2. Propose the new framing (scope change, audience change, JTBD refinement)
3. Log decision in .claude/harness/decision-log.md with:
   - Original framing
   - Invalidating evidence
   - New framing
   - Theory: which framework informed the pivot (Torres "evidence-guided", Cagan "value risk", etc.)
   - Confidence delta (the pivot should REDUCE confidence initially — you have less evidence for the new framing)
4. Update `.claude/diamonds/active.yml`:
   - No decision is removed to move the diamond back (DL-1373): the new framing is recorded by appending. An L2's re-chosen target appends to `targets` (DL-1367); a new experiment toward it is another `start_experiment`
   - Confidence resets to match the new framing's evidence level
   - Add `pivot_history` entry listing old and new framings
5. Update relevant canvas files (purpose.yml, jobs-to-be-done.yml, opportunities.yml)
6. Do NOT archive the old framing — keep it as a pivot_history entry so future agents can see the learning

### Park (inactive-pending-conditions)

Use when the diamond cannot progress right now but may be revisitable later. Example: "park until I have time to do real user interviews" or "park until upstream dependency X ships."

**Workflow**:
1. State the blocking condition(s) — what would un-park this?
2. Log decision in .claude/harness/decision-log.md with:
   - Reason for parking
   - Conditions for resuming
   - Expected timeline (best guess)
   - Theory: Goldratt ToC (constraint waiting on resolution) or Torres (evidence insufficient, acceptable to pause)
3. Update `.claude/diamonds/active.yml`:
   - State → `parked`
   - Add `parked_reason`, `parked_at`, `resume_conditions` fields
4. Parked diamonds remain in `.claude/diamonds/active.yml` but do not count against WIP limits
5. `/mycelium:feedback-review` and `/mycelium:diamond-assess` surface parked diamonds with their resume conditions at session start

### Kill (abandon with documented reason)

Use when the diamond cannot be rescued via pivot or park. Example: the opportunity turned out to be imaginary (no real users, no demand), or the solution space has been exhausted, or the project direction has fundamentally changed.

**Human-only, hard gate in autonomous mode** (per `${CLAUDE_PLUGIN_ROOT}/engine/autonomous-mode.md` human-only registry): an autonomous run never confirms a kill on the human's behalf — rung (c): ledger the kill recommendation with its evidence and leave the diamond in place. Park and pivot remain autonomously available (reversible; ledger + decision-log required).

**Workflow**:
1. State the reason for killing — what evidence makes this diamond dead?
2. Confirm with user (kill is destructive) — present the reason, ask for explicit confirmation
3. Log decision in .claude/harness/decision-log.md with:
   - Final state of the diamond
   - Reason for kill
   - Alternatives considered (why not pivot, why not park?)
   - Theory: Kahneman (sunk cost fallacy — kill is correct when evidence says continuing is worse than stopping)
   - What we learned (the learning is the deliverable for a killed diamond)
4. Update `.claude/diamonds/active.yml`:
   - Move to `killed_diamonds` section (NOT deleted — canvas data is preserved)
   - Add `killed_at`, `killed_reason`, `learnings` fields
5. Do NOT delete canvas artifacts associated with the killed diamond — they are learning for future work
6. Capture the learning in `.claude/memory/patterns.md` and `.claude/memory/corrections.md` as appropriate
7. **Record cycle in `.claude/canvas/cycle-history.yml`**: Killed diamonds are terminal states. Record predicted ICE/effort, actual outcome as "killed", reason, and phase at kill. This feeds adaptive thresholds and pattern detection.

### Dogfood Mode Modifier (from ${CLAUDE_PLUGIN_ROOT}/engine/canvas-guidance.yml)

When the project has `dogfood: true` set, stop conditions become Mycelium learnings rather than project deaths. In dogfood mode, a killed diamond generates a dogfood report entry in `.claude/evals/dogfood-reports/` instead of only being logged as a project kill. The framework gap caught is the real deliverable.

---

## Purpose-stance gate (at `commit_to_build` and `release`)

**Run before recording either:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_purpose_stance.py" --strict --diamond-id <this-diamond-id>
```

**Pass `--diamond-id`.** Without it every diamond committed to build or released is blocking-eligible,
so this decision can fail on a DIFFERENT diamond's missing stance — a stop for a reason that has
nothing to do with the step just taken. With it, the block is scoped to the diamond being moved and
every other one still reports at the never-fail tier. The same scope applies to solutions: only the
solutions this diamond names block (its `front_runner`, or the solution its `object_ref` names; with
neither, the live solutions under the opportunity its `object_ref` names). Every other solution in the
tree reports as WARN and does not block this decision. Through 0.334.1 every solution in the tree blocked
whatever `--diamond-id` said, so one contradiction left on another opportunity's idea stopped every
diamond's `commit_to_build` and `release`.

Non-zero exit **blocks the decision**. It fires when a solution carries no stance against a binding
property, when a verdict has no note, when a declared contradiction has no human override, or when the
property list was derived from a superseded why/how/what.

**AND NOW ON THE DIAMOND ITSELF, which is what this gate was always specified to do.** A diamond
recording `commit_to_build` or `release` must carry its own `purpose_stance`, exactly as a solution does. Until
plugin 0.123.0 the script this gate calls read only `opportunities.yml` — so the gate ran, found the
solutions clean and returned green **while never opening `active.yml`**. It could not see the artifact
whose decision it was guarding. Diamonds elsewhere in their loop, and parked diamonds, report at the
never-fail tier and never block.

**These two decisions and not the earlier ones**, deliberately: they are where a thing becomes real.
Blocking at `set_target` or `start_experiment` turns exploration into paperwork, which is the friction this framework
is already criticised for.

**Exit 0 with "OK (or not in use)" means the project never adopted `purpose_properties`.** That is a
pass, not a gap — do not prompt for adoption from inside a decision.

## Learning Capture (After Every Decision)

After EVERY recorded decision (not just `close`):

1. **Corrections**: "Were any mistakes made since the last decision? I'll draft a corrections.md entry."
2. **Patterns**: "Did anything work particularly well that's worth reusing?"
3. **Delivery journal** (delivery mode): "What implementation decisions and learnings should be recorded?"
4. **Product journal** (discovery mode): "What insights changed our understanding?"

Draft entries for the user. Present for confirmation before saving. This captures learning at the moment of discovery, not retrospectively.

## Post-Build Next-Steps Nudge (at `release`, and after any build or POC produces working code)

After any decision that follows working code (`release`, or the moment the agent finishes a build or POC after `commit_to_build`), emit an explicit next-steps nudge. Closes the **post-build silence** friction surfaced by cohort-tester-2 (mycelium-roadmap decision-log 2026-05-26): framework completed POC and "just stopped and didn't prompt for more info or advise me what to do next."

Format:

> Build complete. What's next?
> 1. `/mycelium:security-review` — OWASP-shaped review of the code just produced (recommended if any risk shape fired during `/mycelium:delivery-bootstrap`)
> 2. `/mycelium:threat-model` — STRIDE pass if the spec involves auth, data handling, file upload, or external boundaries
> 3. `/mycelium:definition-of-done` — checklist before declaring shippable
> 4. `/mycelium:reflexion` — if anything in the build felt unstable, run the self-critique loop
> 5. Refine the spec — was the original ask correct, or did the build reveal a gap?
> 6. Ship as-is — explicit decision to deploy without further review (record reason)
>
> If unclear, my recommendation is: {pick based on risk shapes fired earlier, default `/mycelium:security-review`}.

Cite the risk shapes that fired during bootstrap (per the operating contract's attribution rule (Communication Rule 4)). Never auto-invoke; offer-menu only.

---

## Theory Citations
- Buçinca, Malaya & Gajos: Cognitive Forcing Functions (human judges first, reduces automation bias)
- Torres: Evidence requirements
- Cagan: Four risks
- Christensen: JTBD validation
- Snowden: Cynefin classification
- Shotton/Kahneman: Bias mitigation
- OWASP/STRIDE: Security gates
- GDPR/PbD: Privacy gates
- Smart: BVSSH (now at completion, not just monthly)
- Downe: Service quality (gated for user-facing work)
- Forsgren: DORA metrics + testing requirements
- EU AI Act: Regulatory classification (L3-L5)

## Counter-Argument Check (Bias Mitigation)

Before recording a decision, draft a one-line counter-argument: *"What's the strongest case AGAINST this decision — what gate is borderline, what evidence is weakest, what regression risk is being underweighted?"* If you can't articulate one, run `/mycelium:devils-advocate` before proceeding.

This addresses the bias cluster documented in corrections.md (L5 sycophancy 2026-04-20, eval overfitting 2026-04-30, sharper-framing-isn't-righter 2026-05-03). Common shape: agent prefers what feels right over what evidence supports under competing pressure (be helpful vs. be honest, advance vs. regress). Decision reviews are the canonical context — the agent is incentivized to move forward and may underweight the case for staying where it is or running another experiment.

Especially important at an L4's `close` (DoD signoff) and an L5's `release` and `close` (where the L5-sycophancy correction explicitly named promotional-language drift).
