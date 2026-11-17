---
name: cynefin-classify
description: "Use when facing a new problem to classify its domain (Clear, Complicated, Complex, Chaotic, Confused) and select appropriate methods."
metadata:
  instruction_budget: "20"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Cynefin Classify Skill

Classify problem domain and route to appropriate methods.

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

1. **Describe the problem** in neutral terms.

2. **Ask diagnostic questions**:
   - Can we predict the outcome of actions? (Yes=Clear/Complicated, No=Complex/Chaotic)
   - Do experts agree on the approach? (Yes=Clear, Somewhat=Complicated, No=Complex)
   - Is the situation stable? (Yes=Clear/Complicated/Complex, No=Chaotic)
   - Has this been solved before? (Yes=Clear, Similar=Complicated, No=Complex)

3. **Classify** into one of five domains using cynefin-routing.md.

4. **Select methods** appropriate to the domain:
   - Clear: Best practice, checklists, automation
   - Complicated: Expert analysis, options evaluation, technical spikes
   - Complex: Safe-to-fail probes, experiments, continuous discovery
   - Chaotic: Stabilize, act, then reassess
   - Confused: Decompose into classifiable parts (formerly "Disorder"; "Aporetic" when deliberately entering this state)

5. **Cross-reference with Wardley evolution** if strategic context is available.

6. **Output**:
   ```
   ## Cynefin Classification
   Problem: [description]
   Domain: [Clear/Complicated/Complex/Chaotic/Confused]
   Confidence: [High/Medium/Low]
   Liminal: [Yes/No — is this between domains?]

   Rationale: [why this classification]

   Recommended methods:
   - [method 1]
   - [method 2]

   Warning signs of misclassification:
   - [what would indicate we got it wrong]
   ```

## Canvas Output
Update `.claude/diamonds/active.yml` with the `cynefin_domain` field for the relevant diamond.
If Wardley mapping was referenced, update `.claude/canvas/landscape.yml` component evolution stages.

## Liminal Zones (Snowden, 2019 — Confused followed in 2020)

Most real decisions happen in **liminal zones** — transitional states between domains where characteristics of two adjacent domains blend. If the classification feels uncertain, you may be in a liminal zone rather than a pure domain.

> **THERE IS NO LIMINALITY AT CLEAR, AND THAT IS NOT A GAP — IT IS WHY THE CLIFF EXISTS.** Snowden:
> *"The liminal line is open at the top, closed at the bottom, and **intersects all domains except
> Clear. Liminality in the Clear domain is not visible**, making the boundary between Clear and
> Chaotic a cliff or catastrophic fold."* He names exactly four liminal states — in **Complex**
> ("still uncertain but transiting to Complicated"), **Chaos** ("the **deliberate** removal of
> effective constraints for decision support and/or innovation"), **Complicated** ("where the
> analysis method or type of expertise is in question") and **Confusion** ("one of aporia, a state of
> authentic confusion i.e., being confused and aware").
>
> **So do not mark a Clear situation as liminal.** A `Clear → Complicated` row was listed here until
> 2026-09-20; it is removed. Believing you are easing out of Clear through a transitional zone is the
> precise belief the catastrophic fold punishes.
>
> Note also that the **Chaos** liminal state is a *deliberate entry*, not an involuntary slide — the
> opposite posture from the transition table below.

| Transition | What it feels like | Action |
|---|---|---|
| Complicated → Complex | "Experts disagree and new factors keep emerging" | Shift from analysis to experimentation |
| Complex → Chaotic | "Our experiments aren't converging, things are getting worse" | Stabilize first, experiment later |
| Chaotic → Complex | "We've stopped the bleeding, now what?" | Design safe-to-fail probes |
| Clear → Chaotic (catastrophic fold) | "Everything was fine and then it all collapsed" | See warning below |

### Clear→Chaotic Catastrophic Fold

The most important Cynefin warning: when a system in Clear becomes **complacent** — rigid rules, no sensing, "we've always done it this way" — it can **catastrophically collapse into Chaotic with no warning**. The transition is NOT gradual. There is no intermediate Complicated or Complex stage.

**Detection signs**: Over-reliance on best practices without questioning them. No feedback loops. "We don't need to monitor that." Dismissing edge cases as irrelevant.

**Mycelium connection**: Theory gates and `/mycelium:feedback-review` prevent complacent drift by requiring evidence refresh and active sensing at every transition.

*Source: Snowden (Cynefin evolution, cynefin.io, 2022+)*

## Decision Log (MANDATORY per G-P4)
**APPEND** a `### Cynefin Classification` entry to `.claude/harness/decision-log.md` with: domain classified, key indicators, method routed to, confidence in classification.

## Theory Citations
- Snowden: Cynefin framework (including Liminal zones and Confused/Aporetic domain renaming)
- Wardley: Evolution mapping

## Postflight: Verify-After-Write (claim matches state)

**Hard rule** (per the operating contract's Communication Rules, anti-pattern #7 *write-narration-verification* — mechanism Check 42, graduated v0.39.18; enforced surface expanded to this skill v0.44.0). This skill mandates multi-field canvas updates. Before narrating "updated / wrote / refreshed [canvas]" in any user-facing summary, RE-READ the value fields this skill's MANDATORY says to update and confirm they actually changed — not just `_meta.last_validated` or a freshness stamp. Each field you claim to have updated must reflect its new value. The symmetric half of the Read-before-Write Preflight: that one protects what gets read before a write; this one protects that the write matches the claim. Worked failures: 2026-06-05 #18 (`/dora-check` narrated "updated" with value fields unchanged) + #19 (`/retrospective` left a cycle-history aggregate un-propagated).
