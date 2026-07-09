# Rustdoc Library Documentation Guidelines

Use this router before editing docs for a Rust crate.

## By Task

| What you are doing | Load these files |
|--------------------|------------------|
| Adding crate or module docs | `references/rustdoc-patterns.md` |
| Writing public API examples | `workflows/document-library.md`, `references/rustdoc-patterns.md` |
| Fixing doctests | `references/rustdoc-patterns.md` |
| Preparing docs.rs output | `workflows/document-library.md` |

## By Symptom

| Symptom | Load |
|---------|------|
| Public API is documented by implementation detail | `references/rustdoc-patterns.md` |
| Examples in docs drift from real usage | `workflows/document-library.md` |
| Feature-gated docs fail | `references/rustdoc-patterns.md` |
| Users cannot find the first useful example | `references/rustdoc-patterns.md` |

## Decision Tree

```text
Need crate docs?
|
+-- New consumer would ask "what is this?" -> crate-level docs
+-- Public type has invariants? -> document invariants and examples
+-- Public function can fail? -> document errors
+-- Example is short? -> doctest
+-- Example is multi-file or long? -> examples/ binary
```

## File Index

| File | Purpose |
|------|---------|
| `references/rustdoc-patterns.md` | Documentation, examples, and doctest rules |
| `workflows/document-library.md` | Step-by-step documentation workflow |
