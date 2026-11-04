<!-- GENERATED FILE — DO NOT EDIT.
     Rendered from hosts/capabilities.yaml by hosts/render_capabilities.py.
     Edit the YAML and re-render; CI fails if this file differs from a fresh
     render, so a hand-edit cannot ship. -->

# Host capabilities

Human-readable view of `hosts/capabilities.yaml`. **Nothing reads this file at run
time** — not an orchestrator, not a shim, and above all not a driving agent. The
YAML is consumed by `multi_llm.py`, by `install-host` and by the tests; this
document exists for people reading the repo.

Every value carries a **provenance**: `verified` means a recorded live smoke run
observed it, `documented` means host docs only, `unknown` is the shipping default.
A `documented`-only value never selects the non-conservative path — which is why
hosts whose native subagent dispatch is merely documented ship as
`subagents: executor`, and why a documented command-timeout ceiling is worked
around with `--detach` rather than trusted.

The three **capability verbs** are the spine of each entry. The host-neutral
instruction core says *spawn subagents* / *ask the user* / *run detached*; the
columns below say what each resolves to, and a shim bakes that resolution in as a
sentence when it is installed.


| Host | Shim (repo → installed) | `arguments` | *spawn subagents* | *ask the user* | *run detached* | Default runner | `nested_exec` (spawn/network/creds) | Max subagents | Timeout ceiling | Verified |
|---|---|---|---|---|---|---|---|---|---|---|
| `claude-code` | *not rendered* → `SKILL.md` | `placeholder` | `native` (`Task`) — verified | `structured` (`AskUserQuestion`) — verified | `native` (`run_in_background`) — verified | `claude-code:sonnet` | allowed/allowed/allowed | 10 | 600 s (not raisable) | `arguments`, `ask`, `default_subagent_runner`, `detach`, `installable`, `multi_turn`, `native_tool`, `next_command.skill`, `shim_max_lines`, `subagent_tiers`, `subagents` |
| `codex` | `hosts/codex/shim.md.tmpl` → `SKILL.md` | `placeholder` | `executor` (`agent`) — documented | `free-text` — documented | `python` — documented | `codex:gpt-6-astra` | unknown/unknown/unknown | 4 | none documented | `invocation`, `next_command.default`, `next_command.package`, `package`, `session_runner_provider` |
| `opencode` | `hosts/opencode/shim.md.tmpl` → `commands/multi-llm.md` | `placeholder` | `executor` (`task`) — documented | `free-text` — documented | `required` — verified | `opencode:opencode/big-pickle` | unknown/unknown/unknown | 4 | 120 s (raise via env: `unknown`, config: `unknown`) | `arguments`, `detach`, `headless_invocation`, `install_paths`, `installable`, `invocation`, `multi_turn`, `next_command.default`, `next_command.package`, `package`, `reload`, `shim` |

## Per-host notes and stripped variables

### `claude-code`

