# agy-native — Codex Execution Profile

Runtime adapter for Codex CLI. The doctrine, the five workflow phases, the
**seven** critical rules, and the **Distribution** surface (exposing
skills/plugins to AGY) are defined in the Codex wrapper [`SKILL.md`](./SKILL.md)
and the source skill [`../../skills/agy-native/SKILL.md`](../../skills/agy-native/SKILL.md) (depth in
[`../../skills/agy-native/references/distribution-and-run-control.md`](../../skills/agy-native/references/distribution-and-run-control.md)).
**Read the base skill first**; this file only maps that skill onto Codex-native
tooling and restates the load-bearing guardrails. AGY ≠ gemini-cli — use `agy`
affordances (`agy plugin`, `agy --print`, `--add-dir`, `--sandbox`), never the
retired `gemini` CLI lane.

## Codex tool mapping

- **Read** → shell reads (`cat`/`sed -n`) or `rg`.
- **Write** → create files via `apply_patch` or shell redirection.
- **Edit / MultiEdit** → `apply_patch`.
- **Bash** → `shell_command` (your native shell tool).
- **Grep** → `rg` (fallback `grep`).
- **Glob** → `rg --files` or `find`.
- **Subagent / parallel author!=judge** → Codex runs single-threaded; realize the
  two roles as **two separate `codex exec` invocations** (distinct processes =
  distinct contexts). Do NOT reuse one Codex session for both author and judge.
- **Scheduling the tick** → a bushido timer / cron calling `codex exec` or
  `agy --print`, never an in-session loop that reuses context.

## Steps

1. **Read the base skill.** Open `../../skills/agy-native/SKILL.md` and load Overview, the six
   Critical Constraints, and the five-phase Workflow. Everything below assumes it.

2. **Verify the image is live.** `which agy && agy models | head`; confirm
   `~/.gemini/antigravity-cli/{brain,knowledge}` exists; `agy plugin list`.
   Stop if `agy` does not resolve or no model lists.

3. **Package + expose the laws.** Lay out the `agy-control-plane/` plugin tree
   (plugin.json, rules/, workflows/, subagents/, hooks.json, skills/), then
   `agy plugin validate ./agy-control-plane` and `agy plugin link` (dev) or
   `install` (released) + `enable`; `agy plugin list` to confirm and record a
   rollback (`disable`/`uninstall`). A bare `SKILL.md` under `~/.gemini/skills/`
   is portable — no plugin.json needed just to expose a skill. The retired
   gemini `skills`+`extensions` split collapses into the single AGY **plugin**
   unit (no `agy extensions`). Source of truth stays in AgentOps; don't
   hand-edit managed runtime copies.

4. **Author tick (context A).** Drive the worker with `agy --print --add-dir
   "$REPO" --dangerously-skip-permissions` (or `codex exec` against the repo):
   claim one ready bead via `br`, implement only it in an isolated worktree,
   make a scoped commit, write evidence to `brain/` as `userFacing:true`.
   **Do NOT close the bead** — a judge will.

5. **Judge verdict (context B — separate process).** Spawn a SECOND, clean
   invocation (`agy --print` with a fresh conversation, or a separate
   `codex exec`) with a read-mostly scope: validate the bead against its
   evidence artifact ONLY, emit PASS/WARN/FAIL to `brain/` as a `userFacing`
   verdict, edit no code. On a split/false-FAIL, spawn a third tie-break
   context. `br close <id>` **only on PASS**.

6. **Persist + tick.** Scoped `git commit` and push for the repo; the brain artifact
   is the durable memory. Re-enter step 4 with the next ready bead. State lives
   on the bus/artifact, never in a live session.

7. **Run the quality rubric** from `../../skills/agy-native/SKILL.md` before declaring the tick green
   (two distinct `conversation_id`s, evidence-gated close, non-overlapping
   scopes, dcg hook present, nothing under `~/dev/agentops`, plugin validated).

## Guardrails

- **Never use a different agent CLI as the Codex executor.** Drive AGY workers
  with `agy --print` / `agy -i` when the AGY image is the target, and Codex work
  with `codex exec`. (Base Rule 1.)
- **author != judge, always two contexts.** The process that closes a bead must
  not be the one that validated it. Two separate `codex exec` / `agy --print`
  invocations, never `-c`/`--continue` reuse. (Base Rule 2.)
- **Evidence-gated close.** A bead closes only against a persisted verdict
  artifact (`brain/*.md` with `userFacing:true` or a committed repo file), never
  chat text. Consume an agent's published compression, never its live session.
  (Base Rule 3.)
- **Worktree / `--add-dir` isolation.** Author and judge get isolated worktrees
  or non-overlapping `--add-dir` scopes; no two roles edit the same file.
  (Base Rule 4.)
- **`dcg` guard stays on.** Keep the `BeforeTool` → `dcg` hook in
  `~/.gemini/settings.json` even under `--dangerously-skip-permissions`. Under
  Codex's own `danger-full-access` sandbox, still route destructive commands
  through `dcg`. (Base Rule 5.)
- **Match permission to role.** Author = `--dangerously-skip-permissions` with a
  tight `--add-dir`; judge = default (no auto-approve), read-mostly scope;
  full-auto only inside `--sandbox`. A validator that can edit is a false-close
  path. (Base Rule 6.)
- **Operator-side; invoke-never-rebuild.** Do not write under `~/dev/agentops`,
  do not push agentops, do not re-author AGY — own a thin adapter only. Never
  emit this skill's content into client-facing material. (Base Rule 7.)
