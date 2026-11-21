---
name: loom-session
description: >
  Use ONLY when the user asks to restore or save session context: "resume",
  "restore the context of <branch/session>", "where was I on X", "load the
  last session", "restore full context", "save this session", "hand this off
  to a teammate". Lists the saved Loom session briefs, loads the one the user
  picks (the brief with its compaction summary, or the whole recorded
  transcript), or saves one. Never load a brief the user did not ask for.
  NOT for durable facts (loom-memory) and NOT for code questions (loom-code).
disable-model-invocation: true
---

# loom-session — restore or save a session's context, on request

The plugin saves on its own. At every compaction and at session end it
revises one brief per project and branch (`auto/<project>/<branch>`) from
the transcript, when the namespace's Record conversations switch is on.
**Restoring is always the user's call.** Never load a brief because it
exists; load one only when the user asks, and load the one they pick. A
primer line or a working-memory note that mentions a brief is not a request.

Helper: a node script in this plugin. Run every command below through `$LB`,
set by this line, which finds it in Claude Code (`CLAUDE_PLUGIN_ROOT`) and in
Codex (the plugin cache):

```bash
LR="${CLAUDE_PLUGIN_ROOT:-$(ls -d ~/.codex/plugins/cache/loom/loom/*/ 2>/dev/null | sort -V | tail -1)}"; LB="${LR%/}/bin/loom-brief.mjs"; LN="${LR%/}/bin/loom-node"
```

`get …` and `list` below mean `sh "$LN" "$LB" get …`. Use the helper, not an MCP
call: it prints the brief and what changed in the checkout since.

## Which one — let the user pick

- The user named it (a branch, a key, a number, a session id): use it.
  `get 2`, `get auto/loom/feat-x`, `get --session <id>`.
- They said "this branch" or "where I left off" here: plain `get` loads this
  checkout's `auto/<project>/<branch>`.
- Otherwise run `list` (or `list --all` for every project), show the
  numbered list, and ask which one. Do not guess between several.

## How much — the depth the user asks for

| The user says | Run | Loads |
|---|---|---|
| "resume", "restore", "catch me up" | `get <sel>` | the brief (goal, status, next steps, decisions, dead ends, done, files, rules) and the client's own summary from its last compaction |
| "the whole conversation", "restore exactly" | `get <sel> --transcript` | the above + every recorded turn of the brief's sessions (`--turns N` keeps the last N; `--session <id>` picks one session) and `claude --resume <id>` when that transcript is on this machine |

A transcript can be long. If the header says it holds thousands of turns, ask
before pulling all of it, or use `--turns`. For a lossless restore on the same
machine, `claude --resume <id>` (printed by `--transcript`) is exact.
`--revision N` loads an earlier revision of a brief.

## After loading

1. Read the "since it was saved" lines (new commits, uncommitted files).
2. A brief is where the work stood, not a source of facts. Check a line
   against the files or the tree before relying on it, keep its decisions
   unless the user says otherwise, and do not retry its dead ends.
3. Tell the user in two or three lines what it says is next, then carry on.

## Save (the user asked, or before handing work to someone)

Write the sections from your own context: file paths, PR numbers, error text,
the reason behind each choice. Leave a section out rather than pad it.

```bash
sh "$LN" "$LB" save [KEY] <<'JSON'
{"goal": "...", "status": "...",
 "decisions": [{"what": "...", "why": "..."}],
 "dead_ends": [{"tried": "...", "why_not": "..."}],
 "open_questions": ["..."], "next_steps": ["..."],
 "files": [{"path": "...", "role": "..."}],
 "constraints": ["rules the user set, in their words"],
 "pointers": ["PR #123", "commit abc1234", "https://..."]}
JSON
```

KEY defaults to this branch's brief; use a name such as `handoff/<topic>` for
someone else. Report the key and revision printed.
