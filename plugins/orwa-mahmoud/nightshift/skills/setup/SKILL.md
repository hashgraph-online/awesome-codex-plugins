---
name: setup
description: Scaffold .nightshift/ and propose quality gates for this stack in at most four questions, with every default on one screen; asks, never imposes.
license: MIT
metadata:
  internal: true
---

Set up Nightshift in this project in at most four questions. Scaffold first, then ask the
questions in section 3, apply every answer in the same turn, then print a summary that ends with
the one sentence that starts a shift.

The four state files and what each holds are in
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/shift/state-map.md`. Ordinary plans belong in the drafting table, never in Hunt or the parking lot.

Resolve `$NIGHTSHIFT_PLUGIN_ROOT` to the copy this host installed, as an absolute path.
On Claude Code that is `${CLAUDE_PLUGIN_ROOT}`, on Cursor `${CURSOR_PLUGIN_ROOT}`, and on
Codex `$PLUGIN_ROOT` when set. A skill loaded from a copy another host installed is the
wrong runtime — use the copy under this host's plugins directory. When none of those is
set, use the absolute path this skill was attached from (`skills/setup/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls. Each `$NS/...` path below is where the current layout keeps that file;
`ns path <key>` prints where this workspace keeps it, and `ns path --list` names every key.

Once the workspace and work target are resolved, the bundled mechanical scaffold is
`ns setup --work-target "$WORK_TARGET" --mode "$WORK_MODE"`, which exists on native Windows only;
on every other host this skill writes the same templates itself, as below.
It copies only absent files, writes state version 2 for a new site, persists the work target and
work mode (`-Mode repository` or `-Mode artifact`), and keeps `$NS/` private. It refuses a notes
folder under default repository mode: `use -Mode artifact for a notes folder that is not a Git repository`.
On an existing site at an older state-version its `migration` field describes the move into the
current layout, exactly as the preview below would. Read its output back rather than restating it.
The skill still owns every owner choice below; the
script asks nothing and never invents gates, permissions, profiles, migration approval, a receipts
choice, or a tooling policy.

If the user explicitly identifies a different existing workspace containing `.nightshift/`, show
both absolute paths and ask for confirmation. On yes, run
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" link-workspace --host-root "$TASK_ROOT" --workspace "$PROPOSED_WORKSPACE"`.
The pointer is local-only and state remains in the authoritative workspace; never copy it.

## 0. Reject disposable ChatGPT scratch workspaces

Before creating or changing any file, resolve the project root to an absolute path. If it is under
`/workspace/scratch/`, this is a disposable ChatGPT scratch workspace that cannot affect the user's
repository. **Stop immediately: create no `$NS/` directory, rules, settings, receipts repo,
or other files.** Tell the user directly:

> Nightshift needs a persistent software project workspace. This ChatGPT conversation is using a
> temporary workspace, so files created here will not affect your repository.
>
> Open your project in Codex (a Git repository or a persistent local folder), or start Codex connected to its GitHub repository. Then mention
> Nightshift and say: “Set up Nightshift in this project.”

Do not mention Claude Code in this ChatGPT-specific redirect: the user is already in an OpenAI
product, so give them the shortest OpenAI-native route. Do not infer “temporary” merely because the
project is not a git repository — local non-git projects and the recommended parent-workspace
layout remain valid. The explicit disposable scratch path is the stop signal.

Detect the work mode and the work target. When the choice is ambiguous (several child repositories,
or a folder that could be either mode), explain it and ask before persisting it; that is section
3's first question. An obvious single repository is not asked: it is stated in the summary. Use
`ns_propose_work_mode` (POSIX) or `Get-NSProposedWorkMode` after importing
`Nightshift.psm1` (native Windows):

- `repository` — the workspace is a Git repository, or exactly one immediate non-hidden child is. Skip a symlink or reparse child; it is not a nested checkout.
  several child repositories still mean repository mode; show the choices and require an explicit
  target, never guess.
