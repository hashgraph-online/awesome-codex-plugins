---
name: loom-session
description: >
  Use only when asked to save, resume, restore or hand off a coding session.
  Examples: "where was I on X", "load the last session", "restore full
  context", "restore the Loom session handoff", "save this session".
  List and open the brief the user chooses, or save one. For durable
  facts use loom-memory. For code questions use loom-code.
disable-model-invocation: true
---

# loom-session — restore or save a session's context, on request

With Record conversations on, compaction and session end save a brief for
the project and branch (`auto/<project>/<branch>`). Load only the brief the
user asks for. A primer mention alone is insufficient.

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

## Restore a handoff link

Run `get --handoff '<url>'` with the URL as one shell argument. This reads the
pinned brief from the configured Loom server with the recipient's credentials.
Check the saved commit and checkout warnings before continuing.

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
 "verification": "command or CI check and its observed result",
 "decisions": [{"what": "...", "why": "..."}],
 "dead_ends": [{"tried": "...", "why_not": "..."}],
 "open_questions": ["..."], "next_steps": ["..."],
 "files": [{"path": "...", "role": "..."}],
 "constraints": ["rules the user set, in their words"],
 "pointers": ["PR #123", "commit abc1234", "https://..."]}
JSON
```

KEY defaults to this branch's brief; use a name such as `handoff/<topic>` for
someone else. Report the key and revision printed. In the Conversations
dashboard, open that brief and use **Copy handoff link** to share a revision.
