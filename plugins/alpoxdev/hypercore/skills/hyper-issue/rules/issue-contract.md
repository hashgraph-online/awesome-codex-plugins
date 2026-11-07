# Issue Contract

Use this rule before writing any issue body. It owns classification, the evidence standard, the body language, the required sections, the `hyper:` block, the duplicate check, metadata, and the write verification.

## 1. Classify

Classify by the requested behavior, not by the word the user used.

| Class | Use when | Evidence required |
|---|---|---|
| `bug` | Observed behavior differs from expected or from a violated invariant | The failing repro or log excerpt, plus the cause pinned to a path and line |
| `feature` | New user-visible behavior, or a material expansion of existing behavior | The decided outcome, the affected surface, and the resolved open decisions |
| `task` | Maintenance, refactor, docs, tests, hardening, migration, cleanup | Current state and the exact boundary of the change |

A defect whose cause is not confirmed on the named revision is not a `bug`. Either confirm it, or record it as `bug` with `Assumption:` on the cause line and say what would confirm it. Never relabel an unconfirmed defect as a `task` to skip the cause standard.

Split into separate issues when two items can be implemented and verified independently. Keep them together when they share one intended outcome, one change boundary, or one verification.

## 2. The Evidence Standard

- Every factual line carries a path with a line anchor, a command with its output, or a tracker reference.
- "It feels wrong" is not evidence; a captured failure is.
- Distinguish the symptom, the trigger, the propagation path, and the root cause.
- Do not copy secrets, tokens, personal data, or customer values into a body. Redact them and say what was redacted.
- A body must stay actionable after the original logs, database, or session is gone: convert an inaccessible fact into a minimal fixture, a test vector, or an exact local setup.

## 2a. Body Language

The reader of an issue is an agent starting a fresh session with no access to this conversation. Write for that reader.

- Write the title and the whole body in English, even when the conversation and the run report are in Korean. Keep a quoted error message, log line, or UI string in its original language.
- Write the title like a commit subject: imperative, lowercase after an optional `type(scope):` prefix, no trailing period, at most 72 characters (`fix(orders): return 409 on idempotency key replay`).
- Write body lines as short declarative or imperative sentences with concrete nouns: paths, symbols, commands, status codes. No pronouns that point back into the conversation ("the thing we saw", "as discussed").
- Mark inference with `Assumption: <statement> - Confirm by: <check>`; never hedge a whole paragraph.
- A repository issue template or an explicit user instruction that sets another language wins; record that choice in the run notes.

## 3. Required Sections

Every body has these sections, in this order, with these exact English names:

1. `## What` - one paragraph: what is wrong or what is wanted, and the impact.
2. `## Evidence` - paths, commands, output, logs. Redaction noted.
3. `## Cause` (bug) or `## Intended behavior` (feature or task) - the confirmed cause, or the decided behavior.
4. `## Scope` - the exact change boundary, plus the `hyper:` block.
5. `## Out of scope` - what this issue deliberately does not do.
6. `## Acceptance` - binary checks a reviewer can run.
7. `## Verify` - the literal command that proves the work, and what a pass looks like.

An acceptance criterion that cannot be observed is not acceptance. "Works well" is not acceptance; "`GET /api/x` returns 200 with `status: ready`" is.

## 4. The `hyper:` Block

Inside `## Scope`, one fenced YAML block, written by hand from the evidence:

```yaml
hyper:
  touches:            # paths or globs this issue writes
    - src/api/retry.ts
  depends_on: []      # issue numbers that must land first
  conflicts_with: []  # issue numbers that touch the same code and must not run in parallel
  lane_hint: retry    # short kebab-case name for the write set
  verify: "bun test src/api/retry.test.ts"
  size: s             # s | m | l, from the change boundary
```

Rules:

- `touches` is the write set, not the read set. A file read only for context is not listed.
- A shared file that several issues must edit is listed by every one of them, and the manifest puts them in one lane in dependency order.
- `depends_on` and `conflicts_with` are issue numbers, never guesses. Unknown is `[]`, and the batch stage re-derives the edge from `touches` overlap.
- `verify` is a command that already exists or that the issue itself creates and names. It is never "run the tests".
- `size` `l` means the issue should be split before it is assigned; say so in `## Scope`.

## 5. The Duplicate Check

1. Run one query built from the title's two most specific terms plus the touched path, scoped to open issues.
2. Read the top results' bodies, not only their titles.
3. Record the query and the outcome in the run notes.

| Outcome | Action |
|---|---|
| An open issue covers the same outcome and boundary | Update that issue instead of creating one; add only missing sections |
| An open issue covers part of it | Create this issue, and add `Refs #<n>` in the body |
| An open issue is closed as done | Re-check the target revision; if the defect is gone, report it and create nothing |
| Nothing matches | Create |

A failed or incomplete duplicate query is reported as a gap, not treated as "no duplicate".

## 6. Metadata

- Apply a label, type, or field only when the evidence supports the value and the repository already defines it. Never invent a label name.
- `bug` maps to a bug label or type when one exists; `feature` and `task` map to their own.
- Priority comes from impact, reach, urgency, and available workaround. Size comes from the change boundary in `## Scope`.
- Omitting an uncertain value is correct; guessing is not. Record each omission and its reason in the run notes.

## 7. The Write

1. Create or update once, with the body written to a temporary file and passed by path.
2. Re-read the record: title, body, labels, state, and number.
3. Compare the re-read body with the intended body; a mismatch is reported, not silently accepted.
4. A failed write, or one with an unknown outcome, is reconciled by reading the tracker before any retry. Never create a second issue for the same body.

When the tracker is unavailable or not writable, save the body at `.hyper/issues/<slug>/drafts/<n>-<slug>.md`, record the missing capability, and report the exact command the user can run.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Investigation-first issue authoring with a decision-complete handoff and a duplicate gate before writing | [kdy1-scripts add-issue](https://github.com/kdy1/kdy1-scripts) |
| Per-task dependency and conflict metadata, and one owner for shared files | [automazeio/ccpm](https://github.com/automazeio/ccpm) |
| One issue per independently implementable unit, sized to a single context | [MrLesk/Backlog.md](https://github.com/MrLesk/Backlog.md) |
| A cause must be confirmed on the named revision before it is reported as a defect | [kdy1-scripts add-issue](https://github.com/kdy1/kdy1-scripts) root-cause standard |
| Issue titles and bodies are written in English for a fresh-session agent, like commit messages | user instruction, 2026-11-07 |

### Evidence grade

`LOCAL` - the section list and the `hyper:` key set are this package's design. The classification and duplicate rules are adapted from the named prior art.
