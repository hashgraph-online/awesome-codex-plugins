---
name: since-cutoff
description: Find which dependency APIs this project's Python code uses changed after the model's training cutoff (no model calls), write short AGENTS.md or CLAUDE.md notes from the API diff, each with its source, and keep them in step with the lockfile; optionally measure which of the changes the model gets wrong. Use when the user asks whether the model knows their library versions, when code keeps failing on renamed or removed library APIs, or after upgrading dependencies. Trigger with requests such as "does the model know my openai version", "scan my dependencies for API changes" or "check whether the library notes are up to date".
license: MIT
compatibility: Needs since-cutoff on PATH, or uv or pipx to run it, and network access to PyPI. The run command also needs model access (the claude CLI or a provider API key) and the basedpyright type checker (pip install "since-cutoff[run]", or uvx --with basedpyright since-cutoff run); scan, sync and status make no model calls, and status works offline.
allowed-tools: Bash(since-cutoff scan:*), Bash(since-cutoff sync:*), Bash(since-cutoff status:*), Bash(since-cutoff run:*), Bash(since-cutoff models:*), Bash(since-cutoff unapply:*), Bash(uvx since-cutoff:*), Bash(uvx --with basedpyright since-cutoff:*), Bash(pipx run since-cutoff:*), Read
metadata:
  author: Mohammad Hijjawi
  version: "0.5.0"
---

# since-cutoff

`since-cutoff` is a command-line tool that finds the APIs a project's dependencies changed after
the model's training cutoff and writes notes about them, each with its source. Run the tool and
report what it prints.

## Overview

- `since-cutoff scan` compares, for each dependency, the public API of the latest release on or
  before the model's training cutoff with the version the project pins (a static diff, no model
  calls), and lists the changed APIs the code uses.
- `since-cutoff sync` writes notes from that diff into a marked block in AGENTS.md or CLAUDE.md
  and keeps them in step with the lockfile; `since-cutoff status` checks the block offline, and
  `since-cutoff unapply` removes it.
- `since-cutoff run` is optional. It does the measuring itself by calling a fresh copy of the
  model with no tools and no project context, so **do not answer the probe tasks yourself and
  do not guess results**.

## Prerequisites

