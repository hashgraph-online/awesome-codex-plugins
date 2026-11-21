---
name: retrospective
description: "Structured retrospective after completing a delivery increment or diamond. Captures learning for continuous improvement."
metadata:
  instruction_budget: "58"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Retrospective

Run after every completed **cycle**: a solution leaf reaching a terminal state (launched, archived, killed), or a framework-development arc that shipped. Not only after a diamond completes — a diamond at L0 to L2 can stay open for months while cycles close under it weekly. Measured on the dogfood repo (2026-08-30): 17 cycles in 116 days, median 3.5 days apart, while every diamond stayed open the whole time; the earlier wording ("after every completed delivery diamond or significant milestone") named two units forty times apart and the load-bearing one was the vague one. Source: Forsgren (learning culture).

## Preflight: Read target canvas file(s) before any Write/Edit

**Hard rule.** Before issuing `Write` or `Edit` against any `.claude/canvas/*.yml`, use the **Read tool** on that file in this session. Claude Code's Read-before-Write check requires the `Read` tool specifically — `cat`/`head`/`grep` via Bash do NOT satisfy it.

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

Run these steps IN ORDER. Do not skip any step. **Step 1 (cycle recording) MUST be completed FIRST — before any reflective analysis.**

### Step 1. Record Cycle in `.claude/canvas/cycle-history.yml` AND Decision Log (MANDATORY — DO THIS FIRST)

**This step is critical.** Without it, the learning metabolism has no data. You MUST do BOTH parts (5a and 5b).

#### Step 5a. Write cycle record to `.claude/canvas/cycle-history.yml`

Find the leaf_id and opportunity_id for the delivered solution (from `.claude/canvas/opportunities.yml` or `.claude/canvas/gist.yml`). Then write a cycle record:

```yaml
- cycle_id: cycle-NNN
  leaf_id: "opp-XXX-sol-X"         # From opportunities.yml
  opportunity_id: "opp-XXX"         # Parent opportunity
  diamond_id: "d-XXX"               # From .claude/diamonds/active.yml
  completed_at: "YYYY-MM-DDTHH:MM:SSZ"
  outcome: shipped | partial | failed | discarded
  cycle_class: product-leaf | meta-dogfood | observation  # REQUIRED — see engine/cycle-learning.md#cycle-class
  predicted:
    ice_score: {i: X, c: X.XX, e: X, total: X}  # total = i x c x e (Gilad's ICE; c from his Confidence Meter). REQUIRED recorded when cycle_class=product-leaf; permitted all-zero for meta-dogfood/observation (state why in notes)
    feasibility_risk: low | medium | high        # From four_risks
    effort_estimate: "X days/weeks"              # Original estimate
  actual:
    effort: "X days/weeks"                       # How long it actually took
    dora:                                        # From /mycelium:dora-check or known metrics
      deploy_frequency: "..."
      lead_time: "..."
      change_failure_rate: "..."
      mttr: "..."
  calibration:
    ice_accuracy: "predicted XXX vs actual [outcome description]"
    effort_accuracy: "predicted X days vs actual X days (delta: +/-X)"
    risk_accuracy: "feasibility was [predicted] — actual was [description]"
  demand_type: value                             # value | failure — WHY this cycle exists (Seddon)
  demand_origin: ""                              # required when failure: the earlier work that caused it
  demand_cost_class: null                        # optional: prevention|appraisal|internal-failure|external-failure
  gates_fired:                                   # which theory gates fired; result pass|fail (fail = caught a real gap)
    - {gate: "<gate name>", result: pass, caught: ""}
  regressions:                                   # in-cycle phase regressions (NOT post-delivery rework)
    in_cycle_count: 0
    from_phase: null
    to_phase: null
    trigger: ""
  learnings: "Key learning from this cycle"
```

**`demand_type` is the one field you should already know before the retrospective starts.** Ask why
the cycle existed: did a user, a goal or a deliberate bet ask for it (`value`), or did it exist
because earlier work was wrong, missing or incomplete (`failure`)? **If you are reconstructing the
answer now, say so** — set `reconstructed_post_hoc: true`, because Seddon's method classifies demand
as it ARRIVES and a type assigned weeks later reports on the assessor. **`failure` requires
`demand_origin`**: a failure cycle that cannot name the earlier work that caused it is usually
mis-classed as failure when it is value, or hiding the real cause. **Do not route this through
`rework`** — that block is post-delivery defects in a 14-day window; work begun because earlier work
was incomplete is not a post-delivery regression, it is the reason the cycle exists.

