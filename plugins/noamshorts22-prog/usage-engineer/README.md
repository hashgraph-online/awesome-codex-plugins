# usage-engineer (`ue`)

[![CI](https://github.com/noamshorts22-prog/usage-engineer/actions/workflows/ci.yml/badge.svg)](https://github.com/noamshorts22-prog/usage-engineer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

**Stop paying for wasted agent work.** `ue` is a local CLI that measures and cuts the work coding
agents throw away: 5,000-line logs pasted into context, the same failing command retried, stale
project maps, duplicated instructions. It works with **Codex CLI** and **OpenCode**.

- Zero dependencies, one Python file, no network calls, ever.
- Never reads `auth.json`, cookies, tokens or chat text.
- Never changes your model or reasoning settings. Everything that writes is opt-in and reversible.

## Install

```
pipx install git+https://github.com/noamshorts22-prog/usage-engineer
ue doctor
```

Or run from a checkout with `python ue.py <command>` (Windows: `ue.cmd <command>`).

### As an agent skill

`ue` also ships as an [Agent Skill](https://agentskills.io) that tells the agent when to use it:
long logs go to a file and get compacted, identical failures are not retried, and maps are checked
before work resumes. The skill bundles `ue.py`, so nothing else needs installing.

| Agent | Install |
|---|---|
| Codex CLI | `codex plugin marketplace add noamshorts22-prog/usage-engineer` then `codex plugin add usage-engineer@usage-engineer` |
| Claude Code | `claude plugin marketplace add noamshorts22-prog/usage-engineer` then `claude plugin install usage-engineer@usage-engineer` |
| Any agent (Cursor, Gemini CLI, OpenCode, ...) | `npx skills add noamshorts22-prog/usage-engineer` |

The skill itself is [skills/usage-engineer/SKILL.md](skills/usage-engineer/SKILL.md).

## Two minutes to your first numbers

```
ue audit                      # where did my Codex/OpenCode usage go? (read-only, redacted)
ue summarize-log --file build.log   # keep every error, drop the noise, store the full copy
ue map build --project .      # snapshot the project; `map check` tells you when it is stale
```

## Commands

| command | what it does | writes |
|---|---|---|
| `audit` | usage baseline from local Codex rollout JSONL and the OpenCode SQLite DB, with waste signals; redacted | optional JSON via `--json-out` |
| `summarize-log --file X` | compact view that keeps every failure/error line plus context; stores the byte-exact original and prints its path | `--out` dir |
| `prepare-context --project DIR` | small task pack: request, constraints, git commit/diff id, path hashes, verification commands | `--out` md + json |
| `map build` / `map check` | versioned project map; `check` exits 1 and lists files when anything changed | map json |
| `instructions scan/duplicates/verify` | AGENTS.md inventory, paragraph-level duplicate mapping, mandatory-rule verification | optional json |
| `compare --a R1 --b R2` | per-task paired comparison of two bench runs; refuses non-comparable records; flags quality regressions | stdout |
| `apply-profile --target codex` | opt-in Codex profile `$CODEX_HOME/usage-efficient.config.toml`, used via `codex --profile usage-efficient` | profile + backup + registry |
| `apply-profile --target opencode-project --project DIR` | project `opencode.json` that references the ue instructions (aborts if one exists) | project file |
| `rollback --target codex` | restores the original state; aborts if the file changed after apply | - |
| `bench list/plan` | the 4 frozen paired benchmark cases and the exact commands (no model calls) | stdout |
| `bench run --runner codex --max-calls N --confirm` | opt-in live A/B run with a hard invocation cap and no automatic retries | state dir |
| `doctor` | environment check: versions, config paths, profiles | stdout |
| `selftest` | 34 deterministic tests, no model calls | - |

## Measure before you believe

Efficiency claims about agents are cheap. `ue bench` makes them testable: each of the four frozen
cases (off-by-one bugfix, cross-file rename, regression test, RTL layout fix) runs in a fresh
isolated copy, the agent never sees the solution or the acceptance script, and `ue compare` refuses
to compare runs that used different models, reasoning levels or case versions.

```
ue bench plan
ue bench run-all --runner codex --max-calls 8 --confirm
ue compare --a <baseline-run.json> --b <profile-run.json>
```

### First live result (2026-10-21, n=1 per cell, codex-cli 0.163.0, default model)

A = baseline, B = `context-pack` (a prepared project map handed to the agent up front).

| Case | A total tokens | B total tokens | A pass | B pass |
|---|---:|---:|:-:|:-:|
| bugfix-offbyone | 325,468 | 364,474 | yes | yes |
| crossfile-rename | 286,107 | 281,159 | yes | yes |
| regression-test | 294,160 | 266,461 | yes | no* |
| rtl-cart | 296,432 | 535,727 | yes | yes |

On the three cases both variants passed, B used **30% more** tokens (+273,353), mostly cached
input. So on these small fixtures the context pack does not pay for itself, and `ue` does not claim
it does. One sample per cell is noise-level; treat this as a demonstration of the method, not a verdict.

\* B's failure was environmental: the file the agent wrote under the Codex Windows sandbox was
not readable by the acceptance script (`PermissionError`), so it says nothing about B's quality.

## Safety properties

- Audit output never includes transcript text and redacts your home directory as `%HOME%`.
- Unknown metrics are reported as `UNKNOWN` / `null`, never as `0`.
- `apply-profile` backs up any existing file and records its SHA-256; `rollback` refuses to
  overwrite later edits (exit code 3).
- `apply-profile --target opencode-global` is refused by design.
- Benchmarks refuse to run without `--max-calls` and `--confirm`. `ue` caps the number of
  invocations; it cannot cap tokens or money.

State lives in `~/.usage-engineer` (override with `UE_STATE_DIR`).

## Known limitations

- Model-level efficiency is barely measured: one live run per cell so far (see above). Live runs
  cost quota, so results from your machine are very welcome.
- On Windows, files the agent creates inside the Codex sandbox can be unreadable to the
  acceptance script, which then reports a false failure.
- Token figures derived from character counts are estimates (4 characters per token).
- The OpenCode audit covers `session` table totals, not per-message parsing.

## Roadmap

- Claude Code, Gemini CLI and Aider support in `audit` and `bench`
- A GitHub Action that posts `ue audit` waste signals on agent-authored PRs
- More benchmark cases, contributed by the community

Contributions welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
