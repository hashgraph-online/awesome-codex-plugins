# Rust Crate Publishing Readiness Guidelines

Use this router before preparing a crate for release or publication.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Creating a release PR | `workflows/prepare-crate-release.md` |
| Checking Cargo metadata | `references/publishing-patterns.md` |
| Debugging `cargo publish --dry-run` | `references/publishing-patterns.md` |
| Reviewing package contents | `workflows/prepare-crate-release.md`, `references/publishing-patterns.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Crate builds locally but package dry-run fails | `references/publishing-patterns.md` |
| README or docs mention unavailable APIs | `workflows/prepare-crate-release.md` |
| Package includes generated junk or secrets | `references/publishing-patterns.md` |
| Feature-gated APIs fail on docs.rs | `references/publishing-patterns.md` |

## Decision Tree

```text
Publishing a Rust crate?
|
+-- Metadata incomplete? -> fix Cargo.toml first
+-- Docs/examples unverified? -> run docs and example checks
+-- Feature flags exist? -> run feature matrix
+-- Package contents uncertain? -> cargo package --list
+-- Ready to publish? -> dry-run from clean branch/tag
```

## File Index

| File | Purpose |
|------|---------|
| `references/publishing-patterns.md` | Metadata, package, and release gate rules |
| `workflows/prepare-crate-release.md` | Step-by-step crate publishing readiness process |
