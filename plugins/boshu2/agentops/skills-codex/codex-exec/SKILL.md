---
name: codex-exec
description: 'Run one caller-supplied Codex command Triggers: "run Codex headless", "capture Codex evidence".'
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

1. Confirm `codex login status` for the intended profile.
2. Set the working root explicitly with `-C`.
3. Match the sandbox to the requested effects: read-only for offline review,
   workspace-write for authorized edits, and broader access only when the caller
   explicitly requires network or external effects.
4. Pipe the prompt to stdin (or close stdin) in non-TTY execution so the process
   cannot wait indefinitely for input.
5. A wall-clock **deadline is mandatory** — never run codex unbounded. Use the
   caller's deadline, or the declared default of **600s (10 min)** when the
   caller supplies none, and record which one applied. Enforce it so the whole
   process **tree** is reaped, not just the direct child: run codex in its own
   process group and kill the group on expiry: `setsid` (own process group) +
   `kill -KILL -<pgid>` on the group; `--kill-after` only escalates TERM→KILL
   and plain `timeout <secs> codex …` signals only the direct child. If the
   wrapper cannot guarantee process-group reaping, **do not execute** — that
   host lacks the cleanup capability this skill requires (capability
   unavailable, fail closed). Deadline expiry is
   **fail-closed**: the run is killed and reported as timed-out / not proven,
   partial output preserved — never a completed review.
6. Capture the final response with `-o`, JSONL, or an output schema.
7. Report the typed run result, then stop: the process exit status, the captured
   artifact path, which deadline applied and whether it fired, that the
   process tree was reaped (a run without guaranteed reaping never starts), and whether
   the `codex` binary was present at all. Cancellation is the caller's; this
   skill neither retries nor continues on its own.

Terminal outcomes are explicit: **binary absent** (no `codex` on PATH) → report
unavailable and stop; **deadline expiry** → fail-closed, report the kill and
preserved partial output, never a completed review; **nonzero exit** → runtime
evidence, not a semantic verdict. The caller decides whether to launch another
invocation.

## Example

```bash
# Deadline mandatory; default 600s. `setsid` puts codex in its own process
# group so expiry kills the whole tree, with `--kill-after` escalating
# TERM->KILL. No setsid (or equivalent group kill) available -> do not run:
# fail closed as capability-unavailable.
printf '%s\n' "$PROMPT" | setsid timeout --kill-after=10s "${CODEX_TIMEOUT:-600}" \
  codex exec -C "$WORKSPACE" -s read-only -o "$OUTPUT" -
```

For a validator, the prompt must name the acceptance digest, exact subject
manifest digest, author context ID, evidence, and required checked/not-checked
report. The validator context ID must be distinct from the author's before a
`PASS` verdict is possible. When the caller elects a cross-model fresh
validator, record model identities per
the `agent-native` model-dispatch recipe and match the sandbox to
declared effects.
