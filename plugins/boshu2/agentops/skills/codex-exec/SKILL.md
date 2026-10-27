---
name: codex-exec
description: 'Run one prompt through headless Codex and capture the result. Use when: wanting a one-shot `codex exec` run or CI step. Not for batches or retries.'
skill_api_version: 1
user-invocable: true
hexagonal_role: driving-adapter
practices:
- pragmatic-programmer
consumes:
- codex-command-packet
produces:
- codex-run-output
context_rel:
- kind: supplier-to
  with: validate
metadata:
  capabilities: [codex_exec]
  effects: [run_codex_process, sandbox_tiered_workspace_and_network_effects]
  canonical_status: canonical
  disposition: keep_optional_adapter
  tier: orchestration
  dependencies: []
  stability: stable
output_contract: process exit status and captured Codex output artifact
---
# Codex Exec — one-shot runtime adapter

Run exactly one caller-supplied Codex prompt as one process and capture its
result. This skill does not choose work, retry, validate or continue.

## Rules that change the command

- **Sandbox from declared effects.** `-s read-only` for review or analysis,
  `workspace-write` only for authorized edits, and network or wider access only
  when the caller explicitly requires those effects. "In case it needs it" is
  not a declared effect. A permission denial inside the run (`EPERM`, "Operation
  not permitted") shows only what the mode blocks, not whether the host or the
  code would fail. Quote it and report the check as sandbox-limited under not
  run / `not_checked`: neither a pass nor a failed check. A host-side
  observation still stands; a host run is the caller's decision.
- **Close stdin.** `codex exec` reads the prompt from stdin when no prompt
  argument is given, and appends piped stdin to a prompt argument. A non-TTY run
  (CI, a script) with an open stdin can wait forever: the **stdin hang**. Feed
  the prompt on stdin and let it end, or redirect `</dev/null`.
- **One deadline, never renewed.** Fix one absolute deadline before the first
  attempt. Each invocation, including any retry the caller decides to make,
  gets only the time left before that deadline. A retry never gets a fresh
  budget: a loop that gives each attempt its own new timeout has silently
  multiplied the caller's bound. A missing, zero, negative or malformed bound
  prevents launch; an expired deadline stops before dispatch.
- **No retry here.** Report a timeout, error or empty output as it is. Another
  invocation is the caller's decision, under the same deadline.
- **Capped capture, typed exit.** Capture output to a file under a byte cap and
  report the exit status. A timeout is not a result.

## Run it

In an AgentOps source checkout, use the guarded library. It enforces the
deadline, the combined output cap (10 MiB default), process-group cleanup and
echo detection:

```bash
# AGENTOPS_ROOT: the agentops source checkout. DEADLINE_EPOCH: absolute Unix
# time fixed once by the caller and reused by every invocation in its scope.
. "$AGENTOPS_ROOT/scripts/lib/codex-exec.sh"
CODEX_EXEC_DIR="$WORKSPACE" CODEX_EXEC_SANDBOX=read-only \
CODEX_EXEC_PROMPT_FILE="$PROMPT_FILE" CODEX_EXEC_DEADLINE_EPOCH="$DEADLINE_EPOCH" \
CODEX_EXEC_MAX_OUTPUT_BYTES=10485760 CODEX_EXEC_OUT_FILE="$OUTPUT" \
  codex_exec_guarded </dev/null
```

Outside a Git repository add `CODEX_EXEC_SKIP_GIT_CHECK=1`; to keep the final
message outside the cap, assign `CODEX_EXEC_EXTRA_ARGS=(-o "$LAST")` on its own line first.

An installed skill ships no scripts, so `scripts/lib/codex-exec.sh` is absent
outside a source checkout. Run `codex exec` directly instead, with bash or zsh
(flags as of codex-cli 0.163.0; confirm with `codex exec --help`; add
`--skip-git-repo-check` and `-o <file>` as above):

```bash
case "${DEADLINE_EPOCH:-}" in ''|0*|*[!0-9]*) echo "no valid deadline; not launched" >&2; exit 2;; esac
TO=$(command -v timeout || command -v gtimeout) || { echo "no timeout; not launched" >&2; exit 2; }
remaining=$(( DEADLINE_EPOCH - $(date +%s) ))
[ "$remaining" -gt 0 ] || { echo "deadline passed; not launched" >&2; exit 124; }
set -o pipefail  # bash and zsh: $? is the failing stage, not head's
"$TO" -k 10 "$remaining" \
  codex exec -C "$WORKSPACE" -s read-only - <"$PROMPT_FILE" 2>&1 \
  | head -c 10485760 >"$OUTPUT"
rc=$?  # 124 timed out, 137 killed after grace, 127 no codex, else codex's status
```

An output file exactly at the cap was truncated, and its status reflects the
closed pipe, not a review. The fallback has no survivor check or echo
detection; report both as not enforced.

## Exit codes (guarded library)

| Exit | Meaning |
|---|---|
| 0 | Codex completed and produced output |
| 2 | precondition: binary missing, bounds invalid or missing, capability unavailable, or cleanup unverified; not a result |
| 122 | descendants survived Codex's exit; degraded run |
| 123 | capture or prompt-preparation cap reached; partial evidence kept |
| 124 | deadline expired, or a clean exit with empty output; a stall, not a result |
| 125 | output repeats the prompt; not a result |
| 128+N | cancelled by signal N (129 HUP, 130 INT, 143 TERM) |
| other | Codex's own nonzero status, preserved |

Reserved codes are runtime evidence, never a semantic verdict. A Codex 124 or
137 returns 124 with the STALL line and a Codex 2 or 123 returns silently, so
check the capture and elapsed time before reading one as the runner's.
[Guarded runner internals](references/guarded-runner.md) covers inputs, host
requirements, process supervision and the external sandbox wrapper.

## Report, then stop

```text
command:  exact argv or library call (prompt by reference)
sandbox:  -s value and the declared effect that needs it
bound:    absolute deadline and seconds remaining at launch
capture:  output path, byte cap, truncated yes/no
exit:     status and its meaning from the table
cleanup:  library result, or "not enforced" for the direct fallback
```

A Codex validator follows the
[judgment receipt convention](../agent-native/references/judgment-receipts.md)
and the [model-dispatch recipe](../agent-native/references/model-dispatch.md#association-before-execution):
a requested model flag or the model's own description does not prove which
model ran. Siblings: [claude-exec](../claude-exec/SKILL.md) (one headless
Claude prompt), [agy-native](../agy-native/SKILL.md) (AGY) and
[agent-native](../agent-native/SKILL.md) (worker batches).
