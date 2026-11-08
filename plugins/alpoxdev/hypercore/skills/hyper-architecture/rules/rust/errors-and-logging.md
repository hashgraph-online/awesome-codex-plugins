# Errors and Logging

> Put a `thiserror` enum at every library boundary, `anyhow` at the application boundary, one exit-code mapping at the top, and a `tracing` subscriber that writes diagnostics to stderr.

Rules here are `official` when an opened page in `references/official/rust/rust-crates-2026-11-07.md` states them and `hypercore-default` when this package chose the default.

## 1. Two error libraries, two jobs

`official` — `anyhow` is the application error type: its docs describe `anyhow::Result<T>` for code that reports a failure to a human, and state that it "does not bundle a `derive(Error)` macro" (https://docs.rs/anyhow/latest/anyhow/). `thiserror` derives `std::error::Error` and its docs say it "deliberately does not appear in your public API" (https://docs.rs/thiserror/latest/thiserror/).

`hypercore-default` — The split this package uses:

| Layer | Type | Why |
|---|---|---|
| Library crate public API | `thiserror` enum | Callers can match on variants; the error is part of the contract |
| Binary `run()` and commands | `anyhow::Result` | Context is added at the point of failure; the type is not public |
| Domain functions | `thiserror` enum or a plain `Result<T, DomainError>` | Domain failures are exhaustively matchable |
| WASM exported function | `Result<T, JsValue>` at the boundary, typed error inside | The JavaScript boundary cannot carry a Rust enum |
| MCP tool handler | `Result<CallToolResult, McpError>` from the SDK | The SDK owns the protocol error shape |

`official` — Mixing the two is supported at one defined seam: a `thiserror` variant with `#[error(transparent)]` wrapping `anyhow::Error` delegates `Display` and `source` (https://docs.rs/thiserror/latest/thiserror/). Use it exactly once, in the application layer, when a library error must travel up through a command.

`hypercore-default` — Never place `anyhow::Error` in a public function signature of a library crate. A caller cannot match it, and every future variant becomes a surprise.

## 2. Context, not decoration

`hypercore-default` — Add context where the information exists and cannot be reconstructed later:

```rust
let text = std::fs::read_to_string(&path)
    .with_context(|| format!("reading config {}", path.display()))?;
```

- One `.context(...)` per fallible boundary crossing; not one per line.
- The context names the resource, not the function: `"reading config /etc/app.toml"` beats `"failed in load"`.
- Do not wrap an error whose message already names the resource; nested duplicates read as noise.
- `anyhow`'s backtrace is captured on Rust ≥ 1.65 and shown through `RUST_BACKTRACE` or `RUST_LIB_BACKTRACE` (https://docs.rs/anyhow/latest/anyhow/). Do not print a backtrace by hand.

`official` — `unwrap()` and `expect()` panic. A panic in a binary exits 101; in a WASM module it aborts the instance; in a server it takes down the task. Reserve them for invariants the type system cannot express, and state the invariant in the message.

## 3. Exit codes

`official` — Codes 0–255 are portable, and "Rust sets an exit code of `101` when the process panicked" (https://rust-cli.github.io/book/in-depth/exit-code.html). The book points at BSD `sysexits` — `exitcode::USAGE`, `CONFIG`, `DATAERR`, `NOINPUT`, `IOERR`, and the rest — as the vocabulary for distinct failure classes.

`official` — clap already owns parse failures: `Error::exit` "either prints to `stderr` and exits with a status of `2` or prints to `stdout` and exits with a status of `0`", and `exit_code()` returns 2 exactly when the error kind writes to stderr (https://docs.rs/clap/latest/clap/error/struct.Error.html). `--help` and `--version` therefore exit 0 on stdout; a bad flag exits 2 on stderr before the program's own code runs.

`hypercore-default` — The policy:

| Outcome | Code | Owner |
|---|---|---|
| Success | 0 | `ExitCode::SUCCESS` |
| Help or version requested | 0 | clap |
| Argument parse failure | 2 | clap, untouched |
| Usage error the parser cannot detect | `exitcode::USAGE` (64) | the binary |
| Configuration or input data invalid | `exitcode::CONFIG`/`DATAERR` | the binary |
| Environment or I/O failure | `exitcode::IOERR` | the binary |
| Panic | 101 | Rust, not written by hand |

```rust
fn main() -> std::process::ExitCode {
    let cli = Cli::parse();               // clap handles help/version/parse errors
    init_tracing(cli.verbose, cli.quiet);
    match app::run(cli) {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(err) => {
            tracing::error!("{err:#}");
            std::process::ExitCode::from(exitcode_for(&err))
        }
    }
}
```

- Return `ExitCode` from `main` instead of calling `process::exit` inside a code path, so destructors and buffered writers finish.
- Map error classes to codes in exactly one function. Two mapping sites drift.
- `exitcode` is the book's recommendation, but its current version and maintenance state were not verified for this snapshot; if the crate is not already a dependency, plain constants with the same values are acceptable and the rationale is recorded.
- A WASM module and an MCP server have no exit code to set: a WASM export returns a `Result` to JavaScript, and an MCP server reports failures through the protocol.

## 4. Logging

`official` — `tracing` events replace `println!` for anything that is not the program's deliverable. `tracing-subscriber`'s defaults are `ansi`, `fmt`, `smallvec`, `std`, and `tracing-log`; `env-filter` is not among them, so `EnvFilter` requires an explicit feature (https://docs.rs/tracing-subscriber/latest/tracing_subscriber/).

```toml
[dependencies.tracing-subscriber]
version = "0.3"
features = ["env-filter"]
```

`official` — `EnvFilter::DEFAULT_ENV` is `RUST_LOG`, and `from_default_env()` adds "a default directive enabling the ERROR level" when the variable is empty or unset (https://docs.rs/tracing-subscriber/latest/tracing_subscriber/). So an unconfigured run is quiet rather than verbose, which is the behavior a CLI wants.

`official` — The CLI book's guidance on human-facing logs: `info` as the default level, consistent prefixes so `grep` works, and user-selectable verbosity through `--verbose` or `RUST_LOG` (https://rust-cli.github.io/book/in-depth/human-communication.html).

`hypercore-default` — The setup:

```rust
use tracing_subscriber::{fmt, EnvFilter};

pub fn init(verbose: u8, quiet: bool) {
    let default = match (verbose, quiet) {
        (_, true) => "error",
        (0, _) => "warn",
        (1, _) => "info",
        (2, _) => "debug",
        _ => "trace",
    };
    let filter = EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| EnvFilter::new(default));
    fmt()
        .with_env_filter(filter)
        .with_writer(std::io::stderr)     // stdout stays the deliverable
        .without_time()                   // a CLI log line rarely needs a timestamp
        .init();
}
```

- Explicit flags beat an ambient variable: if `--verbose` is passed, it must win over `RUST_LOG`, or the flag is a lie.
- `.with_writer(std::io::stderr)` is structural, not a convention someone remembers. On a stdio MCP server it is a protocol requirement, not a style choice.
- One subscriber, initialized once, at the process edge. A library never calls `.init()`; a second call panics.
- `tracing::instrument` on command and domain functions when the arguments are cheap to render and the span adds real context; skip it on hot loops and on anything that would log secrets.

## 5. stdout versus stderr

`official` — `std::io::IsTerminal` is the standard way to tell a human from a pipe (https://rust-cli.github.io/book/in-depth/machine-communication.html). The book's rule for machine output is one JSON document per message — line-delimited JSON — and its example is ripgrep's `--json` stream where every record carries a `type` field (`begin`, `match`, `end`, `summary`).

`hypercore-default` — Route table:

| Output kind | Stream | Condition |
|---|---|---|
| Primary result for a human | stdout | always |
| Primary result for a machine | stdout | `--json` given, or stdout is not a terminal |
| Progress, spinners, "wrote 3 files" | stderr | always |
| Warnings and errors | stderr | always |
| MCP protocol frames | stdout | stdio transport only, nothing else |
| Debug and diagnostics | stderr | through `tracing` |

- A `--quiet` flag suppresses progress and warnings, never errors and never the deliverable.
- Never interleave a progress line into a `--json` stream; a consumer parsing line by line will fail on the first human sentence.
- When output is a terminal, a progress indicator may use ANSI; when it is not, it prints nothing. `anstream`'s `AutoStream` adapts ANSI to the terminal's capability, and clap already disables color on a non-TTY (https://docs.rs/anstream/latest/anstream/).

## 6. Never leak

`hypercore-default` — An error message shown to a user names the file, the resource, or the operation. It does not include:

- Credentials, tokens, connection strings, or full environment dumps.
- Internal paths that reveal a deployment layout, when the tool runs as a service.
- A stack trace, unless `RUST_BACKTRACE` was set by the operator deliberately.

Log the detailed cause at `error` or `debug` level on stderr, and return the short message to the caller. For a WASM module the same rule applies: the detail goes to `console.error`, the returned `Result` carries a short message.

## Checklist

- [ ] A `thiserror` enum backs every library public error; `anyhow` never appears in a public signature.
- [ ] `anyhow::Result` is used only from the application layer inward to `run`.
- [ ] At most one `#[error(transparent)]` seam mixes the two, and it is in the application layer.
- [ ] Each fallible boundary crossing adds one `.context(...)` naming the resource.
- [ ] `main` returns `ExitCode` and no code path calls `process::exit`.
- [ ] One function maps error classes to exit codes; 0, 2, and 101 keep their meanings.
- [ ] clap's `Error` is not reformatted or re-exited by hand.
- [ ] `tracing-subscriber` enables `env-filter` wherever `EnvFilter` is constructed.
- [ ] The subscriber is initialized once, at the process edge, and writes to stderr.
- [ ] An explicit verbosity flag beats `RUST_LOG`.
- [ ] stdout carries only the deliverable, or protocol frames when the target is a stdio MCP server.
- [ ] `--quiet` suppresses progress and warnings but never errors or the deliverable.
- [ ] Error messages contain no credentials, tokens, or internal paths.

## Sources

> Checked 2026-11-07. Facts come from the pages recorded in `references/official/rust/rust-crates-2026-11-07.md`.

| Claim | Source |
|---|---|
| `anyhow` is the application error type and has no derive macro; backtraces through `RUST_BACKTRACE` | https://docs.rs/anyhow/latest/anyhow/ |
| `thiserror` derives `std::error::Error`, stays out of the public API, and supports `#[error(transparent)]` | https://docs.rs/thiserror/latest/thiserror/ |
| Exit codes 0–255, panic code 101, and the `exitcode` recommendation | https://rust-cli.github.io/book/in-depth/exit-code.html |
| clap maps help/version to stdout+0 and errors to stderr+2 | https://docs.rs/clap/latest/clap/error/struct.Error.html |
| `env-filter` is not a default feature; `RUST_LOG` default directive is ERROR | https://docs.rs/tracing-subscriber/latest/tracing_subscriber/ |
| `info` default level, consistent prefixes, `--verbose` or `RUST_LOG` | https://rust-cli.github.io/book/in-depth/human-communication.html |
| `IsTerminal`, line-delimited JSON, and ripgrep's `type`-tagged records | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| `anstream` `AutoStream` adapts ANSI to terminal capability | https://docs.rs/anstream/latest/anstream/ |
| Exit-code table, subscriber setup, and the stream routing table above | this package's convention, not an official Rust requirement |
