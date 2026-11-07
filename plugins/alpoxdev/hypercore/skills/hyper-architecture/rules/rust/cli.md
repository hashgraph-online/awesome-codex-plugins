# CLI

> Let clap own parsing and exit codes, keep one subcommand module per verb, make machine output an explicit contract, and ship release binaries with `dist`.

Rules here are `official` when an opened page in `references/official/rust/rust-crates-2026-11-07.md` states them and `hypercore-default` when this package chose the default. The error and exit-code policy is owned by `rules/rust/errors-and-logging.md`; this file covers the argument surface, the output contract, and distribution.

## 1. clap 4.6

`official` — Major is 4. The crate has 20 features and 6 defaults — `color`, `error-context`, `help`, `std`, `suggestions`, `usage` — so `derive` and `env` are opt-in and must be declared (https://docs.rs/crate/clap/latest/features). A crate that uses `#[arg(env = ...)]` without the `env` feature does not compile.

```toml
[dependencies]
clap = { version = "4.6", features = ["derive"] }        # add "env" only when an env fallback exists
clap_complete = "4.6"
```

`official` — The derive surface is `Parser` (a struct of arguments or an enum of subcommands), `Args` (a reusable group, flattenable into other structs), `Subcommand`, and `ValueEnum` (https://docs.rs/clap/latest/clap/_derive/index.html). Three defaults matter in review:

- `rename_all` defaults to `kebab-case`, so `--dry-run` is the field `dry_run` renamed automatically.
- `rename_all_env` defaults to `SCREAMING_SNAKE_CASE`, so `dry_run` reads `DRY_RUN`.
- `#[command(version)]` with no expression takes the crate `version`.

`official` — `ValueEnum` "doesn't work on enums that contain non-unit variants, unless they are skipped" (https://docs.rs/clap/latest/clap/_derive/index.html). An enum with a data-carrying variant must skip it or move that input to another flag.

`official` — Doc comments become `about` and `long_about`, so the documented tip when only the short form should show is `#[command(version, about, long_about = None)]` (https://docs.rs/clap/latest/clap/_derive/index.html).

## 2. Parse once, in `main`

`official` — Do not `unwrap()` a `try_parse()`. `Parser::parse()` or `err.exit()` lets clap apply its own contract: help and version to stdout with status 0, a parse error to stderr with status 2 (https://docs.rs/clap/latest/clap/error/struct.Error.html). A hand-written `.expect("bad args")` converts a usage message into a panic and a 101.

`hypercore-default` — One parse site, in `main`, before any subscriber or I/O work. The parsed `Cli` is passed down by value. Nothing below `run` reads `std::env::args`.

`hypercore-default` — `try_parse()` is legitimate in exactly one place: a test, where the error is an assertion target. Even there, assert on `ErrorKind`, not on a formatted string.

## 3. Subcommand structure

`hypercore-default` — One enum names every verb; one module per verb executes it.

```rust
#[derive(clap::Parser)]
#[command(name = "mytool", version, about, long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Command,
    #[arg(long, global = true)]
    pub json: bool,
    #[arg(long, short, global = true, action = clap::ArgAction::Count)]
    pub verbose: u8,
}

#[derive(clap::Subcommand)]
pub enum Command {
    /// Validate the manifest without writing.
    Check(CheckArgs),
    /// Build every target.
    Build(BuildArgs),
}

#[derive(clap::Args)]
pub struct CheckArgs {
    /// Path to the manifest.
    #[arg(default_value = "Cargo.toml")]
    pub manifest: std::path::PathBuf,
}
```

- `global = true` on cross-cutting flags (`--json`, `--verbose`, `--quiet`) so they work before or after the subcommand.
- `ArgAction::Count` for `-vv`, `ArgAction::SetTrue` for a flag, `ArgAction::Set` for a value. These are explicit because the default depends on the field type.
- Every argument and subcommand has a doc comment; it is the help text.
- Defaults are visible in the help. A hidden default is a support ticket.
- Env fallbacks use `#[arg(env = "MYTOOL_LEVEL")]` and only where a real deployment needs one; a CLI's own flag always wins.

`hypercore-default` — Reusable groups use `#[command(flatten)]` rather than duplicate field lists. A flatten group shared by several verbs is an `Args` struct, not a trait.

## 4. Output contract

`official` — For a machine consumer the CLI book recommends one JSON document per message, line-delimited, with every record carrying a `type` field; its example is ripgrep's `--json` where records are `begin`/`match`/`end`/`summary` (https://rust-cli.github.io/book/in-depth/machine-communication.html).

`hypercore-default` — The contract this package standardizes:

- `--json` writes NDJSON to stdout, one record per line, each with a `type` discriminator. No pretty-printed multi-line objects, because a line-oriented consumer must be able to split on newlines.
- Every record is a `serde::Serialize` value in `output/`, not a hand-built string. Field names stay stable within a major version.
- Record types cover the lifecycle, not only the payload: at minimum a `summary` record with counts and an `error` record with a machine code and a short message. A consumer that reads only `summary` must not need the payload records.
- Human output is the default when stdout is a terminal and `--json` is absent. A piped stdout with no `--json` keeps human output; the flag, not the pipe, decides, so a script's behavior is explicit.
- `std::io::IsTerminal` drives progress and color, never the record shape (https://rust-cli.github.io/book/in-depth/machine-communication.html).
- Exits do not change with `--json`: the same failure produces the same exit code and an `error` record instead of a sentence.

`official` — `serde_json` writes one document per `to_writer` call. Writing each record followed by `\n` and flushing at the end of the run is the observable shape; a buffered writer that only flushes at process exit loses records when the process is killed.

## 5. Completions

`official` — `clap_complete` 4.6.11 provides `generate` (runtime) and `generate_to` (compile time), `Shell`, and an `aot` module; the `generator` and `shells` modules are marked deprecated in favor of `aot` (https://docs.rs/clap_complete/latest/clap_complete/). `CompleteEnv` supports dynamic completion through `COMPLETE=$SHELL <bin>`.

`hypercore-default` — Two acceptable shapes, chosen by whether the binary may write files at build time:

| Shape | When | Cost |
|---|---|---|
| Build-time `generate_to` into an `OUT_DIR`, shipped in the release archive | The release process already ships an archive | Completions are only as fresh as the build |
| Hidden `completions` subcommand using `generate` | Users install from a package manager or `cargo install` | A hidden verb in the parser |

Either way, do not hand-write completion scripts. The generated script follows the parser, and a hand-written one drifts on the first flag rename.

## 6. Distribution with `dist`

`official` — The tool is `dist`, formerly `cargo-dist`; the README opens with that rename (https://raw.githubusercontent.com/axodotdev/cargo-dist/main/README.md). The crates.io package is still `cargo-dist` (0.34.0) and "the package names all currently use the original name", while "it should be invocable as `dist ...`" (https://axodotdev.github.io/cargo-dist/book/install.html).

`official` — The workflow: `dist init` (interactive, re-runnable, `--yes` for defaults) writes the dist config, adds a shippable build profile to `Cargo.toml`, and generates `.github/workflows/release.yml`; releases are triggered by pushing a tag such as `v0.1.0`; `dist build` builds the current platform and `dist plan` prints what CI will build (https://axodotdev.github.io/cargo-dist/book/quickstart/rust.html).

`official` — The generated profile is `[profile.dist]` with `inherits = "release"` and `lto = "thin"`, kept separate so aggressive release settings do not slow local builds (https://axodotdev.github.io/cargo-dist/book/reference/concepts.html). `[profile.*]` sections are only read from the root manifest.

`hypercore-default` — Rules:

- `dist init --yes` once per repository; re-run it after target changes rather than hand-editing the generated workflow.
- `dist plan` before tagging, so the target matrix is reviewed without a release.
- Keep `[profile.dist]` inheriting `release`; a slower local build for a marginal size win is not a trade the team agreed to.
- Choose installers deliberately and record the choice; the installer list is surveyed at init and defaults are not a decision.
- Tag-driven releases only. A local `dist build` is for verification, not for publishing.
- `cargo-binstall` support depends on the release artifacts; do not promise `cargo binstall` unless the release ships a compatible archive.

## 7. Configuration files

`official` — The official CLI book's configuration chapter is still a stub — "TODO / Evaluate crates that exist / Cli-args + multiple configs + env variables" (https://rust-cli.github.io/book/print.html). There is no official recommendation to cite.

`hypercore-default` — Precedence, stated in `--help` when a config file exists: command-line flag, then environment variable, then config file, then built-in default. `figment` (0.10.19) and `config` (0.15.27) exist and were only version-checked for this snapshot; neither is this package's official default, and adopting one is a recorded project decision. A crate that needs one layer of configuration may parse a single file with `serde` and skip both.

## Checklist

- [ ] `derive` is declared explicitly, and `env` only when an environment fallback exists.
- [ ] Parsing happens once in `main`; no `try_parse().unwrap()` exists.
- [ ] clap's own exit contract is untouched: help/version to stdout+0, parse error to stderr+2.
- [ ] One `Subcommand` enum names every verb, and each verb has one command module.
- [ ] Cross-cutting flags are `global = true` and use an explicit `ArgAction`.
- [ ] Every argument and subcommand has a doc comment as its help text.
- [ ] `--json` emits one NDJSON record per line with a `type` field, including a summary and an error record.
- [ ] Machine output is built from serializable structs, not format strings.
- [ ] The exit code does not change with `--json`.
- [ ] Progress and color follow `IsTerminal`; the record shape does not.
- [ ] Completions are generated by `clap_complete`, not hand-written.
- [ ] Release binaries come from `dist`, with `[profile.dist]` in the root manifest and a tag-driven workflow.
- [ ] Configuration precedence is documented when a config file exists.

## Sources

> Checked 2026-11-07. Facts come from the pages recorded in `references/official/rust/rust-crates-2026-11-07.md`.

| Claim | Source |
|---|---|
| clap 4.6.7 features, defaults, and the 20/6 feature counts | https://docs.rs/crate/clap/latest/features |
| Derive surface, `ValueEnum` unit-variant limit, `rename_all` and `rename_all_env` defaults, `long_about = None` | https://docs.rs/clap/latest/clap/_derive/index.html |
| `Error::exit` stdout+0 / stderr+2 contract | https://docs.rs/clap/latest/clap/error/struct.Error.html |
| `clap_complete` `generate`, `generate_to`, `aot`, and `CompleteEnv` | https://docs.rs/clap_complete/latest/clap_complete/ |
| NDJSON with a `type` discriminator and ripgrep's record kinds | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| `IsTerminal` for human versus piped output | https://rust-cli.github.io/book/in-depth/machine-communication.html |
| `dist` rename, package name, install binary name | https://raw.githubusercontent.com/axodotdev/cargo-dist/main/README.md, https://axodotdev.github.io/cargo-dist/book/install.html |
| `dist init`, tag-driven release, `dist plan`, `dist build` | https://axodotdev.github.io/cargo-dist/book/quickstart/rust.html |
| `[profile.dist]` inherits `release` | https://axodotdev.github.io/cargo-dist/book/reference/concepts.html |
| The configuration chapter is still a stub | https://rust-cli.github.io/book/print.html |
| `figment` and `config` versions only (no recommendation) | https://crates.io/api/v1/crates/figment, https://crates.io/api/v1/crates/config |
| The record-type contract, flag actions, and distribution rules | this package's convention, not an official Rust requirement |