- `artifact` — there is no Git repository here. The persistent folder itself is the work target
  (research, docs, audits, planning). Say so plainly: gates, commits, and stack detection that
  require Git do not apply; complete each item with a receipt under `$NS/receipts/`.
  Completion in that folder is `$NS/receipts/`, not a git log.
  When `$NS/receipts` exists but is not a usable directory, say so and do not treat artifact setup as complete.
- scratch (`ns_propose_work_mode` status 2, or `Get-NSProposedWorkMode` throwing) — stop; create
  nothing.

Never persist an ambiguous mode until the owner confirms. Never `git init` a notes folder to change an artifact proposal into repository mode. Then write `$NS/run/work-mode` as `repository` or
`artifact` (one word, one newline) and `$NS/run/work-target` as the absolute canonical path of the
chosen folder. On POSIX: `ns_record_work_target "$NIGHTSHIFT_WORKSPACE" "$WORK_TARGET" "$WORK_MODE"`.
On later setup runs, validate and retain that mode and target unless the owner explicitly changes
them. Repository mode: stack detection, Git checks, gates, commits, and verification operate in
the work target. Artifact mode: inspection, edits, and verification operate in that folder without
pretending it is a repository.

## 1. Scaffold `$NS/` (never clobber an existing shift)

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" scaffold
```

It writes the files every shift uses that are not already there (the punch list, the parking lot,
the snag log, the drafting table and the shift log) and reports `wrote <path>` or `kept <path>`, so
a name the owner already has is left exactly as it is and a second run is a safe repair. Read its
output back. The work orders and the product notebook wait until something needs them: Hunt runs
`ns scaffold work-orders` when it stages an order, and cutting a product-evolution item runs
`ns scaffold product`. The copies carry resolved absolute paths — a person pasting a command out of
their own punch list has no `$NS` — and the shipped templates are unchanged. Never write those
tokens into `rules.json`: revival and clock-out text stay owner-editable, and the gate qualifies
bare `.nightshift/` mentions at injection time.

**State version.** `$NS/state-version` is the schema marker, and it names the layout: this plugin
writes version `2`, which groups `$NS/` by purpose. The scaffold writes it into a `$NS/` it creates.
A site at version `1`, or with no marker (legacy `0`), keeps every state file at the top of `$NS/`
and goes on working there; offer the move as a line on section 3's defaults screen, with

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" migrate-state
```

which only previews: each file with its old and new path, every link it rewrites, every conflict,
and what it leaves in place. Show that preview, and run it again with `--apply`
only after an explicit yes. It refuses while a shift is armed, a watchman is alive or a lock is
held, and it never deletes or overwrites. Never move a state file by hand. A marker newer than `2`, or a malformed
file, fails closed: print the diagnostic, do not rewrite or downgrade it, and do not continue
scaffolding as if the site were current.

## 2. Private by default

Keep run state out of git. If `$NIGHTSHIFT_WORKSPACE` is itself a git repo, append a line
`.nightshift/` to `$NIGHTSHIFT_WORKSPACE/.gitignore` (create the file if needed; do not duplicate
the line). If it is not one — the recommended layout, where the code repo sits a level below —
`.nightshift/` is already outside every repo, so write no `.gitignore` there. Run history is the
owner's; it never enters the project repo.

Copy `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/nightshift-rules-template.json` to
`$NS/rules.json` as-is if it does not already exist, so section 3 shows real values (section 5
covers the file).

## 3. The questions — at most four

Ask these in this order and nothing else. Skip any whose answer is already clear. Never split one
into several turns.

1. **Work target** — only when it is ambiguous, as above.
2. **Gates** — the detected proposal, answered with accept, edit or none (below).
3. **Defaults** — every remaining choice on one screen (below), answered once.
4. **Copy-in files** — only when the owner chose a shift worktree: which ignored files the tests
   need, such as `.env.test`. List only those in `shift.copyIn`; never propose `.env` itself.

A rerun asks the same questions with the owner's current values in place of the defaults, and
changes only what the owner names.

