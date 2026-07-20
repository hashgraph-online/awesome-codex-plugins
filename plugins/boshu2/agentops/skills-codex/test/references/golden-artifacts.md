# Golden Artifacts

Use this reference when `/test` must protect generated files, rendered output, snapshots, reports, command output, or serialized data.

## When Golden Tests Fit

Golden tests are useful when humans care about the exact artifact or when downstream tooling depends on stable shape.

Good targets:

- Generated markdown, JSON, YAML, CLI help, reports, and manifests.
- Rendered templates after dynamic fields are scrubbed.
- Cross-platform output after path and newline normalization.
- Structured output that can be canonicalized before comparison.

Avoid golden tests for volatile output that has no stable contract.

## Golden Modes

| Mode | Description |
|---|---|
| Exact | Byte-for-byte comparison after deterministic generation. |
| Scrubbed | Replace timestamps, temp paths, UUIDs, hashes, and host-specific values before comparing. |
| Semantic | Parse into structured data and compare canonical JSON or sorted fields. |
| Fuzzy numeric | Allow explicit tolerance for floats, timing, or benchmark-like values. |
| Shape-only | Assert required keys and types when full values are intentionally variable. |

## Update Discipline

Never update golden files as the first move.

1. Run the test and inspect the diff.
2. Decide if the diff is intended.
3. If intended, update the golden file and mention why in the summary.
4. If unintended, fix the generator or source data.

## Output

Add this to `.agents/tests/summary.md` when golden files change:

```markdown
## Golden Changes

| Artifact | Verdict | Reason |
|---|---|---|
| <path> | accepted/rejected | <why> |
```

---

**Source:** Adapted from an external skill corpus / `testing-golden-artifacts`. Pattern-only, no verbatim text.
