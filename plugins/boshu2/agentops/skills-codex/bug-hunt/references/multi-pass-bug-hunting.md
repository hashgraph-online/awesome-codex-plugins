# Multi-Pass Bug Hunting

Use this reference for proactive audits or stubborn bug hunts where a single scan is likely to miss secondary failures.

## Loop

1. Pass 1 - surface scan:
   - Read the target scope.
   - Classify concrete findings.
   - Ignore style-only preferences.
2. Fix or file each confirmed finding.
3. Pass 2 - fresh-eyes rescan:
   - Re-read changed files as if someone else wrote them.
   - Look for bugs introduced by the fix.
4. Pass 3 - integration check:
   - Follow data and control flow across boundaries touched by the fix.
   - Verify tests cover the boundary, not just the local function.
5. Pass 4 - final verification:
   - Run focused tests, then the relevant wider gate.
   - Record remaining risks.

## Finding Rules

- A finding needs a file, failing behavior, and expected behavior.
- If the evidence is only "this looks odd", mark it as a question, not a bug.
- Suppress false positives with a one-line rationale so they do not resurface in the same audit.
- Stop after repeated unconfirmed hypotheses and switch to architecture review.

## Output

Add pass accounting to the bug report:

```markdown
## Pass Accounting

| Pass | Files | Findings | False Positives | Notes |
|---|---:|---:|---:|---|
| 1 | <n> | <n> | <n> | <summary> |
| 2 | <n> | <n> | <n> | <summary> |
```

---

**Source:** Adapted from an external skill corpus / `multi-pass-bug-hunting`. Pattern-only, no verbatim text.