- Installable: `false`; reload after install: `none`
- Invocation (documented): invoke it as `/multi-llm:multi-llm <mode-flag> <plan-path> [options]`, or as `/multi-llm <mode-flag> <plan-path> [options]` when the skill is installed as a plain skill under one of `install_paths`.
- Driving agent gets a turn after a command returns (`multi_turn`): `true` — verified. A `false` here is what addresses a failed batch's retry instruction to the human rather than to an agent that will never read it.
- Subagent tiers: full `sonnet`, cheap `haiku`
- Verb sentences a rendered shim carries:
  - **Spawn subagents** — call your host's own subagent tool `Task`: when the task carries `task.prompt_path`, tell the subagent to read that file in full — through line `task.prompt_lines`, paging if one read returns fewer — and follow it verbatim, printing only what it asks; if the file is absent, or the task has no `prompt_path`, pass `task.prompt` verbatim. Take the role from `task.subagent_type` when your tool needs one, and write the JSON it returns to `task.output_path`. Never pass `--exec-subagents` on this host.
  - **Ask the user** — call your host's own structured question tool `AskUserQuestion`, then copy the selected option's command verbatim. Never compose a flag from the user's words.
  - **Run detached** — use your host's own background mechanism `run_in_background`, redirecting stdout and stderr to the phase dir's `orchestrator-run.log` (`> … 2>&1`, the one dispatcher command that takes a redirect: every foreground call runs bare), and give that launch call a timeout of its own, the longest the parameter takes: 7200000 here, in milliseconds (2 hours; a session whose maximum is lower clamps it rather than refusing it). Without one the mechanism stops the command at its default deadline, as short as ten minutes, and a fan-out still running then dies mid-run (exit `143`, `next` `null`). Never pass `--detach` on this host. Then make one **non-waiting** `status <plan> <selector> --host <this host's id> --view run --exit-zero` call — no `--wait`, no `--timeout`, so it answers in well under a second — and relay its `progress:` line and `models:` table once: the count is on the one, and the other's rows are the only thing that says which CLI and model each of them runs. The run writes that roster a few seconds after launch, so repeat that one call once if no table printed yet, adding `--wait --timeout 10` as the wait (never `sleep` before a call: a call that does not start with `uv` loses its permission rule) — and a table that *does* print can still be the previous run's, because the phase dir is re-used and the write that claims it for this fan-out drops the predecessor's `progress` only about 0.2 s in: a table under a `progress:` step that is not `fanout` is the last run's, so make that call again rather than relaying it. That step is the whole test — a head line reading `finished in foreground (…)` rather than `running` is what a re-used dir prints all run long once an earlier `--detach` run left its own terminal `run` record in it, so the tense names no run. Then poll while it runs, one foreground `status <plan> <selector> --host <this host's id> --view run --wait --timeout <interval> --exit-zero` call per turn at a 120-300 s interval, relaying the rendered `progress:` line and, whenever one prints, the `just finished:` line that names the model that turned terminal during that wait — verbatim. Its absence claims nothing: that line is a difference between two readings taken inside one wait, so a model that finished in the gap between polls is already terminal when the next poll takes its baseline — so every poll compares its `models:` table with the previous poll's and names every newly terminal row that line did not name, copying its spec and state word out of the row — a copy, never a recount. Nothing else from the view is relayed mid-run. Spell `--host` out yourself — no launcher printed a command to copy it from, and without it the wait is clamped under the tightest ceiling on record — and give the call itself a timeout of at least the interval plus 30 s, in that parameter's own unit — milliseconds here, so 330000 for a 300 s interval, not 330, which is a third of a second — because this host's default per-call cap is shorter than the interval and would otherwise kill every poll from the first. No exit code from that poll ends the loop except `1`, the unreadable one: nothing on this host names one invocation, so without `--exit-zero` `2` is the steady state and a `0` or a `3` belongs to an earlier run in the same dir and names no verdict for this one: read the exit code as nothing, relay the rendered line exactly as on a `2`, and keep polling. Both calls carry `--exit-zero` so every answer that was read exits `0` and none shows as an error. The loop ends when the background mechanism reports the process exited; read the markers and output paths from `orchestrator-run.log` then, and report a non-zero exit status with that path rather than retrying. A stop at the mechanism's time limit (exit `143`, `next` `null`, `status` still reading `running in foreground`) names no way forward of its own, so offer the user each of these and run none yourself: the launch, made again the same way with `--force` added, which resumes, keeping each model whose result file is in the phase dir (`[SKIP]`) and running the rest (without it, review-code and the commit modes refuse a dir holding results, exit `3`; never `--rerun-all`); and, on a review mode with at least one such file, its `--reaggregate`, which reports with those and lists the rest as failed. Say which models have a file: a `done` row can have none, its result held in memory for the fan-out's end. Where the mode instruction names a continuation for a stopped run (a composite's `[IMPROVE_RERUN]`), offer that instead. The mode instruction names the selector and the rest of the loop.
- Install paths (project): `.claude/skills/multi-llm`
- Install paths (global): `$HOME/.claude/skills/multi-llm`
- Install paths (legacy): *none*
- Runners:
  - `claude-code`: bundled=`true`, needs_auth=`false`, profiles=[generate, agent-readonly, agent-write], usage=`full`
  - `cursor-agent`: bundled=`false`, needs_auth=`true` (`cursor-agent login`), profiles=[generate], usage=`partial`
- Refuse-to-start guards stripped from a dispatched runner: `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`
- Session-scoping variables stripped: `CLAUDE_SESSION_ID`, `CLAUDE_SKILL_DIR`
- Sanctioned exceptions that survive stripping: *none recorded* — audited, found nothing
- Nested-exec notes: Native subagents run in-session; the executor is not on the default path for this host.

### `codex`

