---
name: agy-native
description: 'Drive AgentOps in AGY: loop, plugins'
---
# agy-native

Drive the AgentOps loop on the **Antigravity image** (AGY): the `agy` CLI backed by the brain/knowledge store at `~/.gemini/antigravity-cli/`. This is the third harness alongside the Claude image and the Codex image — same loop laws, AGY-native primitives. **Invoke `agy`, never rebuild it.**

## Overview / When to Use

AGY is Google's Antigravity agent harness exposed as a local CLI (`~/.local/bin/agy`). It speaks the Claude-style packaging shape (plugins, skills, subagents, hooks, MCP) and a **portable `SKILL.md`** — AGY reads skills from `~/.gemini/skills/` directly, so the AgentOps corpus already loads on it. Use this skill when you need the claim->work->validate->close->persist loop running on AGY (driving Gemini, or Claude/GPT models *through* AGY — `agy models` exposes Gemini 3.5/3.1, Claude Sonnet/Opus 4.6, GPT-OSS), as a parallel or fallback to the Claude/Codex images.

**AGY ≠ gemini-cli.** The retired `gemini` CLI lane (`gemini -p`, `gemini skills`, `gemini extensions`, `--approval-mode`, `--worktree`) is gone. Everything here is an AGY affordance; §"Distribution" + the reference file name each AGY equivalent for an old gemini habit.

Verified primitives on this host (`agy --help`, `agy plugin help`, `agy models`):
- **Headless run:** `agy -p "<prompt>"` / `agy --print` (one-shot, prints, exits; `--print-timeout` default 5m). `-c`/`--continue` resumes the most recent conversation; `--conversation <id>` resumes by ID.
- **Plugins:** `agy plugin {list,import,install,uninstall,enable,disable,validate,link}`. `import [gemini|claude]` pulls existing plugin trees in. `install <target>` reads a `plugin.json` (supports `plugin@marketplace`).
- **Permissions:** `--dangerously-skip-permissions` auto-approves tool calls (loop/headless lane); `--sandbox` restricts the terminal.
- **Workspace scope:** `--add-dir <dir>` (repeatable) scopes which repos a run can touch (AGY's write-isolation primitive — it scopes by directory, not by spawning worktrees).
- **Brain/knowledge:** durable agent memory + user-facing artifacts under `~/.gemini/antigravity-cli/{brain,knowledge}/` (per-conversation dirs; `*.md` + `*.md.metadata.json` with `{summary, updatedAt, userFacing}`).

### Folded triggers (ag-s43tg wave 1): the four AGY sibling lanes route here

- **`agy-mcp-plugins` → the Distribution lane.** Use when wiring MCP servers and AgentOps plugin bundles
  into the AGY image with least-privilege access, rollback evidence, and validation hooks — the
  §"Distribution" layer below (plugin trees, `agy plugin link/install`, validate → apply → list →
  record-rollback) owns that mutation protocol.
- **`agy-project-worktree-permissions` → the isolation rules.** Use when proving AGY project/worktree
  isolation with scoped --add-dir permissions, role permission tiers, and `dcg` guardrails — Rules 4–6
  below (non-overlapping `--add-dir` scopes, permission matched to role, the `dcg` BeforeTool hook)
  are that contract, with evidence persisted per Rule 3.
- **`agy-rules-workflows` (triggers: AGY rules, agy-loop, AGY schedule) → Phase 2 law packaging.** Use
  when installing AGY rules, workflow, goal, and schedule controls for AgentOps loop law — the
  `agy-control-plane` plugin tree in Phase 2 (`rules/` + `workflows/` + `hooks.json`) is where the
  agy-loop law lands; schedules drive Phase 5.
- **`agy-sidecar-scheduled-tick` → the Phase 5 recurring driver.** Use when running a
  recurring AGY sidecar loop tick with agentapi evidence capture — Phase 5's tick lane (AGY
  scheduled task, or an external timer / Claude `CronCreate` calling `agy --print`) is that driver.

## ⚠️ Critical Constraints

