# Fuzzing

Use this reference when Test targets parsers, serializers, file readers, protocol decoders, untrusted input handlers, state machines, or security-sensitive validation logic.

## Trigger

Prioritize fuzzing for code that accepts:

- Raw bytes, strings, JSON, YAML, XML, CSV, or custom formats.
- Network request bodies, CLI arguments, file contents, or environment input.
- Deserialized objects from untrusted boundaries.
- State transition sequences where operation order matters.

## Rules

- Keep fuzz targets deterministic.
- Minimize external I/O inside fuzz functions.
- Add seed corpus entries for known edge cases before relying on random discovery.
- Assert invariants, not implementation details.
- Save every crash or regression input as a stable fixture.

## Target Template

Every fuzz target needs:

1. A small wrapper around the real public function.
2. A seed corpus with valid, invalid, empty, boundary, and previously broken inputs.
3. At least one invariant:
   - no panic
   - valid input round-trips
   - invalid input returns an error
   - output remains canonical
   - resource use stays bounded

## Triage

When fuzzing finds a failure:

1. Minimize the input.
2. Add it as a named regression fixture.
3. Write a normal unit test for the minimized case.
4. Fix the bug if repair is authorized; otherwise report the minimized
   reproducer under `defects`.
5. After a fix, re-run fuzzing and the regression test.

Report each target's seed count, duration and findings in
[Test's handoff](../SKILL.md#output-specification); persist them only for a
requested destination.

---

**Source:** Adapted from an external skill corpus / `testing-fuzzing`. Pattern-only, no verbatim text.
