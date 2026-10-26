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
2.1.309; recheck it on other versions. Re-checked on 2026-10-25 against Claude
Code 2.1.309, codex-cli 0.163.0, AGY 1.4.7, gc edge 97503b2 (with Gas City
v1.5.1 docs and source), bd 1.3.1 and ao 3.11.0.

## Failure modes of a quick `claude -p`

1. **Inherited posture.** A plain run loads the user's settings, hooks,
   plugins, MCP servers and CLAUDE.md; a settings `bypassPermissions` default
   held even under `--safe-mode`. Use the clean flags below and set `--tools`
   and `--permission-mode` to the task's effects. They drop settings files,
   MCP servers, skills and commands and keep file tools in the working
   directory; `--bare` also skips CLAUDE.md, auto-memory and plugin hooks.
2. **Renewed time.** One deadline, fixed once by the caller: `$SECS` is the
   time left before it, so a retry spends it instead of renewing it. Make one
   attempt; any other is the caller's decision.
3. **Exit 0 as proof.** A denied call still exits 0 with `is_error: false`
   and "done" (not re-run since 2.1.282). Name targets by path, check
   effects there, and leave acceptance to a fresh validator.
4. **Silent fallback.** With no `claude`, login or model, report and stop
   instead of switching runtimes or passing `--fallback-model`.
5. **Self-review.** Review in a new session, never by `--resume` or
   `--continue` of the author's.

## Run

Redirect the prompt from a file, or pass it as the argument with `</dev/null`,
because print mode reads stdin to EOF: a pipe left open hangs until the bound
kills it (not re-run since 2.1.282). Stock macOS lacks `timeout`: use GNU
`timeout` or Homebrew's `gtimeout`, and launch nothing without one. This
script body makes one launch; the caller supplies `$POSTURE`, `$BUDGET_USD`
and absolute `$PROMPT_FILE`, `$OUT` and `$ERR` paths outside the tree.

```bash
TO=$(command -v timeout || command -v gtimeout) || { echo "no timeout: not launching" >&2; exit 2; }
case "$DEADLINE_EPOCH" in ''|*[!0-9]*) echo "no deadline: not launching" >&2; exit 2;; esac
for p in "$PROMPT_FILE" "$OUT" "$ERR"; do case "$p" in /*) ;; *) echo "not absolute: '$p'" >&2; exit 2;; esac; done
case "$POSTURE" in
  read) TOOLS="Read,Grep,Glob" MODE=dontAsk ;;   # review, research, questions
  edit) TOOLS="Read,Grep,Glob,Edit,Write" MODE=acceptEdits ;;   # authorized changes under $WORKDIR
  *) echo "POSTURE must be read or edit: not launching" >&2; exit 2 ;; esac
cd "$WORKDIR" || exit 2
SECS=$(( DEADLINE_EPOCH - $(date +%s) ))   # DEADLINE_EPOCH: Unix time fixed once by the caller
[ "$SECS" -gt 0 ] || { echo "deadline passed: not launching" >&2; exit 124; }
"$TO" -k 10 "$SECS" claude -p --model "$MODEL" --output-format json \
  --setting-sources "" --strict-mcp-config --disable-slash-commands --restricted \
  --tools "$TOOLS" --permission-mode "$MODE" --permission-prompts none \
  --max-budget-usd "$BUDGET_USD" <"$PROMPT_FILE" >"$OUT" 2>"$ERR"; rc=$?; echo "exit=$rc"
```

Unapproved calls are denied and listed in `permission_denials`. Add `Bash` to
`--tools` only for authorized commands named in `--allowedTools`, e.g.
`"Bash(go test *)"`; with settings hooks dropped, that list is the guard.
`--max-budget-usd` stops after the call that crosses it. `--max-turns <n>`
caps agentic turns in print mode and exits with an error when it is reached:
2.1.309 accepts it although `--help` omits it, and the CLI reference documents
it. Time, budget and an optional turn cap are the bounds.
`--no-session-persistence` keeps no transcript. `--bare` signs in only with
`ANTHROPIC_API_KEY` or an `apiKeyHelper` passed with `--settings`, never an
OAuth login.

A host shell tool may kill a call before `$SECS`, leaving `$OUT` empty since
JSON is written only at exit. When its cap is under `$SECS` plus the 10 s
grace, start the command as a host background job and wait on its completion
notice; a run the host killed was the one attempt. A quiet run is working.

## Result

JSON carries `result`, `is_error`, `terminal_reason`, `api_error_status`,
`session_id`, `permission_denials`, and `modelUsage` keyed by the models
billed; identity evidence needs `stream-json --verbose` per the
[model-dispatch recipe](../agent-native/references/model-dispatch.md). Judge
by exit status and `is_error`: an unknown model exited 1 with
`subtype: "success"`, `terminal_reason: "api_error"` and `api_error_status:
404`. Exit 1 also covers a spent budget or missing input (not re-run since
2.1.282); `timeout` gives 124, or 137 when KILL follows 10 seconds later.
Read the fields before the byte cap, since a cut JSON file no longer parses:

```bash
jq -c '{is_error, terminal_reason, api_error_status, session_id,
  models: (.modelUsage // {} | keys), permission_denials}' "$OUT" >"$OUT.meta"
ok=no; [ "$rc" -eq 0 ] && jq -e '.is_error == false' "$OUT.meta" >/dev/null && ok=yes
CAP=${CAP:-10485760} truncated=no   # the caller's byte cap, 10 MiB default
[ "$(wc -c <"$OUT")" -le "$CAP" ] || { head -c "$CAP" "$OUT" >"$OUT.cut" && mv "$OUT.cut" "$OUT"; truncated=yes; }
```

Return this, and stop:

```text
command: <exact argv>    posture: <tools; permission mode; clean flags>
model: <requested> -> <modelUsage keys>    exit: <status | timeout at N s>
reason: <terminal_reason; api_error_status | none>    session_id: <id | none>
output: <path, bytes, truncated: yes|no>    permission_denials: <count and tools>
```