### Gates

Detect the stack in the persisted work target from
`ns catalog-index --catalog gates` and
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/compose/gates-catalog.md`
(monorepo-aware). Read only the stacks whose Detect matches, in the order the index prints them.
An owner's stack of the same key replaces the shipped one; say where each proposal came from.
A plugin or marketplace manifest may sit at the work-target
root or one directory down at `plugins/<name>/.claude-plugin/` /
`plugins/<name>/.codex-plugin/`; that nested layout is a match when no
language-stack row already won. Show the detected proposal with three first-class answers:

- **accept** the proposal as-is,
- **edit** it — add, remove, or replace with THEIR own commands (any shell command is a valid gate),
- **none** — fully respected: the shift runs without automated checks.

Artifact mode has no stack to detect: skip this question.

### Defaults

One list, each line with its value and one line of meaning. The owner answers **accept all**, or
names what to change in the same reply ("worktree yes, 6 hours, deny sudo"). Apply the changes in
that turn; do not ask a second round.

| Line | Shipped value | Meaning |
| --- | --- | --- |
| Receipts repo | no | a local-only git repo inside `$NS/`, so every punch-list change has history; never pushed, never touches the project's history |
| Shift worktree | no | each shift works in its own git worktree and branch, so the owner's checkout and uncommitted edits stay untouched; show the proposed `shift.prepare` command beside it |
| Site inspection | hourly | the heavier batch (coverage, dead code, Sonar) every N items or H hours; only when gates were accepted or edited |
| Verification profile | `fast` | `fast`, `balanced`, `strict`, or `custom`: when the `## Gates` commands run |
| Typical hours | none | the hours a composed shift gets when the owner names none |
| Execution | `run-direct` | a composed shift starts at once; `review-first` shows it for approval first |
| Tooling policy | `auto-add` | `auto-add` adds standard development tools the project selects; `review-missing` or `existing-tools` hold back |
| Recovery | `host-default` | a stalled or finished worker is revived and clocked out under the host's own permissions; `inherit-recorded-scope` restores a recorded Codex sandbox only |
| Elevation | all allowed | `sudo`, containers, global packages, daemons, external logins; name any to deny |
| Evidence | check `off`, review `off` | whether a missing evidence file blocks a tick, what happens when it cannot be produced, and whether the agent reviews its own evidence |

The proposed `shift.prepare` command comes from the work target's lockfile and installs its
dependencies without changing it (`pnpm-lock.yaml` → `pnpm install --frozen-lockfile`,
`package-lock.json` → `npm ci`, `yarn.lock` → `yarn install --immutable`, `uv.lock` → `uv sync`,
`poetry.lock` → `poetry install`, `Gemfile.lock` → `bundle install`, `Cargo.lock` → nothing).

Present the receipts repo neutrally: never describe the repo as recommended; the default is no.

**Artifact mode** shows only the lines valid there: receipts repo, typical hours, execution,
recovery and evidence. It persists `fast` and existing-tools without showing them: a notes folder
has no repository toolchain to add, and repository-tool policies (`auto-add` and
`review-missing`) are invalid there.

**What this version also offers goes on the same screen**, one line each, never a separate question:

- a state move, when `$NS/state-version` is older than `2` (section 1): the
  `ns migrate-state` preview, applied only after an explicit yes;
- keys this version added to the rules template that the owner's file lacks (section 5);
- a contract restore, when the owner's punch-list contract differs from the shipped one (section 5);
- the shipped rule profiles, any one of which may replace the screen's values (section 5).

## 4. Applying the answers

