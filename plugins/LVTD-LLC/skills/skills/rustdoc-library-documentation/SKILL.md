---
name: rustdoc-library-documentation
description: Write and review Rust library documentation with rustdoc module docs, public API examples, doctests, examples directories, missing-docs gates, docs.rs readiness, and user-first crate narratives. Use when documenting a Rust crate, improving docs before publishing, or turning examples into tested rustdoc.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rustdoc Library Documentation
  category: Rust
  tags: rust,rustdoc,documentation,doctests,library
---

# Rustdoc Library Documentation

Use this skill to make Rust library documentation executable, navigable, and
useful to downstream crate consumers.

## Core Workflow

1. Start from the consumer's first task, not from internal module order.
2. Add crate-level and module-level docs that explain purpose and boundaries.
3. Document public types, functions, errors, features, and invariants.
4. Prefer short compiling examples and doctests for core APIs.
5. Put longer scenarios in `examples/` and reference them from docs.
6. Run docs and doctests before publishing.

## Read Next

| Task | Load |
|------|------|
| Document a public crate API | `guidelines.md`, `workflows/document-library.md` |
| Add doctests or examples | `references/rustdoc-patterns.md` |
| Prepare docs for publishing | `references/rustdoc-patterns.md` |

## Source Notes

Guidance is transformed and paraphrased from Herbert Wolverson,
*Advanced Hands-On Rust*, especially Chapter 4 on documenting a library and
Chapter 15 on sharing crates. Examples are original skeletons.
