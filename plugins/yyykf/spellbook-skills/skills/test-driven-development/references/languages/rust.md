# TDD in Rust

**Load this reference when:** doing TDD in Rust. The core skill is language-agnostic; this file adds only Rust framework choices, idioms, anti-patterns, and tooling. Generic mock pitfalls live in [../testing-anti-patterns.md](../testing-anti-patterns.md) and are not repeated here.

## Test framework & runner

Rust ships a **built-in test harness** — no test framework dependency is needed for unit, integration, or doc tests. You annotate functions with `#[test]` and run them with `cargo test`. This is the idiomatic default; reach for external crates only for what the harness lacks (mocking, parametrization, property tests). See [The Rust Book ch.11](https://doc.rust-lang.org/book/ch11-00-testing.html).

Run commands:

```bash
cargo test                 # whole suite: unit + integration + doc tests
cargo test it_adds_two     # only tests whose name contains "it_adds_two" (substring filter)
cargo test --doc           # only doc tests
cargo test -- --nocapture  # show println! / dbg! output even on passing tests
```

For the loop, `cargo test` already captures output and is quiet on green; add `-q` for one char per test. `cargo test -- --nocapture` (above) floods stdout — use it only when debugging a single test.

Minimal failing-test skeleton (write this first, watch it fail to compile/run):

```rust
// src/lib.rs
pub fn add(a: i64, b: i64) -> i64 {
    unimplemented!() // RED: compiles, panics at runtime → test fails for the right reason
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn adds_two_numbers() {
        assert_eq!(add(2, 2), 4);
    }
}
```

## Idioms & conventions

- **Unit tests live in the same file** inside `#[cfg(test)] mod tests { use super::*; }`. `#[cfg(test)]` means the module is compiled only under `cargo test`, never in release builds — so test code adds zero binary cost and may test private items ([Book ch.11.3](https://doc.rust-lang.org/book/ch11-03-test-organization.html)).
- **Integration tests live in `tests/`** (a sibling of `src/`). Each file there is compiled as a **separate crate** that links your library, so it can only call the **public API** — exactly what an external user sees. Files under `tests/common/mod.rs` (not `tests/common.rs`) are shared helpers and are not run as their own test crate ([Book ch.11.3](https://doc.rust-lang.org/book/ch11-03-test-organization.html)).
- **Assertion macros:** `assert!(cond)`, `assert_eq!(a, b)`, `assert_ne!(a, b)`. On failure `assert_eq!` prints both values (they must be `PartialEq + Debug`). Add a custom message as trailing args: `assert!(ok, "expected ok for input {input}")` ([Book ch.11.1](https://doc.rust-lang.org/book/ch11-01-writing-tests.html)).
- **Expected panics:** `#[should_panic(expected = "substring")]` — the test passes only if the body panics AND the panic message contains that substring ([Book ch.11.1](https://doc.rust-lang.org/book/ch11-01-writing-tests.html#checking-for-panics-with-should_panic)).
- **`Result`-returning tests** let you use `?` instead of `.unwrap()`. The test passes on `Ok(())` and fails on `Err`. Note: you **cannot** combine `#[should_panic]` with a `Result` return type ([Book ch.11.1](https://doc.rust-lang.org/book/ch11-01-writing-tests.html#using-resultt-e-in-tests)):

  ```rust
  #[test]
  fn parses_config() -> Result<(), Box<dyn std::error::Error>> {
      let cfg = Config::from_str("port = 8080")?; // ? bubbles Err → test fails
      assert_eq!(cfg.port, 8080);
      Ok(())
  }
  ```

- **Doc tests** are the `///` code examples in your public API. `cargo test` compiles AND runs them, so they double as always-correct documentation ([Book ch.14.2](https://doc.rust-lang.org/book/ch14-02-publishing-to-crates-io.html#documentation-comments-as-tests)).
- **Async tests** need a runtime attribute; `#[test]` alone cannot drive a future. Use `#[tokio::test]` (requires `tokio` with the `macros` + `rt` features), or `#[async_std::test]` ([tokio docs](https://docs.rs/tokio/latest/tokio/attr.test.html)).
- **`#[ignore]`** skips slow tests by default; run them with `cargo test -- --ignored` ([Book ch.11.2](https://doc.rust-lang.org/book/ch11-02-running-tests.html#ignoring-some-tests-unless-specifically-requested)).

## Rust-specific anti-patterns

**1. `.unwrap()` / `.expect()` on the value under test**
❌ `let v = parse(input).unwrap();` then asserting on `v`.
→ Why wrong: the panic from `unwrap` fires *before* your assertion, so the failure report is a generic `called Result::unwrap() on an Err value` with no domain context, and you never assert the error path. ✅ Fix: return `Result` from the test and use `?`, or assert on the `Result` directly with `assert!(parse(bad).is_err())` / pattern-match the `Err`. (Source: [Book ch.11.1 — Using Result in tests](https://doc.rust-lang.org/book/ch11-01-writing-tests.html#using-resultt-e-in-tests).)

**2. Only inline unit tests; no `tests/` coverage of the public API**
❌ Everything in `#[cfg(test)] mod tests`, nothing in `tests/`.
→ Why wrong: inline tests can reach private items, so they may pass while your *public* surface is broken or unergonomic; integration tests compile as a separate crate and exercise the API exactly as a consumer would. ✅ Fix: add `tests/<feature>.rs` that imports your crate by name and drives only public functions. (Source: [Book ch.11.3 — Integration Tests](https://doc.rust-lang.org/book/ch11-03-test-organization.html#integration-tests).)

**3. Async test with a plain `#[test]`**
❌ `#[test] async fn …` (or building an `async fn` test without a runtime attribute).
→ Why wrong: `#[test]` does not start an executor, so the future is never polled; it either fails to compile or silently does nothing. ✅ Fix: use `#[tokio::test]` / `#[async_std::test]`, matching the runtime your code actually uses. (Source: [tokio `#[test]` docs](https://docs.rs/tokio/latest/tokio/attr.test.html).)

**4. Testing only the `Ok` path**
❌ Asserting success but never that bad input yields the right `Err`.
→ Why wrong: Rust pushes error handling into the type system precisely so failures are explicit; an untested `Err` arm means your error contract is unverified. ✅ Fix: assert the error variant/message, e.g. `assert!(matches!(parse("x"), Err(ParseError::NotANumber)))`. (Source: [Book ch.9.2 — Recoverable Errors with Result](https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html).)

**5. Treating doc examples as prose instead of executable tests**
❌ Writing `///` examples that don't actually compile, or hiding logic behind ```` ```ignore ````/```` ```no_run ```` without reason.
→ Why wrong: `cargo test` runs doc examples, so a non-compiling example is a real (and very common) source of broken docs; skipping them loses free regression coverage of your public API. ✅ Fix: keep examples compiling; use ```` ```should_panic ```` / `# ` hidden setup lines rather than disabling the test. (Source: [rustdoc book — Documentation tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html).)

**6. Reaching for a heavy mocking framework instead of a trait seam**
❌ Pulling in elaborate mocks to fake a concrete struct.
→ Why wrong: in Rust the idiomatic seam is a **trait** injected via generics (`fn run<R: Repo>(r: R)`) or `&dyn Trait`; with a trait boundary a hand-written fake is often a few lines, and `mockall` is only needed for complex expectation matching. ✅ Fix: define the dependency as a trait, inject it, and substitute a small test impl; use `mockall::automock` only when call-count/argument expectations justify it. (Source: [mockall docs](https://docs.rs/mockall/latest/mockall/), which itself frames mocks as objects for trait/struct seams.)

  ```rust
  trait Clock { fn now(&self) -> u64; }           // the seam

  fn is_expired<C: Clock>(clock: &C, deadline: u64) -> bool {
      clock.now() > deadline
  }

  struct FixedClock(u64);                          // 3-line hand-written fake
  impl Clock for FixedClock { fn now(&self) -> u64 { self.0 } }

  #[test]
  fn detects_expiry() {
      assert!(is_expired(&FixedClock(100), 50));   // no mocking crate needed
  }
  ```

## Tooling notes

- **Coverage:** `cargo llvm-cov` (crate [`cargo-llvm-cov`](https://github.com/taiki-e/cargo-llvm-cov)) is the current recommendation — LLVM source-based instrumentation, region-level accuracy, works on Linux/macOS/Windows. `cargo tarpaulin` ([tarpaulin](https://github.com/xd009642/tarpaulin)) is the older alternative but is effectively Linux-x86_64 only. Install: `cargo install cargo-llvm-cov`, run: `cargo llvm-cov --html`.
- **Property-based:** [`proptest`](https://github.com/proptest-rs/proptest) (Strategy-based generation + powerful shrinking; the de-facto standard, in passive maintenance) or [`quickcheck`](https://github.com/BurntSushi/quickcheck) (type-driven, simpler). Use `proptest!` to assert invariants over generated inputs.
- **Trait mocking:** [`mockall`](https://docs.rs/mockall) — annotate a trait with `#[automock]` to get a generated `MockMyTrait` with `expect_*` methods; use the `mock!` macro for foreign types or multiple impl blocks. Requires Rust ≥ 1.77.
- **Parametrization / fixtures:** [`rstest`](https://docs.rs/rstest) — `#[rstest] #[case(2, 4)] #[case(3, 9)]` generates one test per case; `#[fixture]` provides reusable setup, `#[once]` shares it across tests. Works with `#[tokio::test]` for async cases.
- **CLI integration:** [`assert_cmd`](https://docs.rs/assert_cmd) runs your built binary (`Command::cargo_bin("mybin")`), [`predicates`](https://docs.rs/predicates) writes readable output assertions, and [`assert_fs`](https://docs.rs/assert_fs) gives throwaway temp dirs/files. See the [CLI Book — Testing](https://rust-cli.github.io/book/tutorial/testing.html).

All of the above are `[dev-dependencies]`. Pin with `cargo add --dev <crate>`, which writes the current version (e.g. `rstest = "0.26"`, `mockall = "0.14"`, `assert_cmd = "2"`, `predicates = "3"`) — verify exact numbers on crates.io rather than copying pins.

## Quick reference

| Need | Tool / attribute | Command / note |
|---|---|---|
| Unit test (private OK) | `#[cfg(test)] mod tests` + `#[test]` | same file as code |
| Public-API test | file in `tests/` | separate crate, public items only |
| Executable docs | `///` examples | `cargo test --doc` |
| Run one test | substring filter | `cargo test <name>` |
| Expected panic | `#[should_panic(expected = "…")]` | not usable with `-> Result` |
| Use `?` in a test | `-> Result<(), Box<dyn Error>>` | passes on `Ok(())` |
| Async test | `#[tokio::test]` / `#[async_std::test]` | plain `#[test]` won't poll |
| Skip slow test | `#[ignore]` | `cargo test -- --ignored` |
| Coverage | `cargo-llvm-cov` (preferred) | `cargo llvm-cov --html` |
| Property tests | `proptest` / `quickcheck` | `proptest!` macro |
| Trait mocks | `mockall` `#[automock]` | prefer trait + generics first |
| Parametrized / fixtures | `rstest` `#[case]` / `#[fixture]` | one test per case |
| CLI black-box | `assert_cmd` + `predicates` | `Command::cargo_bin(...)` |