- **Receipts repo** — on yes: if `$NS/.git` does not exist, run `git -C "$NS" init` rather than
 `cd`-ing there. The run state is then versioned in its own local-only git repo.
 Ensure `$NS/.gitignore` contains `STOP` and `/run/`, the runtime's own folder, anchored so each
 archive folder's `run/` records stay versioned; rewrite a bare `run/` line as `/run/` and
 preserve the other lines. A site still at version `1` keeps the runtime's files at the top of `$NS/`, so there it
 names the transient markers instead: `STOP`, `.stall`, `.notified`, `deadline`, `.session-end`,
 `.shift-pulse`, `.mint-failed`, `.shift-session`, `.shift-session.tmp.*`, `.shift-worker`,
 `.shift-lease`, `.shift-lease.tmp.*`, `.mutex-scope`, `.mutex-scope.tmp.*`, `.watchman`,
 `.watchman-tick`, `.budget.tsv`, `.item-sessions/`, `.plan-room`, `.lock.d/`, and `.lease-lock.d/`; migrate-state adds `/run/` with the move. Make one initial commit only when setup created the receipts repository.
 Creating the repo does **not** turn on headless auto-commit — that is `receiptsAutoCommit`
 in `rules.json`, shipped `false`; the owner commits the receipts tree when they want.
 **Never add a remote to it, never push it.**
 On native Windows, rerun the bundled scaffold with the same
 `--work-target` plus `--receipts`; the idempotent pass creates only this local receipts repo.
