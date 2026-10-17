# Go Language Correctness Checklist

## Version

- [ ] The module and relevant file language versions are known.
- [ ] Version-dependent advice is gated by the declared language version.
- [ ] Runtime and compiler observations are not presented as language guarantees.

## Numbers

- [ ] Sign and width are checked before conversion.
- [ ] Size, offset, addition, and multiplication bounds are checked before use.
- [ ] Floating-point equality follows a documented domain policy.

## Collections

- [ ] Slice ownership and mutation authority are explicit.
- [ ] Views, clipped capacity, and independent copies are distinguished.
- [ ] Retained subslices or substrings cannot pin surprising amounts of memory.
- [ ] Pointer-bearing tails are cleared when retention matters.
- [ ] Map-backed output is sorted when deterministic output is contractual.
- [ ] Equality matches domain meaning and cannot panic on dynamic values.

## Iteration and Resources

- [ ] Range copies are understood before mutation.
- [ ] Loop capture guidance matches the language version and declaration form.
- [ ] `break` exits the intended construct.
- [ ] Per-iteration resources close before the next iteration.

## Text

- [ ] Byte, rune, and grapheme limits are named accurately.
- [ ] External UTF-8 validity is checked when required.
- [ ] Literal suffix removal does not use cutset trimming.
- [ ] String assembly and preallocation are bounded.

## Verification

- [ ] Boundary, aliasing, invalid-text, and deterministic-output tests exist.
- [ ] The repository's tests, race checks, vetting, and linters pass.
- [ ] Performance claims are routed to measured evidence.