- **Rule 1 — Never `claude -p` for workers (LAW 0).** AGY runs on Gemini OAuth (and proxied Claude/GPT). Drive AGY workers with `agy --print` or `agy -i`, Codex with `codex exec`, Claude only via NTM panes / subagents. **Why:** `claude -p` bills the API per-token, not the Max sub; the overnight factory burned API this exact way (banned).
- **Rule 2 — author != judge, always two contexts.** The subagent that closes a bead must NOT be the one that validates it. Spawn the judge as a separate async subagent with a clean context (or a separate `agy --print` invocation; **never** `-c`/`--continue` across roles — it shares context). **Why:** a self-grading worker is a flatterer; independent verdict is the membrane (control-plane LEARNINGS: a tie-break quorum caught a false-FAIL).
- **Rule 3 — evidence-gated close.** A bead closes only against a persisted verdict artifact (a `brain/*.md` with `userFacing:true` or a committed repo file), never against chat text alone. **Why:** agents are ephemeral; the system carries state. Consume an agent's *published compression*, never its live session.
- **Rule 4 — worktree / `--add-dir` isolation.** Concurrent author and judge get isolated worktrees or non-overlapping `--add-dir` scopes. No two roles edit the same file. **Why:** prevents swarm races and clobbered work.
- **Rule 5 — `dcg` guard stays on.** `~/.gemini/settings.json` wires a `BeforeTool` hook on `run_shell_command` to `dcg`. Do not remove it even under `--dangerously-skip-permissions`. **Why:** it blocks destructive commands the auto-approve flag would otherwise let through.
- **Rule 6 — match permission to role.** Author = `--dangerously-skip-permissions` with a **tight** `--add-dir`; judge = **default** (no auto-approve) with a read-mostly scope; full-auto only inside `--sandbox`. **Why:** auto-approve is a blast-radius choice — a validator that can edit is a false-close path.
- **Rule 7 — operator-side; invoke-never-rebuild.** This drives the flywheel harness. Do NOT write under `~/dev/agentops`, do NOT git push agentops, do NOT treat AGY as something to re-author. **Why:** AGY is Emanuel's substrate (ACFS doctrine) — own a thin adapter, not the tool.

## Distribution — exposing skills/plugins to AGY

AGY discovers capability through three layers (weight ascending): a **portable `SKILL.md`** under `~/.gemini/skills/<name>/` (read directly — no packaging), a **plugin** tree with `plugin.json` (`skills`/`subagents`/`hooks`/`mcpServers`), and **MCP servers** (the `agy-mcp-plugins` lane). The retired gemini split of `skills` vs `extensions` collapses into the single AGY **plugin** unit — there is no `agy extensions` surface; treat a former gemini "extension" as an AGY plugin.

Dev discipline (folded from the retired extension lane): **`agy plugin link <path>`** for local development (live edits, never a stale copy); **`agy plugin install <dir|name@marketplace>`** for released/remote artifacts; don't run both for one plugin. **Source of truth stays in AgentOps** — do not hand-edit the managed runtime copies under `~/.gemini/skills/`. Every mutation: **validate → apply → list → record rollback** (see references). Full verb list, install-vs-link table, and the permission×output×scope matrix: **[references/distribution-and-run-control.md](references/distribution-and-run-control.md)**.

## Workflow / Methodology

### Phase 1: Verify the image is live
```bash
which agy && agy models | head        # CLI present, models reachable
ls ~/.gemini/antigravity-cli/{brain,knowledge}   # brain store exists
agy plugin list                       # what's already imported/enabled
```
**Checkpoint:** confirm `agy` resolves, a model lists, and the brain dir exists before dispatching any tick.

### Phase 2: Package + expose the laws
A bare `SKILL.md` under `~/.gemini/skills/` is portable — no `plugin.json` needed just to expose a skill. To bundle rules + workflows + subagents + hooks + MCP, lay out a plugin tree (the `agy-control-plane` unit):
```
agy-control-plane/
  plugin.json   # { name, version, skills, subagents, hooks, mcpServers }
  rules/        # invariant law (author!=judge, evidence-gated close, scoped commit)
  workflows/    # slash-command loop trajectories (claim->work->validate->close->persist)
  subagents/    # worker.md, validator.md, tie-break.md, scout.md
  hooks.json    # pre/post-tool guardrails (close gate, format/lint, dcg)
  skills/       # or rely on portable ~/.gemini/skills/
```
```bash
agy plugin import claude               # pull an existing plugin tree in (optional)
agy plugin validate ./agy-control-plane
agy plugin link ./agy-control-plane    # dev (live edits) — or `install` for released
agy plugin enable agy-control-plane
agy plugin list                        # confirm enabled (rollback: disable/uninstall)
```
**Checkpoint:** `agy plugin validate` passes and `agy plugin list` shows the plugin enabled.

### Phase 3: One headless tick (author)
Spawn the author in a tight scope with scoped-auto-edit permission; let it claim and work one ready bead:
```bash
agy --print --add-dir "$REPO" --dangerously-skip-permissions \
  "Claim one ready bead via br. Implement only it in this worktree. \
   Commit scoped. Write evidence to brain as userFacing. Do NOT close it — a judge will."
```
**Checkpoint:** a scoped commit exists and an evidence artifact landed in `brain/`; the bead is implemented but still OPEN.

### Phase 4: Independent verdict (judge — separate context)
Spawn the judge as an async subagent / second `agy --print` with a **fresh context and a read-mostly scope** (default permissions, no auto-approve):
```bash
agy --print --add-dir "$REPO" \
  "Validate bead <id> against its evidence artifact ONLY. You did not author it. \
   Emit PASS/WARN/FAIL to brain as a userFacing verdict. Do not edit code."
```
On a split or false-FAIL, spawn a third **tie-break** subagent. Close the bead (`br close <id>`) **only** on PASS.
**Checkpoint:** verdict artifact persisted by a *different* context than the author; bead closed only if PASS.

