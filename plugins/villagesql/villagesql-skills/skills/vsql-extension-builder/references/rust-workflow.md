# Rust Extension Workflow

Load this file when `language: rust` is set in
`.claude/tracking/architecture.md`. It replaces the C++-specific steps
in Phases 1–3 and 6. All other skill rules (gates, personas, philosophy,
acceptance criteria, UAT) apply unchanged.

## Naming Conventions

| Context | Form | Example |
|---|---|---|
| Repo / directory name | `vsql-<name>` | `vsql-rot13` |
| Cargo package name | `vsql_<name>` | `vsql_rot13` |
| SQL install name | matches `name` in `manifest.json` | `vsql_rot13` |
| VEB output file | `dist/<cargo-package-name>.veb` | `dist/vsql_rot13.veb` |

Rust extensions use the same naming as C++ extensions — the language
is recorded in `Cargo.toml` and `manifest.json`, not in the repo name.
Match the convention used by the reference examples in `vsql-rust-sdk`
(`vsql_rot13`, `vsql_rational`).

## Phase 1: SDK Discovery & Feasibility

### SDK Discovery (replaces Phase 1 step 2)

There is no staged SDK directory for Rust. The `villagesql` crate is the
SDK. To verify the crate version matches the running server:

1. Find the installed Rust SDK source. Check `~/.villagesql/credentials.txt`
   for a `RUST_SDK_PATH` entry first; fall back to asking the user.
2. Read `Cargo.toml` at the crate root and extract the `version` field.
3. Compare to the server's `villagesql_server_version` from Phase 0. The
   crate major and minor versions must match the server major and minor
   versions. If they differ, pause and ask the user to update the SDK.
4. Note the confirmed crate version as `sdk_version` in the conversation
   (written to `.claude/tracking/architecture.md` in Phase 2).

### Feasibility (replaces Phase 1 step 3)

Read the `villagesql` crate source — specifically the `InValue`, `VdfReturn`,
and `Type` enums, plus the `extension!`, `func!`, and `custom_type!` macros.
These define what the Rust SDK can express today.

**Available in the Rust SDK (stable):**
- VDF functions: scalar functions over `&[InValue]` → `VdfReturn`
- Zero-argument VDFs (e.g. `currency_count()`) work; pass `[]` for params
  in `func!`
- Custom types: fixed-length binary storage via `custom_type!` (encode,
  decode, compare, hash)
- Null handling: `InValue::Null` variant and `VdfReturn::null()`
- Error and warning returns: `VdfReturn::Error(String)` and
  `VdfReturn::Warning(String)`

**Known behaviors that constrain design** (see
`references/capabilities.md` → "STRING return size and charset"):
- STRING returns are capped at 256 bytes. Designing a 0-arg "return all
  rows as JSON" function will hit this — chunk or prefix-filter instead.
- STRING results carry the `binary` charset; callers consuming results
  via MySQL JSON functions need `CONVERT(... USING utf8mb4)`.

**Not yet available in the Rust SDK:**
- Aggregate functions
- Preview APIs (background threads, SQL sessions, sys vars)
- Variable-length column storage (Column Storage ABI)

If the user's request requires any unavailable capability, present the
gap explicitly before Phase 2. Do not proceed with a workaround that
silently drops the capability — the user must confirm the reduced scope.

## Phase 2: Scaffold & API Bootstrap

### Scaffold (replaces Phase 2 step 1)

No template repo exists for Rust extensions. Scaffold manually:

```bash
cargo new --lib vsql-<name>
cd vsql-<name>
```

Configure `Cargo.toml`:
```toml
[package]
name = "vsql_<name>"
version = "0.0.1"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
villagesql = "<crate-version-from-sdk-discovery>"
```

Create `manifest.json` next to `Cargo.toml`:
```json
{
  "name": "vsql_<name>",
  "version": "0.0.1",
  "description": "<one-line description>",
  "author": "<author>",
  "license": "GPL-2.0"
}
```

Initialize git and create `.gitignore`:
```
/target/
/dist/
.claude/
```

Create the tracking directory and write all Phase 0–1 conversation notes
to `.claude/tracking/` as specified in Phase 2 step 3 of the main skill.

