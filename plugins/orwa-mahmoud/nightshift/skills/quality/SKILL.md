---
name: quality
description: Find and work the project's applicable quality debt across tests, code, accessibility, contracts, documentation, dependencies, and security. Supports guided or automatic selection and review-first or run-direct execution.
---

Quality is the broad entry point for this project's quality work. It uses the same selection and
launch modes as Hunt.

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
Never search or guess. The shell's working directory persists
between Bash calls, so never use a bare path.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT`: use
`${CLAUDE_PLUGIN_ROOT}` on Claude Code; on Codex use `$PLUGIN_ROOT` when available, otherwise derive
it from the absolute path attached to this skill (`skills/quality/SKILL.md`). Substitute that
absolute path below; never search for the plugin.

**State map:** `punch-list.md` → owner-approved work active in this shift;
`drafting-table.md` → known work staged for a later shift; `parking-lot.md` → unresolved owner
decisions plus the default chosen so work continues; `work-orders.md` → timed catalog work composed
only through Hunt. Ordinary known plans never become work orders.

Read these before scanning:

- `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/execution-modes.md`
- every applicable entry under
 `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/shifts/`

Quality includes: lint, types, tests, flaky tests, coverage, dead code, TODO/FIXME debt,
accessibility, localization, API contract drift, documentation drift, CI warnings, direct
dependencies, and vulnerability advisories. `clear-quality-debt.md` remains the generic finite
core-tooling entry; specialized entries retain their own safety rules and definitions of done.
GitHub issue hunts are catalogued under Hunt and start from imported drafts. Quality does not import, search, or work GitHub issues.

## 1. Choose selection and launch

Ask two independent choices:

1. **Guided** (the owner chooses quality areas) or **Automatic** (Nightshift selects every
  applicable high-value area that fits the hours).
2. **Review first** or **Run directly**.

Automatic mode requires hours. Guided mode asks for scope and requires hours only when an
open-ended entry is selected. In review-first mode scanning is read-only and the clock starts only
after approval. In run-direct mode the clock begins immediately and findings are implemented
without another pause under the decision policy in `execution-modes.md`.

## 2. Detect and scan

Detect the stack from the gates catalog (monorepo-aware) when the work mode is repository,
including a plugin or marketplace manifest at the work-target root or under `plugins/<name>/`,
and inspect repository-owned tooling and evidence. In artifact mode inspect the persistent
folder's files and any existing manifests or reports; do not require git history or stack
detection that needs a repository. Completion in that folder is `$NS/receipts/`, not a git log.
Refuse to compose, cut, or arm when `$NS/receipts` exists but is not a usable directory.
If `$NS/work-mode` is missing and Setup would propose artifact, refuse to compose, cut, or arm and send the owner to Setup; do not `git init` a notes folder.
Refuse to compose, cut, or arm when work-mode is malformed.
Refuse to compose, cut, or arm when the work target cannot be resolved.
Skip quality-debt entries whose discovery surface is
absent. Do not `git init` a notes folder to make them applicable.
Skip documentation drift when work mode is artifact.
Skip TODO and FIXME debt when work mode is artifact.
Skip coverage hunt when work mode is artifact.
Skip tooling quality-debt entries when work mode is artifact. Then apply the discovery rules from every relevant quality
entry. Never install a tool
merely to manufacture findings. In review-first mode use report-only commands: no fix flags and no
writes. If `$NS/` does not exist, review-first may report, but any run-direct request must
stop and point to Setup (`/nightshift:setup` on Claude Code, or ask Nightshift to set up on Codex)
before work can be armed.

## 3. Rank and deduplicate

Map each finding to one catalog entry so work is never duplicated. In Automatic mode rank using
the shared mode contract, run finite entries first, and use at most one open-ended entry for useful
remaining time. In Guided mode keep only the areas and scope the owner selected.

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

Never write to the punch list on anything but an explicit **fix now** in review-first mode. Items there are the shift
the next start will work, so writing them on a survey puts work in front of the owner that nobody
agreed to — the box and the start belong together, or neither happens.

## 5. Run directly

When run directly was chosen, do not present the three-answer review menu. Compose one ordered Hunt
work order, append it to `$NS/work-orders.md` (heading, hours, and item; never
clobber orders already sitting there), then enter the same Hunt cut and Start lifecycle used by
**fix now**. Never write the punch list first. Follow
Start's entire preflight before cutting or arming, including the one-shift check, state and work
target validation, stale run-control markers, deadline handling, rules, and unattended permissions.
Only after it passes, cut the order and arm one shift with
`touch "$NS/.shift-armed"` on POSIX, or
`New-Item -ItemType File -Force "$NS\.shift-armed"` in native
Windows PowerShell; log the start, run the binding probe
(`: nightshift-binding-probe` on POSIX, `$null = 'nightshift-binding-probe'`
on native Windows), classify Codex `$NS/.shift-session` line 1 with
`ns_codex_identity_kind` from `$NIGHTSHIFT_PLUGIN_ROOT/lib/lib.sh` (native
Windows: `Get-NSCodexIdentityKind` after
`Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force`) before arming the watchman or beginning
item work, and arm the watchman exactly as the Start skill requires.
Unsupported or malformed identities refuse as Start requires — never resume
them. Claude Code uses
`$NIGHTSHIFT_PLUGIN_ROOT/runtime/claude/watchman.sh`; Codex uses
`$NIGHTSHIFT_PLUGIN_ROOT/runtime/codex/watchman.sh`; Cursor uses
`$NIGHTSHIFT_PLUGIN_ROOT/runtime/cursor/watchman.sh`; native Windows uses
`& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\start-watchman.ps1"`
`-Project "$NIGHTSHIFT_WORKSPACE" -HostName claude` (Codex: `-HostName codex`).
Implement and verify the selected entry contracts, and continue
until the finite work is clear or the shared deadline ends. Record significant decisions and
rollback instructions in `$NS/parking-lot.md`; never create a second
shift per quality area.

If the stack no longer matches the current `## Gates` block, say so in one line and point to
Setup (`/nightshift:setup` on Claude Code, or ask Nightshift to set up on Codex) — gates belong to
setup, not to this command.
