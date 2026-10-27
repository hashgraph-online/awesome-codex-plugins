# Conformance Harnesses

Use this reference when Test needs to prove an implementation follows an external contract, compatibility surface, schema, protocol, CLI behavior, or generated artifact shape.

## Trigger

Choose conformance testing when the target has a contract that can be exercised repeatedly:

- JSON schema, OpenAPI, protobuf, or CLI output schema.
- Golden behavior from an existing implementation.
- Round-trip parse/render/serialize behavior.
- Cross-runtime compatibility claims.
- Generated artifacts that must remain in sync with source files.

## Harness Patterns

| Pattern | Use When | Check |
|---|---|---|
| Reference implementation | A known-good implementation exists | Candidate output matches reference output for the same inputs. |
| Golden contract | Output is deterministic or can be canonicalized | Compare scrubbed output to checked-in golden fixtures. |
| Round trip | Parser and renderer both exist | `decode(encode(x)) == x` or equivalent invariant. |
| Spec matrix | Behavior is enumerated in a contract table | Each must-support row is a case with its own assertion; a table-test row suffices. |
| Process harness | The target is a CLI/script/daemon | Run the process with fixture inputs and assert exit code, stdout/stderr, and artifacts. |

## Required Loop

1. Identify the contract source of truth.
2. Build fixtures from the contract, not from the implementation under test.
3. Run the current implementation and capture output.
4. Canonicalize dynamic fields before comparing.
5. Fail loudly on unknown fields, missing fields, wrong exit codes, or silently skipped cases.
6. List contract rows left uncovered, with the reason, under `not_checked`.

## Stop Criteria

Stop when every must-support contract row has a mechanical test or is listed
under `not_checked`. Report the contract, cases and gaps in
[Test's handoff](../SKILL.md#output-specification); persist them only for a
requested destination.

---

**Source:** Adapted from an external skill corpus / `testing-conformance-harnesses`. Pattern-only, no verbatim text.
