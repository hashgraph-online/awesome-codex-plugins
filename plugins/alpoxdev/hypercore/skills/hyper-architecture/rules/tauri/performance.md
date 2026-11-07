# Performance

> Ship the documented release profile, drop unused commands from the binary, and treat the webview bundle as a separate budget.

Rules are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default. The order is typical impact, not a measured ranking.

## Measure first

A Tauri app has two independent weight problems: the Rust binary and the webview assets. Measure both, and never attribute a slow start to the wrong one.

| Goal | Command or tool |
|---|---|
| Release build and installer | `tauri build` |
| Binary size | `ls -l` on the built binary and the bundles under `src-tauri/target/release/` |
| Rust dependency weight | the release profile in `src-tauri/Cargo.toml`, then compare binary size before and after one profile change |
| Webview bundle composition | the frontend stack's own analyzer on its production build (for a Vite frontend, the Vite performance rules) |
| Startup timing | a release build, launched outside the dev loop, with the webview devtools closed |
| Field Core Web Vitals for the webview | the frontend app's own RUM hook, if the frontend is instrumented |

Profile every measurement in a release build. A dev build carries incremental compilation settings and unoptimized dependencies, so its size and startup time say nothing about the shipped app.

## Rules

1. `official` — Ship the documented `[profile.release]` in `src-tauri/Cargo.toml`: `codegen-units = 1`, `lto = true`, `panic = "abort"`, and `strip = true`. Choose `opt-level = "s"` when binary size matters more than speed, or `opt-level = 3` when it does not.
2. `official` — Keep `[profile.dev] incremental = true` so the dev loop stays fast. Do not copy release-profile settings into `dev`.
3. `official` — Enable `build.removeUnusedCommands: true` in `tauri.conf.json`. It removes commands that are never allowed in the capability files, so the app does not pay for commands it cannot call.
4. `official` — List only the commands the app actually uses in the capability files instead of relying on `defaults`. This is the other half of `removeUnusedCommands`: the removal only reaches what the ACL excludes.
5. `official` — Treat the nightly-only additions (`trim-paths = "all"`, `rustflags = ["-Cdebuginfo=0", "-Zthreads=8"]`) as opt-in for nightly toolchains. They are not part of the stable profile and must not be presented as the default.
6. `official` — Audit the webview bundle with the frontend stack's own analyzer before touching the Rust profile. The Rust release profile cannot fix a bloated webview bundle, and most startup weight in a Tauri app comes from the frontend.
7. `hypercore-default` — Measure binary size after each profile change, one change at a time. `lto = true` and `codegen-units = 1` trade link time for runtime and size, and the trade has to be visible in a number before it stays.
8. `hypercore-default` — Keep the frontend on the same performance budgets as a web app for the webview surface: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at the 75th percentile where those metrics are meaningful for the app.

## Do not

- Assume `opt-level = "s"` is correct by default; it prioritizes size, and a CPU-heavy frontend bridge may want `3`.
- Copy the nightly `rustflags` block into a stable-toolchain project.
- Leave `defaults` in the capability files while expecting `removeUnusedCommands` to strip the binary; the two must agree.
- Blame the Rust profile for a slow first paint that the webview bundle caused.
- Measure with `cargo build` alone and call it the shipped size; `tauri build` produces the bundles users download.
- Enable `panic = "abort"` in a library crate that the app links and expect unwinding-based recovery to still work.
- Reformat or re-tune the frontend build inside a Tauri performance pass; that belongs to the frontend stack's own performance rules.

## Checklist

- [ ] Release build measured before any change: binary size and webview bundle size recorded separately.
- [ ] `[profile.release]` matches the documented set, with the `opt-level` choice justified.
- [ ] `[profile.dev] incremental = true` is present.
- [ ] `build.removeUnusedCommands: true` is on and the capability files list used commands rather than `defaults`.
- [ ] Nightly-only profile keys are absent unless the toolchain is nightly.
- [ ] Webview bundle was audited with the frontend analyzer, and its findings are not attributed to the Rust profile.
- [ ] One profile lever changed per measurement, with before and after numbers.

## Sources

> Checked 2026-11-07. Facts and URLs below come from the performance research lane's Tauri findings; the lane opened each page on 2026-11-07 and its source ids are kept in parentheses.

| Claim | Source |
|---|---|
| Documented `[profile.release]` values, the `opt-level` size-versus-speed note, `[profile.dev] incremental`, and the nightly-only additions (L-64) | https://raw.githubusercontent.com/tauri-apps/tauri-docs/v2/src/content/docs/concept/size.mdx |
| `build.removeUnusedCommands` and the advice to list used commands instead of `defaults` (L-64) | https://raw.githubusercontent.com/tauri-apps/tauri-docs/v2/src/content/docs/concept/size.mdx |
| Frontend bundle analysis belongs to the frontend stack's own analyzer (L-64, L-17) | https://raw.githubusercontent.com/tauri-apps/tauri-docs/v2/src/content/docs/concept/size.mdx, https://nextjs.org/docs/app/guides/package-bundling |
| Current `tauri` crate version 2.12.5, matching the recorded baseline (L-71) | https://crates.io/api/v1/crates/{axum,tauri,tower-http} |
| Core Web Vitals thresholds at p75, per device class (L-67) | https://web.dev/articles/vitals |
