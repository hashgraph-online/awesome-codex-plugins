# Publishing Patterns

Patterns for preparing Rust crates for release through Cargo.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| Cargo metadata | Consumer-facing package fields in `Cargo.toml`. |
| Package dry-run | Local simulation of package creation and publish checks. |
| Package contents | Files included by Cargo after include/exclude rules. |
| Docs.rs readiness | Whether docs build under published package constraints. |
| Release gate | Checks required before a publish command is allowed. |

## Core Rules

1. Treat published packages as immutable user contracts.
2. Verify `Cargo.toml` metadata before release: description, license, repository,
   readme, keywords, categories, and version.
3. Run tests, docs, and feature-matrix checks before packaging.
4. Inspect package contents with Cargo before publishing.
5. Exclude local artifacts, fixtures with secrets, and generated junk.
6. Ensure README examples match the published API.
7. Publish from a clean working tree and intentional version/tag.

## Metadata Checklist

- [ ] `name` is final and available.
- [ ] `version` follows the release plan.
- [ ] `description` is concise and user-facing.
- [ ] `license` or `license-file` is set.
- [ ] `repository` points to the public source if applicable.
- [ ] `readme` exists and matches crate behavior.
- [ ] `keywords` and `categories` are accurate.
- [ ] Feature flags are documented.

## Package Inspection Commands

```bash
cargo fmt --check
cargo test
cargo test --all-features
cargo test --no-default-features
cargo test --doc
cargo package --list
cargo publish --dry-run
```

Adapt the feature commands to the crate's supported matrix.

## Review Smells

| Smell | Risk | Fix |
|-------|------|-----|
| README only works from repo path | Published users cannot follow it | Test from package assumptions |
| Missing license metadata | Cargo or users cannot classify usage | Add license field/file |
| Dry-run skipped | Publish failure discovered too late | Run dry-run before PR completion |
| Package includes local artifacts | Leaks noise or secrets | Use include/exclude and inspect list |
