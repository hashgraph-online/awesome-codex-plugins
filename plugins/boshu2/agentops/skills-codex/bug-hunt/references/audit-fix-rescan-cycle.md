# Audit-Fix-Rescan Cycle

## When to Use

Reach for the multi-pass cycle when one pass is not enough:

- Pre-release or pre-merge hardening.
- Reviewing code generated in a long agent session or by another agent.
- Audit Mode (`$bug-hunt --audit`) over more than a handful of files.
- After a batch of non-trivial fixes that may have shifted invariants nearby.

## Why Iterate

Each pass surfaces a different layer:

1. Loud defects: null derefs, missing `await`, resource leaks, unsanitized input.
2. Defects masked by the loud ones: logic errors, edge cases, partial error handling.
3. Defects you introduced while fixing layers 1 and 2: regressions, broken invariants.
4. Verification: confirm nothing remains visible.

Stopping at pass 1 ships a partially-fixed tree. Stopping at pass 2 ships your own regressions.

## The Cycle

```
audit  →  fix  →  rescan
  ▲                  │
  └──── not clean ───┘
```

## Pass Contracts

| Pass | Mode | Done When |
|------|------|-----------|
| 1. Surface | Scanners + line-by-line read | Loud defects fixed or filed |
| 2. Re-read | Manual fresh-eyes review of touched files | No new findings on re-read |
| 3. Integration | Test suite + diff vs merge base | Tests green, no regressions |
| 4. Verify | Rescan with the pass-1 tools | Scanner exits clean |

Collapse to two passes for small scope; expand for security or pre-release work.

## Pass 1 — Surface

Run the audit-mode workflow in `skills-codex/bug-hunt/SKILL.md` (Audit Steps 1–4). Triage every finding into:

- Real bug → fix and record `file:line` plus the change.
- False positive → record one-line justification.
- Defer → mark for pass 2 with a reason.

## Pass 2 — Re-read

Reload every file touched in pass 1 and read it top to bottom. Ask:

- Did the fix change a precondition other code in this file relies on?
- What edge cases did the original defect hide (empty input, single element, boundary, concurrency)?
- Are there structurally-similar defects elsewhere in the same file?
- Does the trace through callers and tests still hold?

## Pass 3 — Integration

```
go test ./...        # or pytest, npm test, cargo test
git diff <merge-base>..HEAD
```

Read the change as a whole, not just the latest commit. Regressions filed during pass 3 go back to pass 1 of the next iteration.

## Pass 4 — Verify

Rerun the scanners and reads from pass 1 against the post-fix tree. Pass 4 succeeds only when no new findings appear and convergence criteria hold (`references/convergence-criteria.md`).

## Per-Pass Notes

Append to the audit report each iteration:

```markdown
## Pass N — YYYY-MM-DD
- Scope this pass:
- Bugs fixed: N (file:line each)
- False positives: N (one-line justification each)
- Deferred to pass N+1: N (with reason)
- Tests run: <suite> — <result>
- Convergence status: see references/convergence-criteria.md
```

## Anti-Patterns

| Avoid | Do instead |
|-------|------------|
| Running pass 1 only | Add at least one re-read pass for any non-trivial fix set |
| Suppressing findings without a reason | One-line justification per suppression |
| Trusting only a green test suite | Tests + scanner + manual re-read together |
| Counting timeouts as bug-hunt failures | Track per `references/failure-categories.md` |
| Reading only the latest commit | Read the full diff against the merge base |

---

> Pattern adopted from `multi-pass-bug-hunting` (ACFS skill corpus). Methodology only — no verbatim text.
