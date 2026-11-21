---
name: bias-check
description: "Use before any research activity or significant decision. Reviews cognitive biases relevant to the current stage."
metadata:
  instruction_budget: "27"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Bias Check Skill

Pre-research and pre-decision bias review.

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

1. **Identify context**: What stage (L0-L5)? What activity (research, decision, evaluation)?

2. **Load stage-specific checklist** from ${CLAUDE_PLUGIN_ROOT}/harness/cognitive-biases.md for the current scale.

3. **For each bias on the checklist**:
   - Is this bias likely active in the current situation? (Yes/No/Maybe)
   - If Yes/Maybe: What specific mitigation will be applied?
   - Document the assessment.

4. **Check agent's own biases** (from ${CLAUDE_PLUGIN_ROOT}/harness/cognitive-biases.md agent section):
   - Sycophancy: Am I agreeing with the user when evidence says otherwise?
   - Recency: Am I overweighting recent context over earlier evidence?
   - Pattern matching: Am I assuming this is like something I've seen before without checking?
   - Completionism: Am I filling gaps with speculation rather than acknowledging uncertainty?

5. **Output bias briefing**:
   ```
   ## Bias Check: [Activity]
   Stage: [L0-L5]

   ### Active Risks
   | Bias | Risk Level | Mitigation |
   |------|-----------|------------|
   | ...  | High/Med/Low | ... |

   ### Agent Self-Check
   - Sycophancy: [OK/Risk]
   - Recency: [OK/Risk]
   - Pattern matching: [OK/Risk]
   - Completionism: [OK/Risk]

   ### Proceed? [Yes / Yes with caution / Pause and address]
   ```

6. **System-level bias diagnosis** (Meza):
   Before attributing resistance or poor outcomes to cognitive bias, check if the "bias" is actually a rational response to a badly designed system. Ask:

   | Phase | System Question | If Yes: Fix the System, Not the Person |
   |-------|----------------|---------------------------------------|
   | Awareness | Does the person know the desired behavior? | Fix communication, not cognition |
   | Motivation | Does the system reward the desired behavior? | Fix incentives, not mindset |
   | Ability | Can the person realistically do it? | Fix resources/process, not training |
   | Reinforcement | Is the behavior sustained by the environment? | Fix feedback loops, not habits |
   | Sustainability | Can it persist without ongoing intervention? | Fix structure, not willpower |

   If 2+ phases point to systemic causes, the primary intervention is system redesign, not individual debiasing. Update the bias briefing output above to flag the system-level root cause.

   The 5 phases above are a systemic diagnostic inspired by behavioral design models (COM-B, Fogg Behavior Model), not a named framework. They are prompts for investigation, not rigid steps.

   *Source: Robert Meza (The Bias Gap — diagnostic tool, aimforbehavior.com). Not to be confused with Thaler & Sunstein's "Nudge" theory.*

## When to Surface This Skill

This skill should be triggered:
- Before any research activity (interviews, surveys, data analysis)
- Before significant decisions at any diamond scale
- **At L5 market transitions**: Before launch tier classification and go-to-market planning, check for optimism bias (overweighting positive signals), confirmation bias (seeking validation of "ready to ship"), and anchoring (fixating on initial positioning)
- When `/mycelium:diamond-progress` or `/mycelium:diamond-assess` detects bias-related gate failures

## Canvas Output
Record bias check in `.claude/canvas/opportunities.yml` under `bias_checks` section with date, biases mitigated, and research design adjustments made.

## Recording the Bias gate
When this check feeds a diamond's `bias` gate, apply the pass criteria in
`${CLAUDE_PLUGIN_ROOT}/engine/theory-gates.md` §5 as written. **A planned mitigation counts as
documented**: a named action and the test, owner or later transition that will carry it out. A
disconfirming source that is cited and weighed has been sought, even though it is not yet resolved.
"A citation is not a resolution" is true, and it is not this gate's test: resolution is demanded by
the Cynefin gate (`start_experiment`, complex domain) and the Four Risks gate. Record `not-passed` for
what the fail column names, or for a named bias with no mitigation at all.

## Decision Log (MANDATORY per G-P4)
**APPEND** a `### Bias Check` entry to `.claude/harness/decision-log.md` with: activity assessed, active bias risks found, mitigations applied, agent self-check results.

## Theory Citations
- Kahneman: Thinking, Fast and Slow (System 1/System 2)
- Shotton: The Choice Factory (behavioral biases in decision-making)
- Torres: Continuous Discovery Habits (bias in research)
- Robert Meza: The Bias Gap (systemic bias reframing -- when "bias" is a rational response to a badly designed system)
