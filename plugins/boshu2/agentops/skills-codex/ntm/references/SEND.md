# `ntm send` — Exhaustive Flag Reference

## Contents

- [Default targeting behavior](#default-targeting-behavior)
- [Agent-type selectors (with `:variant` filter)](#agent-type-selectors-with-variant-filter)
- [Pane selectors](#pane-selectors) — `--pane`, `--panes`, `--all`, `-s/--skip-first`, `--project`, `--tag`
- [Input sources](#input-sources) — `--file`, stdin, positional, priority order
- [Base prompt (prepended to every target)](#base-prompt-prepended-to-every-target)
- [`-c/--context` file-range injection](#-c--context-file-range-injection)
- [Templates and variables](#templates-and-variables) — `-t/--template`, `--var`
- [Smart routing (`--smart` + `--route`)](#smart-routing---smart----route)
- [Distribute mode (auto-distribute from bv triage)](#distribute-mode-auto-distribute-from-bv-triage)
- [Batch / broadcast](#batch--broadcast)
- [CASS duplicate-detection](#cass-duplicate-detection) — `--cass-check`, `--no-cass-check`, workarounds
- [Prefix, suffix, hooks, dry-run](#prefix-suffix-hooks-dry-run)
- [Output shapes](#output-shapes)
- [Error matrix](#error-matrix)
- [Scenario catalog](#scenario-catalog) — 10 copy-ready recipes

---

Covers every flag registered in `/dp/ntm/internal/cli/send.go`. Source citations use
`send.go:line` shorthand; all paths are under `/dp/ntm/internal/cli/`.

## Default targeting behavior

With **no** target flags, `send` targets all agent panes in the session and **excludes**
the user pane. This is almost always what you want from automation.

- `--all` expands the target set to include the user pane.
- `-s/--skip-first` explicitly excludes pane 0 (the user pane). Mostly useful together
  with `--all` to get "every pane except the operator shell" broadcast semantics.

## Agent-type selectors (with `:variant` filter)

Custom flags implemented by `sendTargetValue` (`send.go:297-341`). All four accept
`NoOptDefVal=true`, so bare `--cc` means "any Claude pane," while `--cc=opus` filters
by `tmux.Pane.Variant` exact equality.

| Flag | AgentType | Example | Notes |
|------|-----------|---------|-------|
| `--cc[=variant]` | `cc` (Claude) | `--cc=opus` | Variant is an open string, not pre-enumerated |
| `--cod[=variant]` | `cod` (Codex) | `--cod=gpt-5` | |
| `--gmi[=variant]` | `gmi` (Gemini) | `--gmi=pro` | |
| `--agy[=variant]` | `agy` (AGY / Antigravity) | `--agy` | Same selector semantics as tri-vendor spawn |

`--cc=false` is treated as a no-op (`send.go:320-322`). Selectors can be combined:
`--cc --cod` sends to all Claude + Codex panes. Combining with `--pane=N` ANDs: a
specific pane that doesn't match the type yields zero targets + error.


### AGY (Antigravity) — `--agy` send selector

AGY panes spawned with `ntm spawn --agy=…` are targeted by **`--agy`** on
`ntm send` (same family as `--cc` / `--cod` / `--gmi` / `--agy`):

```bash
ntm send <session> --agy "run the tests"
ntm send <session> --agy --file packet-agy.md
```

For a specific pane index (or when mixing file + type filters), use **`--pane=N`**
(or `--panes=`) with `-f/--file`:

```bash
ntm send <session> --pane=3 --file packet-agy.md
```

**Do not** use `agy -p` / `gemini -p` for swarm workers (LAW 0).

**`--gmi` vs AGY:** `--gmi` selects **Gemini CLI** (`gmi` agent type) panes.
**AGY / Antigravity** is a separate agent family (`agy`); tri-vendor smoke uses
`--agy` at spawn and send time. See
[`/using-atm`](../../using-atm/SKILL.md) § Tri-vendor.

## Pane selectors

| Flag | Type | Purpose | Source |
|------|------|---------|--------|
| `-p/--pane` | int | Single pane by index (default -1 = unset) | `send.go:727` |
| `--panes` | string | CSV of indices or ranges; parsed by `robot.ParsePanesArg` | `send.go:728,652` |
| `--all` | bool | Include the user pane | `send.go:725` |
| `-s/--skip-first` | bool | Explicitly skip pane 0 | `send.go:726` |
| `--project` | string | Broadcast to all sessions sharing a `SessionBase` | `send.go:775` |
| `--tag` (repeatable) | []string | Match panes by tag (OR logic) | `send.go:735` |

### Conflicts

- `--pane` + `--panes` → `cannot use --pane and --panes together` (`send.go:658`).
- `--project` + specific session name → `cannot use --project with a specific session name` (`send.go:580`).

### Addressing disambiguation (don't mis-target)

Three different selector families coexist and use **different index spaces** — easy to mis-address and silently hit the wrong pane (or the operator pane). When combined, they **AND** together (intersection); an empty intersection errors rather than broadcasting.

| Selector | Index space | Selects | Typical use |
|----------|-------------|---------|-------------|
| `--pane=N` / `--panes=N,M` | **tmux pane index** (verify live; base-index may be 1 — OC-028/OC-045) | exactly that pane / that explicit set | targeted dispatch to a known pane |
| `--cc` / `--cod` / `--gmi` / `--agy` (+ `:variant`) | **agent type**, not index | all panes of that type | broadcast to a model class |
| `--agent <idx>` (batch/broadcast only, default `-1`) | **round-robin selector** over agent panes, NOT a tmux index | one agent per batch item, rotating; `-1` = auto round-robin | distributing a batch across agents |

Rules: `--agent` is a batch-distribution knob (`send.go:772`), **not** a synonym for `--pane`. Don't reach for `--agent 2` to mean "pane 2" — use `--pane=2`. With no target flags at all, `send` hits every agent pane and excludes the user pane (the usual automation default); `--all` re-includes the user pane. Verify the live pane index immediately before any raw `tmux send-keys` (OC-045).

### `--all` vs `--project`

These are orthogonal axes.

- `--all` scope: **panes within one session**, includes the user pane.
- `--project` scope: **all sessions whose `SessionBase(name)` matches**, iterates each session and applies the intra-session pane filter independently.

You can combine them: `ntm send --project myproject --all "x"` → every pane of every session variant, including each session's user pane.

## Input sources

Resolved by `getPromptContent` (`send.go:851-891`) in priority order. First match wins.

| Priority | Source | Flag | Source-label in JSON |
|----------|--------|------|----------------------|
| 1 | File | `-f/--file` | `file:<path>` |
| 2 | Stdin | (pipe; only when no args) | `stdin` |
| 3 | Positional args | (joined with spaces) | `args` |

- Empty file errors at `send.go:862`.
- Empty stdin with no prefix errors at `send.go:878`.
- `--prefix` / `--suffix` (`send.go:730-731`) wrap file or stdin content; **ignored for positional args** (`send.go:889`).

## Base prompt (prepended to every target)

- `--base-prompt <string>` (`send.go:763`).
- `--base-prompt-file <path>` (`send.go:764`).
- Config fallbacks: `cfg.Send.BasePrompt`, `cfg.Send.BasePromptFile` (`send.go:594-595`).

Resolution precedence: flag string > flag file > config string > config file (`send.go:597`).

## `-c/--context` file-range injection

Repeatable `StringArray` (`send.go:732`). Parsed by `prompt.ParseFileSpec` (`send.go:698`).

Syntax (documented at `send.go:539`):

| Form | Meaning |
|------|---------|
| `path` | Whole file |
| `path:10-50` | Lines 10–50 inclusive |
| `path:10-` | Line 10 through end |
| `path:-50` | Start through line 50 |

Multiple `-c` accumulate in order. `prompt.InjectFiles` (`send.go:705`) prepends them to
the final prompt with file headers + code fences.

```bash
ntm send myproject --cc \
  -c internal/auth/service.go:1-80 \
  -c internal/auth/middleware.go \
  "Review these handlers side by side and propose a unification."
```

## Templates and variables

- `-t/--template <name>` (`send.go:733`): loads named template via the template loader.
- `--var key=value` repeatable (`send.go:734`).

Templates are resolved from project `.ntm/templates/` then user `~/.config/ntm/templates/`
(enumerate with `ntm template list`).

Template engine supports:

- `{{variable}}` substitution
- `{{#var}}...{{/var}}` conditional blocks (non-empty → include)
- `{{file}}` auto-bound to `--file` content

When `-t` is given the input path flows through `runSendWithTemplate` (`send.go:686`).

```bash
ntm send myproject --cc \
  -t fix \
  --var issue="nil pointer deref in JWT validator" \
  --var severity="P0" \
  --file internal/auth/service.go
```

## Smart routing (`--smart` + `--route`)

| Flag | Default | Source |
|------|---------|--------|
| `--smart` | false | `send.go:738` |
| `--route <strategy>` | `""` | `send.go:739` |

Strategies (per help at `send.go:739`): `least-loaded`, `round-robin`, `affinity`, `sticky`, `random`.

Decision returned in `SendResult.RoutedTo *SendRoutingResult` (`send.go:91-97`) with
`{PaneIndex, AgentType, Strategy, Reason, Score}`.

## Distribute mode (auto-distribute from bv triage)

| Flag | Default | Source |
|------|---------|--------|
| `--distribute` | false | `send.go:742` |
| `--dist-strategy` | `balanced` | `send.go:743` |
| `--dist-limit N` | 0 (one per idle agent) | `send.go:744` |
| `--dist-auto` | false (skip confirmation) | `send.go:745` |

Valid `--dist-strategy`: `balanced`, `speed`, `quality`, `dependency`.

`--dist-auto` + `--dry-run` is rejected (`send.go:605`). Use one or the other.

## Batch / broadcast

| Flag | Default | Source |
|------|---------|--------|
| `--batch <file>` | `""` | `send.go:767` |
| `--delay <dur>` | `""` (parsed by `time.ParseDuration`) | `send.go:768` |
| `--confirm-each` | false | `send.go:769` |
| `--stop-on-error` | false | `send.go:770` |
| `--broadcast` | false | `send.go:771` |
| `--agent <idx>` | -1 (round-robin) | `send.go:772` |
| `--randomize` | false | `send.go:756` |
| `--seed <int64>` | 0 (time-based) | `send.go:757` |
| `--priority-order` | false | `send.go:760` |

Batch file format: one prompt per line, or `---` separated blocks (`send.go:767`).

Randomization uses xorshift64 Fisher-Yates (`send.go:424-441`). Seed 0 uses
`time.Now().UnixNano()` and the chosen value is returned as `SeedUsed` in the JSON
result so you can reproduce.

> `--confirm-each` in batch mode **blocks on stdin** per prompt. In automation or cron,
> omit it or the command hangs.

## CASS duplicate-detection

Default ON. CASS (Cross Agent Session Search) queries past sessions for prompts similar
to what you're about to send and aborts with a confirmation if one is found.

| Flag | Default | Source |
|------|---------|--------|
| `--cass-check` | true | `send.go:748` |
| `--no-cass-check` | false | `send.go:749` |
| `--cass-similarity <float>` | 0.7 | `send.go:750` |
| `--cass-check-days N` | 7 | `send.go:751` |

In practice this blocks repeat-sends in tending loops. Two ways to bypass:

1. **Per-call (recommended in scripts):** `ntm send ... --no-cass-check`.
2. **Structural (recommended for automation):** `ntm --robot-send=<session>` is non-interactive and never prompts.
3. **Rotating suffix trick** (widely used in operator loops): append a marker that changes each pass — `"... Tend pass 17 at 16:40"` — which keeps the message distinctive enough to pass the similarity gate.

## Prefix, suffix, hooks, dry-run

| Flag | Purpose | Source |
|------|---------|--------|
| `--prefix <str>` | Prepend to prompt (file/stdin sources only) | `send.go:730` |
| `--suffix <str>` | Append to prompt (file/stdin sources only) | `send.go:731` |
| `--no-hooks` | Disable PreSend/PostSend hook chain | `send.go:752` |
| `--dry-run` | Emit `SendDryRunResult` without sending | `send.go:753` |

## Output shapes

### Normal send (`SendResult`, `send.go:49-64`)

```json
{
  "success": true,
  "session": "myproject",
  "targets": [{"pane": 2, "agent": "cc"}],
  "delivered": 1,
  "failed": 0,
  "routed_to": { "pane_index": 2, "agent_type": "cc", "strategy": "least-loaded", "reason": "idle for 34s", "score": 0.92 },
  "randomized": false,
  "seed_used": 0,
  "error_code": ""
}
```

### Dry-run (`SendDryRunResult`, `send.go:75-88`)

```json
{
  "would_send": [
    { "pane": 2, "agent": "cc", "prompt": "...", "prompt_preview": "...", "source": "file:task.md", "priority": 0 }
  ]
}
```

## Error matrix

| Condition | Message |
|-----------|---------|
| `--pane` + `--panes` | `cannot use --pane and --panes together` |
| `--project` + session arg | `cannot use --project with a specific session name` |
| No session + no `--project` | `session name required (or use --project)` |
| `--project` with zero matches | `no sessions found for project %q` |
| Empty file or stdin with no prefix | `prompt content is empty` |
| `--dist-auto` + `--dry-run` | Rejected as incompatible |

## Scenario catalog

### 1. One-shot message to all Claude agents

```bash
ntm send myproject --cc "Summarize current blockers in three bullets."
```

### 2. Target two specific panes with a file prompt

```bash
ntm send myproject --panes=2,3 --file prompts/refactor.md
```

### 3. File-range context injection for code review

```bash
ntm send myproject --cc=opus \
  -c internal/auth/jwt.go:40-120 \
  -c internal/auth/middleware.go:1-60 \
  --prefix "Context: we're hardening JWT validation." \
  "Review and propose concrete fixes."
```

### 4. Smart-routing a new task to the least-loaded agent

```bash
ntm send myproject --smart --route=least-loaded \
  "Take the next ready authentication bead and implement."
```

### 5. Distribute bv triage across idle agents

```bash
ntm send myproject --distribute --dist-strategy=dependency --dist-auto
```

### 6. Scripted batch with deterministic ordering

```bash
ntm send myproject --batch prompts.txt --delay=30s --seed=42 --stop-on-error
```

### 7. Cross-session broadcast to every label variant

```bash
ntm send --project myproject \
  "Sync to main and report any conflicts you encounter."
```

### 8. Non-interactive send from an automation loop

```bash
ntm --robot-send=myproject --panes=2 \
    --msg="Tend pass ${PASS} at $(date +%H:%M)" \
    --type=cc
```

### 9. Template + variables + file

```bash
ntm send myproject --cc \
  -t fix --var issue="nil deref" --file internal/auth/jwt.go
```

### 10. Bypass CASS dedup for a retry

```bash
ntm send myproject --pane=2 --no-cass-check "Please retry; previous send was rejected."
```
