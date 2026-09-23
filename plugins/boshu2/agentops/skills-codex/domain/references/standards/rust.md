# Rust Standards (Tier 1)

## Required
- `cargo fmt` (automatic)
- `cargo clippy` passes (no warnings)
- All public items documented (rustdoc)

## Error Handling
- Use `Result<T, E>` for fallible operations
- Implement custom errors with `thiserror` or `anyhow`
- Never `unwrap()` in library code (OK in tests/bins)
- Use `?` operator for error propagation

## Adapter Recursion Guard
- Subprocess adapters that can invoke their own kernel must set a guard env var
  on every child command: `<TOOL>_IN_PROGRESS=1`.
- Kernel entry must reject re-entry when that env var is already present.
- This is a two-end check: set-on-spawn plus check-at-entry. One end alone is
  not enough.
- Source pattern: commit `97e16fe`, bead `mo-l1tyqp.23`, and
  `MTO_SKILL_AUDIT_IN_PROGRESS` from the Mt Olympus skill-audit adapter fix.

```rust
pub const GUARD_ENV: &str = "MY_TOOL_IN_PROGRESS";

fn command() -> std::process::Command {
    let mut cmd = std::process::Command::new("sh");
    cmd.env(GUARD_ENV, "1");
    cmd
}

fn entry() -> Result<(), MyError> {
    if std::env::var_os(GUARD_ENV).is_some() {
        return Err(MyError::Recursion);
    }
    Ok(())
}
```

## Ownership & Borrowing
- Prefer references over cloning
- Use `&str` in function params over `String`
- Add explicit lifetime annotations when needed
- Clone sparingly and document why

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| `unwrap()` | Panic on None/Err | Use `?` or pattern match |
| Mutable statics | Data races | Use `once_cell` or `Mutex` |
| String allocation | Performance | Use `&str` in function params |
| Lifetime errors | Borrow checker reject | Add explicit lifetimes |
| Unsafe block | Memory unsafety | Add `// SAFETY:` comment |
| Excessive `.clone()` | Performance waste | Use references or `Cow<T>` |

## Unsafe Code
- Always add `// SAFETY:` comment explaining invariants
- Minimize unsafe scope
- Prefer safe abstractions

## Security
- Minimize `unsafe` blocks — each needs `// SAFETY:` justification
- Use `secrecy::Secret<T>` for sensitive values (prevents accidental logging)
- Validate all external input before deserialization (`serde` validators)
- Prefer `ring` or `rustls` over OpenSSL bindings

## Documentation
- All public items must have rustdoc comments (`///`)
- Include `# Examples` section in doc comments for complex APIs
- Use `#![deny(missing_docs)]` in library crates
- Run `cargo doc --no-deps` to verify doc builds

## Testing
- `cargo test` (built-in)
- `cargo test --doc` (doc tests)
- Use `#[cfg(test)]` modules
- `cargo bench` for benchmarks