**Populate `gates_fired` and `regressions` from the analysis you already do below** (Step "Where did the theory gates catch a real problem?" → `gates_fired`; "How many regressions occurred?" → split: mid-cycle phase regressions go to `regressions.in_cycle_count`/`from_phase`/`to_phase`/`trigger`, post-launch defects stay in `rework.post_delivery_regressions`). If no gate fired and no regression occurred, write the empty/zero forms explicitly — absence recorded is a measurement; a missing field is not (anti-pattern #9, Fail-Open on Absent Input).

Update `calibration_summary.total_cycles` count. If total_cycles reaches a multiple of 5, prompt: "5 cycles since last review. Run `/mycelium:framework-health` to check calibration?"

**Hard gate on `cycle_class: product-leaf`**: if the cycle being closed shipped an OST solution leaf, `predicted.ice_score` must be a recorded score. Recorded means: `total` is not zero, or `total` is zero and the three factors are there with at least one of them above zero (an Impact of 0 is legal in Gilad's ICE and totals 0; changed 0.319.0, until then the rule was "`total` must be non-zero"). `{i: 0, c: 0, e: 0, total: 0}` is not a score. Copy the score as it stood when the cycle opened, whichever arithmetic it was written under; do not recompute an older average or product into the current form. If no score is recorded, do NOT write the record yet — stop and ask: "This cycle shipped a product leaf but has no recorded ICE prediction. Was `/mycelium:ice-score` run before the cycle opened? If yes, copy the score from `opportunities.yml`. If no, this is a Check 38 violation — class the cycle as `meta-dogfood` if no design tradeoff was actually scored, or backfill the ICE score with an honest reconstruction noted as `reconstructed_post_hoc: true`." Reconstructed scores are excluded from calibration aggregates but preserved for the audit trail.

#### Step 5b. Log cycle calibration summary in .claude/harness/decision-log.md

Write a decision log entry titled "Cycle calibration record" that includes ALL of the following (use these exact words):

- **cycle** number and diamond ID
- **predicted** ICE score and effort estimate (from the original canvas)
- **actual** outcome and effort (from what really happened)
- **calibration** assessment: was the prediction accurate?
- **effort** delta: if the estimate was an **underestimate** or overestimate, state the **accuracy** gap (e.g., "effort accuracy: predicted 5 days vs actual 7 days, 40% underestimate")
- Risk dimension accuracy (e.g., "feasibility was predicted medium — actual confirmed, analytics pipeline was indeed the hardest part")

This decision log entry ensures the calibration data is auditable alongside other decisions, not just buried in cycle-history.yml.

### Step 2. What Went Well?
- Which patterns from patterns.md were reused successfully?
- What new approaches worked?
- Where did the theory gates catch a real problem?

### Step 3. What Didn't Go Well?
- What mistakes were made? (Add to corrections.md)
- Where did we skip a guardrail and regret it?
- What took longer than expected and why?

### Step 4. What Should Change?
- New corrections to add
- New patterns to capture
- Process improvements
- Guardrail adjustments
- ADR review (if `docs/adr/` exists): did implementation follow the decided approach? Any consequences that turned out differently than expected? Mark superseded ADRs.

### Step 5. BVSSH Dimension Check
- **Better**: Did quality improve or degrade?
- **Value**: Did we deliver actual user value?
- **Sooner**: Was our flow efficient?
- **Safer**: Did we maintain security and trust?
- **Happier**: How is team satisfaction? Customer advocacy? Societal impact? Was compute usage proportionate to value (not wasteful)?

### Step 6. Rework Follow-Up (14-day window)

If this retrospective is for a cycle completed more than 14 days ago, check:
- How many corrections were logged against this delivery since completion? → `rework.post_delivery_corrections`
- How many regressions occurred? → `rework.post_delivery_regressions`
- Days to first regression? → `rework.days_to_first_regression`

Update the cycle record in `.claude/canvas/cycle-history.yml` with the rework fields. This is the denominator — the hidden cost of delivery that velocity metrics miss.

If this retrospective is for a just-completed cycle, prompt: "Set a reminder to check rework in 14 days. Run `/mycelium:retrospective rework-check [cycle-id]` after that."

*Source: Paddo (the denominator problem — 43% of AI-assisted code requires post-delivery debugging). Forsgren (change failure rate as a trailing indicator).*

## Root Cause Analysis (when "What Didn't Go Well" surfaces a significant problem)

Use these two complementary techniques. Fishbone gives breadth (all possible causes). 5 Whys gives depth (one cause traced to its root).

### Fishbone Diagram (Ishikawa)

Map all potential causes before investigating any. Structure:

```
                        ┌─ People (skills, handoffs, communication)
                        ├─ Process (gates, cadence, workflow)
Problem ◄───────────────├─ Product (canvas, evidence, assumptions)
(effect)                ├─ Platform (tools, infra, dependencies)
                        ├─ Principles (which theory/guardrail failed?)
                        └─ Pressures (deadlines, scope, external)
```

1. Write the specific problem at the head
2. Brainstorm causes in each category — add as branches
3. Drill into sub-causes until you reach actionable items
4. Vote/rank the most likely root causes for investigation

Ishikawa's original 6M manufacturing categories: Man (Manpower), Machine, Method, Material, Measurement, Mother Nature (Environment). Adapted for product development as: Man→People, Machine→Platform, Method→Process, Material→Product (inputs to the work), Measurement→Principles (what we measure against), Mother Nature→Pressures (external forces).

### 5 Whys (Toyoda)

For the top-ranked cause from the fishbone, ask "why?" five times:

1. Why did this happen? → [first-level cause]
2. Why did that happen? → [second-level cause]
3. Why? → [deeper]
4. Why? → [deeper]
5. Why? → [root cause — usually systemic]

**Stop rule**: Stop when ANY of these conditions are met:
- You reach something you can **change systemically** (a guardrail, gate, or process step)
- Asking "why" again would require **speculation** rather than verifiable fact
- You reach a cause **outside your sphere of influence** (an escalation point, not a dead end)
- The answer would be **the same regardless** of asking "why" (you've hit bedrock)

**Anti-pattern**: Stopping at "human error" — that's never the root cause. Ask why the system allowed the error.

*Source: Ishikawa (cause-and-effect diagrams), Toyoda/Ohno (5 Whys), adapted for agentic product development.*

### Waste Identification (Ohno — 7 Wastes / TIMWOOD)

"Eliminating waste is the foundation of lean." (Ohno)

Before root cause analysis, identify which waste category the problem falls into:

| Waste | Product Development Form | Detection |
|---|---|---|
| **T**ransportation | Handoffs between people/teams, between discovery and delivery | Count handoffs in the value stream |
| **I**nventory | WIP, unshipped code, unfinished features, unmerged branches, open PRs | Check WIP limits, branch age |
| **M**otion | Context switching between tasks, tools, codebases | Track focus time vs fragmented time |
| **W**aiting | Blocked tasks, review queues, approval bottlenecks, blocked dependencies | Measure wait-to-work ratio |
| **O**verproduction | Building features nobody uses, YAGNI violations | Compare shipped features to validated needs |
| **O**verprocessing | Gold-plating, unnecessary abstraction, premature optimization | "Would removing this step reduce value?" |
| **D**efects | Bugs, rework, corrections, failed deployments | Track defect escape rate |

Also watch for: **Muri** (overburden → BVSSH Happier / sustainable pace) and **Mura** (unevenness → delivery cadence variation).

*Source: Taiichi Ohno, Sakichi Toyoda (Toyota Production System). Mapped to product development via Poppendieck (Lean Software Development).*

## Blameless Post-Mortem Format (SRE)

For incidents or significant failures, use the SRE blameless post-mortem:
1. **Timeline**: What happened, when, in what order
2. **Impact**: Who was affected, how severely, for how long
3. **Contributing factors**: What conditions led to this (NOT "who caused it")
4. **Root cause**: The systemic issue, not the human action (use fishbone + 5 Whys above)
5. **Action items**: Specific, assigned, time-bound improvements
6. **What went well**: What prevented it from being worse

Rule: No blame. Focus on the system, not the person. *Source: Beyer et al. (SRE)*

## Refactoring Prompt

After delivery retrospective, always ask:
- "Are there refactoring opportunities? Duplicated logic (DRY)? Unnecessary complexity (KISS)?"
*Source: Beck (XP), Fowler (Refactoring)*

## Output
1. Update `.claude/memory/corrections.md` with new corrections
2. Update `.claude/memory/patterns.md` with new patterns
3. Update `.claude/memory/delivery-journal.md` with retrospective entry
4. Update .claude/canvas/bvssh-health.yml if dimensions changed
5. Log in .claude/harness/decision-log.md
6. Record cycle in `.claude/canvas/cycle-history.yml` (see Cycle History Recording above)
7. **Doctrine retrospective, when it is due** — see below.

## The doctrine retrospective, and its firing condition (v0.230.0)

Doctrine is the one register with a named producer and, until this release, **no trigger**.
*"Learn these continuously"* is not a trigger, and an un-triggered retrospective is the shape that
has failed repeatedly in this project — a mechanism that runs when someone remembers is a mechanism
that reads green while doing nothing.

**IT IS DUE WHEN**: `.claude/canvas/doctrine.yml#last_reviewed` is **absent**, or **earlier than the
newest `completed_at` in `diamonds/active.yml#completed_diamonds`** — or a climate prediction is
past its `horizon` with no `outcome`. That is the trigger — an event that already gets recorded,
not a calendar someone has to keep. It became checkable only in this same release, when completion
stopped being conflated with archival and got a writer; before that there was no event to hang it on.

**YOU DO NOT HAVE TO REMEMBER TO ASK.** `scripts/check_doctrine_due.py` evaluates the condition and
`session-start` relays its line, so a due retrospective arrives unprompted. Run it directly any time:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_doctrine_due.py" --project-dir .
```

*v0.231.0 shipped this condition with no evaluator — it lived only as the paragraph you are reading,
so it fired when someone happened to open this skill. That is the "runs when a person remembers"
shape the condition was written to replace, and **a condition nothing computes reads as satisfied**.
The evaluator landed in v0.231.2. Note what it will NOT say: with no diamond in `completed_diamonds`
it reports that the trigger cannot fire, explicitly not that doctrine is current.*

When it is due, ask Wardley's question — *"look for what has changed and always ask why?"* — and
write to `.claude/canvas/doctrine.yml`:

- **Doctrine**: did something we learned turn out to apply *universally* to our own work? Add it with
  the incident it came from. **`learned_from` is required**, because a principle with no incident
  behind it was imported rather than learned. Doctrine **grows and never completes** — *"the more you
  play the game then the more forms of doctrine you'll discover"* — so **do not compute coverage
  against a total.** There is no total. That is what made the 2026-04 audit's ratios unscoreable.
- **Climate**: score any prediction whose horizon has passed — `held`, `failed`, or `unclear`.
  **`unclear` is a real answer** and beats forcing a verdict; leaving it `unscored` is also honest,
  but `unscored` must never be reported as `held`. Add new predictions **dated**, because a
  prediction that cannot go stale cannot be scored.

Then stamp `last_reviewed`. **An empty doctrine register after a review is a legitimate outcome** —
write the stamp anyway, or the trigger fires forever and the nudge gets muted.

## Counter-Argument Check (Bias Mitigation)

Before finalizing the retrospective, draft a one-line counter-argument for each major claim: *"What's the strongest case that this 'went well' was actually luck? That this 'went wrong' was actually unavoidable? That this 'pattern' is actually noise?"* If you can't articulate counter-cases, run `/mycelium:devils-advocate` before locking in the corrections/patterns.

This addresses the bias cluster documented in corrections.md (L5 sycophancy 2026-04-20, eval overfitting 2026-04-30, sharper-framing-isn't-righter 2026-05-03). Retrospectives are particularly bias-prone — narrative coherence is rewarded, the agent is incentivized to find tidy patterns, and post-hoc rationalization is the natural mode. Counter-arguments break that gravity.

### Hindsight Bias Check

Retrospectives are the natural home of *hindsight bias* — the "I knew it all along" effect that rewrites uncertainty as foreknowledge. For every claim of the form "we should have seen X coming," ask: *would I have predicted X with the evidence available BEFORE the outcome?* If the honest answer is "no, that evidence only became diagnostic in retrospect," log it as a learning about evidence interpretation, not as a missed signal. This protects future retrospectives from manufacturing false should-have-knowns that distort confidence calibration.

*Source: Fischhoff, "Hindsight ≠ Foresight: The Effect of Outcome Knowledge on Judgment Under Uncertainty" (1975).*

Especially important when proposing graduation candidates (recurring corrections → guardrails) — make sure the recurrence is real, not 3 instances of pattern-matching by the agent itself.

## Postflight: Verify-After-Write (claim matches state)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 *write-narration-verification* — mechanism Check 42, graduated v0.39.18; enforced surface expanded to this skill v0.44.0). This skill mandates multi-field canvas updates. Before narrating "updated / wrote / refreshed [canvas]" in any user-facing summary, RE-READ the value fields this skill's MANDATORY says to update and confirm they actually changed — not just `_meta.last_validated` or a freshness stamp. Each field you claim to have updated must reflect its new value. The symmetric half of the Read-before-Write Preflight: that one protects what gets read before a write; this one protects that the write matches the claim. Worked failures: 2026-06-05 #18 (`/dora-check` narrated "updated" with value fields unchanged) + #19 (`/retrospective` left a cycle-history aggregate un-propagated).
