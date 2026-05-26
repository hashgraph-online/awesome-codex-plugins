# Deadlock And Hang Triage

Use this reference when the symptom is a stuck command, stalled daemon, blocked test, live-lock, retry storm, or suspected deadlock.

## First Split

Classify the process before changing code:

| Signal | Likely Class | Next Move |
|---|---|---|
| High CPU | Livelock, spin, retry storm | Capture stack samples and logs around loop conditions. |
| Low CPU, process alive | Deadlock, blocked I/O, waiting on child process | Capture goroutine/thread/process stacks. |
| Growing memory | Leak, unbounded queue, stuck cleanup | Capture heap or allocation evidence. |
| Repeated external calls | Retry storm or missing backoff | Inspect timeout/backoff/circuit-breaker behavior. |
| Parent waiting forever | Child process or pipe handling bug | Inspect subprocess lifecycle and stdout/stderr drains. |

## Evidence Order

1. Capture process tree and command line.
2. Capture thread/goroutine stacks with the safest available tool.
3. Capture recent logs.
4. Identify locks, channels, waits, subprocesses, sockets, or files involved.
5. Reproduce with a focused timeout test when possible.

## Fix Discipline

- Do not add arbitrary sleeps as a fix.
- Prefer bounded timeouts, context cancellation, drain loops, and explicit lifecycle ownership.
- Add a regression test that fails fast instead of hanging forever.
- If a timeout is the only assertion, keep it short and explain why it is stable.

## Report Addendum

```markdown
## Hang Evidence

| Evidence | Path or Command | Finding |
|---|---|---|
| Process tree | `<command>` | <summary> |
| Stack sample | `<path>` | <summary> |
| Timeout regression | `<test>` | <summary> |
```

---

**Source:** Adapted from an external skill corpus / `deadlock-finder-and-fixer`. Pattern-only, no verbatim text.
