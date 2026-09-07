---
name: nightshift
description: Run an accountable autonomous shift — work a punch list to completion, evolve a product from research, park decisions instead of asking, and leave receipts. Use when the user wants to work through a todo list autonomously, spend remaining agent usage, run overnight, polish or improve a product, research competitors and ship opportunities, add test coverage, find and fix everything, or keep reviewing until it is clean.
---

# nightshift — the brain

You are working a **shift**: a punch list the clock-out gate won't let you abandon. Your job is to
finish every item to its own standard, safely, leaving receipts. This skill is how you run one.

**State map:** `punch-list.md` → owner-approved work active in this shift;
`drafting-table.md` → known work staged for a later shift; `parking-lot.md` → unresolved owner
decisions plus the default chosen so work continues; `work-orders.md` → timed catalog work composed
only through Hunt. Never route an ordinary plan through Hunt, call later work “parked,” or put a
known task in the parking lot.

Resolve the host-opened project folder to an absolute `$TASK_ROOT`: use `${CLAUDE_PROJECT_DIR}` on
Claude Code; on Codex honor Nightshift's `${CODEX_PROJECT_DIR}` recovery override when present,
otherwise capture `pwd -P` before any other shell call. Resolve `$TASK_ROOT/.nightshift-link` when
present and call the validated absolute target `$NIGHTSHIFT_WORKSPACE`; otherwise set
`NIGHTSHIFT_WORKSPACE="$TASK_ROOT"`.

Bind the Nightshift directory once: `NS="$NIGHTSHIFT_WORKSPACE/.nightshift"`. On native Windows,
`$NS = Join-Path $NIGHTSHIFT_WORKSPACE '.nightshift'`. After this bind, Nightshift files are
`$NS/<name>` for every read, write, and shell command. Catalog and owner-facing prose may use the
short names (`punch-list.md`, `parking-lot.md`, `STOP`). Never re-resolve. Helpers that take
`--project` or `-Project` still receive `"$NIGHTSHIFT_WORKSPACE"`.
Never search or guess.
The shell's working directory persists between Bash calls, so never rely on a bare path.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT`: use
`${CLAUDE_PLUGIN_ROOT}` on Claude Code; on Codex use `$PLUGIN_ROOT` when available, otherwise derive
it from the absolute path attached to this skill (`skills/nightshift/SKILL.md`). Substitute that
absolute path below; never search for the plugin.
On native Windows, resolve the same plugin root from `$env:CLAUDE_PLUGIN_ROOT` or `$env:PLUGIN_ROOT`.

If `$NS/` doesn't exist yet, tell the user to run Setup, then Start.
Give the host-native spelling: `/nightshift:setup` and `/nightshift:start` on Claude Code, or ask
Nightshift to set up and start on Codex. Those skills own scaffolding and preflight; this skill
owns the work.

## Persistent-workspace boundary

Nightshift is an engineering workflow for a persistent project workspace. If the resolved project
root is under `/workspace/scratch/`, stop before setup or shift work and give the OpenAI-native
redirect from the setup skill: open the project you want Nightshift to change in Codex (or connect
Codex to its GitHub repository), then mention Nightshift there. Never create durable-looking run
state in a disposable ChatGPT scratch workspace, and never claim those temporary files affect or
preserve the user's repository. A non-git project outside that explicit scratch path remains valid.

## The contract is above `## Items`

`$NS/punch-list.md` has a contract section, then `## Items`. The contract binds YOU for the
whole shift: **never edit, trim, or reword it, and never delete an item** — not even to end the
shift. The owner may change the `## Gates` block anytime, so **re-read the punch list at the start of
every item; never cache it.** If you ever notice the contract or an item was altered, restore it
from git before continuing. In repository mode that is the work-target history, or
`git -C "$NS"` when the owner opted into a local receipts repo. In artifact mode restore only
from that receipts repo when it exists; do not `git init` the notes folder to invent history.
On native Windows use `git -C` against `$NS` when Git is installed — the same receipts repo.
If `$NS/punch-list.md` has no git history, park the conflict and keep the on-disk file.

## One item at a time

Top to bottom, one item, no batching:

1. **Read** the item and the current `## Gates` block.
2. **Build** it fully — production-ready, no stubs, no "documented for later". If you can do it now,
  do it now. Effort is never a reason to defer: "this deserves a focused session" — this IS the
  focused session. Only correctness justifies narrowing an item.
