# Golden Artifacts

Use this reference when Test must protect generated files, rendered output,
snapshots, reports, command output or serialized data, and before accepting a
change to a checked-in artifact that defines a behavior contract.

## When golden tests fit

Golden tests are useful when the artifact itself is the interface: humans care
about the exact output, or downstream tooling depends on its stable shape.

Good targets:

- Generated markdown, JSON, YAML, CLI help, reports and manifests.
- Rendered templates after dynamic fields are scrubbed.
- Cross-platform output after path and newline normalization.

They are weak when the output is volatile, host-specific or easier to assert
through a structured parser; avoid them for output with no stable contract.

## Choose one comparison mode up front

| Mode | Use when | Required guard |
|---|---|---|
| Exact | Bytes are intentionally stable | Deterministic generator and stable inputs. |
| Scrubbed | Output has timestamps, temp paths, UUIDs, hashes or host values | The scrubber covers every volatile field. |
| Structured | JSON, YAML or CSV can be parsed | Canonical ordering or sorted fields before comparison. |
| Fuzzy numeric | Floats, timings or benchmark-like values vary | An explicit tolerance stated in the test. |
| Shape | Values are intentionally variable | Required keys and types are asserted. |
| Diff review | A human-readable artifact changed | The accepted diff and its reason are stated in the commit message or Test's handoff. |

## Update discipline

Never refresh a golden file as the first move or just to make a test pass.

1. Run the current test and inspect the diff.
2. Identify the source change that produced it.
3. Decide whether the diff is intended behavior, fixture drift or a bug.
4. Update the artifact only for intended behavior or fixture drift, and state
   why in the commit message or Test's handoff.
5. For a bug, fix the generator or source data instead.

## Review checklist

- Dynamic fields are scrubbed or parsed away.
- The fixture input is checked in near the artifact or named in the test.
- The test fails on missing fields, extra unknown fields and wrong exit codes
  when those are part of the contract.
- The update command is documented in the test or a nearby fixture comment.

Report accepted and rejected artifact changes in
[Test's handoff](../SKILL.md#output-specification); persist them only for a
requested destination.

---

**Source:** Adapted from an external skill corpus / `testing-golden-artifacts`. Pattern-only, no verbatim text.
