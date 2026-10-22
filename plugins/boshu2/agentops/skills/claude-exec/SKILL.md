---
name: claude-exec
description: 'Run one prompt through headless Claude with scoped permissions and a time bound. Use when: scripting or automating a `claude -p` call, even a simple one.'
skill_api_version: 1
user-invocable: true
hexagonal_role: driving-adapter
practices: [pragmatic-programmer, design-by-contract]
consumes: [claude-command-packet]
produces: [claude-run-output]
context_rel:
- kind: supplier-to
  with: validate
- kind: separate-ways
  with: codex-exec
context: {window: inherit, intent: {mode: none}, sections: {exclude: [HISTORY]}}
metadata:
  tier: orchestration
  dependencies: []
  capabilities: [claude_exec]
  effects: [run_claude_process, permission_tiered_workspace_effects]
  canonical_status: canonical
  disposition: keep_optional_adapter
  stability: stable
output_contract: process exit status and captured Claude output artifact
---
# Claude Exec — one-shot runtime adapter

Run one caller-supplied prompt through Claude Code print mode and capture the
result, only when the caller selects Claude: the native agent stays the
default and batches belong to `agent-native`. Flags match `claude --help` for
2.1.282; recheck it on other versions.

## Failure modes of a quick `claude -p`

1. **Inherited posture.** A bare run loads the user's settings, hooks,
   plugins, MCP servers and CLAUDE.md; a settings `bypassPermissions` default
   held even under `--safe-mode`. Use the clean flags below and set `--tools`
   and `--permission-mode` to the task's effects.
2. **Renewed time.** One bound, from the caller's remaining time: a retry
   spends it instead of renewing it. Make one attempt; any other is the
   caller's decision.
3. **Exit 0 as proof.** A denied call still exits 0 with `is_error: false`
   and "done", and a bare file name once landed in the run's scratchpad, not
   `$WORKDIR`. Name targets by path, check effects there, and leave
   acceptance to a fresh validator.
4. **Silent fallback.** With no `claude`, login or model, report and stop
   instead of switching runtimes or passing `--fallback-model`.
5. **Self-review.** Review runs as a separate session, never the author's.

## Run

Redirect the prompt from a file, or pass it as the argument with `</dev/null`,
because print mode reads stdin to EOF: a pipe left open hangs until the bound
kills it. Stock macOS lacks `timeout`: use GNU `timeout` or Homebrew's
`gtimeout`, and launch nothing without one.

```bash
TO=$(command -v timeout || command -v gtimeout) || { echo "no timeout: not launching" >&2; exit 2; }
cd "$WORKDIR" || exit 2
# Read-only: review, research, questions.
"$TO" -k 10 "$SECS" claude -p --model "$MODEL" --output-format json \
  --setting-sources "" --strict-mcp-config --disable-slash-commands \
  --tools "Read,Grep,Glob" --permission-mode dontAsk \
  <"$PROMPT_FILE" >"$OUT" 2>"$ERR"; echo "exit=$?"
# Edit-capable: authorized file changes under $WORKDIR.
"$TO" -k 10 "$SECS" claude -p --model "$MODEL" --output-format json \
  --setting-sources "" --strict-mcp-config --disable-slash-commands \
  --tools "Read,Grep,Glob,Edit,Write" --permission-mode acceptEdits \
  <"$PROMPT_FILE" >"$OUT" 2>"$ERR"; echo "exit=$?"
```

Print mode never prompts: unapproved calls are denied and listed in
`permission_denials`. Add `Bash` to `--tools` only for authorized commands
named in `--allowedTools`, e.g. `"Bash(go test *)"`; with settings hooks
dropped, that list is the guard. `--max-budget-usd` stops after the call that
crosses it, and `--help` lists no turn cap, so bound a run by time and budget.
`--no-session-persistence` keeps no transcript.

## Result

JSON carries `result`, `is_error`, `session_id`, `total_cost_usd`,
`num_turns`, `permission_denials`, and `modelUsage` keyed by the models
billed; identity evidence needs `stream-json --verbose` per the
[model-dispatch recipe](../agent-native/references/model-dispatch.md). Judge
by exit status and `is_error`: an unknown model exited 1 with
`subtype: "success"`. Exit 1 also covers a spent budget or missing input;
`timeout` gives 124, or 137 when KILL follows 10 seconds later. Keep at most
the caller's byte cap (10 MiB default), mark a cut file truncated, return
this, and stop:

```text
command: <exact argv>    posture: <tools; permission mode; clean flags>
model: <requested> -> <modelUsage keys>    exit: <status | timeout at N s>
session_id: <id | none>    output: <path, bytes, truncated: yes|no>
permission_denials: <count and tools>
```