3. **Gate** — run the item gate (the `## Gates` commands) right before the commit or artifact
  receipt. It must be green. No suppressions without a written reason beside them.
4. **Receipt** — repository mode: one conventional commit in the work target, local by default.
  Artifact mode: one completion receipt in `$NS/receipts/` via
  `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/write-receipt.sh"` (native Windows:
  `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\write-receipt.ps1"`), recording the item, outputs,
  verification, and sources. Never tick without that receipt. Push yourself only when the punch
  list explicitly says to.
5. **Tick** the box to `- [x]`. Never fake a tick: the box means the work behind it is complete.

Cited research, SEO audits, sourced documentation, and research synthesis follow
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/cited-research.md`. Verify those reports with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/check-report.sh"` (native Windows:
`& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\check-report.ps1"`) before the commit or artifact receipt.

Then the next item. Item anatomy: one top-level checkbox per task, plain `-` sub-bullets, its own
**Verify** and **Commit** lines. Promote owner-approved work from
`$NS/drafting-table.md` into `## Items`; never invent scope the owner
didn't ask for.

## Park, don't ask

A shift runs while the owner sleeps. If a decision is genuinely theirs, do NOT ask — the gate denies
it anyway. Instead: choose the most sensible production-grade default, record the decision and your
reasoning in `$NS/parking-lot.md` in plain language, and keep working.
The owner reviews it over coffee. Known later work is not a decision: stage it in
`$NS/drafting-table.md`.

When the owner selected **run directly**, that is explicit authority to choose and implement
reasonable, reversible production defaults within the stated scope and time. Do not turn ordinary
code, API, design, localization, or cleanup judgments into blockers merely because alternatives
exist. Preserve compatibility or provide migration and rollback, verify the result, and record the
choice, evidence, alternatives, shipped result, and rollback in
`$NS/parking-lot.md`. Stop only for
publishing, merging, deploying, production-data deletion, secrets exposure, spending, or legal/licensing
decisions outside the coding-work authorization.

## Snag log discipline

Before reporting findings in a review or walkthrough, read
`$NS/snag-log.md` and dedupe against ALL seen
— fixed AND rejected — so a later cycle never re-reports an earlier one. Append dispositions after
acting: `finding · evidence · fixed/rejected-because/accepted-tradeoff · date`.

## Walkthroughs

A walkthrough is one open box that stays open while a scan → fix → re-scan loop runs. It ends only
at its declared condition:

- **Coverage hunt** — write meaningful tests until quitting time. Coverage is a tripwire, never a
 target; no padding, exclusions need a reason.
- **Defect hunt** — review, dedupe against the snag log, fix behind the gate, re-review. Stop when a
 full pass finds nothing NEW (converged) or at quitting time. **Zero new findings is success** —
 stop even with time on the clock.
- **Product evolution (standing loop)** — understand the product, research its space, rank an
 evidence-backed opportunity map, and build the strongest complete improvements that fit the
 clock on an isolated branch or, in artifact mode, inside the persistent folder. Lint and tests verify the work; they do not choose the roadmap.
 Small fixes through substantial features are valid, but the shift never merges itself and never
 leaves a half-built production path. The single `building` opportunity is the continuation
 record: read it first on resume and keep its completed work, rejected paths, exact next action,
 and remaining verification current at meaningful boundaries. Only quitting time ends the item.

Log one line per cycle to `$NS/shift-log.md`. A cycle that finds
nothing new is success, not idleness.

## Quitting time — a whistle, not an axe

If a deadline is set, past it you start NOTHING new — but you FINISH the unit already in your hands
(the current item, or the current walkthrough cycle), clock out orderly, and stop, even slightly
over. The gate makes this mechanical; you make it graceful. Deadlines belong to open-ended work: a
finite item list ends at its last tick; never start a walkthrough without one.

## Red-tag yourself when stuck

If you catch yourself unable to finish an item — looping or blocked on an external constraint — **red-tag it
yourself**: record the owner decision in `$NS/parking-lot.md` as
`stalled — needs human`, note why, and move to the next
item. Do not loop. The gate's stall warning is the backstop, not the plan.

## Ending the shift

You may stop only when every box is `- [x]`, or the owner issues a stop-work order
(`$NS/STOP`). If a shift must end mid-work, clock out orderly: a
`wip:` commit (repository mode) or an artifact receipt (artifact mode)
plus one handover line in `$NS/shift-log.md`, then
stop. History is append-only on shift — no `reset --hard`,
`rebase`, `amend`, or force operations; the night's receipts must survive to morning.
