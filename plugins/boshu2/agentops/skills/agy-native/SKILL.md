---
name: agy-native
description: 'Run a supplied task in headless AGY (Antigravity, Gemini) and collect its result. Use when: AGY, Antigravity or Gemini is requested by name; never a fallback.'
practices: [team-topologies, design-by-contract]
hexagonal_role: driving-adapter
consumes: [explicit-packet]
produces: [agy-run-evidence]
context_rel:
- kind: separate-ways
  with: codex-exec
skill_api_version: 1
user-invocable: true
metadata:
  tier: cross-vendor
  dependencies: []
  capabilities: [dispatch_explicit_packet, provide_fresh_context]
  effects: [start_agy_session]
  canonical_status: canonical
  disposition: keep_optional_adapter
output_contract: AGY runtime evidence
---

# AGY Native

Run a supplied packet in AGY (Antigravity) only when the caller explicitly
selects that runtime. Scope the run to the supplied workspace and packet,
return runtime evidence, and stop.

## Before launch

1. **Read the live surface.** Run `agy --help` for flags and defaults and
   `agy models` for the current model set. The CLI changes faster than skill
   text. **Wrapper drift** is a run built from remembered syntax that silently
   changed: it looks scoped and is not.
2. **Absent means stop.** If `agy` is missing or its help cannot be read,
   report the absence and stop. Never fall back silently to Codex, Claude or
   any other runtime; a substitute needs a new caller selection. Nothing routes
   work to AGY on its own either. The repository reviewer library rates AGY a
   routine-tier, degraded-fallback reviewer; that rating applies only when a
   caller opts in, and it is not an automatic route.
3. **Set an explicit bound.** Print mode (`agy -p` / `--print`) is the headless
   path, and it has no built-in limit: `--print-timeout` defaults to `0`, which
   waits until the turn completes (AGY 1.2.14). Pass `--print-timeout` from the
   caller's remaining deadline and hold the same bound outside the process. A
   run stopped at the bound is a timeout, not a result.
4. **Name the posture** (below) and confirm the packet's declared effects and
   the caller's authorization cover it.
5. **Keep author and validator apart.** A validator is a new run in a new
   conversation, never `-c`/`--continue` or `--conversation <author-id>`. A
   session that reviews its own work forfeits the fresh judgment that makes a
   validator's evidence usable. Validators stay read-only and hand judgment to
   Validate; they never write the core verdict.

## Permission posture (disclose it; never assume it)

Flags choose the posture. Name the one used:

- No posture flag: AGY prompts for each tool permission. A headless run has no
  one to answer, so a prompt can stall it until the bound.
- `--dangerously-skip-permissions`: auto-approves every tool call. Use it only
  when the declared effects and the caller's authorization cover that blast
  radius.
- `--sandbox`: restricts the session's terminal access.
- `--mode` (`plan`, `accept-edits`): changes the execution mode; confirm its
  current meaning in `agy --help`.

## Command

Every `agy` flag below appears in `agy --help` for AGY 1.3.1; recheck before use.
`DEADLINE_EPOCH` is an absolute Unix time the caller fixes once and reuses for
every run in its scope, so a second run gets what is left rather than a new
bound. `POSTURE` is a Bash array of the posture flags chosen above, for example
`POSTURE=(--sandbox)`; an empty array means AGY asks for each tool.
`PROMPT_FILE` is an absolute path. The packet goes by path, not inline: a short
`-p` pointer plus `--add-dir`, as `scripts/lib/codex-exec.sh` does, because a
large inline prompt can be dropped while the run still looks scoped.

```bash
TO=$(command -v timeout || command -v gtimeout) || { echo "no timeout: not launching" >&2; exit 2; }
remaining=$(( DEADLINE_EPOCH - $(date +%s) ))
[ "$remaining" -gt 0 ] || { echo "deadline passed; not launched" >&2; exit 124; }
cd "$WORKSPACE" || exit 2
"$TO" -k 10 "$remaining" \
  agy --print-timeout "${remaining}s" --model "$MODEL" --output-format json \
  "${POSTURE[@]}" --add-dir "$(dirname "$PROMPT_FILE")" \
  -p "Read the task packet at $PROMPT_FILE and do what it describes." >"$OUT" 2>"$ERR"
rc=$?  # 124, or 137 after the 10 s grace: the outer bound stopped the run
```

`--print-timeout` takes a duration with a unit, such as `300s`. Add flags before
`-p` so none lands after the prompt text. AGY's help does not say which status
it returns when its own print timeout fires, so a run that ends at the bound is
a timeout unless its output shows a finished turn.

## Return

```text
command:      exact argv (prompt by reference)
posture:      permission, sandbox and mode flags used
model:        requested model; observed model if AGY reported one, else unknown
conversation: id AGY reported, else unknown
bound:        --print-timeout value and the outer deadline
outcome:      exit status | timed out | not run (reason)
artifacts:    captured output and changed-file paths
```

AGY plugin, memory, permission, retry and session state are runtime facts; they
never become AgentOps phase, queue or completion state. Installation, plugin
mutation and recurring scheduling need separate explicit authorization.
