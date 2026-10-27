---
name: rust-coder
description: "Implement, refactor, and migrate production Rust with repository-grounded ownership, type-driven invariants, explicit errors, safe concurrency, minimal unsafe code, and verified Cargo workflows. Use for Rust features, crates, CLIs, services, libraries, async code, FFI, performance work, migrations, or substantial .rs and Cargo.toml changes, including requests such as 'rust-coder', 'write Rust', or 'implement this Rust feature with Codex'."
requires:
  programs: []
  harness:
    - {slot: 4.shell, need: required}
    - {slot: 4.file-read-write, need: required}
---

# Rust Coder

Implement directly in the current Codex session. Do not launch another Codex process.

Read [references/standards.md](references/standards.md) completely before editing. Repository instructions and the declared toolchain override generic preferences.

## Inspect

Read the smallest complete set of evidence:

- Nearest `AGENTS.md`, `CLAUDE.md`, and repository instructions.
- Root and target `Cargo.toml`, `Cargo.lock`, `rust-toolchain*`, Cargo configuration, lint and format configuration, features, targets, and continuous-integration commands.
- Every target file in full, its parent exports, immediate callers, traits, types, errors, feature gates, platform boundaries, focused tests, and one or two tested sibling modules.
- The exact format, check, test, Clippy, feature, and target commands used by the crate.

Determine the edit mode, crate kind, toolchain and minimum Rust version, public contract, ownership, resource lifecycle, error model, concurrency and cancellation, safety boundary, and invariants. Default to a hard cut; preserve compatibility only when an explicitly confirmed published contract requires it.

Ask only when an unresolved fact could change public behavior, durable state, safety, or migration semantics. Otherwise make repository-grounded assumptions and continue.

## Design and implement

Resolve the change in this order:

1. Domain invariants and invalid states.
2. Ownership, borrowing boundaries, and resource lifetimes.
3. Types, state transitions, public API, and errors.
4. Concurrency, cancellation, and platform boundaries when relevant.
5. Implementation mechanics and measured optimization.

Work directly with the available read and edit tools. Make the smallest coherent change and preserve unrelated work. Reuse existing crates, types, traits, errors, runtime, and helpers. Do not add dependencies, features, configuration, compatibility paths, `unsafe`, smart pointers, clones, lint suppressions, or abstractions merely to satisfy the compiler.

Treat borrow-checker and trait errors as design feedback. Keep checking and revising until the observable success criteria pass.

## Verify

1. Review the diff; every changed line must trace to the request.
2. Run the repository's exact commands. Without stronger local commands, use focused equivalents of `cargo fmt --all --check`, `cargo check`, `cargo test`, and `cargo clippy --all-targets --all-features -- -D warnings`.
3. Exercise every changed public feature combination and target that local tooling can validate.
4. Search changed production Rust for unexplained `clone`, `Arc`, `Rc`, `Box`, interior mutability, `unwrap`, `expect`, panics, placeholders, `unsafe`, and lint suppressions.
5. Add documentation, compile-fail, property, concurrency, Miri, package, or consumer checks only when the changed contract makes them relevant.

If a check fails, fix the exact observed failure and rerun it. Stop after three failed correction rounds and report the blocker instead of widening scope, cloning around ownership, adding unsafe code, or weakening validation.

## Report

Lead with the outcome. Name changed files, consequential assumptions, ownership/type/error decisions, compatibility decisions, and every command actually run with its result.
