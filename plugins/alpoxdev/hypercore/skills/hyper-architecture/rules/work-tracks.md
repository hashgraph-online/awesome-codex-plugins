# Work Tracks

> After routing, choose which of the three tracks run on each target, run them in one fixed order, and verify each with its own evidence.

## 1. The three tracks

| Track | Owns | Files read |
|---|---|---|
| architecture | Folder layout, routes, module and server boundaries, data access, validation, platform seams | `stacks/<stack>/core.md` and the files it routes to |
| setup | Lint, format, type-check, toolchain pinning, editor and hook glue, the CI check order | `rules/setup/<language>.md` for each language the target uses, `rules/setup/repo.md`, and the templates in `assets/templates/setup/` |
| performance | Build output, bundle and asset weight, rendering and data-loading cost, runtime and release-profile settings | `rules/<stack>/performance.md` |

Languages per stack for the setup track:

| Stack | Setup files |
|---|---|
| nextjs, tanstack-start, vite, electron, expo, lynx, astro, hono | `rules/setup/typescript.md` |
| tauri | `rules/setup/typescript.md` and `rules/setup/rust.md` (the `src-tauri` crate) |
| axum, rust | `rules/setup/rust.md` |

`rules/setup/repo.md` applies to every target once per repository, not once per package.

## 2. Choosing tracks

Choose from the request words, never from what looks missing in the repository.

| Request | Tracks |
|---|---|
| A whole-project request with no narrower scope: "아키텍처 잡아줘", "셋업해줘", "알아서 다 해줘", "전체 수정", "set up this project", a new project, or a bare `hyper-architecture` call | architecture, setup, performance |
| Folders, routes, layers, boundaries, data access, platform seams | architecture |
| Lint, format, oxlint, Prettier, ESLint or Biome migration, rustfmt, clippy, analyzer, tsconfig, git hooks, CI checks | setup |
| Slow pages, bundle size, build size, Lighthouse, Core Web Vitals, startup time, jank, release profile, "최적화", "성능" | performance |
| Two of the rows above in one request | the union, in the order of §3 |

"점검만", "리뷰만", "audit only", or "report only" keeps every chosen track in report mode: findings with file paths, no edits.

## 3. Order

Run the chosen tracks in this order on each target:

1. **setup** — first, so the formatter, linter, and type checker exist before later edits are verified.
2. **architecture** — the stack guide's own workflow.
3. **performance** — last, measured on the structure the architecture track left.

Each track finishes with its own verification before the next starts. A failed gate in one track stops that target; the report names the failed gate and the tracks that did not run.

## 4. Track rules

### Setup

- Detect first: read the existing lint, format, and type configs (`.eslintrc*`, `eslint.config.*`, `biome.json*`, `.prettierrc*`, `.oxlintrc.json`, `tsconfig*.json`, `rustfmt.toml`, `clippy.toml`, `[lints]` in `Cargo.toml`, `lefthook.yml`, `.husky/`) and the scripts that run them.
- The target standard is oxlint and Prettier for TypeScript, and rustfmt and clippy for Rust. When a project uses another tool and records no decision to keep it (in `AGENTS.md`, `CONTRIBUTING.md`, or a config comment), migrate to the standard with the language file's migration steps. A recorded decision wins; report it instead of migrating.
- Never weaken an existing rule that is stricter than the template. Merge the template into the existing config.
- A repository-wide format pass changes every file. Run it only for a new project or under `전체 수정`, as its own step with nothing else in it. Otherwise format only the files this run touched.
- Add or update the package scripts or task runner entries that run the checks, so the CI check order in `rules/setup/repo.md` can call them.

### Architecture

- Follow the routed stack guide exactly; this file adds nothing to its rules.

### Performance

- Measure before changing: name the build, bundle, profile, or audit command and record its number.
- Change one lever at a time, from the stack file's rule list, and re-run the same measurement on a production build. At most three changes per target per run; list the rest as next steps.
- Keep a change only when the measured number improves and every check from the setup and architecture tracks still passes; otherwise revert it. Report the before and after numbers.
- A rule whose measurement cannot run here (no device, no production build, no network) is reported as not measured; it is never claimed as a gain.

## 5. Report

Print one Korean line per target and track after the routing line:

```text
<target path> / <track>: <완료|점검만|중단> - <evidence: command and result, or the stop reason>
```

## Sources

> Checked 2026-11-07. This file is this package's own procedure; the tool choices it names are the user's stated standard.

| Claim | Source |
|---|---|
| oxlint, Prettier, rustfmt, and clippy as the shared lint and format standard, and setup plus performance work joining architecture work in this skill | user instruction, 2026-11-07 |
| Setup before architecture before performance, the format-pass rule, and the measure-change-measure loop | this package's chosen procedure, not a validated optimum |
