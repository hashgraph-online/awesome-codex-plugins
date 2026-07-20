# Conformance Harnesses

Use this reference when `/test` needs to prove an implementation follows an external contract, compatibility surface, schema, protocol, CLI behavior, or generated artifact shape.

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
| Spec matrix | Behavior is enumerated in a contract table | Each row has one test case and one assertion target. |
| Process harness | The target is a CLI/script/daemon | Run the process with fixture inputs and assert exit code, stdout/stderr, and artifacts. |

## Required Loop

1. Identify the contract source of truth.
2. Build fixtures from the contract, not from the implementation under test.
3. Run the current implementation and capture output.
4. Canonicalize dynamic fields before comparing.
5. Fail loudly on unknown fields, missing fields, wrong exit codes, or silently skipped cases.
6. Write a coverage matrix showing contract rows covered and uncovered.

## Output

Add a short conformance section to `.agents/tests/summary.md`:

```markdown
## Conformance Coverage

| Contract | Cases | Covered | Gaps |
|---|---:|---:|---|
| <schema or spec> | <n> | <n> | <missing cases> |
```

## Stop Criteria

Stop when every must-support contract row has a mechanical test or a documented exclusion with owner and rationale.

---

**Source:** Adapted from an external skill corpus / `testing-conformance-harnesses`. Pattern-only, no verbatim text.
