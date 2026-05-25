# Debugger Attach Triage

Use this reference before attaching a debugger to a live or hung process.

## Preconditions

1. Confirm the process ID and command line.
2. Check whether attaching will pause the whole process.
3. Check ptrace or platform attach policy.
4. Prefer read-only snapshots before interactive mutation.
5. Record the original system setting before changing it.

## Snapshot Order

Use the least invasive evidence first:

| Evidence | When |
|---|---|
| Logs and stderr | Always first. |
| Stack dump signal or runtime endpoint | When supported by the runtime. |
| Process sampling | When attach policy blocks a debugger. |
| Debugger attach | When stacks are needed and pause is acceptable. |

## Attach Rules

- Attach, collect, detach. Do not leave the target paused.
- Capture all threads, not just the hot one.
- Save raw backtrace output with timestamp and PID.
- Restore any relaxed attach policy before closeout.
- If a debugger changes timing enough to hide the bug, switch to sampling or instrumentation.

---

**Source:** Adapted from an external skill corpus / `gdb-for-debugging`. Pattern-only, no verbatim text.
