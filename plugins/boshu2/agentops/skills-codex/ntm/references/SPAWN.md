# `ntm spawn` — Exhaustive Reference

## Contents

- [Project resolution (read this first)](#project-resolution-read-this-first)
- [Agent-count flags](#agent-count-flags) — `--cc`, `--cod`, `--gmi`, `--agy`, `--cursor`, `--windsurf`, `--aider`, `--oc`, `--local`/`--ollama`
- [Pane layout](#pane-layout) — `--no-user`, `--worktrees`, `-l/--label`
- [Prompt delivery](#prompt-delivery) — `--prompt`, `--init-prompt`, `--marching-orders`
- [Recipes / workflows / templates / personas](#recipes--workflows--templates--personas)
- [Stagger (prompt delivery pacing)](#stagger-prompt-delivery-pacing)
- [Session profiles](#session-profiles)
- [CASS context injection](#cass-context-injection)
- [Auto-assign pipeline (spawn then claim work)](#auto-assign-pipeline-spawn-then-claim-work)
- [Privacy, safety, resilience](#privacy-safety-resilience)
- [Interactive wizard](#interactive-wizard)
- [Error matrix](#error-matrix)
- [Scenario catalog](#scenario-catalog) — 9 common spawn patterns

---

Spawn creates (or extends) a tmux session with typed agent panes. Flag registrations
are at `/dp/ntm/internal/cli/spawn.go:1210-1294`.

Spawn does **not** attach. On success it prints how to run `ntm attach`.

## Project resolution (read this first)

`ntm spawn <name>` resolves the project directory by:

1. Looking up `<name>` under `projects_base` (`ntm config get projects_base`, or env `NTM_PROJECTS_BASE`).
2. Falling back to a symlink in `~/ntm_Dev/` if the name doesn't match a directory.

**Session name must equal the project directory basename.** If it doesn't, agent-mail,
beads, and file reservations will register under a different project key than NTM sees.
This is the single most common cross-tool breakage; always set `NTM_PROJECTS_BASE` to the
parent of your project directory, and use the directory's basename as the session name.

## Agent-count flags

All accept `N` or `N:model` (`/dp/ntm/internal/cli/agent_spec.go:74-103`). `N` ≥ 1.
Model allowed charset: `^[A-Za-z0-9._/@:+-]+$` (`agent_spec.go:14`). Multiple flags of
the same type accumulate — `--cc=2:opus --cc=1:sonnet` yields 2 Opus + 1 Sonnet panes.

| Flag | Agent | Source |
|------|-------|--------|
| `--cc N[:model]` | Claude | `spawn.go:1211` |
| `--cod N[:model]` | Codex | `spawn.go:1212` |
| `--gmi N[:model]` | Gemini | `spawn.go:1213` |
| `--agy N[:model]` | AGY / Antigravity CLI | `spawn.go:1380` |
| `--cursor N[:model]` | Cursor | `spawn.go:1220` |
| `--windsurf N[:model]` | Windsurf | `spawn.go:1221` |
| `--aider N[:model]` | Aider | `spawn.go:1222` |
| `--oc N[:model]` | Opencode (`opencode` binary unless `[agents] oc` overrides) | `spawn.go:1235` |
| `--local N` | Ollama-backed | `spawn.go:1214` |
| `--ollama N` | alias of `--local` (sums) | `spawn.go:1215` |
| (plugin flags) | per-plugin | Dynamically registered, `spawn.go:1287-1294` |


**AGY (`--agy`):** spawns an interactive Antigravity TUI pane — never `agy -p` / `--print` (LAW 0). Pane numbering for tri-vendor layouts is easiest to verify from spawn `--json` `panes[]` or tmux; **`atm mapping` depends on Agent Mail** and may be empty when AM is down (healthy panes still exist). Cross-link: [`/using-atm`](../../using-atm/SKILL.md) § Tri-vendor.

Ollama specifics:

- `--local-model <name>` default `codellama:latest` (`spawn.go:1216`).
- `--local-host <url>` overrides `OLLAMA_HOST` / `NTM_OLLAMA_HOST` (`spawn.go:1217`).
- `--local-fallback` converts local agents to cloud if preflight fails (`spawn.go:1218`).
- `--local-fallback-provider` `cc|cod|gmi`, default `cod` (`spawn.go:1219`).

### Codex launcher verification and fallback

`--cod` creates Codex-typed panes, but treat the launcher as verified only after
robot observation. If `ntm spawn <project> --cod=1` leaves the pane at a bare `zsh`
prompt, the next prompt will be parsed by the shell rather than Codex.

Verify before dispatch:

```bash
ntm spawn myproject --cod=1
ntm --robot-tail=myproject --panes=2 --lines=20
ntm --robot-snapshot
```

If the pane is not an active Codex session, use Codex directly from the target repo
or isolated worktree:

```bash
codex exec -s danger-full-access --skip-git-repo-check -C /path/to/gitdir \
  "Read AGENTS.md, claim bead <id>, implement only that scope, run the gate, and report evidence."
```

Do not paste or send the worker contract into a bare shell pane.

## Pane layout

| Flag | Effect | Source |
|------|--------|--------|
| `--no-user` | Omit user pane — total panes = agents (vs agents+1) | `spawn.go:1224` |
| `--worktrees` | Each agent gets an isolated worktree on branch `ntm/<session>/<agent>` | `spawn.go:1266` |
| `-l/--label <label>` | Session becomes `project--label` (parallel workspace) | `spawn.go:1230` |

### Label rules (`/dp/ntm/internal/config/label.go:64-78`)

- Non-empty, ≤ 50 chars.
- Must not contain `--` (reserved separator).
- Must match `^[a-zA-Z0-9][a-zA-Z0-9_-]*$`.
- Project name cannot contain `--` (errored by `ValidateProjectName`, `spawn.go:954-956`).
- `SessionBase(name)` strips the `--<label>` suffix for cross-session broadcasts.

## Prompt delivery

| Flag | Purpose | Source |
|------|---------|--------|
| `--prompt <string>` | Injected into each agent at launch | `spawn.go:1247` |
| `--init-prompt <string>` | Sent *after* agents become ready (paired with `--assign`) | `spawn.go:1248` |
| `--marching-orders <file>` | Per-pane prompts using `pane:N <prompt>` syntax | `spawn.go:1273` |

`--marching-orders` file format: each line is either `pane:N <prompt>` or a global line
(applied to all unspecified panes). User pane is always excluded.

## Recipes / workflows / templates / personas

These are three overlapping asset families. Know the difference.

### `-r/--recipe <name>` (`spawn.go:1225`)

An **agent-count template**. Loads from `recipe.NewLoader()` (`spawn.go:1026`). Built-ins
at `spawn.go:867`: `quick-claude`, `full-stack`, `minimal`, `codex-heavy`, `balanced`,
`review-team`. User recipes live in `~/.config/ntm/recipes/`; project overrides in
`.ntm/recipes/`. Enumerate with `ntm recipes list`.

### `-t/--template <name>` / `--workflow` (`spawn.go:1226`)

A **workflow template** adding coordination metadata on top of a recipe. Loaded via
`workflow.NewLoader()` (`spawn.go:1047`). Built-ins: `red-green`, `review-pipeline`,
`specialist-team`, `parallel-explore` (`spawn.go:868`).

**Mutually exclusive** with `--recipe` (`spawn.go:1044-1046`).

**Workflow ≠ pipeline YAML.** `ntm pipeline run` workflows are a separate concept
(see `PIPELINES.md`). Enumerate spawn workflows with `ntm workflows list`.

### `--persona name[:count]` (`spawn.go:1223`)

Repeatable. Personas are **prompt specializations** attached to an agent pane. Schema
at `/dp/ntm/internal/cli/persona_spec.go:53-76`. Registry: built-ins + user
(`~/.config/ntm/personas.toml`) + project (`.ntm/personas.toml`).

Combines with `--cc=N` — persona agents are ADDITIONAL to count agents.

```bash
# 3 Claude + 1 architect-persona agent + 2 implementer-persona agents
ntm spawn myproject --cc=3 --persona=architect --persona=implementer:2
```

## Stagger (prompt delivery pacing)

Three overlapping flag families for backward-compat. For new code, prefer
`--stagger-mode=smart`.

| Flag | Values | Source |
|------|--------|--------|
| `--stagger[=<dur>]` | optional duration; bare enables 30s (`fixed`) | `spawn.go:1235` |
| `--stagger-mode <mode>` | `smart`, `fixed`, `none` | `spawn.go:1238` |
| `--stagger-delay <dur>` | fixed delay (used with `--stagger-mode=fixed`), default `30s` | `spawn.go:1239` |

- `smart` — adapts delay based on rate-limit tracker observations.
- `fixed` — uniform `--stagger-delay` between sends.
- `none` — all prompts fire immediately.

**Panes are always created at once for dashboard visibility; only prompt delivery is staggered.**

### The spawn-then-separate-send boot race

`--stagger` / `--stagger-mode=smart` only pace prompts **baked into the spawn** (`--prompt` / `--marching-orders`). They do nothing for the common pattern of a bare `ntm spawn` (returns immediately) followed by a **separate** `ntm send` / `--robot-send` seconds later: `spawn` returns *before* the pane agent boots to its input box, so the first separate send can land before the input is rendered and is **silently dropped**. The pane looks spawned but is never-engaged (CLI alive, 0.0% CPU, no indicator).

Cures, in order of preference:

- `--assign` — spawn **waits until agents become ready**, then runs `ntm assign`. This is the readiness-wait baked in.
- `--init-prompt="…"` (paired with `--assign`) — delivered *after* agents become ready, unlike `--prompt` which fires at launch.
- `ntm --robot-wait=<session> --wait-until=ready --panes=<pane>` before the first separate send.
- Manual guard: poll `tmux list-panes -F '#{pane_current_command}'` until it shows the agent process AND `capture-pane` shows the input box rendered, then dispatch and verify the working/thinking indicator.

If a pane is already never-engaged from a dropped first send, **re-dispatch — do not restart** (the CLI is healthy; it just never received the order). This is the transient counterpart to the permanent bare-shell case below. See `vibing-with-ntm` OC-047.

## Session profiles

Saved spawn configurations you can reapply.

| Flag | Purpose | Source |
|------|---------|--------|
| `--profile <name>` | Load saved spawn options | `spawn.go:1283` |
| `--profiles foo,bar` | CSV of persona names mapped to agents in order | `spawn.go:1276` |
| `--profile-set <name>` | Named persona set (e.g. `backend-team`) | `spawn.go:1277` |

Explicit flags override loaded profile values (`spawn.go:1199`). Save with `ntm profile save`.

`--profiles` and `--profile-set` are mutually exclusive (`spawn.go:1092-1094`).

## CASS context injection

Injects past-session context (summaries, prior decisions) into fresh panes via CASS.

| Flag | Default | Source |
|------|---------|--------|
| `--cass-context <query>` | `""` (uses auto-generated) | `spawn.go:1242` |
| `--no-cass-context` | false | `spawn.go:1243` |
| `--no-recovery` | false (session-recovery prompt injection) | `spawn.go:1244` |
| `--cass-context-limit N` | 0 (config default) | `spawn.go:1245` |
| `--cass-context-days N` | 0 (config default) | `spawn.go:1246` |

`--no-cass-context` and `--no-recovery` are independent toggles — recovery injection
runs separately from CASS context injection.

## Auto-assign pipeline (spawn then claim work)

With `--assign`, spawn waits until agents become ready then runs `ntm assign` against
them automatically.

| Flag | Default | Source |
|------|---------|--------|
| `--assign` | false | `spawn.go:1253` |
| `--strategy <name>` | (inherits assign default `balanced`) | `spawn.go:1254` |
| `--limit N` | 0 (unlimited) | `spawn.go:1255` |
| `--ready-timeout <dur>` | `60s` | `spawn.go:1256` |
| `--assign-verbose` / `--assign-quiet` | false | `spawn.go:1257-1258` |
| `--assign-timeout <dur>` | `30s` | `spawn.go:1259` |
| `--assign-agent <type>` | `""` | `spawn.go:1260` |
| `--assign-cc-only` / `--assign-cod-only` / `--assign-gmi-only` | false | `spawn.go:1261-1263` |

See `ntm assign` for strategy details (`balanced`, `speed`, `quality`, `dependency`, `round-robin`).

## Privacy, safety, resilience

| Flag | Effect | Source |
|------|--------|--------|
| `--safety` | Errors if session exists (prevents accidental reuse) | `spawn.go:1250` |
| `--privacy` | Disables session data persistence | `spawn.go:1269` |
| `--allow-persist` | Override `--privacy` | `spawn.go:1270` |
| `--auto-restart` | Monitor + restart crashed agents per `[resilience]` config | `spawn.go:1227` |

Without `--safety`, spawn is additive: existing sessions are reused and new panes appended.

## Interactive wizard

`-i/--interactive` triggers the wizard **only** if no specs given (`spawn.go:972`):
`len(agentSpecs)==0 && recipe=="" && template=="" && len(personaSpecs)==0`.

Wizard populates specs and returns; not used from scripts.

## Error matrix

| Condition | Message |
|-----------|---------|
| No agents | `no agents specified` (`spawn.go:1341`) |
| `--safety` + existing session | `session '%s' already exists (--safety mode prevents reuse; use 'ntm kill %s' first)` |
| Invalid label | via `config.ValidateLabel` (`spawn.go:961`) |
| Project name has `--` | `project name %q contains '--'` (`label.go:85`) |
| `--recipe` + `--template` | mutually exclusive (`spawn.go:1044-1046`) |

## Scenario catalog

### 1. Balanced swarm

```bash
ntm spawn myproject --cc=3 --cod=2 --gmi=1 --stagger-mode=smart
```

### 2. Labeled variant alongside an existing session

```bash
ntm spawn myproject --label=frontend --cc=2 --worktrees
# Session: myproject--frontend
# Worktree branches: ntm/myproject--frontend/cc_1, cc_2
```

### 3. Recipe-driven spawn

```bash
ntm spawn myproject -r full-stack
```

### 4. Workflow + personas

```bash
ntm spawn myproject -t red-green \
  --persona=test-writer --persona=implementer:2
```

### 5. Pinned model variants

```bash
ntm spawn myproject --cc=2:opus --cc=1:sonnet --cod=1:gpt-5
```

### 6. No-user swarm (headless, for CI)

```bash
ntm spawn ci-worker --no-user --cc=4 --auto-restart
```

### 7. Spawn then auto-claim bv-prioritized work

```bash
ntm spawn myproject --cc=3 --cod=2 \
  --assign --strategy=dependency --limit=5
```

### 8. Ollama-only local swarm with cloud fallback

```bash
ntm spawn myproject --local=4 \
  --local-model='llama4:70b' \
  --local-fallback --local-fallback-provider=cod
```

### 9. Marching orders file

```bash
cat > /tmp/orders.txt <<'EOF'
pane:2 You own internal/auth; pick the next ready bead there.
pane:3 You own internal/storage; pick the next ready bead there.
You are part of a swarm; reserve your edit surface before editing.
EOF

ntm spawn myproject --cc=2 --cod=2 --marching-orders=/tmp/orders.txt
```