- Installable: `true`; reload after install: `new-session`
- Invocation (verified): invoke it by name rather than as a slash command — `Use the multi-llm skill with exactly these arguments: <the same arguments the Claude Code skill takes>`. Codex installs this shim as a **skill**, which is model-invoked rather than typed: its composer answers `/multi-llm` with `Unrecognized command`.
- Driving agent gets a turn after a command returns (`multi_turn`): `true` — documented. A `false` here is what addresses a failed batch's retry instruction to the human rather than to an agent that will never read it.
- Subagent tiers: resolved from `providers.yaml` `driver.subagent_runner{,_cheap}` (this host does not dispatch subagents natively)
- Verb sentences a rendered shim carries:
  - **Spawn subagents** — run the dispatcher with `--exec-subagents`: it dispatches every materialized task itself and continues past each marker in the same process. Never spawn a subagent by hand on this host.
  - **Ask the user** — print the numbered option block exactly as the dispatcher rendered it and copy the selected option's command verbatim, and only under `--interactive`. Otherwise the documented `--yes` default applies and nothing is asked.
  - **Run detached** — pass `--detach` (which implies `--yes`) on every fan-out mode, then poll `status <plan> --view run`. Do this even when you expect the run to be quick: a fan-out started in the foreground cannot be handed back to once your turn ends. Only a single-model, non-fan-out call may stay in the foreground. Never combine `--detach` with a host background mechanism — pick one.
- Install paths (project): `.codex/skills/multi-llm`
- Install paths (global): `$HOME/.codex/skills/multi-llm`
- Install paths (legacy): `$HOME/.codex/prompts/multi-llm.md`
- Runners:
  - `claude-code`: bundled=`false`, needs_auth=`true` (`claude login`), profiles=[generate, agent-readonly, agent-write], usage=`full`
  - `codex`: bundled=`true`, needs_auth=`false`, profiles=[generate, agent-readonly, agent-write], usage=`full`
- Refuse-to-start guards stripped from a dispatched runner: *none recorded* — the env diff has not run yet
- Session-scoping variables stripped: *none recorded* — the env diff has not run yet
- Sanctioned exceptions that survive stripping: *none recorded* — the env diff has not run yet
- Nested-exec notes: Filled by the Phase 2 nested-exec smoke: --exec-subagents launched from inside `codex exec`'s own sandboxed shell, for both the same-host runner and a third-party one.

### `opencode`

- Installable: `true`; reload after install: `new-session`
- Invocation (verified): invoke it as `/multi-llm <the same arguments the Claude Code skill takes>`.
- Driving agent gets a turn after a command returns (`multi_turn`): `true` — verified. A `false` here is what addresses a failed batch's retry instruction to the human rather than to an agent that will never read it.
- Subagent tiers: resolved from `providers.yaml` `driver.subagent_runner{,_cheap}` (this host does not dispatch subagents natively)
- Verb sentences a rendered shim carries:
  - **Spawn subagents** — run the dispatcher with `--exec-subagents`: it dispatches every materialized task itself and continues past each marker in the same process. Never spawn a subagent by hand on this host.
  - **Ask the user** — print the numbered option block exactly as the dispatcher rendered it and copy the selected option's command verbatim, and only under `--interactive`. Otherwise the documented `--yes` default applies and nothing is asked.
  - **Run detached** — pass `--detach` (which implies `--yes`) on every fan-out mode and poll `status <plan> --view run`. This host caps a single shell command below a fan-out's runtime, so no foreground fan-out path is offered.
- Install paths (project): `.opencode/commands`
- Install paths (global): `$XDG_CONFIG_HOME/opencode/commands`, `$HOME/.config/opencode/commands`
- Install paths (legacy): *none*
- Runners:
  - `claude-code`: bundled=`false`, needs_auth=`true` (`claude login`), profiles=[generate, agent-readonly, agent-write], usage=`full`
  - `opencode`: bundled=`true`, needs_auth=`false`, profiles=[generate, agent-readonly, agent-write], usage=`full`
- Refuse-to-start guards stripped from a dispatched runner: *none recorded* — the env diff has not run yet
- Session-scoping variables stripped: *none recorded* — the env diff has not run yet
- Sanctioned exceptions that survive stripping: *none recorded* — the env diff has not run yet
- Nested-exec notes: Filled by the Phase 3 nested-exec smoke from inside `opencode run`.
