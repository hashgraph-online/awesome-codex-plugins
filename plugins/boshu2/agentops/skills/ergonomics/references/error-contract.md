# Error contract

Use this when checking an observed failure, or a failure path a design
introduces, against the nine items in [Ergonomics](../SKILL.md#what-to-examine).
Judge meaning, not spelling: a field named differently that carries the same
fact satisfies the item.

## Which items apply

| Failure class | Example | Items that apply |
|---|---|---|
| Rejected before any work | unknown flag, missing argument, invalid value | what, next step, code, no secrets, channel. Retry is implied: fix the input and run again. |
| Environment | missing dependency, expired login, absent config | all items except unknown-outcome; next step may be a precise request to a human. |
| Partial or uncertain mutation | timeout after an upload began, one of five writes failed | all items; side effects and how to check the outcome are mandatory. |
| Unexpected | crash, unhandled exception | all items, plus a pointer to the full trace (a file path, or a request id for a remote service). |

In a proposed design, an item left unspecified on a failure path the design
introduces is a fail. For a built tool, a failure class you never triggered or
saw in supplied output is not observed; do not extrapolate from the paths you
did see.

## Channel by surface

- **CLI:** the message on stderr and a non-zero exit code that differs by
  class when the caller would act differently. In machine mode, stdout holds
  one parseable error object with the same facts and nothing else.
- **HTTP API:** an error status that matches the class (never 200 with an error
  body) and a structured body with the code and the offending parameter. A
  remote service returns a request id instead of internal traces.
- **MCP or agent tool:** an error result the model can read, with the code,
  next step and offending input in its text or structured content. Never a
  success result whose text describes a failure.
- **SDK or library:** a typed error carrying the code and fields as attributes,
  so a caller can branch without parsing the message.
- **Docs and help:** the documented error lists the code and the fix; channel
  does not apply.

## Health and diagnostic commands

A health command is itself a surface. Keep three outcomes apart: a check that
could not run (tool not installed, binary failed to launch), a check that ran
and failed, and a check deliberately skipped. Report the checked tool's own
exit status, not the status of a pipe, filter or parser that read its output.
A missing optional tool is an absence with an install hint, not a failure of
the whole check. When any check could not run, say so instead of reporting the
remainder as healthy.

## Worked example

A command uploads a batch and the connection drops partway.

Weak, exit 0:

```text
Error: request failed
```

The agent sees exit 0 and moves on, or sees the text and reruns the upload,
creating duplicates. Findings: channel (failure reported as success), what
(no batch named), why (no underlying cause), next step, retry safety (no word
on side effects), unknown outcome (no way to check), code, context (no version
or config).

Repaired, exit 75, with the next step on the last line:

```text
notes push: batch 41 (12 files) timed out after 30s while uploading to notes.example.net [PUSH_TIMEOUT]
  effects: unknown; some files may be stored, so a plain rerun may duplicate them
  context: notes 3.2.0, config ./notes.toml, env NOTES_ENDPOINT set
  docs: notes explain PUSH_TIMEOUT
  next: notes status --batch 41; if it shows "incomplete", notes push --batch 41 --resume (safe to repeat)
```

Machine mode prints the same facts on stdout:

```json
{"ok": false, "code": "PUSH_TIMEOUT", "docs": "notes explain PUSH_TIMEOUT",
 "message": "batch 41 (12 files) timed out after 30s while uploading to notes.example.net",
 "input": {"batch": 41, "files": 12}, "effects": "unknown", "retry_safe": false,
 "check": "notes status --batch 41",
 "next": {"if": "status shows incomplete", "run": "notes push --batch 41 --resume", "repeat_safe": true},
 "context": {"version": "3.2.0", "config": "./notes.toml", "env": ["NOTES_ENDPOINT"]}}
```

The env var is named, not printed. The next step is a command the reader can
run as written, and blind retry is ruled out until the outcome is checked.
