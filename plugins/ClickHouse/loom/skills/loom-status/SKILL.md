---
name: loom-status
description: >
  Use when Loom seems quiet or wrong: a loom tool answers "unauthenticated",
  "not available" or an empty result for something the user says was saved;
  the session-start primer did not appear; the user asks "is loom working",
  "why didn't it remember", "is my token ok", or a Loom hook says
  `Executable not found in $PATH: "node"` or `node: not found`, or prints a
  `loom:` line about Node.js 18+.
  Checks the Node hook runtime, then runs the plugin's client check and reads
  its lines, so the answer names the cause (missing runtime, unreachable
  server, rejected or expired token, no writer grant on the write namespace,
  plugin or MCP entry missing, stranded captures) and the one fix. NOT for
  server-side operations (that is `loom doctor` on the server) and NOT for
  deciding what to remember (loom-memory).
disable-model-invocation: true
---

# loom-status — why is Loom quiet?

Every client-side failure is silent by design: the hooks fail open, a 401
reads as "no memories", a viewer token makes every capture a 403 nobody
sees. This skill diagnoses. It writes nothing to Loom and changes nothing
on the machine unless the user agrees to the one fix it names.

`<root>` below is the installed plugin: `$CLAUDE_PLUGIN_ROOT` in Claude
Code; in Codex, the newest `~/.codex/plugins/cache/loom/loom/*/` directory.

## Check in this order; the first failure is the cause

1. **Local runtime.** `sh "<root>/skills/loom-status/scripts/ensure-node.sh" --check`
   prints the Node 18+ the hooks run under (Claude Code: the `node` on PATH;
   Codex: the launcher's pick), or one line saying none was found or the one
   found is too old. A second line names a launch that finds none, with its
   fix: relay it. On a failure, tell the user the hooks cannot run and offer
   the fix: for Claude Code, set `PATH` in the `env` block of its settings to
   the whole search path with Node 18+'s directory first (that `PATH`
   replaces every session's); under Codex `LOOM_NODE=/path/to/node` reaches
   the hooks, and the MCP header helper needs that Node on PATH. Else the same
   script without `--check` installs Node (root or passwordless sudo, then
   apt/dnf/yum, apk or Homebrew). Run it only when the user says yes; if it
   exits 2, report its blocker line, do not retry. After an install the user
   restarts the session: SessionStart hooks cannot rerun in this one.
   An MCP-only client has no hooks and skips this step.
2. **Server, token, auth, grant.** `sh "<root>/bin/loom-node" "<root>/bin/loom-client-status.mjs"`
   prints JSON whose `checks` come in this order: `server`, `server version`
   (only when the server is older), `token`, `source`, `auth`, `namespace`,
   `flush` (`ok` is false when `server`, `token`, `auth` or `namespace` fails).
   `source` names the lookup that supplied the token.
   In Claude Code the server checked is the one the MCP entry calls: the
   plugin's install URL when a session saved it, else `LOOM_BASE_URL`, else
   localhost. In Codex, whose entry lives in its own config, it is the
   hooks' server and `source` only names the lookup.
   It ships with the plugin: do not look for a Loom checkout or install the
   Python CLI. It sends no test write; a listed grant is evidence of
   permission, not proof a write landed. If `loom` is already
   on PATH, `loom doctor --client --json` adds deeper checks.
3. **Plugin registration.** `claude plugin list` (or `codex plugin list`)
   shows the `loom` plugin enabled; `/mcp` in the session (or `codex mcp list`)
   shows the `loom` server connected. A missing entry is the cause even when
   every check above passed.
4. **Stranded captures.** The client check's `flush` line (WARN only).

## Report

One cause — the first failing step — and one next action from
[reference.md](reference.md). Do not guess at causes no check reported. If
everything passes, ask what the user expected to find: the memory may never
have been written.
