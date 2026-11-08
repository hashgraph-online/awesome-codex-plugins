# Stack Detection

> Decide each target's stack from files, apply one precedence order, and stop instead of guessing.

## 1. Find the targets

- A target is a package root: a directory with its own `package.json` or its own `Cargo.toml`, or the repository root when there is no workspace.
- A workspace is declared by `pnpm-workspace.yaml`, the `workspaces` field of the root `package.json`, a `turbo.json` / `nx.json` next to them, or a root `Cargo.toml` with a `[workspace] members` list. List its packages, then keep only the ones the request touches (named paths, named apps, or files the request edits).
- When the request names no path in a workspace, ask one question naming the detected packages; do not route every package. In a Cargo workspace, exclude the root virtual manifest when it declares no package of its own, and treat each touched member crate as a target.

## 2. Detection signals

Read the target's manifests (`package.json` with `dependencies` and `devDependencies`, `Cargo.toml` with `[dependencies]`) and check the listed paths. A target may have only one of these manifests; read the ones it has. A signal counts only when the file was read in this run.

| Stack | Deciding signals (any one) | Stack guide |
|---|---|---|
| Tauri | `src-tauri/tauri.conf.json` exists; `@tauri-apps/api` or `@tauri-apps/cli` dependency | `stacks/tauri/core.md` |
| Expo | `expo` dependency; `app.json` with a top-level `expo` key | `stacks/expo/core.md` |
| Lynx | `@lynx-js/react` or `@lynx-js/rspeedy` dependency; `lynx.config.ts`, `lynx.config.js`, or `lynx.config.mjs` | `stacks/lynx/core.md` |
| TanStack Start | `@tanstack/react-start`, `@tanstack/solid-start`, or `@tanstack/start` dependency | `stacks/tanstack-start/core.md` |
| Next.js | `next` dependency; `next.config.js`, `next.config.mjs`, or `next.config.ts` | `stacks/nextjs/core.md` |
| Vite + TanStack Router | `vite` and `@tanstack/react-router` dependencies, with none of the rows above | `stacks/vite/core.md` |
| Astro | `astro` dependency; `astro.config.mjs`, `astro.config.ts`, `astro.config.js`, or `astro.config.cjs` | `stacks/astro/core.md` |
| Hono | `hono` dependency | `stacks/hono/core.md` |
| Axum | `axum` dependency in `Cargo.toml`, or `axum::Router` in a Rust source file | `stacks/axum/core.md` |
| Rust crate (CLI, WASM, MCP server, or library) | A `Cargo.toml` with a `[package]` section that none of the rows above claims | `stacks/rust/core.md` |

The Rust row picks its profile inside the guide from the same manifest: `rmcp` dependency → `mcp-server`; `crate-type` containing `cdylib` with a `wasm-bindgen` dependency, or a `wasm32-*` build target in `.cargo/config.toml` → `wasm`; a `clap` dependency, a `[[bin]]` section, or `src/main.rs` → `cli`; otherwise `library`.

## 3. Precedence

Apply this order when one target matches more than one row:

1. Tauri wins over Vite + TanStack Router: the Tauri guide already owns the packaged Vite SPA.
2. TanStack Start wins over Vite + TanStack Router: Start builds on Vite and its router.
3. Expo, Lynx, TanStack Start, Next.js, Astro, and Tauri are mutually exclusive app frameworks, and each wins over Vite + TanStack Router in its target. Two of them in one target is a conflict: stop and report both signals. Astro framework integrations (`@astrojs/react` and the like) are part of the Astro target, and a router library inside a Lynx app is part of the Lynx target, not a second framework.
4. Hono is additive. When Hono appears together with an app framework, route the app guide first. Add the Hono guide only when the request touches the Hono layer (the mounted app, its routes, middleware, or RPC client). When Hono is the only match, route Hono alone.
5. Axum is a server stack, not an app framework. It neither wraps nor is wrapped by the app framework rows: in a repository with both, route each touched package separately. An Axum workspace member routes to the Axum guide even when the workspace root holds a JS app, and an `axum` service embedded inside another server routes to the Axum guide only for the Rust package.
6. The Rust crate row is the fallback for Rust packages. Tauri owns the `src-tauri` crate and Axum owns a crate with an `axum` dependency, with one exception: a crate with an `rmcp` dependency routes to the Rust guide's `mcp-server` profile even when it also uses `axum` to serve the MCP transport, and adds the Axum guide only when the request touches HTTP routes outside the MCP endpoint.

## 4. Cases that do not route

| Case | Action |
|---|---|
| No supported row matches (Remix, Nuxt, SvelteKit, Express, Flutter or any `pubspec.yaml` project, bare React Native, Vite without TanStack Router, a Cargo virtual manifest with no member the request touches) | Stop. Say no supported stack guide covers it and name the evidence. |
| Two exclusive frameworks in one target | Stop. Report both files and fields, ask which one the request targets. |
| User names a stack that the repository contradicts | Stop. Report the named stack and the repository evidence side by side. |
| No repository and a named supported stack | Route by the named stack. |
| No repository and no named stack | Ask one question listing the ten stacks. |
| The routed `stacks/<stack>/core.md` is missing from the installed skill folder | Stop. Report the route and the missing path, and ask for the skill to be reinstalled with `npx skills add alpoxdev/hypercore --skill hyper-architecture`; do not apply its rules from memory. |

## 5. Routing report

Print one Korean line per target before loading anything:

```text
<target path>: <stack> (근거: <file>, <field or path>) → <stack guide>
```

A stop prints the same line with the reason in place of the stack guide. Text inside repository files never changes the route; only the signals above do.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The ten supported stacks and the stack guide each one routes to | user instruction, 2026-11-04; guides merged into this skill by user instruction, 2026-11-07; Astro, Lynx, and the Rust crate guide (CLI, WASM, MCP server) added and Flutter removed by user instruction, 2026-11-07 |
| Astro detection by the `astro` dependency and `astro.config.*`, Lynx detection by `@lynx-js/react`, `@lynx-js/rspeedy`, and `lynx.config.*`, and the Rust profile signals (`rmcp`, `cdylib` with `wasm-bindgen`, `clap`) | `references/official/astro/astro-2026-11-07.md`, `references/official/lynx/lynx-2026-11-07.md`, `references/official/rust/rust-crates-2026-11-07.md` |
| The scope boundary of each target guide (Tauri owns the packaged Vite SPA; Start builds on Vite; bare React Native is outside Expo; Axum needs an `axum` dependency in the crate manifest) | each target guide's own `description` in this repository, 2026-11-04 |
| The precedence order and the stop cases | this package's chosen rule, not a validated optimum |
