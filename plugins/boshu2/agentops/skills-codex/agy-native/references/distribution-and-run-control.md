# agy-native — distribution surface + run-control reference

Overflow detail for the `agy-native` skill: how skills/plugins reach the AGY
image, and the full permission/output-format matrix for headless runs. The main
SKILL.md states the rules; this file is the operational depth.

> Clean-room note: all command surfaces below are **AGY (Antigravity)**
> affordances (`agy plugin`, `agy --print`, `--sandbox`, `--add-dir`). The
> retired `gemini` CLI lane (`gemini skills`, `gemini extensions`,
> `--approval-mode`, `--worktree`) is **not** used — AGY ≠ gemini-cli. Where an
> old gemini-cli habit existed, the AGY equivalent is named.

## 1. The AGY distribution surface

AGY exposes capability to the agent through three layers, in increasing weight:

| Layer | Unit | How AGY discovers it | When to use |
|---|---|---|---|
| **Portable skill** | a bare `SKILL.md` (+ `references/`) under `~/.gemini/skills/<name>/` | AGY reads `SKILL.md` directly — no packaging | exposing one AgentOps skill; the corpus already lives here (jsm-managed) |
| **Plugin** | a tree with `plugin.json` (`skills`, `subagents`, `hooks`, `mcpServers`) | `agy plugin install <dir>` / `name@marketplace` | bundling rules + workflows + subagents + hooks + MCP as one installable unit (the `agy-control-plane` unit) |
| **MCP server** | a server entry in `plugin.json` `mcpServers` or `~/.gemini/settings.json` | started by AGY at session init | giving the agent tools beyond shell (the `agy-mcp-plugins` lane) |

**Replaces the retired gemini-cli model:** the old lane split this into `gemini
skills` (agent skills) + `gemini extensions` (broader packages). AGY collapses
both into the **plugin** unit plus the **portable SKILL.md** — there is no
separate `agy extensions` surface. Treat a former gemini "extension" as an AGY
plugin.

## 2. Verified plugin verbs (`agy plugin help`)

```
agy plugin list                      # what's discovered + enabled/disabled
agy plugin import [gemini|claude]    # pull an existing Claude/Gemini plugin tree in
agy plugin install <dir|name@market> # reads plugin.json; supports marketplace refs
agy plugin uninstall <name>
agy plugin enable <name>
agy plugin disable <name>
agy plugin validate <dir>            # checks plugin.json before activation
agy plugin link <path>              # link a local tree (live edits, dev lane)
```

## 3. Install vs link — the dev discipline (folded from the retired ext lane)

- **`agy plugin link <path>`** for local AgentOps development. Edits to the
  source tree are reflected live; you are never reviewing a stale installed copy.
- **`agy plugin install <dir|name@marketplace>`** for released / remote
  artifacts only.
- **Do not mix** link and install for the same plugin without removing the old
  one first — two discovery copies conflict.
- **Source of truth stays in AgentOps** (`~/dev/agentops/skills/…` or the plugin
  tree under version control). Do **not** hand-edit the managed runtime copies
  under `~/.gemini/skills/` as if they were canonical — runtime copies drift and
  are hard to review.

## 4. Mutation protocol (every install/link/enable/disable)

1. **Validate first** (for a plugin tree): `agy plugin validate <dir>`. Malformed
   `plugin.json` breaks the image at activation, not at install.
2. **Apply** the change (`install` / `link` / `enable` / `disable`).
3. **List after every mutation**: `agy plugin list`. Command exit success is not
   proof — confirm the runtime discovery surface actually shows the new state.
4. **Record rollback**: every `install`/`link` names its matching
   `uninstall`/`disable`. Image setup must be reversible.

```bash
agy plugin validate ./agy-control-plane     # 1
agy plugin link ./agy-control-plane          # 2 (dev)  — rollback: agy plugin uninstall agy-control-plane
agy plugin enable agy-control-plane          #          — rollback: agy plugin disable agy-control-plane
agy plugin list                              # 3 confirm enabled
```

