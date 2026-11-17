---
name: gist-plan
description: "GIST planning workflow. Structure goals into ideas, steps, and tasks using Gilad's evidence-guided framework."
metadata:
  instruction_budget: "32"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# GIST Planning

Replace opinion-based roadmaps with evidence-guided planning. Source: Gilad (Evidence Guided).

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

### 1. Set Goals (Quarterly)
- Derive from North Star input metrics or OKRs
- Format: "Improve [metric] from [current] to [target] by [date]"
- Maximum 3 goals per quarter
- Update .claude/canvas/gist.yml goals section

### 2. Generate Ideas (Ongoing)
- Ideas are hypothetical ways to achieve goals
- Most ideas fail (>80%) -- this is expected and planned for
- Generate many, hold loosely
- Store in .claude/canvas/gist.yml idea bank with ICE scores
- Never commit to an idea until evidence supports it

### 3. Score with ICE + Confidence Meter
Use `/mycelium:ice-score` to prioritize. GIST is Gilad's framework, and the ICE it uses is his: **ICE = Impact x Confidence x Ease**, each 0-10 (*Evidence-Guided*, ch. 3: the ICE score *"is simply the three values multiplied together"*). The three dimensions are Ellis's; the scale from 0, Ease as the effort to build the idea in full, and the Confidence Meter are Gilad's.
- Impact is the estimated improvement in the goal's metric (step 1). 0 is a legal Impact.
- Ease is the effort to build the whole idea, not to run the next step.
- Confidence is NOT gut feel. It is summed from the evidence you hold, with Gilad's Confidence Meter: the weights and caps are in `/mycelium:ice-score` Step 2, and this skill does not carry a second copy of them. An idea backed only by opinion scores near zero (0.01 for a conviction, 0.1 for others' agreement); only test results take it above 4.6; only launch data makes it 10.
- Rescore after every experiment, and whenever something is learned (Gilad, *ICE Done Right*, p. 15: *"every time you learn something new that changes your perspective on an idea [...] you should rescore it"*). Replace the three factors and the total together.
- The total is a hint for comparing ideas, never a pass mark: *"The scores themselves are meaningless — they’re just a way to compare ideas"* (*ICE Done Right*, p. 4). Always show it with its Impact, Confidence and Ease.
> *What this step said before, kept so a reader of an older canvas can place its numbers. Until 0.318.2: "Mycelium uses 0.0-1.0", with a 0.1-0.9 scale. In 0.318.2: Confidence 1-10 in bands (1-3 gut feel or desk research, 4-6 some direct evidence, 7-10 test-validated), and "The score is an average". Since 0.319.0: the product, with the meter. The bands were Mycelium's and are in no version of Gilad's meter; the average is Ellis's arithmetic (and one Gilad's ebook allows), not the one GIST's own materials use. A score written before 0.319.0 cannot be ranked against one written now: see `/mycelium:ice-score`, "Which ICE this is".*

### 4. Design Steps (per top idea)
- Steps are small, time-boxed activities that build evidence
- Each step has: hypothesis, method, success criteria, **MoSCoW priority**
- Tag each step as **Must** / **Should** / **Could** / **Won't** (DSDM):
  - **Must**: Non-negotiable. Delivery fails without this. All REVIEW checks apply.
  - **Should**: Important. Ship if time allows. All REVIEW checks apply.
  - **Could**: Nice-to-have. Cut first when timebox runs out. NUDGE checks only.
  - **Won't**: Explicitly out of scope for this cycle. Documented for future reference.
- Steps follow a confidence ladder: assessment -> exploratory experiment -> feature experiment -> launch
- Each step produces evidence that increases or decreases confidence
- If evidence is negative: pivot or kill the idea (sunk cost is irrelevant)
- For user-facing ideas, frame hypotheses in Lean UX format: "We believe [outcome] for [users] if [change]." (Gothelf)
- **When a delivery timebox is exceeded**: Flex scope using MoSCoW — cut Could/Won't before compromising Must/Should

### 5. Execute Tasks (Sprint-level)
- Tasks belong to the CURRENT step only
- Don't plan tasks for future steps
- Standard agile execution

### 6. Reprioritize (Continuous)
After each step completes:
- Update ICE scores based on new evidence
- Re-rank ideas
- Park the ideas that no longer make the cut: keep them in the idea bank with their score and what was learned, out of the working set. Gilad's Parked bank *"can be as long as needed and hold ideas indefinitely"*, and a test result is what sends an idea there: the test lets you *"decide whether to keep pursuing the idea (keep it in the working set) or drop it (move it to Parked)"* (*ICE Done Right*, pp. 9 and 11). **There is no ICE threshold.** Until 0.319.0 this line read "Kill ideas below threshold"; no source gives the total a threshold, and Mycelium's own was retired in the same release (`engine/adaptive-thresholds.md`).
- Surface new ideas from discovery work

### Shape Up: Appetite Over Estimates
Instead of asking "how long will this take?", ask "how much is this worth?" (Shape Up by Basecamp). Set an **appetite** — the maximum time you're willing to invest — then design the solution to fit within it. If the solution can't fit, narrow the scope, don't extend the timebox. This connects naturally to MoSCoW: appetite defines the timebox, MoSCoW decides what fits within it.

## Anti-Pattern: The Feature Roadmap
If your GIST board looks like a feature list with dates, you're doing it wrong. Goals are outcomes, ideas are hypotheses, steps are experiments.
