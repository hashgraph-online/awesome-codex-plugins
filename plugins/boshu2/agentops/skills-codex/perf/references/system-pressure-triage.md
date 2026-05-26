# System Pressure Triage

Use this reference when slow tests, stuck agents, failing local models, or sluggish builds may be caused by host pressure rather than target-code performance.

## Triage Order

1. CPU saturation and load average.
2. Memory pressure and swap activity.
3. Disk fullness and I/O wait.
4. Process count and stale worker sessions.
5. Competing builds, language servers, model servers, or runaway test loops.
6. Network or remote-service dependency slowness.

## Rules

- Diagnose before killing processes.
- Preserve user-owned interactive sessions unless explicitly approved.
- Prefer graceful shutdown before force kill.
- Do not tune OS-level settings without operator approval.
- Record host pressure separately from application performance.

## Output

If host pressure affects the result, add this section to the perf report:

```markdown
## Host Pressure

| Resource | Observation | Impact |
|---|---|---|
| CPU | <value> | <impact> |
| Memory | <value> | <impact> |
| Disk/I/O | <value> | <impact> |
```

---

**Source:** Adapted from an external skill corpus / `system-performance-remediation`. Pattern-only, no verbatim text.
