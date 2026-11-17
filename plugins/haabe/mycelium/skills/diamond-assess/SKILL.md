---
name: diamond-assess
description: "Use to evaluate the current state of a diamond. Checks theory gates, confidence levels, and recommends next action."
metadata:
  instruction_budget: "82"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Diamond Assess Skill

## First: are Mycelium's hooks running here? (v0.286.0)

Run `find .claude/state/hooks-alive "${TMPDIR:-/tmp}/mycelium-hooks-alive-$(id -u)" -mmin -60 2>/dev/null`. If it prints a path (since v0.318.0 the hooks also stamp the temp folder in a project with no Mycelium state yet, where they do nothing else), say nothing
about it and go on. If it prints nothing, Mycelium's hooks did not run in this session: its gates
and the rules it gives the agent at session start are off, and nothing else will say so. Tell the
user in one line before anything else: "Mycelium's hooks are not running in this session, so its
gates are off. On Codex CLI, open `/hooks`, trust Mycelium's hooks and start a new session; on
Claude Code, check the plugin is enabled in `/plugin`." Then carry on with this skill.

Evaluate current diamond state and recommend next action.

## Preflight: Read-before-Recommend (gate-narration discipline)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 graduation v0.39.16). Every gate-status narration, blocker statement, hold claim, or "what's missing" verdict this skill emits MUST cite the canvas file + field path of the source evidence (e.g., `per purpose.yml#why`, `per opportunities.yml#opp-005#status`, `per landscape.yml:1520`). Adjacent-surface inference (different opportunity, different ht, different topic) MUST be tagged as inference, not asserted as gate state. This skill ran an un-mechanized version of its own diagnosis in cluster-instances.md instance #17 (2026-06-02) — confabulated an "L0 unclear" blocker from comms-friction evidence while the L0 purpose was clear and canvas-documented; collapsed only after the founder articulated the underlying model and grep verified the canvas already had it. The preamble exists so this skill stops being the recursive case.

## Workflow

0. **Cognitive Forcing (ALWAYS FIRST — before any analysis)**:

   Before presenting any assessment, ask the human for their unprimed judgment:

   > "Before I run the gates — where do you think this diamond stands right now? What feels solid and what feels shaky?"

   Wait for the human's response. Record it. Then proceed with the full assessment below. After presenting the assessment (step 10), compare:

   > "You said [X]. The gates say [Y]. Where do we differ?"

   **The turn that asks this question ends with a `Next:` line, like every turn in which a skill ran** (contract rule 12). The question is the next action: `Next: say where you think this diamond stands, what feels solid and what feels shaky (per: diamond-assess step 0)`. Without that line the Stop hook `hooks/next-action-check.sh` blocks the turn, and Claude Code shows the block to the person as "Stop hook error" under a question they have not answered yet. On the dogfood project, 3 of that hook's first 5 blocks were this pause (2026-10-05 to 2026-10-22).

   This prevents the agent's analysis from anchoring the human's judgment. The human's pre-assessment often catches things the gates miss (Hoskins consistently outperformed the agent on product judgment calls).

   *Source: Buçinca, Malaya & Gajos (Cognitive Forcing Functions, Harvard CHI/CSCW 2021) — forcing initial human judgment before AI output significantly reduces automation bias and over-reliance on incorrect AI recommendations.*

   **Autonomous mode** (per `${CLAUDE_PLUGIN_ROOT}/engine/autonomous-mode.md`): in a declared autonomous run, substitute at rung (b) — record the declared persona's unprimed judgment BEFORE reading any canvas or gate state (the ordering is the load-bearing part, not the human authorship), tag it `source_class: internal_simulated`, and ledger the substitution. The post-assessment comparison still runs: persona judgment vs gate verdict.

1. **Identify the diamond**: Which diamond (ID, scale, position) is being assessed?

2. **Gather current state**:
   - Where it is (`scale_locks.position`: no decision yet, target set, committed to build, released; the mode with it)
   - Evidence collected so far
   - Confidence score with breakdown
   - Blockers or risks

