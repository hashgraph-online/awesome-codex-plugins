---
name: codex-exec
description: 'Run one caller-supplied Codex command non-interactively and capture evidence. Triggers: "run Codex headless", "capture Codex evidence".'
---
# Codex Exec — one-shot runtime adapter

Run exactly one caller-supplied Codex prompt and capture its result. This skill
does not choose work, retry failures, validate by itself, or control continuation.

One prompt, one process, one captured artifact is what makes the run auditable:
when nothing loops, every byte of output traces to exactly one invocation, and
a disagreement about what happened is settled by the artifact.

Named failure mode — **stdin hang**: a non-TTY run left waiting forever on an
open stdin nobody will write to; always pipe the prompt or close the stream.

Anti-pattern: granting workspace-write or network access "in case the prompt
needs it". Corrective: match the sandbox to the declared effects; a review
prompt runs read-only, full stop.

## Procedure

1. Confirm the intended executable, profile, and caller-supplied prompt.
2. Set the working root explicitly with `-C`.
3. Match the sandbox to the requested effects: read-only for offline review,
   workspace-write for authorized edits, and broader access only when the caller
   explicitly requires network or external effects.
4. Use `scripts/lib/codex-exec.sh` and `codex_exec_guarded`. Pipe the prompt,
   provide a prompt file/argument, or close stdin in non-TTY execution.
5. Supply `CODEX_EXEC_TIMEOUT` as positive finite seconds or inherit an
   absolute `CODEX_EXEC_DEADLINE_EPOCH`. There is no fixed ten-minute default:
   without an explicit timeout, use the deadline's remaining time; with both,
   the earlier bound wins, including capability probes and prompt preparation.
   Pass the same deadline to successive calls; a new invocation cannot renew
   it. Missing both bounds, or empty, zero, negative or malformed explicit
   values, prevents launch. An expired deadline times out before dispatch.
6. Capture stdout with `CODEX_EXEC_OUT_FILE` and optionally separate stderr with
   `CODEX_EXEC_STDERR_FILE`. `CODEX_EXEC_MAX_OUTPUT_BYTES` defaults to **10 MiB**
   (10485760 bytes) and must be a positive finite integer. It caps stdout and
   stderr **combined**; file-prompt copies and AGY/local-mlx stdin preparation
   each use the same cap. Capture sinks must be regular files (or `/dev/null`).
   Reviewer workspace writes, including files it writes with `-o`, are outside
   this capture cap.
7. Report the typed run result, then stop: the process exit status, the captured
   artifact path, the timeout/deadline and capture cap applied, and whether
   cleanup was triggered. Cancellation is the caller's; this skill neither
   retries nor continues on its own.

The supported host must have `/usr/bin/perl` with its core POSIX, IO::Select,
Fcntl, and Time::HiRes modules, a monotonic clock, process-group signalling,
and a resolved `timeout`/`gtimeout` supporting `--foreground`. Missing capability
fails closed. The embedded adapter mechanism establishes one owned process
group before launching the reviewer. It sends TERM then KILL after 200 ms on
expiry, cancellation, excess output, or direct-parent exit; it bounds pipe
draining to a further short cleanup window rather than waiting indefinitely
for descendants to close inherited pipes. This includes ordinary descendants
left by a successful parent and TERM-resistant children. It does **not** promise
cleanup of processes that deliberately escape the owned group or session.
Group members remaining after direct-parent exit are reported as `rep-survivor`
(exit 122): the run remains degraded even when cleanup subsequently succeeds.
After its cleanup window the adapter checks whether the owned group still
exists. Remaining membership, including zombies it cannot independently reap,
is reported as `CLEANUP-UNVERIFIED` (exit 2), never successful cleanup.

`CODEX_EXEC_WRAP` remains Codex-only: the sealed launch order is wrapper →
resolved timeout → reviewer, with Codex's sandbox bypass only when the external
wrapper supplies the sandbox. The capture/cleanup supervisor runs outside that
sealed launch. No process-wide file-size limit restricts reviewer work products.

Terminal outcomes are explicit: **unavailable/invalid limits** → 2;
**descendants left after direct-parent exit** → 122;
**capture/input limit** → 123; **deadline expiry or empty consumed output** →
124; **prompt echo** → 125; **cancellation** → 128 + signal number. Other genuine
reviewer exit codes are preserved. These reserved codes describe runtime
evidence, never a semantic verdict. On timeout, cancellation, or excess output,
partial capture stays in caller-provided files; an adapter-owned output sink is
streamed before removal. Failed prompt preparation reports its preserved partial
input path. The caller decides whether to launch another invocation.

## Example

```bash
# REVIEW_TIMEOUT_SECONDS is selected by the caller. Alternatively export
# CODEX_EXEC_DEADLINE_EPOCH once and omit CODEX_EXEC_TIMEOUT below; retain
# that same absolute deadline for every invocation in its scope.
. "$AGENTOPS_ROOT/scripts/lib/codex-exec.sh"
CODEX_EXEC_DIR="$WORKSPACE" CODEX_EXEC_SANDBOX=read-only \
CODEX_EXEC_PROMPT_ARG="$PROMPT" CODEX_EXEC_TIMEOUT="$REVIEW_TIMEOUT_SECONDS" \
CODEX_EXEC_MAX_OUTPUT_BYTES=10485760 CODEX_EXEC_OUT_FILE="$OUTPUT" \
  codex_exec_guarded </dev/null
```

For a validator, the prompt must name the acceptance digest, exact subject
manifest digest, author context ID, evidence, and required checked/not-checked
report. The validator context ID must be distinct from the author's before a
`PASS` verdict is possible. When the caller elects a cross-model fresh
validator, record model identities per
the `agent-native` model-dispatch recipe and match the sandbox to
declared effects.

For caller-required model identity, preserve native session metadata and terminal
events as well as rendered output. The [judgment receipt convention](../agent-native/references/judgment-receipts.md)
binds exact transcript byte spans and their SHA-256 through existing
`evidence_refs`; the consumer supplies expected profiles, subject and acceptance
independently. A requested model flag, Codex `turn_context` configuration, stdout
marker or model self-description does not prove actual model identity. Missing
native reporting stays `identity_unverified` and cannot satisfy a required leg.
