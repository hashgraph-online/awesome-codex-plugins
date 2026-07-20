# Golden Artifact Strategy

Use this reference before accepting changes to snapshots, generated reports,
rendered docs, CLI output fixtures, or other checked-in artifacts that define a
behavior contract.

## Strategy

Golden artifacts are useful when the artifact itself is the interface. They are
weak when the output is volatile, host-specific, or easier to assert through a
structured parser.

Choose one comparison mode up front:

| Mode | Use When | Required Guard |
|---|---|---|
| Exact | Bytes are intentionally stable | Deterministic generator and stable inputs. |
| Scrubbed | Output has timestamps, paths, or IDs | Scrubber covers every volatile field. |
| Structured | JSON/YAML/CSV can be parsed | Canonical ordering before comparison. |
| Shape | Values are intentionally variable | Required keys and types are asserted. |
| Diff review | Human-readable artifact changed | Diff is attached to the validation note. |

## Update Rules

Do not refresh a golden artifact just to make a test pass.

1. Run the current test and inspect the diff.
2. Identify the source change that produced the diff.
3. Decide whether the diff is intended behavior, fixture drift, or a bug.
4. Update the artifact only for intended behavior or fixture drift.
5. Add a short note explaining why the new artifact is accepted.

## Review Checklist

- Dynamic fields are scrubbed or parsed away.
- The fixture input is checked in near the artifact or named in the test.
- The test fails on missing fields, extra unknown fields, and wrong exit codes
  when those are part of the contract.
- The update command is documented in the test or nearby fixture comment.

## Output

Add an acceptance table to `.agents/tests/summary.md` when golden files change:

```markdown
## Golden Artifact Review

| Artifact | Decision | Evidence |
|---|---|---|
| <path> | accepted/rejected | <diff or command> |
```

---

**Source:** Adapted from an external skill corpus / `testing-golden-artifacts`. Pattern-only, no
verbatim text.
