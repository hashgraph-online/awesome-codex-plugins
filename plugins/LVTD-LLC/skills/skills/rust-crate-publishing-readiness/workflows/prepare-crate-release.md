# Prepare Crate Release Workflow

Use this workflow before publishing a Rust crate or opening a release PR for a
reusable library.

## Prerequisites

- Intended crate version.
- Release branch or clean working tree.
- Current Cargo feature list.

**Reference**: `references/publishing-patterns.md`

## Workflow Steps

### Step 1: Check Consumer Metadata

**Goal**: Make the package understandable on crates.io.

- [ ] Verify package name, version, description, license, repository, readme,
      keywords, and categories.
- [ ] Confirm README examples match public API.
- [ ] Confirm feature flags are documented.

### Step 2: Validate Code, Docs, and Features

**Goal**: Catch broken release configurations.

- [ ] Run formatting checks.
- [ ] Run tests for default features.
- [ ] Run tests for no-default and all-features when supported.
- [ ] Run doctests and docs.
- [ ] Run examples if the crate ships examples.

### Step 3: Inspect Package Contents

**Goal**: Ship the files users need and nothing surprising.

- [ ] Run `cargo package --list`.
- [ ] Confirm license, README, examples, and required fixtures are included.
- [ ] Confirm local artifacts, large generated files, and secrets are excluded.

### Step 4: Dry-Run Publish

**Goal**: Exercise Cargo's publish checks without releasing.

- [ ] Run `cargo publish --dry-run`.
- [ ] Fix metadata, docs, or packaging errors.
- [ ] Re-run dry-run after fixes.

### Step 5: Final Release Gate

**Goal**: Publish only from an intentional state.

- [ ] Confirm working tree is clean.
- [ ] Confirm version and changelog/release notes match.
- [ ] Confirm tag or release plan is agreed.
- [ ] Publish or leave clear manual publish instructions if credentials are not
      available.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Publishing from dirty tree | Release cannot be reproduced | Clean and tag intentionally |
| Package contents not inspected | Missing files or accidental leaks | Run `cargo package --list` |
| Testing only local workspace | Package build differs | Use dry-run |

## Exit Criteria

- [ ] Metadata is complete.
- [ ] Tests/docs/features pass for supported configurations.
- [ ] Package contents and dry-run are verified.
