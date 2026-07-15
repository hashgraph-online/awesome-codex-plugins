---
name: codex-exec
description: Run one caller-supplied Codex command
---
# Codex Exec — one-shot runtime adapter

Run exactly one caller-supplied Codex prompt and capture its result. This skill
does not choose work, retry failures, validate by itself, or control continuation.

## Procedure

1. Confirm `codex login status` for the intended profile.
2. Set the working root explicitly with `-C`.
3. Match the sandbox to the requested effects: read-only for offline review,
   workspace-write for authorized edits, and broader access only when the caller
   explicitly requires network or external effects.
4. Pipe the prompt to stdin (or close stdin) in non-TTY execution so the process
   cannot wait indefinitely for input.
5. Capture the final response with `-o`, JSONL, or an output schema.
6. Report the process exit status and captured artifact, then stop.

A nonzero process exit is runtime evidence, not a semantic verdict. The caller
decides whether to launch another invocation.

## Example

```bash
printf '%s\n' "$PROMPT" | codex exec -C "$WORKSPACE" -s read-only \
  -o "$OUTPUT" -
```

For a validator, the prompt must name the acceptance digest, exact subject
manifest digest, author context ID, evidence, and required checked/not-checked
report. The validator context ID must be distinct from the author's before a
`PASS` verdict is possible.
