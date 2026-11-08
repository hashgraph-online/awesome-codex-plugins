# Code Conventions

> Rust project coding rules/axum

---
## Stable Compatibility Rule

Project tooling owns formatting and lint level. `rustfmt` and `clippy` are the baseline in most Rust repositories, but the exact lint set is a project decision. The naming rules/axum below are enforced by the language for most items and by this skill for module files; they are not universal framework requirements beyond that.

- Inspect `rustfmt.toml`, `clippy.toml`, workspace lint configuration, edition, MSRV, and existing module style before enforcing style.
- Preserve type inference and explicit public signatures; do not add broad `dyn` or boxed errors to satisfy a style preference.
- Prefer `unknown`-equivalent safe types at boundaries: typed DTOs over `serde_json::Value`, `&str` over `String` in read-only parameters.
- Never hand-edit generated code, SQLx offline metadata, or migration files unless their owning tool and repository workflow explicitly permit it.
- A module rename is behavioral: update `mod` declarations, `use` paths, tests, and configuration in the same change.

## Module and File Naming

> Rust module files are `snake_case`. This is a language convention enforced by the compiler's lint, not the kebab-case rule used by the TypeScript stacks.

| Type | Rule | Example |
|------|------|---------|
| Modules and files | `snake_case` | `user_profile.rs`, `request_id.rs` |
| Directories | `snake_case` | `routes/`, `services/`, `repositories/` |
| Types and traits | `CamelCase` | `AppState`, `UserRepository` |
| Functions and methods | `snake_case` | `create_user`, `find_by_email` |
| Constants and statics | `SCREAMING_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| Crate names | `snake_case` | `api`, `persistence` |

Allowed exceptions:

- Tool-required root files such as `Cargo.toml`, `Cargo.lock`, `rustfmt.toml`, `clippy.toml`, `build.rs`
- Generated files and migration artifacts owned by SQLx
- Existing module names that would break a public crate API if renamed

In `전체 수정` mode, scan all module files and rename `camelCase` or `kebab-case` violations to `snake_case` when every `mod` declaration, import, test path, and configuration reference can be updated in the same change.

---

## Rust Rules

| Rule | Description | Example |
|---|---|---|
| Error type | One application error enum with `thiserror` | `#[derive(thiserror::Error)] pub enum AppError` |
| Question mark | Propagate with `?` and `From` conversions | `let user = repo.get(id).await?;` |
| No panics on input | No `unwrap()`/`expect()` on request-derived values | `ok_or(AppError::BadRequest("missing id"))?` |
| Async traits | No `#[async_trait]` on axum 0.8 extractors | `impl FromRequestParts<S> for Auth` |
| Shared state | `Arc` only when shared across tasks; `AppState` is `Clone` | `#[derive(Clone)] pub struct AppState` |
| Locking | Do not hold `std::sync::Mutex` across `.await`; use `tokio::sync::Mutex` when necessary | `let guard = state.lock.lock().await;` |
| Logging | `tracing` macros, not `println!`, in libraries and handlers | `tracing::warn!(%id, "not found")` |
| Public docs | `///` on public items that are not self-explanatory | `/// Returns the user or `AppError::NotFound`.` |
| Visibility | Keep modules private by default; expose only the composition function and public contracts | `pub(crate)` unless external use is intended |
| Feature flags | Add a feature only when it changes dependencies or build cost, and document it | `[features] default = []` |

---

## Import Order

```rust
use std::sync::Arc;

use axum::{extract::State, Json};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;

use crate::error::AppError;
use crate::repositories::users::UsersRepository;
use crate::state::AppState;

use super::dto::CreateUser;
```

Group as standard library, external crates, crate-relative, then local `super`/`self`. Let `rustfmt` and the project's import configuration settle the blank-line policy; do not fight the formatter.

---

## Comment Style

- Prefer short block comments only where a code group needs orientation.
- Do not add line-by-line narration.
- Keep comments durable and architecture-oriented; do not reference a task, ticket, or agent.
- Document invariants that the type system cannot express, such as ordering or transaction assumptions.

## Sources

> Checked 2026-11-05. No external source outside this package's own references informed this file; official axum behavior is delegated to [`references/official/axum/axum-docs.md`](../../references/official/axum/axum-docs.md), verified 2026-11-05.

| Claim | Source |
|---|---|
| Rust naming conventions and module file rules/axum | [Rust API guidelines](https://rust-lang.github.io/api-guidelines/naming.html) |
| `rustfmt` and `clippy` as project tooling | [rustfmt](https://rust-lang.github.io/rustfmt/), [clippy](https://doc.rust-lang.org/clippy/) |
| `thiserror` 2.0 derive | [thiserror](https://docs.rs/thiserror/latest/thiserror/) |
