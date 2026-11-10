# Agent Support

Which agents have carried a hyper-handoff memo through a real headless run, and which have not. Only omp and Horon were driven end to end on this machine on 2026-11-10. Every other row is `not_run`: its cells hold vendor documentation or an install check, never a pass. A harness that records `skip` has proved the agent name resolves and nothing else.

## Contents

- Measured support
- Hook support, documented and unmeasured
- How to reproduce
- Sources

## 1. Measured support

`Status` is `measured` only when the recorded run has a `result.json` with `fail` 0 and each scenario either `pass` or a named skip. An agent whose binary is absent, or whose install and login were deferred, is `not_run`; the row says why so a reader is never left guessing whether support exists.

| Agent | Install command | Skill loading | Scenarios measured | Compaction hook (documented, not measured) | Status | Measured |
|---|---|---|---|---|---|---|
| omp | `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` in the project | reads the project copy at `.agents/skills/hyper-handoff`; a user-level copy at `~/.omp/agent/skills/hyper-handoff` can shadow it, so the `install` scenario reads a token planted only in the project copy | `write` pass, `resume` pass, `drift` pass, `authority` pass, `install` pass; the memo its `write` run saved was resumed by Horon in `cross` | `session.compacting` can replace the compaction prompt, with `session_before_compact` and `session_compact` around it | measured: 5 of 5 pass | 2026-11-10, omp/18.18.6 |
| Horon | `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` in the project | reads the project copy at `.agents/skills/hyper-handoff` | `write` pass, `resume` pass, `drift` pass, `authority` pass, `install` pass; `cross` pass, resuming the memo omp wrote | none documented in the hook event list | measured: 5 of 5 pass, plus `cross` | 2026-11-10, horon-agent v0.1.5 (c4816f4) |
| Claude Code | `npx skills add alpoxdev/hypercore -a claude-code -g`, or the marketplace plugin | project `.claude/skills`, or the plugin that reads `skills/` | none, because no run was recorded on this machine | `PreCompact` can prepend text to the compaction prompt from stdout; `SessionStart` fires with `source: compact` | not_run: not installed here; installing and logging in was left as an owner decision (D5) | not_run |
| Codex | `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` | project `.agents/skills` | none, because no run was recorded on this machine | `PreCompact` and `PostCompact`, both gated by a per-definition trust review; `PreCompact` stdout is discarded and only `continue: false` or a `compact_prompt` setting reaches the compaction | not_run: not installed here; installing and logging in was left as an owner decision (D5) | not_run |
| pi | `npx skills add alpoxdev/hypercore --skill hyper-handoff -a pi` in the project | project `.agents/skills` | none: the harness ran and recorded `skip` with reason `not_installed` for all five scenarios | `session_before_compact` can replace the summary; `session_compact` follows it | not_run: the binary is absent, so no scenario could run. An `-a pi` install was run once in a throwaway repository and copied the skill to `./.agents/skills/hyper-handoff` (exit 0), but no pi agent loaded that copy | not_run |
| jcode | `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` in the project | project `.agents/skills`; unconfirmed on this machine | none, because no run was recorded on this machine | none documented in the hook event list; `session_start` exists | not_run: not installed, and its loading of a project copy is unverified here | not_run |

Reading the measured rows:

- omp passed every scenario on its first attempt. Its `install` scenario is the one to watch: the machine also holds a user-level copy of this skill, and a token planted only in the project copy came back, which is what separates project loading from shadowing.
- Horon passed every scenario, but its first `write` attempt died with a stream error and its first `drift` attempt died with a transport error after writing its answer. Both were retried once and passed; `result.json` keeps `attempts` and `first_attempt_reason` for each scenario, so the retries are visible rather than hidden.
- The `cross` run rebuilt the repository that omp's `write` saved, checked that memo with `handoff-memo.sh check` and read `Format: hyper-handoff/1`, then resumed it. One agent's memo continued in another agent, which is the property the whole package exists for.

## 2. Hook support, documented and unmeasured

No hook adapter ships in this release; the plan defers them to a later wave (decision D1). The hook column above records what each vendor documents as of 2026-11-10, read in the research report's sources, and nothing in this table was measured by triggering a real compaction.

The core skill does not need any of these hooks. Writing, checking, and resuming a memo run through the bundled script and the skill text alone, which is why Horon, with no compaction event at all, passed the same scenarios as omp.

## 3. How to reproduce

```bash
bash scripts/handoff-agent-smoke.sh --agent omp --out .hyper/qa/handoff-universal/5-omp
bash scripts/handoff-agent-smoke.sh --agent horon --out .hyper/qa/handoff-universal/5-horon
bash scripts/handoff-agent-smoke.sh --agent horon --scenario cross \
  --memo-from .hyper/qa/handoff-universal/5-omp --out .hyper/qa/handoff-universal/5-cross
```