## 5. Run-control matrix (permissions × output × scope)

The retired gemini lane used `--approval-mode {plan,auto_edit,yolo}`,
`--output-format {json,stream-json}`, and `--worktree`. The AGY equivalents:

| Concern | Retired gemini-cli | **AGY equivalent** | Use for |
|---|---|---|---|
| Read-only / plan | `--approval-mode plan` | default (no auto-approve) + read-mostly `--add-dir`; do not pass `--dangerously-skip-permissions` | the **judge** — validate, never edit |
| Scoped auto-edit | `--approval-mode auto_edit` | `--dangerously-skip-permissions` **with** a tight `--add-dir "$REPO"` and the `dcg` BeforeTool hook on | the **author** in a loop tick |
| Full auto / sandbox | `--approval-mode yolo` (host-sandboxed) | `--dangerously-skip-permissions` only inside `--sandbox` (restricts the terminal) | unattended runs on an isolated host |
| Write isolation | `--worktree <name>` | pre-created git worktree + `--add-dir "$WORKTREE"` (AGY scopes by directory, not by spawning worktrees) | concurrent author/judge, no clobbering |
| Structured output | `--output-format json/stream-json` | parse `agy --print` output; for streaming/factory loops capture the run dir under `brain/<conversation-id>/` and the `*.md.metadata.json` (`{summary, updatedAt, userFacing}`) as the durable record | factory ticks that machine-read results |
| Resume | `--resume` | `-c`/`--continue` (most recent) or `--conversation <id>` (by id) — **never** use for author→judge handoff (would share context) | continuing one role's own work |

**Author launch (scoped auto-edit):**
```bash
agy --print --add-dir "$REPO" --dangerously-skip-permissions \
  "Claim one ready bead via br. Implement only it in $REPO. Commit scoped. \
   Write evidence to brain as userFacing. Do NOT close it."
```

**Judge launch (read-mostly, fresh context):**
```bash
agy --print --add-dir "$REPO" \
  "Validate bead <id> against its evidence artifact ONLY. You did not author it. \
   Emit PASS/WARN/FAIL to brain as a userFacing verdict. Edit no code."
```

## 6. Evidence layout (durable, not chat)

A run record lives in the brain store, never only in the terminal:

```
~/.gemini/antigravity-cli/brain/<conversation-id>/
  <name>_verification.md            # the verdict / evidence body
  <name>_verification.md.metadata.json   # { summary, updatedAt, userFacing:true }
```

Capture, per role: the changed files, the commands run + exit codes, the diff,
and the verdict. The judge's verdict artifact (`userFacing:true`) is the only
thing an `ao beads exec close` may cite — never a live transcript. Consume an agent's
**published compression** (this artifact + the committed repo file + the bead
transition), never its live session.

## 7. Troubleshooting (distribution + run-control)

| Problem | Cause | Fix |
|---|---|---|
| New skill not discovered | wrong source path or disabled | `agy plugin list`; for a bare skill confirm `~/.gemini/skills/<name>/SKILL.md` exists, then `enable` |
| `agy plugin install` fails: "failed to read plugin.json" | target isn't a plugin dir | point at a dir with `plugin.json`, or `name@marketplace`; for a bare skill use `~/.gemini/skills/` |
| Edits not reflected | reviewing an installed copy, not the linked source | `uninstall` then `agy plugin link <source>` |
| Two copies conflict | linked + installed variants coexist | `disable`/`uninstall` one |
| Worker edited outside scope | `--add-dir` too broad / missing | tighten `--add-dir` to the single repo/worktree |
| Worker ran a destructive command | auto-approve under `--dangerously-skip-permissions` | the `dcg` BeforeTool hook must block it — confirm it's wired in `~/.gemini/settings.json` |
| Judge agreed too easily | reused context via `-c`/`--continue` | spawn a fresh conversation; enforce read-mostly scope |
| Headless run exits empty | `--print` timed out / no model reachable | raise `--print-timeout`; confirm `agy models` lists a model; check OAuth |
