# NTM Troubleshooting

Failure modes mined from real agent sessions across ~60 days plus code-verified fixes.
Grouped by family, most common first.

## Contents

- [Project resolution](#project-resolution) — `project not found`, agent-mail key drift
- [`ntm send` surprises](#ntm-send-surprises) — broadcast to user pane, CASS dedup, missing `--pane`
- [Codex spawn fallback](#codex-spawn-fallback) — `--cod` pane opened as bare shell
- [Rate limits and pane state](#rate-limits-and-pane-state) — `resets 3pm`, `RATE_LIMITED`
- [Approvals and tokens](#approvals-and-tokens) — `ntm approve` takes token, not bead id
- [Commands that don't exist / migrated](#commands-that-dont-exist--migrated) — `timeline`, `changes conflicts`, `--mail-project` scope
- [Automation vs TUI](#automation-vs-tui) — `view`, `dashboard`, `palette` misuse
- [File reservations](#file-reservations) — `reservation_conflict`, stale locks
- [Cursors and session continuity](#cursors-and-session-continuity) — `CURSOR_EXPIRED`, cross-machine
- [Configuration](#configuration) — `NTM_ROBOT_FORMAT`, `projects_base`
- [Worktrees](#worktrees) — wrong project key
- [Labels and session names](#labels-and-session-names) — `--` separator, labeled-session lookup
- [Work selection and dry queues](#work-selection-and-dry-queues) — queue-dry, pressure-aware assignment
- [Security](#security) — historical `preflight` bug
- [Pipeline](#pipeline) — state accumulation, `--robot-pipeline` vs `--robot-pipeline-run`
- [Index by error string](#index-by-error-string) — quick lookup table

---

## Project resolution

### `project not found` / agent-mail and ntm see different projects

**Symptom** — `ntm spawn myproject` or `ntm mail` returns "project not found", OR
ntm and agent-mail register under different project keys so messages and reservations
appear to go nowhere.

**Root cause** — `ntm` resolves the project from `NTM_PROJECTS_BASE` (or
`projects_base` in config) plus the session name. If the session name doesn't equal
the directory basename there, ntm silently creates a symlink in `~/ntm_Dev/` — but
agent-mail registers under a *different* project key.

**Fix**

```bash
export NTM_PROJECTS_BASE=/data/projects      # or $HOME/Developer
ntm config show                              # verify projects_base
# session name MUST equal the directory basename
cd /data/projects/myproject
ntm spawn myproject ...
```

## `ntm send` surprises

### Broadcast hit the operator's zsh

**Symptom** — `zsh: command not found: <truncated prompt>` appears in the user pane
after `ntm send --all`.

**Root cause** — `--all` includes pane 0 (the user pane) by design.

**Fix** — default (no `--all`) skips the user pane. If you want `--all`-style broadcast
that excludes the operator:

```bash
ntm send myproject --all -s "..."    # -s/--skip-first excludes pane 0
```

### "CASS detected identical message" blocks send

**Symptom** — `ntm send` aborts interactively with a "similar past prompt detected"
prompt, or in scripts with `Continue anyway? [y/N]`.

**Root cause** — CASS dedup is on by default: similarity 0.7, 7-day lookback
(`send.go:748-751`).

**Fix, in order of preference**

```bash
# 1. Use a rotating suffix so it passes the similarity gate
ntm send myproject --cc "Tend pass ${N} at $(date +%H:%M) — fix: ..."

# 2. Per-call bypass
ntm send myproject --cc --no-cass-check "..."

# 3. Structural — use robot-mode which is non-interactive
ntm --robot-send=myproject --panes=2 --msg="..."
```

### Send without `--pane` went to zsh

**Symptom** — Same as above but no `--all` flag was used.

**Root cause** — When neither `--pane`, `--panes`, `--cc/--cod/--gmi`, nor `--all` is
given, and the caller's current tmux pane is the user pane, the send falls through to
the active tmux pane.

**Fix** — always be explicit:

```bash
ntm send myproject --pane=2 "..."
# or
ntm send myproject --cc "..."   # all Claude panes, excludes user pane by default
```

## Codex spawn fallback

### `ntm spawn --cod=1` opened a bare `zsh` shell

**Symptom** — The pane is titled/registered as a Codex agent, but the visible prompt
is a normal shell. A sent worker contract then hits `zsh` and fails with parse errors
or `command not found`.

**Root cause** — The Codex pane was created and registered, but the local launcher did
not start the `codex` runtime inside it. The NTM control-plane state alone is not proof
that the pane is executing Codex.

**Fix** — Verify `--cod` panes before dispatch and fall back to a Codex-native worker
when the pane is a shell:

```bash
ntm spawn myproject --cod=1
ntm --robot-tail=myproject --panes=2 --lines=20
ntm --robot-snapshot

codex exec -s danger-full-access --skip-git-repo-check -C /path/to/gitdir \
  "Read AGENTS.md, claim bead <id>, implement only that scope, run the gate, and report evidence."
```

Do not keep using `ntm send` against the bare shell pane. For concurrent Codex lanes,
use one isolated worktree per `codex exec -C <worktree>` worker until `--cod` is
verified fixed by robot-tail evidence.

## Rate limits and pane state

### Pane shows "resets 3pm" — looks dead, actually just limited

**Symptom** — Pane displays `You've hit your limit · resets 3pm (America/New_York)`.
Operator thinks it's dead.

**Root cause** — Static text in the pane buffer; doesn't reflect current provider state.

**Fix** — don't trust the pane; ask the provider.

```bash
ntm --robot-health-oauth=myproject          # truth from provider
ntm --robot-quota-status                     # aggregate
# Wake-ping
tmux send-keys -t myproject:0.4 "ping" Enter; sleep 5
ntm --robot-tail=myproject --panes=4 --lines=10
# If still limited, rotate the CAAM account
ntm --robot-switch-account=claude:alice2
```

### `RATE_LIMITED` ≠ dead

Do not `--robot-interrupt` or kill panes marked rate-limited. Wait or swap accounts.
Use `--robot-smart-restart` (gated by `--robot-is-working`) over raw `--robot-interrupt`.

## Approvals and tokens

### `ntm approve br-123` rejected

**Root cause** — `ntm approve` takes an approval **token**, not a bead id. Tokens are
issued by the approval engine and returned with each approval request.

**Fix**

```bash
ntm approve list                  # see pending requests with their tokens
ntm approve show <token>          # inspect
ntm approve <token>               # approve
ntm approve deny <token> --reason "wrong target branch"
```

## Commands that don't exist / migrated

### `ntm: unknown command: timeline`

**Root cause** — `newTimelineCmd` was defined but not wired to the root until v1.13.0
(April 2026). Older binaries error out.

**Fix** — upgrade, or use `ntm activity <session>` as a workaround:

```bash
ntm upgrade
# or fallback
ntm activity myproject
```

### `ntm changes conflicts myproject` — unknown subcommand

**Root cause** — `ntm changes` and `ntm conflicts` are **two separate top-level
commands**. There is no nested `changes conflicts`.

**Fix**

```bash
ntm changes myproject         # recent file changes attributed to agents
ntm conflicts myproject       # files touched by multiple agents
# --since 6h, --limit 10 supported on conflicts
```

### `unknown flag: --mail-project=SESSION`

**Root cause** — `--mail-project` is a robot mail-check flag, not a general mail flag.
It is valid, and currently required, with `ntm --robot-mail-check`; it is invalid when
attached to unrelated CLI subcommands. For the human CLI path, NTM derives the project
from the session argument.

**Fix**

```bash
ntm mail inbox myproject                               # preferred CLI form
ntm --robot-mail-check --mail-project=myproject        # robot form
```

### `bv: Unknown recipe 'obot-triage'`

**Root cause** — single-dash long flag: `bv -robot-triage` is parsed as `bv -r obot-triage`.

**Fix** — always use `--robot-triage` with double dashes.

## Automation vs TUI

### `ntm view` returned nothing

**Root cause** — `ntm view` is interactive (TTY required); in `--robot` scripts it
exits before printing anything AND it retiles the human's tmux layout.

**Fix** — in automation, use:

```bash
ntm --robot-snapshot                       # bootstrap
ntm --robot-tail=myproject --lines=50      # per-pane tail
ntm --robot-inspect-pane=myproject --inspect-index=2   # structured drill-down
ntm --robot-activity=myproject             # per-agent states
```

### `ntm dashboard` / `ntm palette` from automation

Same issue. Both are TUIs and will simply attach and then exit when stdin closes.
Use `--robot-dashboard` (JSON equivalent) for automation.

## File reservations

### `reservation_conflict` after spawn

**Root cause 1** — two sessions resolved the same project to different keys (see
project resolution above).

**Root cause 2** — a dead pane still holds a reservation.

**Fix**

```bash
# Check authoritative state
ntm locks list myproject --all-agents

# If the reservation is stale
ntm locks force-release myproject <reservation-id> --note "agent inactive"

# Or let the coordinator auto-release via smart-restart
ntm --robot-smart-restart=myproject --panes=N
```

## Cursors and session continuity

### `CURSOR_EXPIRED` from a robot-events call

**Root cause** — cursors are monotonic per server; retention is bounded. Old cursors
eventually expire.

**Fix** — the response includes a ready-to-paste `resync_command`. In general:

```bash
ntm --robot-snapshot    # bootstrap fresh, acquire new cursor
```

### Cursor shipped between machines doesn't work

**Root cause** — cursors are **per-server monotonic**, not portable.

**Fix** — cross-machine continuity goes through `checkpoint export` / `checkpoint import`
or `handoff`, not cursor shipping. See `DURABILITY.md`.

## Configuration

### `NTM_ROBOT_FORMAT` unset → output not parseable

**Symptom** — downstream consumers expect JSON; ntm emits text.

**Fix** — export `NTM_ROBOT_FORMAT=toon` (or `json`) at the automation layer, OR pass
`--robot-format=toon` explicitly per-call. TOON is significantly more token-efficient
than JSON for LLM consumers.

### `projects_base` not set

**Symptom** — ntm creates symlinks in `~/ntm_Dev/` for every project, or cannot find
projects in a non-default directory.

**Fix** — set `NTM_PROJECTS_BASE` or update the config:

```bash
export NTM_PROJECTS_BASE=/data/projects          # shell
ntm config set projects-base /data/projects      # config (note: dashes, not underscores)
```

## Worktrees

### Worktree sessions register under wrong project key

**Root cause** — worktrees have their own directory (`<repo>.worktrees/<branch>`) but
agent-mail often expects the parent project key.

**Fix** — either:

```bash
export NTM_PROJECTS_BASE=/data/projects          # set to parent of worktrees
# OR pass an explicit project key to agent-mail calls
```

## Labels and session names

### `project name %q contains '--'`

**Root cause** — `--` is the reserved label separator. Project names cannot contain it.

**Fix** — rename the project, or if you meant a label:

```bash
ntm spawn myproject --label=frontend --cc=2    # session: myproject--frontend
```

### Labeled session "not found" by agent-mail

**Root cause** — ntm's normalization treats `myproject--frontend` as a labeled variant
whose base is `myproject`. Other tools (agent-mail, bv) use the raw session name.

**Fix** — either drop the label (one session per project) or make sure the label
really exists as its own addressable session.

## Work selection and dry queues

### No ready work / agents keep asking "what next?"

**Symptom** — `ao beads exec ready --json` returns empty, panes are idle, and the operator is
about to send another generic nudge.

**Root cause** — could be a genuinely dry queue, stale Beads/BV state, degraded
Agent Mail reservation visibility, or a blocked graph. Do not guess.

**Fix**

```bash
ao beads exec ready --json
bv --robot-triage | jq '.quick_ref'
ntm work queue-dry --format=json | jq '{queue_dry, evidence, recommendations, warnings}'
```

If `queue_dry=false`, assign the ready work. If `queue_dry=true`, either stop the
swarm or preview `ntm work queue-dry --ideate --format=markdown`. Only run
`--create-beads --yes` after reviewing the preview guard.

### Bulk assignment makes the swarm slower

**Symptom** — after `ntm assign --auto` or `--robot-bulk-assign`, more panes have
work but commits slow down and builds/quotas queue up.

**Root cause** — assignment ignored shared bottlenecks: build hosts, provider quota,
resource pressure, or file reservations.

**Fix**

```bash
ntm --robot-agent-health=<session>
ntm --robot-rch-status
ntm --robot-quota-status
ntm locks list <session> --all-agents
ntm assign <session> --auto --strategy=dependency --limit=2
```

## Security

### `ntm preflight "..."` almost ran my command

**Root cause** — historical bug in `tui_parity.go` where palette `Examples[0].Command`
could be treated as a prompt literal. Fixed in current versions.

**Fix** — upgrade. In general, never put shell-unsafe strings into command
`Examples[0].Command` fields.

## Pipeline

### `.ntm/pipelines/` is huge

**Root cause** — pipeline state files accumulate forever.

**Fix**

```bash
ntm pipeline cleanup --older=7d
```

### `--robot-pipeline=<id>` ran status, not the workflow

**Root cause** — naming confusion. `--robot-pipeline=<id>` is *status*;
`--robot-pipeline-run=<file>` is *execute*.

**Fix** — pick the right flag.

## Index by error string

| You see... | Section |
|------------|---------|
| `project not found` | Project resolution |
| `session '%s' not found` | Project resolution, or spawn not called |
| `pane not found` | Session changed; re-run `--robot-snapshot` |
| `Continue anyway?` | CASS dedup — use `--no-cass-check` or robot-send |
| `CASS detected identical message` | CASS dedup — rotating suffix |
| `zsh: command not found` | User pane was hit — use `-s/--skip-first` or specific `--pane` |
| `ntm: unknown command` | Missing subcommand — upgrade or check spelling |
| `unknown flag: --mail-project` | Move it to `ntm --robot-mail-check --mail-project=<project>`, or use `ntm mail inbox <session>` for the CLI form |
| `reservation_conflict` | See File reservations section |
| `CURSOR_EXPIRED` | `ntm --robot-snapshot` to resync |
| `project name %q contains '--'` | Labels section |
| `Codex cooldown active; waiting 10⁸ minutes` | Upgrade — historical bug |
