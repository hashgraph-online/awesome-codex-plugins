# Review Language Correctness Workflow

Review Go code for representation, ownership, iteration, and text defects before
approving implementation or generated code.

## When to Use

- Reviewing agent-generated or unfamiliar Go.
- Debugging unexpected mutation, retention, ordering, or Unicode behavior.
- Validating parsers, collection transforms, or resource loops.

## Workflow Steps

### 1. Establish the Contract

- [ ] Record module and file language versions and supported targets.
- [ ] Identify external inputs, output formats, and resource limits.
- [ ] Separate language guarantees from implementation observations.

### 2. Review Representation

- [ ] Check numeric sign, width, conversion order, and overflow.
- [ ] Define float-comparison policy where applicable.
- [ ] Add just-inside and just-outside boundary cases.

### 3. Trace Ownership

- [ ] Mark every slice and map as owned, borrowed, shared, or transferred.
- [ ] Trace aliases through slicing, append, copying, and retention.
- [ ] Verify deterministic map-backed output and semantic equality.

### 4. Review Iteration and Lifetime

- [ ] Check range copies, mutation targets, and loop-variable semantics.
- [ ] Check `break`, `defer`, and per-iteration cleanup scopes.
- [ ] Route cross-goroutine ownership to `go-concurrency-pipelines`.

### 5. Review Text

- [ ] Identify byte, rune, or grapheme semantics.
- [ ] Validate UTF-8 and exact trimming behavior.
- [ ] Bound string assembly and retained substrings.

### 6. Prove the Result

- [ ] Add focused boundary and aliasing tests.
- [ ] Run repository tests, vetting, race checks, and supported-version lanes.
- [ ] Route measured allocation or runtime questions to `go-performance-testing`.

## Exit Criteria

- [ ] Every conversion and ownership boundary is deliberate.
- [ ] Iteration and cleanup behavior matches the declared Go version.
- [ ] Text units and external encoding contracts are explicit.
- [ ] Tests exercise the discovered failure modes.