- **Shift worktree** — on yes set `shift.isolation` to `worktree`, `shift.prepare` to the proposed
 command (or the owner's), and `shift.copyIn` to question 4's answer, in `$NS/rules.json`.
- **Gates** — write the accepted or edited commands and the site-inspection interval into the
 `## Gates` block of `$NS/punch-list.md`, replacing the placeholder. On none, leave the placeholder
 as-is. The block is plain markdown the owner may edit anytime; run Setup again
 (`/nightshift:setup` on Claude Code, or ask Nightshift to set up on Codex) to re-detect after a
 stack change. The contract's immutability binds the agent, not the owner.
- **Verification profile, hours, execution, tooling** — persist with
 `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" shift-policy defaults-set --verificationProfile <name> --hours <n|null> --toolingPolicy <name> --execution review-first|run-direct`.
 The helper writes the `shift` block of `$NS/rules.json` — the one file the owner edits — and
 reports what it stored; never put the answer in the punch list. It only prefills what Hunt and
 Quality compose with; either skill may change it for a single shift.
- **Recovery, elevation, evidence** — write only the keys the owner changed
 (`recovery.launchScope`, `elevation.<category>.policy`, `receipts.evidence.check`,
 `receipts.evidence.unavailable`, `receipts.evidence.review`) into `$NS/rules.json`, keeping every
 other value byte for byte.
- **State move, template keys, contract, profile** — apply each only on the owner's explicit yes,
 as section 1 and section 5 describe.

## 5. Permissions — configured by the owner

An unattended shift cannot answer permission prompts. Say once that the owner configures
permissions directly in the host before starting unattended work; this is a statement, not a
question. Never write permission modes,
allowlists, or approval settings, and never enable permission bypass on the owner's behalf.
Nightshift adds no restriction of its own beyond what the host permits unless the owner sets one.

Recovery uses `recovery.launchScope` in `$NS/rules.json`. The shipped `host-default` adds no
permission arguments and uses the owner's independently configured host permissions; it does not
promise the same scope as the original session. `inherit-recorded-scope` restores a recorded
restricted Codex sandbox when supported; missing or unsupported scopes refuse recovery. The legacy
`host-grant` value is refused. Never change the active session's permissions. If the owner keeps
interactive approvals, say that a prompt or denial can leave unattended work needing their
attention.

## 6. The rules file — every knob in one place

`$NS/rules.json` is the owner's one config file, defaults inline. It lives in nightshift's own
folder on purpose: everything nightshift is in one place, kept out of repo history by the same
`.nightshift/` gitignore, versioned by the receipts repo when one exists — and deleting `$NS/`
removes all of nightshift, rules included. Validate the file with
`jq -e 'type == "object"'` and report a broken one plainly — never half-apply it. On native
Windows, validate with `Get-Content -Raw -LiteralPath "$NS\rules.json" | ConvertFrom-Json`;
PowerShell's JSON parser is built in, so native setup has no `jq` or Python prerequisite.

The template's `$schema` field points at
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/nightshift-rules.schema.json` so editors
catch invalid names, types, and values; it is ignored at runtime. Editor discovery is documented
in https://github.com/orwa-mahmoud/nightshift/blob/main/docs/knobs.md.

The rules file is portable across hosts, so never generate a host-specific copy. Its `toolDeny`
map carries three native question names: `AskUserQuestion` for Claude Code, `request_user_input`
for Codex, and `AskQuestion` for Cursor. A non-empty value denies that exact tool with the owner's
message; an empty value allows it. All three entries stay present so deleting a key can never
activate an invisible default. JSON has no comments; the schema descriptions and
https://github.com/orwa-mahmoud/nightshift/blob/main/docs/knobs.md#tool-rules are the inline help.

The hooks read this file directly on every tool call: an owner's edit applies from their very next
action. Nothing is synced anywhere, nothing needs a restart, and there is no second copy. Env vars
of the matching names (`NIGHTSHIFT_FORBIDDEN_COMMANDS`, `NIGHTSHIFT_TOOL_RULES`, …) remain
session-start overrides for tests and one-off exceptions — say so only if asked. If Claude Code's
`$TASK_ROOT/.claude/settings.local.json` still carries `NIGHTSHIFT_*` env keys an earlier version
synced from this file, offer to remove them on the defaults screen: the file is the one copy.

**Local rule profiles.** The defaults screen may list the shipped examples in
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/profiles/` (every version-1 or version-2 JSON
file there). Preview the one the owner names with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" apply-profile --profile <name> --mode fill|replace`.
The helper prints the preview and the complete next file; read it out rather than describing it.
Applying requires an explicit yes and `--apply`. Refuse `--apply` while armed. Profiles are a one-time local copy — no network, no
subscription. After applying a profile,
write a preset receipt from
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/receipts/cycle-specialist-evidence.md` so branch mode,
allowed sources, verification profile, receipt retention, resource limits, and direct-mode
boundaries trace to `rules.json`. Owner rules remain authoritative;
presets never capture hidden policy.

**Template evolution — offer, never impose.** On a re-run with the file already present, compare
the shipped template's top-level keys and its nested `toolDeny` keys to the owner's file (read the
JSON in the skill; do not ask the owner to install `jq` or Python; on native Windows,
`(Get-Content -Raw -LiteralPath "$NS\rules.json" | ConvertFrom-Json).PSObject.Properties.Name`
and the same for `.toolDeny`). List each missing key with its default on the defaults screen —
"this version added `request_user_input`; add it?" — and never
touch a value the owner already has. A missing native question key is a configuration error, not
permission to invent a fallback.

Same posture for the contract: if the shipped punch-list template's contract (the text above
`## Items`) has changed since the owner's copy was scaffolded, or the owner's contract is
leftover campaign text (a finished branch, release, or issue-close list), put one line on the defaults
screen that shows the diff and offers to restore the template contract. The owner's
wording wins every conflict, and a punch list with open boxes is never touched at all.
Never rewrite without an explicit yes.

## 7. Summarize

Print the workspace-state path and resolved work target, what was scaffolded, whether a receipts
repo was created, the gates that were written (or that none were), and the defaults now in
`$NS/rules.json`. End with the one sentence that starts a shift, for example: say *"improve this
project for 5 hours"*. Hunt composes it from the catalog and starts. Hand-written work goes in
`$NS/staging/drafting-table.md`, is promoted into the punch list, and starts with
`/nightshift:start` on Claude Code, or by asking Nightshift to start on Codex. Name
`/nightshift:customize` for every other setting; editing `$NS/rules.json` by hand or asking in
plain words works the same. The open-ended product-evolution shift keeps its evidence and ranked
work in `$NS/product/product-research.md` and `$NS/product/opportunity-map.md`, written the first
time such an item is cut.
