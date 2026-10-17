# Go Language Correctness Rules

## Numbers

- Parse into the intended width when practical.
- Reject negative-to-unsigned and out-of-range narrowing before conversion.
- Check `a > max-b` before unsigned addition and `a > max/b` before
  multiplication when overflow is possible.
- Treat sizes from untrusted input as both arithmetic and resource limits.
- Document float tolerance with units, scale, and boundary cases.

## Slices

- Use `make([]T, n)` when filling by index and `make([]T, 0, n)` when appending.
- Use `len(s) == 0` for emptiness unless nil carries an explicit wire meaning.
- Allocate destination length before `copy`, or use `append([]T(nil), src...)`.
- Copy at ownership boundaries when later mutation or retention must be independent.
- Clip capacity with `s[:len(s):len(s)]` only to restrict append authority;
  do not call it a copy.
- Clear pointer-bearing tails before truncating when discarded references must die.
- Do not assert append capacity-growth heuristics in tests.

## Maps and Comparisons

- Size a map when cardinality is known and material.
- Sort keys before deterministic output.
- Do not depend on visibility of inserts made during map iteration.
- Use a domain-specific equality function for open-ended or semantic values.
- Never make runtime map internals part of correctness or portability logic.

## Range and Resources

- Mutate slice elements by index when range would copy the element.
- Check whether ranging an array value causes an undesirable copy.
- Determine loop-variable semantics from the module or file language version.
- Use labels or returns when `break` must escape an outer construct.
- Move per-iteration acquisition into a helper so deferred cleanup runs promptly.

## Text

- Name byte, rune, and grapheme limits explicitly.
- Validate external UTF-8 before applying Unicode semantics.
- Do not index a string at a rune-range byte offset and call the byte a rune.
- Prefer `strings.Builder` or `bytes.Buffer` for substantial incremental assembly.
- Guard preallocation arithmetic before calling `Grow`.
- Use `TrimSuffix` for a literal suffix and cutset trim functions only deliberately.
- Clone a retained substring only when independent lifetime is required.

## Verification

- Test minimum, maximum, just-outside, negative, empty, nil, and oversized inputs.
- Test aliasing by mutating caller and callee views independently.
- Test deterministic output across repeated runs.
- Include ASCII, multibyte UTF-8, invalid UTF-8, combining marks, and emoji where relevant.
- Run tests under every supported Go language version when semantics differ.
