---
case: log-L2
description: Use when a command failed with long output, and the user needs the cause, not the whole output.
---

# The line that failed

Shapes: log.

```sh
go test ./... > test-out.txt 2>&1 || true
stickypane log add worklog --time "go test failed: store_test.go:88: want 3 notes, got 2 (full output: test-out.txt)"
stickypane note show test-out.txt
```

Find the line closest to the cause (the first failing assertion, the
first error, not the last stack frame) and log only it, with the path to
the full output. Read the output before you write the line: a guessed
cause is worse than none.

Done when: the log line names the file and line of the failure and the
path of the full output.