- A Python project with its dependencies in `pyproject.toml`, `requirements.txt` or a lockfile.
- since-cutoff on PATH, or uv or pipx to run it (`uvx since-cutoff`, `pipx run since-cutoff`).
- Network access to PyPI; `status` works offline.
- For `run` only: model access, through the `claude` CLI for Claude Code models or the
  provider's API key for other models, and the basedpyright type checker: `pip install
  "since-cutoff[run]"`, or run it as `uvx --with basedpyright since-cutoff run`. Without it,
  `run` stops at once and says so. `scan`, `sync` and `status` make no model calls.

## Instructions

1. Work from the project root (the directory with `pyproject.toml`, `requirements.txt` or a lockfile).
2. Pick the command. Use the arguments the user gave, if any (`scan`, `sync`, `status` or `run`,
   with flags such as `--apply`, `--quick` or `--model`); otherwise:
   - quick look, no model calls: `since-cutoff scan` (then offer `sync`, step 7)
   - full measurement, with notes a model writes and keeps only when their example
     type-checks: `since-cutoff run --quick`
3. Name the model. Without `--model`, the tool tests the model your coding agent is set up with
   (`SINCE_CUTOFF_MODEL`; inside Claude Code, only Claude Code's settings; elsewhere the Claude
   Code, Codex, Gemini CLI, OpenCode and Aider settings, the project's before the user's) and
   says where it read it ("model from ..."). If that is not the model you are, or it warns that
   no model setting was found, add `--model PROVIDER:MODEL` for the model you are (for example
   `--model openai:gpt-5.4`, or `--model claude-code:MODEL` for a model picked with `/model`).
   `run` calls Claude Code models through the `claude` CLI and other models through their
   provider's API key.
4. Before `run`, tell the user that it sends prompts (package names, versions, public API
   signatures and generated tasks, never their source code) to the model provider they choose,
   uses their API credits or Claude Code usage, and can take 5-20 minutes. Wait for a yes.
   `scan` needs no confirmation.
5. Run it. If `since-cutoff` is not installed, use `uvx since-cutoff` with the same arguments
   (or use `pipx run since-cutoff`); for `run`, `uvx --with basedpyright since-cutoff run`,
   which adds the type checker. Start `run` in the background or with a long timeout, not a
   2-minute foreground call. Everything is cached, so re-running after an interruption resumes
   quickly.
6. Summarise the result card: the model and its training cutoff, how many dependencies changed
   after the cutoff, what was stale, and the held-out before/after numbers. Quote each interval
   with the number it belongs to: the bootstrap CI goes with the difference of the task-level
   rates, the other CI with "changes fixed: X of Y". If the run compared baseline notes
   (`--compare`), give each block's "changes fixed" with its CI, and call one block better
   only when report.md's head-to-head sign test for it has a small p-value.
7. Only write notes into the user's files if they asked for it. After `scan`, run
   `since-cutoff sync --dry-run`, show the user the diff it prints, and only when they agree run
   `since-cutoff sync --yes`: it writes the notes from the API diff into a marked block in
   AGENTS.md (or CLAUDE.md if that is the file the project uses) and, run again later, keeps
   them in step with the lockfile. When `scan` suggests `sync --scope imported` (the code uses
   none of the changed APIs yet), add it to both commands. After `run`, `--apply` writes that
   run's notes in place of the whole block; `since-cutoff sync` then adds the notes from the
   diff for the other changed APIs the code uses, keeping the run's `[type-checked]` ones.
   `since-cutoff unapply` removes the block again. `since-cutoff status` says, without the
   network, whether the notes still match the lockfile; from since-cutoff 0.4.0 the Claude Code
   plugin runs it when a session starts (the first time, uvx downloads since-cutoff).

## Output

- The terminal: the model, its training cutoff and where the tool read the model, the
  dependencies that changed after the cutoff, and the changed APIs the code uses, each with its
  note. `run` adds the result card of step 6.
- `.since-cutoff/report.md`: the full report. Read it when the user wants details.
- The notes block in AGENTS.md or CLAUDE.md, written only by `sync --yes` or `run --apply`. The
  notes in it are API reference facts about the versions the project pins: what was removed,
  renamed or deprecated after the release at your training cutoff, each tagged with what was
  checked, for example `[diff]` (a static comparison of the two releases' public APIs),
  `[diff + library]` (the library's own deprecation text names the replacement),
  `[diff + move checked]`, `[diff + metadata]` (the two releases' Requires-Dist: the package
  requires another library, such as `httpx2` instead of `httpx`, and its API takes that
  library's types), `[diff; probable rename]` (a guess, labelled as one) or
  `[type-checked]` (written during `run`; its example passed the type check). Check them when
  you write code that uses those libraries, and claim no more than the tag says.

## Error Handling

- No lockfile or pinned versions found: tell the user which file the tool asked for; do not
  invent versions.
- A model or login error during `run`: report the message and offer `scan`, which makes no
  model calls.
- `sync` exits with code 4: the block was edited by hand. Tell the user, and pass `--force`
  only if they say so.
- `sync` without `--yes` asks on the terminal; with no terminal to ask in it writes nothing and
  exits with code 3. Show the `--dry-run` diff and use `--yes` once the user agrees.
- `status` exits with code 3 when the notes are out of date: offer `sync` as in step 7.
- `run` was interrupted: run the same command again; it resumes from the cache.

## Examples

**Example 1: "Does the model know the library versions this project pins?"**

```bash
since-cutoff scan
```

Summarise what it lists. If the user wants notes, show the diff and write once they agree:

```bash
since-cutoff sync --dry-run
since-cutoff sync --yes
```

**Example 2: "Measure which of these changes you get wrong, and add the notes."**

Tell the user what `run` sends, what it costs and how long it takes (step 4). After a yes, start
it in the background (with `--model` if step 3 calls for it), then show the notes `sync` would
add for the other changed APIs:

```bash
since-cutoff run --quick --apply
since-cutoff sync --dry-run
```

**Example 3: "I upgraded openai. Are the notes in AGENTS.md still right?"**

```bash
since-cutoff status
```

If the notes are out of date, show the diff of `since-cutoff sync --dry-run` and run
`since-cutoff sync --yes` once the user agrees; to remove them, `since-cutoff unapply`.

## Quick lookups without a run

If the since-cutoff MCP server is connected (the Claude Code plugin starts it), its tools answer
from a static diff, with no model calls: `api_changes` (one package, optionally one `symbol`),
`project_changes` (every dependency of the project) and `model_cutoff`. Pass your own model id
as `model`. Use them before writing code against a dependency that may be newer than your
training data; use the CLI above when the user wants the model measured or notes written.

## Resources

- [since-cutoff on GitHub](https://github.com/MohammadHijjawi97/since-cutoff): the README, with
  every command, flag and exit code, and what each note tag means.
- [How it works](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/docs/how-it-works.md):
  the diff, the notes and the measurement in detail.
- [Privacy](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/PRIVACY.md): what `run`
  sends to the model provider, and what stays on the machine.
- [Changelog](https://github.com/MohammadHijjawi97/since-cutoff/blob/main/CHANGELOG.md): what
  changed in each release.
