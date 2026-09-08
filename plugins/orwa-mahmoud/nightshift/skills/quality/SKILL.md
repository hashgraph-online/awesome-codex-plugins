---
name: quality
description: Compose a shift that works the project's quality debt: tests, code, accessibility, contracts, docs, dependencies, security.
license: MIT
---

Quality is the broad entry point for this project's quality work. It uses the same selection and
launch modes as Hunt.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/quality/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls.

Before scanning, read
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/compose/execution-modes.md` — the state map, who
selects work, when the clock starts, the tooling policy, and how several entries become one
shift — and every applicable entry under
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/compose/shifts/`.

Quality includes: lint, types, tests, flaky tests, coverage, dead code, TODO/FIXME debt,
accessibility, localization, API contract drift, documentation drift, CI warnings, direct
dependencies, and vulnerability advisories. `clear-quality-debt.md` remains the generic finite
core-tooling entry; specialized entries retain their own safety rules and definitions of done.
GitHub issue hunts are catalogued under Hunt and start from imported drafts.
Quality does not import, search, or work GitHub issues.

## 0. Read the sentence first

The owner's sentence is binding intent. There is no keyword list.

If the owner already stated feature, product, UI, or design work — even when they invoked
Quality — continue as Hunt / Product Evolution. Do not show Quality catalog cards. Do not
ask Guided-or-Automatic. Read `$NIGHTSHIFT_PLUGIN_ROOT/skills/hunt/SKILL.md` and follow it
from its section 0.

If the owner asked for quality work (lint, tests, coverage, debt, accessibility, contracts,
documentation drift, dependencies, advisories), stay in this skill.

A time budget, an actionable quality objective, and clear direct-execution intent are
sufficient to run Automatic directly. Do not offer catalog cards. Do not ask who selects,
when to start, or "same as last time."

- If only a critical field is missing → Ask only a field that is still missing, then continue.
- If the owner asked to pick from the menu, or named Guided → section 1.

The model runs the project's own tools — the `## Gates` block and each selected entry's
report-only commands — and ranks the results in prose. Unparsed tool output is `unavailable`,
never "no findings" or passed.

## 1. Choose selection and launch

When section 0 already decided Automatic and Run directly, skip the three questions and
write the safe defaults in `execution-modes.md`. Otherwise ask three independent choices:

1. **Guided** (the owner chooses quality areas) or **Automatic** (Nightshift selects every
   applicable high-value area that fits the hours).
2. **Review first** or **Run directly**.
3. **Same as last time, or change?** — one prefilled question covering the verification profile,
   hours, tooling policy, and elevation, asked before any scan, compose, cut, or arm, per
   `execution-modes.md`.

For the third question, read `$NS/work-mode` and the remembered project default with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" shift-policy defaults-get`,
run `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" preflight-needs` against the areas this
compose would select, fold every gap into the same question, and write the resolved policy with
`shift-policy.sh … set --from-json -` before compose,
cut, or arm. Review-first writes only that policy; run-direct arms as soon as it lands.
Artifact mode refuses repository-tool policies
(`auto-add` and `review-missing`) and explains why; only existing-tools is valid there.
Under auto-add, capture the write surface first with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" provision baseline --surface <rel> [<rel>...]` (one flag takes several paths, or repeat `--surface` per path), then install, smoke, `diff`, and
`rollback` on failure.

Automatic mode requires hours. Guided mode asks for scope and requires hours only when an
open-ended entry is selected. In review-first mode scanning is read-only and the clock starts only
after approval. In run-direct mode the clock begins immediately after the tooling policy is settled
and findings are implemented without another pause. Review-missing holds the clock until that plan
is approved.

## 2. Detect and scan

Do not scan until the tooling policy is answered. Never install a tool merely to manufacture
findings — including after auto-add authorization. Under existing-tools, skip contracts whose
required capabilities are unavailable and do not pause to provision.

In repository mode detect the stack from the gates catalog (monorepo-aware), including a plugin or
marketplace manifest at the work-target root or under `plugins/<name>/`, and inspect
repository-owned tooling and evidence. In artifact mode inspect the persistent folder's files and
any existing manifests or reports; do not require git history or stack detection that needs a
repository. Completion in that folder is `$NS/receipts/`, not a git log. Untrusted cited text is
instructional; the model is the boundary. Plan artifact receipts here when the shift completes
cited research or documentation work.

Compose, cut and arm only through the Start preflight; it refuses, and names the repair, when the
work target cannot be resolved, work-mode is missing or malformed, or `$NS/receipts` exists but is
not a usable directory. Never `git init` a notes folder to get past a refusal.