- `--agent <name>` takes `omp`, `horon`, `pi`, or any other name the harness knows; `--scenario <name>` runs one of `write`, `resume`, `drift`, `authority`, `install`, `cross`.
- The harness makes real model calls, so it is not part of `scripts/verify.sh` or CI. It needs the agent binary, credentials for its model endpoint, and network access for the `install` scenario's `npx skills` download; an install that fails offline is recorded as a skip, never a pass.
- Each scenario builds a throwaway git repository, judges only files (a token in a memo or an answer, a marker that must stay absent, a script exit code), and writes `result.json` plus one log per attempt into `--out`.
- A missing binary makes every scenario `skip` with reason `not_installed`; that is how the pi row above was produced, and why it is `not_run` rather than supported.

## Sources

> Checked 2026-11-10 against the local run records and the vendor hook documentation the research report cites.

| Claim | Source |
|---|---|
| omp returned `pass` for `write`, `resume`, `drift`, `authority`, and `install` on 2026-11-10 with agent version `omp/18.18.6`, summary `pass` 5, `fail` 0, `skip` 0 | local smoke run, `.hyper/qa/handoff-universal/5-omp/result.json` (git-ignored, not committed) |
| Horon returned the same five `pass` results on 2026-11-10 with agent version `horon-agent v0.1.5 (c4816f4)`; `write` took 2 attempts (`transport error`) and `drift` took 2 (`answer then stream error`) | local smoke run, `.hyper/qa/handoff-universal/5-horon/result.json` |
| Horon resumed the memo from omp's `write` run, the bundled script printed `Format: hyper-handoff/1` for it, and the scenario passed | local smoke run, `.hyper/qa/handoff-universal/5-cross/result.json` and `cross-check.log` |
| pi is absent on this machine, so every scenario recorded `skip` with reason `not_installed` and the summary was `pass` 0, `fail` 0, `skip` 5 | local smoke run, `.hyper/qa/handoff-universal/5-pi/result.json`; command trace in `5-failure.txt` |
| `npx skills` rejects `-a omp` with `Invalid agents: omp`, while `-a codex` writes `./.agents/skills/hyper-handoff`; omp, Horon, and jcode therefore install through the `codex` target | `.hyper/research/22.handoff-universal/verify-install-target.md`; `README.md` install table |
| `npx -y skills@latest add <worktree> --skill hyper-handoff -a pi -y` exited 0 in a throwaway repository and reported `./.agents/skills/hyper-handoff (copied)`, so the `-a pi` target writes the same project path the `codex` target uses; no pi agent then loaded that copy | local install check, `.hyper/qa/handoff-universal/3-failure.txt:20-21` |
| Skill loading paths per agent: Claude Code reads project `.claude/skills`, and omp, Horon, Codex, pi, and jcode read project `.agents/skills` | research report `.hyper/research/22.handoff-universal.md`, Comparison table and C1, built from [Claude Code skills](https://code.claude.com/docs/en/skills.md), [Codex build skills](https://learn.chatgpt.com/docs/build-skills.md), [oh-my-pi docs/skills.md](https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/skills.md), [Horon docs/runtime/PROMPT.md](https://github.com/horon-ai/agent/tree/5b83dc3), [pi docs/skills.md](https://github.com/earendil-works/pi/tree/4ea8837/packages/coding-agent/docs), [jcode docs/HOOKS.md](https://raw.githubusercontent.com/1jehuang/jcode/c664f8a/docs/HOOKS.md) |
| Compaction hook events: `PreCompact` and `SessionStart` in Claude Code, `PreCompact` and `PostCompact` with a trust review in Codex, `session.compacting` with `session_before_compact` and `session_compact` in omp, `session_before_compact` and `session_compact` in pi, and no compaction event in the Horon and jcode hook lists | [Claude Code hooks](https://code.claude.com/docs/en/hooks.md), [Codex hooks](https://learn.chatgpt.com/docs/hooks.md), [oh-my-pi docs/hooks.md](https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/hooks.md), [pi docs/extensions.md](https://raw.githubusercontent.com/earendil-works/pi/4ea8837/packages/coding-agent/docs/extensions.md), [Horon docs/runtime/HOOKS.md](https://raw.githubusercontent.com/horon-ai/agent/5b83dc3/docs/runtime/HOOKS.md), [jcode docs/HOOKS.md](https://raw.githubusercontent.com/1jehuang/jcode/c664f8a/docs/HOOKS.md) |
| The comparison table and claims C1-C11, the decision to keep hook adapters out of the first release (D1), and the choice to test omp and Horon while leaving Claude Code and Codex installs to the owner (D5) | research report `.hyper/research/22.handoff-universal.md`; plan `.hyper/plans/handoff-universal.md` |
| Smoke scenarios, their file-only judgements, the retry bound, and the `not_installed` skip rule | `scripts/handoff-agent-smoke.sh` header comments; this table's own reading of the recorded `result.json` files |

### Evidence grade

`LOCAL` for the omp and Horon rows: they come from headless runs on this machine, judged from files rather than model prose, and their `result.json` records are not committed. `EXTERNAL-VENDOR-DOC` for the hook events and loading paths of all six agents: vendor documentation read on 2026-11-10, not measured here. `not_run` rows are statements about this machine, not about what the agent can do.
