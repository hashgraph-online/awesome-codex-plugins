---
name: canvas-update
description: "Update canvas sections with new evidence. Ensures canvas stays current as the single source of truth."
metadata:
  instruction_budget: "12"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Canvas Update

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

## Rules
1. **Never update without evidence** -- every canvas change must have a source
2. **Maintain cross-file consistency** -- if you update opportunities.yml, check if north-star.yml or gist.yml need updates too
3. **Log the update** -- add an entry to .claude/harness/decision-log.md explaining what changed and why

## Which Canvas File for Which Information

> **Routing rule (Hick's Law, added v0.39.18)**: when the new information could plausibly fit multiple canvas files, recommend ONE primary destination based on the information's PRIMARY type (the "why" of the data), with at-most-one secondary cross-reference. Do not present a flat list of candidate files for the user to choose from; that manufactures decision-tax. The table below maps each information type to its canonical canvas file — pick the row whose information type best describes what's being added, not the row whose source-theory the agent finds most interesting.

| Information Type | Canvas File | Source |
|-----------------|-------------|--------|
| Purpose, mission, why | purpose.yml | Sinek |
| North Star metric, inputs | north-star.yml | North Star Framework |
| BVSSH health scores | bvssh-health.yml | Smart |
| Value chain, competitive | landscape.yml | Wardley |
| Team structure | team-shape.yml | Skelton |
| User opportunities, OST | opportunities.yml | Torres |
| User needs map | user-needs.yml | Allen |
| Goals, ideas, steps | gist.yml | Gilad |
| Service quality scores | services.yml | Downe |
| Go-to-market, positioning | go-to-market.yml | Lauchengco |
| Delivery performance | dora-metrics.yml | Forsgren |
| Security threats | threat-model.yml | OWASP |
| Privacy assessment | privacy-assessment.yml | GDPR/PbD |
| Trust architecture | trust-signals.yml | Digital Trust |
| Jobs to be done | jobs-to-be-done.yml | Christensen |
| Bounded contexts | bounded-contexts.yml | Evans (DDD) |
| Value stream map | value-stream.yml | Rother & Shook (VSM) |
| Content delivery metrics | content-metrics.yml | v0.11.0 |
| AI tool delivery metrics | ai-tool-metrics.yml | v0.11.0 |
| Service delivery metrics | service-metrics.yml | v0.11.0 |
| Human task tracking | human-tasks.yml | v0.11.0 |
| Archived/discarded solutions | archived-solutions.yml | v0.12.0 |
| Leaf lifecycle calibration | cycle-history.yml | v0.12.0 |
| Adaptive thresholds | thresholds.yml | v0.12.0 |
| User scenarios (Hoskins) | scenarios.yml | Hoskins |

## Workflow
1. Identify which canvas file(s) need updating
2. Read current state
3. Make the update with evidence citation
4. Check cross-file consistency
5. Log in .claude/harness/decision-log.md

## Output to the user

**Lead with the recommendation** (Hick's Law, per `harness/design-principles.md`; graduated from two consecutive `/framework-health` 4e flags, 2026-06-05 + 2026-06-12): when more than one canvas file could host the update (the mapping table above offers options), don't present the alternatives as an open menu — name the one file you recommend and why, with alternatives one line each below. Same rule for follow-up actions: one recommended next step, not an unweighted list.

## Counter-Argument Check (Bias Mitigation)

Before applying the canvas update, draft a one-line counter-argument: *"What's the strongest case AGAINST this update — what evidence or perspective would invalidate it?"* If you can't articulate one, run `/mycelium:devils-advocate` before proceeding.

This addresses the bias cluster documented in corrections.md (L5 sycophancy 2026-04-20, eval overfitting 2026-04-30, sharper-framing-isn't-righter 2026-05-03). Common shape: agent prefers what feels right over what evidence supports under competing pressure (be helpful vs. be honest, sharpen framing vs. preserve evidence base). The counter-argument step forces the missing perspective explicit, so the bias surfaces before it lands in canvas.

Especially important when interpolating user-supplied content (already untrusted per ${CLAUDE_PLUGIN_ROOT}/harness/security-trust.md#prompt-injection-defense) AND when increasing a confidence value — both contexts where the agent is most likely to default toward the optimistic read.