**Reference implementation:** `vsql_rot13` in the Rust SDK examples is
the canonical minimal starting point for a string VDF. `vsql_rational` is
the canonical starting point for a custom type. Read the relevant example
before writing any implementation code.

**`custom_type!` intrinsic default.** Every custom type needs an encodable
intrinsic default. With no `default:` set, the server encodes the empty
string `''` at `CREATE TABLE` and type initialization fails with:

```
Type 'X.Y' failed to initialize: from_string VDF failed to encode intrinsic default input ''
```

Either set `default:` to a value your `encode` accepts, or ensure
`encode("")` succeeds. The
[vsql-uuid](https://github.com/villagesql/vsql-uuid) nil-UUID default
is the canonical pattern for choosing a value.

**File structure for a VDF-only extension:**
```
vsql-<name>/
├── Cargo.toml
├── Cargo.lock
├── manifest.json
├── .gitignore
├── src/
│   └── lib.rs
└── mysql-test/
    └── t/
        └── <name>_basic.test
```

### API Bootstrap (replaces Phase 2 step 2)

Read the `villagesql` crate source (the same path verified in Phase 1)
and extract the exact enum variants and macro signatures used in this
extension. Record in `.claude/tracking/architecture.md`:

- `InValue` variants relevant to this extension's parameter types
- `VdfReturn` variants this extension will return
- `Type` variants used in `func!` registration
- `custom_type!` macro fields if a custom type is needed

**Gate (same as main skill Phase 2 gate):** Paste a verbatim 3–5 line
excerpt from the actual crate source showing the enum definitions or
macro signature. Gate fails if no excerpt is shown.

## Phase 3: Build & Test Commands

### Build, Package, Install (replaces Phase 3 step 3)

```bash
export VillageSQL_BUILD_DIR=<build_dir>
cargo vsql install
```

`cargo vsql install` compiles in release mode, packages the `.veb`, and
copies it to the server's VEB directory in one step.

To reinstall (after code changes):
```bash
cargo vsql install
```

When reinstalling via SQL shell, run `UNINSTALL` and `INSTALL` as
**separate** `mysql -e` invocations — same rule as the main skill.

### Test (replaces Phase 3 step 4)

```bash
cargo vsql test           # run MTR suite
cargo vsql test --record  # record/update .result files
```

MTR test files live in `mysql-test/t/` and results in `mysql-test/r/`.
Test file format and conventions are identical to C++ extensions — see
`references/environment.md` for test writing conventions.

### Code Simplification (Phase 3 step 6 — Rust adaptations)

The three parallel simplification agents apply. Rust-specific patterns to
flag in addition to the standard probes:

**Agent 1 — Reuse & AI-Slop (Rust additions):**
- `.unwrap()` or `.expect()` in non-test code without justification
- `clone()` on data that could be borrowed
- Manual UTF-8 validation when `std::str::from_utf8` exists
- Matching on `InValue` variants the function doesn't actually support,
  returning an error that could instead be caught by the registration
  type signature

**Agent 3 — Efficiency (Rust additions):**
- Unnecessary heap allocation (`String::from`, `to_string()`) in hot paths
  where a `&str` return would suffice
- Vec allocation where a fixed-size array fits

## Phase 6: README Build Section

Replace the C++ build instructions with:

```markdown
## Building

Requires the [VillageSQL Rust SDK](https://github.com/villagesql/vsql-rust-sdk)
and `cargo-vsql`.

```bash
export VillageSQL_BUILD_DIR=/path/to/villagesql/build
cargo vsql install
```

## Testing

```bash
cargo vsql test
```

To regenerate expected output after changing test assertions:

```bash
cargo vsql test --record
```
```

## CTO Checklist Adaptations

The Phase 4 CTO checklist (`references/cto-checklist.md`) was written for
C++. When running it against a Rust extension, apply these substitutions:

| C++ checklist item | Rust equivalent |
|---|---|
| No raw pointer arithmetic | No `unsafe` block without a comment explaining why safe |
| No manual memory management | N/A — Rust ownership handles this |
| Unnecessary casts (`static_cast`, etc.) | Unnecessary `.into()` / `as` casts where type inference suffices |
| Buffer size correctness | `Vec` bounds: no manual index arithmetic without bounds check |
| Copyright headers on `.cc`/`.h` files | Copyright header on `src/lib.rs` |

All other checklist items apply as written.