2b. **Surface parked diamonds with resume conditions**:
   - Read `.claude/diamonds/active.yml` for diamonds with `state: parked` (or a `parked_diamonds` section).
   - For each, evaluate `resume_conditions` against current canvas/world state. If the awaited condition now holds, surface it as resumable: "Parked: [id] (parked [date], condition: '[condition]'). That looks satisfied — resume?" If not yet met, list it with its condition in one line. If a parked diamond has NO `resume_conditions`, flag it (unreachable except by memory — add conditions or decide park → kill).
   - Implements the surface promised in `/mycelium:diamond-progress` § Park; found unimplemented by the 2026-06-12 gap analysis (no skill read `resume_conditions`).

2c. **Scale occupancy (records against cycles, v0.217.0)**:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_scale_occupancy.py" --canvas-dir .claude/canvas
```

Report the line for each scale with records, and each live L1's trigger set as the script lists it (founder ruling 2026-11-12, `engine/diamond-rules.md`): if one of the events has happened, say so and name what the trigger says the L1 then does; whether it happened is for the person to confirm, the script cannot tell. Since v0.302.0 (DL-1367) it counts desired outcomes against L2s and chosen targets against L3s, since an L2 maps one outcome and an L3 works one target; before that, "73 opportunity records, 0 active L2 cycles" was the one-line diagnostic that would have surfaced the dogfood project's shape in May 2026, four months before a founder named it from lived experience ("how I never could get past L1 whilst the product already existed"). A record and a cycle are different objects; a scale with records and no cycle ever opened has an intake and no outlet, and both doors are in `/ost-builder`. A parent's phase does not forbid work below it; its missing ARTEFACT does (Entry locks, v0.245.0). Also run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scale_locks.py" --check` and report each open diamond whose lock does not hold, with what is missing: that is the next thing to produce, ahead of any work inside the diamond.