### Phase 5: Persist + tick the loop
- Persist: scoped `git commit`$push for the repo; the brain artifact is the durable memory.
- Tick: AGY's native scheduled-task / slash-workflow is the recurring driver; otherwise drive externally with Claude `CronCreate` or a bushido timer calling `agy --print` (in-session, never `claude -p`).
**Checkpoint:** the loop can re-enter Phase 3 with the next ready bead; state is on the bus/artifact, not in a live session.

## Output Specification

**Format:** a completed loop tick — git commits + beads transitions + brain artifacts.
**Filename / path:**
- Evidence + verdict: `~/.gemini/antigravity-cli/brain/<conversation-id>/<name>_verification.md` (+ `.metadata.json`, `userFacing:true`).
- Code: scoped commit in the target repo (one bead per commit).
- Beads: `br` transition (claim -> close), JSONL synced to git.
**Structure of a tick:** `{ bead_id, author_context_id, judge_context_id, verdict (PASS|WARN|FAIL), evidence_path, commit_sha }`.

## Quality Rubric

- [ ] No `claude -p` anywhere; AGY workers driven by `agy --print` / `agy -i` (Rule 1).
- [ ] Author and judge ran in **distinct** contexts/conversations (Rule 2) — verifiable by two `conversation_id`s.
- [ ] Bead closed only against a persisted `userFacing` verdict artifact, not chat (Rule 3).
- [ ] Author and judge had non-overlapping `--add-dir` / worktree scopes (Rule 4).
- [ ] `dcg` BeforeTool hook still present in `~/.gemini/settings.json` (Rule 5).
- [ ] Author had auto-edit + tight scope; judge ran default (no auto-approve), read-mostly (Rule 6).
- [ ] Nothing written under `~/dev/agentops`; no agentops push (Rule 7).
- [ ] `agy plugin validate` passed and `agy plugin list` shows the plugin enabled; every mutation listed + a rollback recorded.

## Examples

- **Fallback tick when the Claude image is rate-limited:** import a plugin (`agy plugin import claude`), run Phase 3–4 on Gemini 3.5 Flash, persist, hand the next bead back to the Claude image.
- **Cross-vendor author!=judge:** author with `agy --print --model "Gemini 3.5 Flash (High)"`, judge with `agy --print --model "Claude Opus 4.6 (Thinking)"` — two vendors, one loop, no shared context.
- **Expose a new AgentOps skill to AGY (dev):** `agy plugin link ~/dev/agentops/skills/<name>` (or drop a portable `SKILL.md` in `~/.gemini/skills/<name>/`), then `agy plugin list` to confirm discovery; rollback `agy plugin uninstall <name>`.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `agy plugin install` fails: "failed to read plugin.json" | target isn't a plugin dir / missing `plugin.json` | point at a dir containing `plugin.json`, or `name@marketplace`; for a bare skill use `~/.gemini/skills/` |
| New skill not discovered | wrong source path / disabled | `agy plugin list`; confirm `~/.gemini/skills/<name>/SKILL.md`, then `enable` |
| Edits not reflected | reviewing an installed copy, not the linked source | `uninstall`, then `agy plugin link <source>` |
| Headless run exits empty | `--print` timed out or no model reachable | raise `--print-timeout`; confirm `agy models`; check OAuth in `~/.gemini/settings.json` |
| Worker tried a destructive command | auto-approve under `--dangerously-skip-permissions` | the `dcg` BeforeTool hook should block it — confirm it's wired |
| Judge agreed with author too easily | same context reused (`-c`/`--continue`) | spawn a fresh conversation (no `--continue`); enforce read-mostly scope |

## See Also / References

- **[references/distribution-and-run-control.md](references/distribution-and-run-control.md)** — full plugin verb list, install-vs-link discipline, mutation protocol, the permission×output×scope matrix (AGY equivalents for retired gemini flags), and the brain evidence layout.
- Research input: `~/.agents/research/agy-native-harness-2026-06-06.md` (AGY primitives, official docs index, open questions).
- [`$dual-pane-atm`](../dual-pane-atm/SKILL.md) — **in-ATM AGY** (interactive pane-3 TUI via `atm send`) vs this skill's **headless** `agy --print` / sidecar paths; do not conflate them.
- Sibling AGY skills: `agy-rules-workflows` (goal/schedule loop law), `agy-mcp-plugins` (MCP servers + plugin packaging), `agy-headless-evidence` (agentapi sidecar + JSONL evidence).
- Sibling images / loop substrate: `ntm` (tmux swarms), `beads-br` (br tracker), `agent-mail` (coordination), `dcg` (destructive-command guard), `caam` (account lanes).
- Loop doctrine: control-plane LEARNINGS (author!=judge, evidence-gated close); memory `never claude -p for workers`; ACFS invoke-never-rebuild + fork-and-own doctrine.
- Official Antigravity docs: cli-overview, cli-plugins, subagents, hooks, ide-workflows, ide-rules (see research file for URLs).
