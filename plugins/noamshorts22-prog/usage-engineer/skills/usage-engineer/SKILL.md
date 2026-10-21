---
name: usage-engineer
description: Cut wasted tokens in coding-agent sessions without lowering quality. Use when a command prints a long log or test output, when the same command keeps failing, when resuming work from an older project map or handoff, when AGENTS.md or other instruction files may be duplicated, or when the user asks where their Codex or OpenCode usage went, why they hit a rate limit, or how to make the agent cheaper. Runs a bundled zero-dependency Python CLI locally; no network, never reads credentials.
license: MIT
compatibility: Needs Python 3.9+. Usage audit reads local Codex CLI and OpenCode data; the other commands work in any agent.
metadata:
  author: noamshorts22-prog
  version: "0.3.0"
  homepage: https://github.com/noamshorts22-prog/usage-engineer
---

# usage-engineer

Every token an agent spends on a 5,000-line log, a retried command or a stale map is paid for again
on every later turn. This skill removes that waste. It never lowers the bar: requirements, tests and
verification stay exactly as strict as without it.

## The CLI

All commands run the bundled script, which has no dependencies and makes no network calls:

```
python <skill-dir>/scripts/ue.py <command>
```

`<skill-dir>` is the folder this SKILL.md is in. If `ue` is on PATH (installed with pipx), `ue <command>`
is the same thing. Use `python3` where `python` is not Python 3, and `py -3` on Windows if neither is
found. If no Python is reachable (the Codex sandbox on Windows can hide a per-user install), say so
once and still follow the rules below by hand; do not retry the same command.

## Rules

1. **Long output goes to a file, not the conversation.** When a build, test run or log will print more
   than about 100 lines, redirect it to a file and summarize it:

   ```
   <command> > build.log 2>&1
   python <skill-dir>/scripts/ue.py summarize-log --file build.log
   ```

   The summary keeps every error and failure line with context plus the last 20 lines, and prints the
   path of a byte-exact copy of the full log. Read slices of that copy only when the summary is not
   enough. Never rerun a command just to see its output again.

2. **Two identical failures means change approach.** If the same command fails twice with the same
   input, do not run it a third time. Read the error, change the input, or try a different method.

3. **Check a map before trusting it.** Before resuming from an older session, handoff or project map,
   check whether the files changed:

   ```
   python <skill-dir>/scripts/ue.py map check --project . --map <map.json>
   ```

   Exit code 1 means STALE and lists the changed files: re-read those, and only those. Build a map
   at the end of a work session so the next one can check it:

   ```
   python <skill-dir>/scripts/ue.py map build --project .
   ```

4. **Read narrowly.** Search first (`rg`, `grep`) and read the matching range instead of whole files.
   Do not re-read a file that has not changed.

5. **Report what actually ran.** Never describe a check as passing unless it ran in this session.
   Keep the path to the full failure output in the report so nothing is lost by summarizing.

## Measuring usage

When the user asks where their usage went, why they hit a limit, or whether a change helped, measure
before advising:

```
python <skill-dir>/scripts/ue.py audit --days 7
```

It reads local Codex CLI rollout files (`$CODEX_HOME/sessions`) and the OpenCode database, read-only,
with home paths redacted. It reports input, cached, output and reasoning tokens, incomplete turns,
and two waste signals: oversized tool outputs (with an estimate of the tokens they cost) and
repeated identical tool calls. It never reads `auth.json`, cookies, tokens or
chat text. Report its numbers as measured; label anything else as an estimate.

## Other commands

| Command | Use it when |
|---|---|
| `prepare-context --project . --task "<task>" --verify "<test command>"` | starting a non-trivial task: writes a small pack with the request, constraints, git state and the checks to run. It narrows the start, not correctness: widen whenever evidence requires it. |
| `instructions duplicates --project .` | AGENTS.md, CLAUDE.md or similar files may repeat the same paragraphs, which are then paid for on every turn. |
| `doctor` | something does not work: prints versions, paths and the state folder. |

Printed paths start with `%HOME%`, which stands for the user's home directory (redaction keeps it
out of logs and reports); expand it before opening the file.

Nothing above changes the model, reasoning effort or agent settings. Output files go to
`~/.usage-engineer` (override with `UE_STATE_DIR`) unless `--out` is given.

## Honest limits

Saving claims are cheap. In the project's own first A/B run, handing the agent a prepared context pack
used about 30% more tokens on small tasks, so do not promise savings from `prepare-context`. The rules
above that avoid re-sending output (1, 2 and 4) are the reliable wins. Full benchmark harness and
results: https://github.com/noamshorts22-prog/usage-engineer