3. **Check theory gates for next transition**:
   - Reference ${CLAUDE_PLUGIN_ROOT}/engine/theory-gates.md for the current transition
   - Check `product_type` from `.claude/diamonds/active.yml` -- gates conditioned on product_type include:
     - **Security Gate**: full OWASP for software/ai_tool; platform-only for content; infra-only for service
     - **Delivery Metrics Gate**: routes to product-type-appropriate metrics canvas
     - **Service Quality Gate**: Downe applies to consumption experience for all product types; Nielsen only for digital interfaces
   - Evaluate each applicable gate: Pass / Fail / Insufficient Evidence / N/A (if gate doesn't apply to this product_type)
   - **Read-before-claim (HARD RULE; anti-pattern #7 instance #4, 2026-05-09):** Before claiming a required-evidence bucket is *missing* or *partial* (e.g., "Wardley Map | Missing", "user_research_synthesis | Insufficient"), the agent MUST use the **Read tool** on the canvas file that bucket maps to (e.g., `landscape.yml`, `user-needs.yml`, `opportunities.yml`, `gist.yml`). Spawn-note text, theory-gates.md references, and prior conversation context do NOT count as evidence of the bucket's actual state — only reading the file does. Treating consistency between spawn-note phrasing and an absence-claim as causal evidence is anti-pattern #7 (Consistency-as-Evidence). The graduation case for instance #4 was the agent recommending "build the Wardley map now" when the map was substantially complete — the agent had not opened landscape.yml.
   - Document what is missing for failed gates, naming the specific canvas file read and the specific field that is empty/incomplete (not the inference that it should be empty).

4. **Check confidence threshold**:
   - Reference ${CLAUDE_PLUGIN_ROOT}/engine/confidence-thresholds.yml for the current scale
   - Apply `project_type_adaptations` to compute effective threshold (see ${CLAUDE_PLUGIN_ROOT}/engine/confidence-thresholds.yml)
   - If `project_type` in `.claude/diamonds/active.yml` is empty or absent, ask "is this a solo hobby, a solo product, or a team product?" before comparing, write the answer as `/mycelium:diamond-progress` step 3 says, and never apply the base threshold silently (v0.328.0). If the person declines, compare against the base and say the bar is unadapted because the scope is unknown.
   - Compare current confidence to the **effective** threshold, only at the decisions the scale's
     `threshold_applies_at` lists when it has one (the L3's is `close`, its exit, v0.259.0);
     otherwise name the evidence the next decision needs from `evidence_by_decision` (keyed by
     decision since v0.308.1; by `product_type` where the evidence differs, `software` the
     fallback: v0.269.0)
   - Identify what would increase confidence

5. **Check for anti-patterns**:
   - Reference ${CLAUDE_PLUGIN_ROOT}/harness/anti-patterns.md
   - Flag any detected failure modes
   - For L1/L2 diamonds: also check for **system archetypes** (Senge) — Fixes That Fail, Shifting the Burden, Limits to Growth, Eroding Goals
   - At L3->L4 transitions: also run the **Design Completeness Check** (quality/CLAUDE.md) to verify all layers of the product design stack have evidence. Source: Mill, building on Garrett.

6. **Check canvas health**:
   - Run the `/mycelium:canvas-health` checks inline: missing required files, stale confidence, inconsistent evidence types
   - Report any critical or warning-level findings
   - This catches silent canvas degradation before it affects progression decisions

6c. **Read the market canvas at L1 and L2, not only at L5** (added 0.191.0, founder ruling
   2026-09-10: "L5 should share data with multiple of the previous diamonds, as well as pass
   relevant data back to L2"). `.claude/canvas/go-to-market.yml` is Lauchengco's L5 canvas, but
   two of its sections are inputs to earlier scales and were read by nothing before L5:
   - **L1 Strategy**: read `go-to-market.yml#channel_intelligence`. Whether the chosen segment is
     REACHABLE, and by what posture, is a strategy fact; a strategy diamond that closes Define
     without a read of reachability is choosing a segment blind. State the newest dated entry
     read and what it says about the segment under assessment.
   - **L2 Opportunity**: read the same section for channel OUTCOMES that confirm or contradict an
     opportunity's assumptions (the L5 -> L2 loop in `engine/feedback-loops.md`, which until now
     fired only on launch completion). A channel that returned nothing on a named population is
     evidence about the opportunity, and it belongs on the opportunity's record.
   - If the file has no `channel_intelligence` section, say so: "no channel ledger on this canvas"
     is a gate finding at L1, not an omission to pass over.
   The surface registry (`engine/surface-registry.yml#channel-evidence`) declares this skill as a
   reader, and `check_surface_registry.py` fails if this step stops naming the file.

6b. **Check metric snapshot freshness** (v0.14; L0/L1/L2/L5 only):
   - If the current diamond scale is L0, L1, L2, or L5 AND `.claude/jit-tooling/active-metrics.yml` exists:
     - For each `status: active` source, find the newest file in `.claude/evals/metrics/<source>/`.
     - If the newest snapshot is >7 days old (or missing entirely), flag as a warning and recommend `/mycelium:metrics-pull`.
     - If `.claude/jit-tooling/active-metrics.yml` is missing, recommend `/mycelium:metrics-detect` (softer — info-level, not a gate).
   - Rationale: evidence loops for Purpose/Strategy/Opportunity/Market depend on external signal freshness. A stale snapshot silently anchors confidence.
   - Do NOT block progression on stale snapshots — this is a NUDGE, not a gate.

7. **Check corrections.md**:
   - Any relevant past mistakes to avoid?

7b. **Check trio perspective coverage** (Torres Product Trio):
   - For the diamond's next decision, verify all three perspectives (product/design/engineering) have been applied.
   - Reference `${CLAUDE_PLUGIN_ROOT}/engine/theory-gates.md` §Trio Perspective Requirement for the per-scale coverage matrix.
   - Flag any missing perspectives as a gap: "Design perspective not yet applied at L[X]. Consider running `/mycelium:usability-check` or `/mycelium:service-check`."
   - If perspectives are in conflict, recommend `${CLAUDE_PLUGIN_ROOT}/engine/perspective-resolution.md`.

7c. **Check outcome Definition-of-Done presence** (retrofit detector for `/mycelium:define-done`):
   - Read `.claude/diamonds/active.yml` for this diamond's `definition_of_done` (non-empty `outcome` + `signal`).
   - If **absent**: surface it before the coaching check — "This diamond has no explicit outcome Definition of Done, so 'done' is defaulting to the implicit-harshest bar. Run `/mycelium:define-done` to pin it (problem → signal → kill-criterion)." This is the validated retrofit path — the *question* is what produced a real bar ("fits, not ships") when L0 was retrofitted; a back-filled field is not. Cite `per diamonds/active.yml` (field absent).
   - If **present**: **ASK THE HUMAN TO STATE IT FROM MEMORY BEFORE YOU SHOW IT.** *"Before I read it back — what does this diamond's Definition of Done say?"* Then show the recorded one and name any divergence. **The divergence IS the finding**, and it is invisible to every presence check in the framework.
     - **Why this exists (consumer-reported 2026-08-31).** This detector fires on ABSENCE. On a project whose DoD was present, richly specified and refined three times, the owner asked what L0 claimed answered: *"I don't remember what L0 claims first of all, so it is quite hard to say what to say about status."* **A Definition of Done its owner cannot recall is not steering anything**, and it reads as satisfied to every check there is. The skill's own principle — the *question* is what produced a real bar, a back-filled field is theatre — applies just as much to a field that was well-made and then went unread.
     - Costs one question, needs no new field. If they state it and it matches, say so and move on; that is a real pass rather than an assumed one.
     - **After they answer, show the sizes (v0.225.0):** `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_dod_shape.py" --diamond-id <id>` prints the bar (outcome+signal+threshold+kill_criterion), the `definition_of_done.log[]` and everything else, in characters, plus any dated key written as a field (LOG-AS-KEYS). Show it AFTER the recall answer, never before: the number is the explanation for the answer, not a prompt for it. No threshold is applied, deliberately; a recall failure beside a 21k-character bar, or a recall pass beside a 700-character one, is the data that would set one. Record the pair (recalled or not, bar size) in the decision log. If LOG-AS-KEYS is non-empty, move those entries into `log[]` as `{date, text, moved_from}`.
     - If it diverges, do NOT quietly correct them to the recorded text. Ask which one is right — a DoD the owner has silently outgrown is a signal to re-run `/mycelium:define-done`, not a memory failure to patch.
   - Then carry its `signal` into the coaching check below as the concrete "what does done look like" answer rather than re-eliciting it.

8. **Coaching check** (Rother's Coaching Kata):
   Surface these five questions in the output to prompt the human's thinking:
   **ORDER IS CONDITIONAL — ask Q2 first when no target condition exists yet.** Rother: *"Note that
   **before a target condition has been established, the order of questions 1 and 2 is reversed**
   from what is shown here."* The five questions presuppose a target: *"The five questions come into
   play once you are 'on the staircase,' that is, in the PDCA phase of the improvement kata, **after
   a target condition has been established**."* Asking "what is the target condition?" of a diamond
   that has none is the failure this ordering exists to prevent.

   1. What is the **target condition** for this diamond? (What does "done" look like?)
   2. What is the **actual condition** right now? (Summarize from steps 2-7 above)
   3. What **obstacles** are preventing progress? Which one are you addressing now?
   4. What is your **next step**? What do you **expect** will happen? (Force a prediction before acting)
   5. When can we **check what we learned** from that step? (Commit to a review point)
   The coach (human) should answer these, not the agent. The agent surfaces them.
   *Source: Rother (Toyota Kata) — the 5 questions install scientific thinking as a daily habit.*

   **Once set, a target condition is FROZEN.** Rother: *"Once a target condition is established —
   even an initially vague one — **its content and achieve-by date are not easily changed**."* And
   the target comes before the work: *"Toyota will usually not start trying to improve or move
   forward before a target condition has been defined. This ensures that people's efforts will be
   focused on actual needs rather than on various ideas and opinions about what we can do."*
   **Amending a target at closing time is how a cycle passes by moving its own goalposts** — record a
   supersede with a reason instead of editing.*

   **Autonomous mode** (per `${CLAUDE_PLUGIN_ROOT}/engine/autonomous-mode.md`): rung (b) — the declared persona answers all five, the answers are ledgered and tagged `internal_simulated`, and question 5's review point is a committed date the next human session can check.

9. **Log assessment in .claude/harness/decision-log.md** (MANDATORY):
   - APPEND a `### Diamond Assessment` entry to `.claude/harness/decision-log.md`
   - Include: diamond ID and scale, gates passed/failed, current confidence with rationale, evidence gaps
   - This log entry is essential for auditability — every assessment should be documented

10. **Recommend next action**:
   - If all gates pass and confidence meets threshold: recommend recording the next decision (`/mycelium:diamond-progress`)
   - If gates fail: recommend specific actions to address failures
   - If confidence is low: recommend evidence-gathering activities
   - If anti-patterns detected: recommend corrective actions
   - If the loop must iterate: recommend the decision to append (another `start_experiment`, a re-chosen front runner with another `commit_to_build`, DL-1373) and why; a recorded decision is never removed (DL-1374)
   - A recommendation is not a ruling. This skill writes nothing to `.claude/diamonds/active.yml`, so a session-start item that says a diamond "has no ruling yet" or "was last ruled on" a date stays open after this assessment; it clears when `/mycelium:diamond-progress` records the decision, or when the person rules on the item itself. Say this when you recommend, so the person records the decision instead of running the assessment again.

11. **Play devil's advocate**: Before recommending progression, ask:
    - What are we most likely wrong about?
    - What evidence have we dismissed?
    - Is there a simpler path we're overlooking?

12. **Report harness thickness** (informational):
    - Count: total skills, active guardrails, mandatory reads, hooks, theory gates
    - Count from the tree at run time, never from a previous run or this file: skills are `skills/*/SKILL.md`, theory gates are the numbered headings under *Gate Definitions* in `engine/theory-gates.md`, hooks are the commands registered in `hooks/hooks.json`. (A hardcoded line here said 13 gates while the engine defined 15.)
    - If thickness has increased since last assess, note it
    - This is observability, not a gate — purely informational
    - *Source: Trivedy (Anatomy of an Agent Harness, LangChain blog — "scaffolding should decrease as models improve," but harnesses remain valuable as they engineer systems around model intelligence)*

## Closing path (derive it; do not make the human ask for it)

**Run once during the assessment and print its output verbatim under a `## Closing path` heading,
before the coaching check:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/derive_closing_path.py" --project-dir . --diamond-id <this-diamond-id> --write
```

`--write` (v0.187.0) also STORES the derivation on the diamond as `closes_on`, stamps `reader` on the
assumptions and `on_close` on the tasks it names, and reports when a named input has landed since the
last store as a `CLOSING PATH FIRED` proposal; act on that proposal before the coaching check.
Since v0.322.1 it does not store over hand-written content: when the stored `closes_on` holds a key
or an item the script never writes, the block is left as it is and a `CLOSING PATH NOT STORED` line
names the diamond, the place and the keys such content can live under.
It reads the diamond's `theory_gates_status`, the leaves under the opportunities that cite the
diamond (assumptions with no verdict, and whether a test is named for each), the open human tasks
whose `diamond_ref` names it (with horizons), a gate whose status is stale against the leaves under it,
and rulings already asked in `what_would_move_it`. It prints one row per pending gate: what would
flip it, who owns that, and the date if the record holds one. Since v0.299.0 the rows are grouped
by what each gate is owed before: the next move's decisions (named), the safety gates that move
needs (the release gate also reads them per exposure record), gates only a later move needs, and
gates passed with a risk recorded, which count as passed and are not owed.

**Three lines added in v0.197.0, each from a dogfood day.** (1) `READ DUE on N task(s)`: a task's
`read_dates` entry whose date has passed with no activity recorded on the task since. Run that read
before the gate table; two 48-hour reads fell due on 2026-09-10 and five sessions walked past them
because only `horizon` was watched. The same line reaches session start via
`scripts/check_reads_due.py`. (2) When a `CLOSING PATH FIRED` proposal does not choose a path, say
so on the record: write `ruling:` and `ruled_at:` under that entry in `closes_on.fired`; the block is
script-owned but those two keys survive re-derivation. (3) If the summary says the diamond's
`rolls_up_to` is prose that keys to no outcome id, the tree is unread, not empty: set `rolls_up_to`
to the outcome id the opportunities roll up to (`opportunities.yml#desired_outcomes.<id>`). The
dogfood L1 read "0 of 0 live leaves" for two days on exactly that, and the fix was one field.

**Why this exists (consumer-reported 2026-09-09).** The assessment reported status; the founder
asked twice ("what's needed to close define?", "work through the distance points") before the path
was derived, and every input to it was on disk before the session opened: leaf assumptions with null
verdicts and a read dated four days out, a `four_risks: pending` field stale since a blind review three
days earlier, a ruling already on his desk. His words on the framework: *"too passive about keeping
up with data and progress ... The user most certainly doesn't have the state of every nitbits of the
project, and can't tell the agent what is needed to progress."* The script derives; this skill prints.
Where the script says "nothing on record moves any pending gate", say that: it is the finding, and it
is what the human needs to hear before being asked five coaching questions.

## Purpose-properties state (report it, do not fix it here)

Run once during the assessment and report the line verbatim:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_purpose_stance.py" --canvas-dir .claude/canvas
```

Three states, three different things to say:

- **"OK (or not in use)" AND `purpose.yml` has no `purpose_properties`** — say once that nothing below
  has ever been checked against this project's own why/how/what, and that
  `/mycelium:purpose-properties` derives them. **Once. It is a standing condition, not news, and
  repeating it every assessment is how a nudge gets muted.**
- **WARN lines about a stale `derived_from_hash`** — this is the one to surface loudly. The purpose
  changed after the properties were derived, so **every stance below them was reasoned under a
  definition that no longer holds.** Report it as invalidated work, not as a lint finding.
- **Otherwise** — report the findings as part of the assessment and move on.

**The PMF read, at L5 only (v0.232.0).** Read the diamond's `pmf` block — it is L5's entry condition
and nothing else consults it.

- **ABSENT entirely** — say so once, and say which of two things it means, because they are opposite.
  An L5 opened by `/launch-tier`'s spawn edge always carries one, so a missing block means either
  **this diamond predates v0.232.0** (ordinary for any L5 opened by hand — report it, offer
  `/mycelium:launch-tier`'s Step 1 to fill it, and move on) or **it was opened bypassing the spawn
  edge**, which is worth one question: what categorised the release as a major launch? **Absent is
  not `not-yet-measurable`.** The latter is a recorded judgement that the sample is too small; the
  former is nobody having looked. Reporting them the same way is how an unasked question reads as an
  answered one. *(Branch added v0.234.2: the bands below shipped without it, while the L0 bearing
  check one section down carried its own absent-case from the start — the same rule written in one
  place and not the adjacent one, which is the shape this file already documents twice.)*

- **`band: not-yet-measurable`** — report it as the true state and say what would change it: a sample
  large enough for a percentage to mean anything. **Do not treat it as a failure** and do not suggest
  estimating the number; the band exists precisely so an L5 can run honestly without one.
  Ellis's five follow-up questions work at any n and are available now — surface them as the move.
- **A band with a stale or missing `as_of`, or an `n` small enough to make the percentage noise** —
  say so beside the band. PMF is exactly the kind of number that goes stale, and a percentage over a
  handful of users reads as authoritative while carrying almost no information.
- **`very_disappointed_pct: null` with a band other than `not-yet-measurable`** — that is a band with
  no reading behind it. Flag it; it is the shape a fabricated gate-clearance takes.
- **`green`** — report it plainly, with `n` and `as_of` in the same sentence. It is a licence to
  pursue growth (Ellis), not a licence to stop measuring.

**The bearing check, at L0 only (v0.230.0).** Read `purpose.yml#just_cause`.

- **Present** — run its own check against what has actually happened since `reviewed`: does any
  decision taken in that window resemble `contradicting_decision`? If one does, **that is the
  finding**, and it is a finding about the project, not about the field. Say which decision, cite
  it, and let the user rule. Restamp `reviewed` when they do. **Do not compute a drift score** —
  origin, bearing and position are three references, not coordinates, and nothing arithmetical runs
  on them.
- **Absent** — say once, at L0 only, that the project has an origin and a position but no bearing,
  so there is nothing for drift to be measured against, and that `/mycelium:purpose-properties`
  Step 6 offers one. **Once.** An absent bearing is a legitimate state and a project may run
  without one; repeating this every assessment is how a nudge gets muted, which the bullet above
  already learned the hard way.

**Do not derive properties from inside this skill.** Assessment reports state; changing the purpose
layer is a deliberate act with its own entry point.

## Output Format

**ALWAYS output in plain language first, then technical details.**
Use `${CLAUDE_PLUGIN_ROOT}/engine/status-translations.md` for translations.

**ALWAYS render the journey map first.** Follow `${CLAUDE_PLUGIN_ROOT}/engine/wayfinding.md` to render the "You Are Here" map before any other output. This orients the user to where they are in the full L0→L5 progression before diving into gate details.

**Phase-index narration discipline** (per ht-012 cohort-log f9, shipped v0.23.21): when surfacing routing decisions or flagging empty canvas fields, **do NOT narrate internal phase numbers ("Phase 6 questions", "Phase 4 Landscape") to the user**. Reference the outcome instead: "the project-type question", "the landscape mapping step". L0–L5 diamond scales are framework-external vocabulary and ARE narratable (they appear in user-facing docs); Phase-N indices are internal skill structure and are NOT.

```
[Journey map from ${CLAUDE_PLUGIN_ROOT}/engine/wayfinding.md — rendered first]

## Where We Are

Current focus: [plain-language description from ${CLAUDE_PLUGIN_ROOT}/engine/status-translations.md]
  [1-2 sentences of context]
  Confidence: [plain word] ([number], [Gilad level]) -- [why this level, what would increase it]

## Progress

[N] of [M] diamonds complete:
  [Name]: [STATUS] -- [plain-language one-liner]
  [Name]: [STATUS] -- [plain-language one-liner]

## Theory Gate Check (for next transition)

| Gate | Status | Suggested Skill |
|------|--------|----------------|
| Evidence | Pass/Fail | /mycelium:user-interview or /mycelium:assumption-test |
| Four Risks | Pass/Fail | /mycelium:assumption-test |
| ... | ... | ... |

Render any **Fail** row so it pops (e.g. `**FAIL**` or a leading `Blocking:` line under the table) rather than letting it sit indistinguishable from `Pass` — the failing gate is the one the reader must not scroll past. Von Restorff; per `harness/design-principles.md`.

## What I'd Challenge (Devil's Advocate)
- [Key assumption to question]
- [Evidence gap to flag]

## Coaching Check (for the human)
1. What does "done" look like for this diamond?
2. Given what we know now, what's the biggest obstacle?
3. What's your next step -- and what do you expect will happen?
4. When should we check what we learned?

## Recommended Next Step
[Plain-language recommendation with theory justification]

Suggested actions:
  - /skill-name -- [why this is relevant now]
  - /skill-name -- [why this is relevant now]
```

## Theory Citations
- Buçinca, Malaya & Gajos: Cognitive Forcing Functions (human judges first, then AI presents — reduces automation bias)
- Torres: Evidence-based progression
- Gilad: Confidence scoring with contextual explanation
- Cagan: Four risks assessment
- Snowden: Cynefin classification
- Shotton/Kahneman: Devil's advocate bias check
- Rother: Coaching Kata (5 questions for scientific thinking)
