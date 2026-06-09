# Metamorphic Testing

Use this reference when `$test` needs stronger evidence than example-based
assertions can provide, especially for ranking, transforms, parsers, planners,
and other behavior where one exact expected answer is too narrow.

## When To Use It

Metamorphic tests fit when the target should preserve or transform properties
across related inputs.

Good targets:

- Parsers and serializers with round-trip or normalization behavior.
- Search, ranking, scoring, or filtering code with monotonicity rules.
- Refactors where old and new paths should agree on observable output.
- Data transforms where field order, whitespace, or batching should not matter.
- CLI wrappers where equivalent flags or input forms should converge.

Avoid metamorphic tests when the contract is a single fixed artifact. Use a
golden artifact strategy for that case.

## Relation Patterns

| Relation | Example Check |
|---|---|
| Round trip | `decode(encode(x))` preserves the normalized value. |
| Idempotence | Applying the operation twice equals applying it once. |
| Commutativity | Reordering independent inputs keeps the same result. |
| Monotonicity | Adding a stronger signal cannot lower the ranked result. |
| Equivalence | Two public entry points produce the same observable output. |
| Partitioning | Batched input equals the merged output of smaller batches. |

## Test Loop

1. Name the invariant before writing cases.
2. Generate or hand-pick related inputs that differ in one controlled way.
3. Run the real public API, CLI, or script on every related input.
4. Compare the property that must hold, not private implementation details.
5. Add any failure input as a stable regression fixture.

## Output

Record the invariant and generated cases in `.agents/test/summary.md`:

```markdown
## Metamorphic Coverage

| Target | Relation | Cases | Findings |
|---|---|---:|---|
| <target> | <relation> | <n> | <none or issue> |
```

---

**Source:** Adapted from an external skill corpus / `testing-metamorphic`. Pattern-only, no
verbatim text.
