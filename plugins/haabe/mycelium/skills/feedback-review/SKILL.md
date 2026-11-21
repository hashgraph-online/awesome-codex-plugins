---
name: feedback-review
description: "Aggregate feedback signals across all active loops. Reports health, trajectory, overdue checks, regression warnings, and Goodhart's Law violations."
metadata:
  instruction_budget: "55"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Feedback Review

Single-place health check across all Mycelium feedback loops. Run periodically or when something feels off.

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

## When to Use
- Weekly as part of regular practice
- When metrics aren't moving despite active work
- When the team feels busy but unproductive
- After a failed launch or unexpected regression
- When `/mycelium:diamond-assess` shows stale diamonds

## Workflow

### 1. Check Loop 1 (Immediate) Health
- How many reflexion iterations are averaging? (1 = healthy, 3 = struggling)
- Any corrections logged this session? Are they new patterns or repeats?
- Is the preflight gate catching issues, or are issues slipping through?

### 2. Check Loop 2 (Incremental) Health
- Are diamond phases progressing? Or stalled?
- Are ICE confidence scores increasing with each GIST step?
- Is the delivery journal being updated? (Empty = no incremental learning)
- Are retrospectives happening after delivery increments?

### 2b. Parked-Diamond Resume Check
Read `.claude/diamonds/active.yml` for diamonds with `state: parked` (or a `parked_diamonds` section). For each, evaluate its `resume_conditions` against current canvas/world state:
- **Condition met** (the awaited event happened — dependency shipped, evidence arrived, date passed): surface as resumable — "Parked: [id] ([parked_at], condition: '[resume_conditions]'). That condition now holds — ready to resume? Run `/mycelium:diamond-progress` to re-activate."
- **Condition not yet met**: list with its condition (one line) so parked work stays visible, not forgotten.
- **No `resume_conditions` recorded**: flag it — a parked diamond without resume conditions is unreachable by anything but memory; prompt the user to add them or decide park → kill.

This implements the surface promised in `/mycelium:diamond-progress` § Park ("feedback-review and diamond-assess surface parked diamonds with their resume conditions") — a promise that stood unimplemented until the 2026-06-12 gap analysis found no skill read `resume_conditions`. Abandonment is a non-event; nothing else surfaces this.

### 3. Check Loop 3 (Strategic) Health
**First, the schedule (v0.329.0).** The cadence of every scheduled review is data in `engine/review-schedule.yml`, and one script reads each review's last run from what the review itself writes:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_schedule.py" --list --project-dir .
```

Report every row whose state is `due`, with its cadence and last run, and recommend running it. This is the command the session-start NEXT ITEM `reviews-overdue` sends people to, so a person who came from it must find the overdue reviews named here. A row `elsewhere` is reported by its own session-start check (bvssh, delivery metrics); `n/a` does not apply to this project. Do not judge cadence from the decision log: its headings were measured to undercount runs.

Then read canvas trend data:
- **BVSSH**: Any dimension declining? (Check `bvssh-health.yml` trend fields)
- **North Star**: Are input metrics moving? Flat for 2+ months = strategic concern.
- **Delivery metrics**: Any metric degrading? Check the product-type-appropriate canvas: `dora-metrics.yml` (software), `content-metrics.yml` (content), `ai-tool-metrics.yml` (ai_tool), `service-metrics.yml` (service).
- **Wardley Map**: its cadence is the schedule's (every 30 days, as engine/feedback-loops.md sets it; this line said "stale > 3 months" until v0.329.0, which disagreed with that file).
- **Corrections themes**: Are the same types of mistakes recurring? (Pattern = graduate to guardrail)

### 4. Check Loop 4 (Transformative) Health
- When was the last eval benchmark run? (The schedule's `eval-runner` row, from step 3.)
- Are eval pass rates improving, stable, or declining?
- Are any skills consistently underutilized? (Check .claude/harness/decision-log.md for skill invocation patterns)
- Has the escape hatch been used? How often? (Frequent = process too heavy for context)

### 5. Regression Warning Check
From `${CLAUDE_PLUGIN_ROOT}/engine/feedback-loops.md`, check active triggers:
- DORA declined 2+ times? -> Warn about L4/L3 regression
- Confidence stagnant 3+ steps? -> Warn about opportunity reframing
- Same correction 3+ times? -> Suggest guardrail graduation
- BVSSH Safer declining while Sooner improving? -> Flag the BVSSH anti-pattern

### 6. Goodhart's Law Check
For each active metric, verify its counter-metric:
- Deployment frequency up BUT change failure rate also up? -> False improvement
- Confidence score up BUT evidence type hasn't changed? -> Inflation
- Test coverage up BUT defect leakage unchanged? -> Meaningless tests
- Diamond velocity up BUT regression rate also up? -> Rushing through gates
- Evidence source count up BUT external evidence ratio declining? -> Internal echo chamber risk. Suggest `/mycelium:handoff` to plan external conversations.

## Output Format

```
## Feedback Loop Health Report

### Loop 1 (Immediate): [Healthy / Warning / Struggling]
- Reflexion avg iterations: [N]
- New corrections this period: [N] ([N] repeats of existing patterns)
- Secret detection blocks: [N]

### Loop 2 (Incremental): [Healthy / Warning / Struggling]
- Diamonds progressed this period: [N]
- Confidence trajectory: [improving / flat / declining]
- Delivery journal entries: [N]
- Retrospectives completed: [N]

### Loop 3 (Strategic): [Healthy / Warning / Overdue]
- BVSSH last checked: [date] ([days ago])
  Trajectory: B[trend] V[trend] S[trend] S[trend] H[trend]
- North Star: [current] -> [target] ([trajectory])
- DORA: [classification] ([trajectory])
- Wardley map last refreshed: [date]

### Loop 4 (Transformative): [Active / Dormant]
- Last eval run: [date]
- Pass rate trend: [improving / stable / declining]
- Escape hatch uses: [N] in last quarter

### Regression Warnings
- [Any active triggers from ${CLAUDE_PLUGIN_ROOT}/engine/feedback-loops.md]

### Goodhart's Law Check
- [Any metric/counter-metric divergences]

### Recommended Actions
1. [Most urgent feedback loop action]
2. [Second priority]
3. [Third priority]
```

## Canvas Output
Update `.claude/canvas/bvssh-health.yml` trend fields if BVSSH was assessed.
Update `.claude/canvas/dora-metrics.yml` trend fields if DORA was assessed.
Log review in `.claude/memory/product-journal.md`.

## Theory Citations
- Kim: Three Ways of DevOps (Second Way: amplify feedback)
- Argyris: Single/double/triple-loop learning
- Meadows: Leverage points in systems
- Goodhart: When a measure becomes a target
- Forsgren: DORA metrics as feedback signals
- Smart: BVSSH as holistic health feedback
