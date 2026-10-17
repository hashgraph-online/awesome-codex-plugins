# Document Library Workflow

Use this workflow when documenting a Rust crate or preparing docs for release.

## Prerequisites

- Public API surface or planned release diff.
- Current feature list.
- Known primary user task.

**Reference**: `references/rustdoc-patterns.md`

## Workflow Steps

### Step 1: Define the Reader Path

**Goal**: Make first use obvious.

- [ ] Identify the main task a new user wants to complete.
- [ ] Write crate-level docs around that task.
- [ ] Link to important modules and examples.

### Step 2: Document Public API Contracts

**Goal**: Explain what callers can rely on.

- [ ] Document public structs, enums, traits, and functions.
- [ ] Add invariants, errors, panics, and feature requirements.
- [ ] Avoid documenting private implementation mechanics.

### Step 3: Add Executable Examples

**Goal**: Prevent example drift.

- [ ] Add short doctests to core APIs.
- [ ] Hide noisy setup lines where helpful.
- [ ] Move long flows into `examples/`.

### Step 4: Validate Docs

**Goal**: Catch docs that compile only in one configuration.

- [ ] Run `cargo test --doc`.
- [ ] Run docs with `--all-features` when feature-gated APIs exist.
- [ ] Check generated docs navigation for missing first-use guidance.

### Step 5: Prepare Release Notes

**Goal**: Make documentation changes visible to users.

- [ ] Summarize new or changed examples.
- [ ] Note feature-gated documentation.
- [ ] Include docs commands in the PR test plan.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Docs mirror module internals | New users cannot find the happy path | Start from caller task |
| Examples are not compiled | They drift quickly | Use doctests |
| Feature docs omitted | Users cannot enable APIs | Document feature flags |

## Exit Criteria

- [ ] First-use path is clear from crate docs.
- [ ] Public API contracts are documented.
- [ ] Doctests and docs build pass for relevant features.