Skip quality-debt entries whose discovery surface is absent.
Skip documentation drift when work mode is artifact.
Skip TODO and FIXME debt when work mode is artifact.
Skip coverage hunt when work mode is artifact.
Skip tooling quality-debt entries when work mode is artifact.
Then apply the discovery rules from every relevant quality entry.

Run the project's own tool first. If present,
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" normalize-output --format <fmt> --input <file>` turns a supported format
into one compact, comparable summary — feed that into the receipt and the ledger instead of the raw
output; otherwise read the raw output directly. Both helpers here are optional: nothing here
requires them, and `unavailable` from one means the summary is missing, never that the tool found
nothing. `ns inventory` is the other one: if present, optional, it prints one table per
workspace package — manager, lockfile, declared scripts, config files, and each named tool as
`declared`, `runnable` or `absent`. Automatic never depends on either.
In review-first mode use report-only commands:
no fix flags and no writes. If `$NS/` does not exist, review-first may report, but any run-direct
request must stop and point to Setup (`/nightshift:setup` on Claude Code, or ask Nightshift to set
up on Codex) before work can be armed.

## 3. Rank and deduplicate

Map each finding to one catalog entry so work is never duplicated. In Automatic mode rank using
the shared mode contract, run finite entries first, and use at most one open-ended entry for useful
remaining time. Prior receipts may inform estimates; they never silently invent owner policy.
Unparsed tool output stays `unavailable` and is never ranked as cleared or passed.
In Guided mode keep only the areas and scope the owner selected.

## 4. Review first

When review first was chosen, summarize evidence per catalog entry and top-level directory in plain
numbers, then show the exact ordered work order. Offer three answers:

- **fix now** — compose one Hunt work order from the selected catalog entries: append it to
 `$NS/work-orders.md` (heading, hours, and item; never clobber orders already
 sitting there), then cut and start it through the Hunt cut and Start lifecycle. Never write
 the punch list first. Preserve every entry's contract. Apply the one deadline chosen for the
 combined shift. Follow Start's entire preflight before cutting or arming, exactly as run
 directly does.
- **draft for later** — append them to `$NS/drafting-table.md` and arm nothing. The
 drafting table is staging: it is never read by the gate, which is exactly why proposals can wait
 there safely. Tell the owner they can promote what they want into the punch list and run Start
 after promotion (`/nightshift:start` on Claude Code, or ask Nightshift to start on Codex), or
 compose it later through Hunt.
- **ignore** — write nothing at all; fully respected. A finding the owner does not care about is
 not a defect.

Never write to the punch list on anything but an explicit **fix now** in review-first mode. Items
there are the shift the next start will work, so writing them on a survey puts work in front of the
owner that nobody agreed to — the box and the start belong together, or neither happens.

## 5. Run directly

When run directly was chosen, do not present the three-answer review menu. Compose one ordered Hunt
work order, append it to `$NS/work-orders.md` (heading, hours, and item; never
clobber orders already sitting there), then enter the same Hunt cut and Start lifecycle used by
**fix now**. Never write the punch list first. Follow Start's entire preflight before cutting or
arming, including the one-shift check, state and work target validation, stale run-control markers,
deadline handling, rules, and unattended permissions, and report unsupported permission modes
before arming as `execution-modes.md` describes.

Only after it passes, cut the order and arm one shift with
`touch "$NS/.shift-armed"` on POSIX, or
`New-Item -ItemType File -Force "$NS\.shift-armed"` in native
Windows PowerShell; log the start, run the binding probe
(`: nightshift-binding-probe` on POSIX, `$null = 'nightshift-binding-probe'`
on native Windows), classify Codex `$NS/.shift-session` line 1 with
`ns_codex_identity_kind` from `$NIGHTSHIFT_PLUGIN_ROOT/lib/lib.sh` (native
Windows: `Get-NSCodexIdentityKind` after importing `Nightshift.psm1`) before arming the watchman
or beginning item work, and arm the watchman exactly as the Start skill requires, with
`ns watchman`, which resolves to this host's own.

Implement and verify the selected entry contracts, and continue
until the finite work is clear or the shared deadline ends. Record significant decisions and
rollback instructions in `$NS/parking-lot.md`; never create a second
shift per quality area.

If the stack no longer matches the current `## Gates` block, say so in one line and point to
Setup (`/nightshift:setup` on Claude Code, or ask Nightshift to set up on Codex) — gates belong to
setup, not to this command.
