# Repository Setup Baseline

> One root `.editorconfig` and `.gitattributes`, one hook runner (lefthook), editor recommendations, and a fixed CI check order that every language's own setup file fills.

Rules are `official` when an opened page under `## Sources` states them and `hypercore-default` when this package chose the default. This file runs once per repository, not once per package. Templates live in `assets/templates/setup/repo/`.

## 1. Detect first

`hypercore-default` — Read before writing. A repository that already runs a hook runner keeps it when the choice is recorded; otherwise migrate to lefthook (see §3).

| Look for | Meaning |
|---|---|
| `.editorconfig` | Editor rules in force; check `root = true` and per-language indent |
| `.gitattributes` | Line-ending and binary rules in force |
| `lefthook.yml`, `lefthook.yaml`, `.lefthook.yml` | lefthook already installed |
| `.husky/`, `package.json` → `husky`, `lint-staged` | husky + lint-staged in use |
| `.vscode/extensions.json`, `.vscode/settings.json` | Editor recommendations already exist |
| `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Makefile`, `justfile` | Where the CI order actually lives |

`.git/hooks` is generated state, never an edit target.

## 2. Editor and line-ending hygiene

`official` — One `.editorconfig` at the repository root with `root = true`; the standard properties are `end_of_line`, `insert_final_newline`, `trim_trailing_whitespace`, `indent_style`, `indent_size`, `charset` (https://editorconfig.org/).

| Copy | To | Purpose |
|---|---|---|
| `assets/templates/setup/repo/editorconfig` | `.editorconfig` | Root editor rules |
| `assets/templates/setup/repo/gitattributes` | `.gitattributes` | Line endings, binary marks, generated lockfiles |

`hypercore-default` — Indent is 2 for the web languages and 4 for Rust, matching Prettier's defaults and rustfmt's `tab_spaces`. Prettier reads `.editorconfig`'s `indent_size`, `end_of_line`, and `max_line_length` unless the Prettier config overrides them, so the two files must agree (https://prettier.io/docs/options).

`hypercore-default` — `trim_trailing_whitespace = false` for `*.md`: two trailing spaces are a hard line break, and stripping them changes rendered output.

`official` — `.gitattributes` with `* text=auto` normalizes line endings on commit; explicit `eol` rules per extension override it (https://git-scm.com/docs/gitattributes).

`hypercore-default` — Keep the working tree LF everywhere with `* text=auto eol=lf`, add explicit `*.sh text eol=lf`, and pin Windows-only launchers (`*.bat`, `*.cmd`, `*.ps1`) to `eol=crlf`. Mark binary assets `binary` so a diff never tries to merge them, and mark lockfiles `linguist-generated=true` so review tools fold them.

`hypercore-default` — Never add `*.md text=auto` style exceptions that fight the formatter; when a Markdown file must keep CRLF, fix the file rather than widening the attribute rule.

## 3. Git hooks

`hypercore-default` — lefthook is the default hook runner. It is one binary for every language in a polyglot repository, runs jobs in parallel, and rewrites staged files with `stage_fixed`, so a Rust crate and a TypeScript package share one config instead of two Node-only tools (https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration.md).

| Copy | To | Purpose |
|---|---|---|
| `assets/templates/setup/repo/lefthook.yml` | `lefthook.yml` | Pre-commit format/lint and pre-push typecheck/test |

`official` — `stage_fixed: true` works only in `pre-commit`; it re-stages the files a command rewrote so the commit contains the formatted version (https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/stage_fixed.md).

`official` — Use `jobs:` rather than the legacy `commands:`; `jobs` was added in lefthook 1.10.0, `glob` accepts a list since 1.10.10, and `root` filters file paths for `pre-commit` and `pre-push` (https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/jobs.md, https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/glob.md).

`hypercore-default` — Add `lefthook` as a dev dependency (npm `latest` 2.2.2) and run `lefthook install` once per clone; never commit generated `.git/hooks` scripts (https://registry.npmjs.org/lefthook).

`hypercore-default` — husky plus lint-staged is the alternative, not the default: both are Node-only, so a Rust-only or mixed repository either duplicates the hook logic or installs Node just to format. A repository that already runs husky keeps it when `AGENTS.md` records that decision.

`hypercore-default` — Hook scope:

| Stage | Jobs | Why |
|---|---|---|
| `pre-commit` | `prettier --write` on staged web files, `oxlint` on staged JS/TS, `cargo fmt --all` and `cargo clippy` on staged `*.rs` | Fast, file-scoped, fixes what it can |
| `pre-push` | `typecheck` and `test` | Catches what formatting cannot |

`hypercore-default` — A hook never runs the full test suite on every commit; that belongs to CI or `pre-push`. A hook that takes more than a few seconds gets skipped by habit, and a skipped hook checks nothing.

## 4. Editors

`official` — The oxlint editor extension is `oxc.oxc-vscode`; recommend it in `.vscode/extensions.json`, run fixes on save with `"editor.codeActionsOnSave": {"source.fixAll.oxc": "always"}`, and enable type-aware mode with `"oxc.typeAware": true` (https://oxc.rs/docs/guide/usage/linter/editors.html).

`hypercore-default` — Recommended `.vscode/extensions.json` entries: `oxc.oxc-vscode` for lint fixes and the Prettier editor extension for formatting. The Prettier extension's marketplace id is not part of this snapshot's verified evidence; read it from the extension's own listing rather than copying an id from memory.

`hypercore-default` — Editor settings that must match the repository config. Set `editor.defaultFormatter` to the Prettier extension's published id, read from its own listing:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": { "source.fixAll.oxc": "always" },
  "oxc.typeAware": true
}
```

`hypercore-default` — When the project keeps ESLint (the Expo exception in `rules/setup/typescript.md`), `editor.codeActionsOnSave` gains `"source.fixAll.eslint": "explicit"`; leave `oxc` on `always` so the fast pass still runs first.

`hypercore-default` — A Rust editor setup uses `rust-analyzer` with `rustfmt` on save; the clippy diagnostics come from the same `cargo clippy` run the CI uses, so an editor-only setting never becomes the policy.

## 5. CI check order

`hypercore-default` — The order is fixed because each step is cheaper than the next and a failure should stop the pipeline early:

```text
format check → lint → typecheck → test → build
```

`hypercore-default` — Per language, the step maps to a concrete command:

| Step | TypeScript | Rust |
|---|---|---|
| format check | `prettier --check .` (`npm run format:check`) | `cargo fmt --all --check` |
| lint | `oxlint` (`npm run lint`; `oxlint && eslint` for Expo) | `CARGO_BUILD_WARNINGS=deny cargo clippy --all-targets --all-features` |
| typecheck | `tsc --noEmit` (`npm run typecheck`; `astro check` for Astro) | implied by `cargo check`/`cargo clippy`; add `cargo check --all-targets` only when clippy is not in the job |
| test | `npm test` | `cargo test --all-targets` |
| build | the stack's build command | `cargo build --release` |

`hypercore-default` — A monorepo with both languages runs the whole sequence per package, not one merged job: a Rust failure must not hide a TypeScript formatting failure. Cache the dependency install and `target/`, never the lint result.

`official` — `prettier --check` exits non-zero when any file needs formatting, which is what makes it a usable first gate (https://prettier.io/docs/cli).

`hypercore-default` — The build step runs last and only on a green pipeline; it is not a substitute for `typecheck`, and `astro check` is a typecheck step, never a build step.

`hypercore-default` — Any CI step that runs `oxlint --type-check` already covers `tsc --noEmit`; running both doubles the wait for the same finding. Pick one and record which in the workflow file.

## Checklist

- [ ] Existing `.editorconfig`, `.gitattributes`, hook runner, and editor settings were read first.
- [ ] One root `.editorconfig` with `root = true`; `*.md` keeps trailing whitespace.
- [ ] `.gitattributes` has `* text=auto`, explicit LF for scripts, binary marks, and generated lockfiles.
- [ ] lefthook is the hook runner unless a recorded decision keeps husky.
- [ ] The hook config uses `jobs:`, not `commands:`, and `stage_fixed` appears only under `pre-commit`.
- [ ] `lefthook install` runs per clone; no `.git/hooks` file is committed.
- [ ] `oxc.oxc-vscode` and the Prettier extension are recommended in `.vscode/extensions.json`.
- [ ] CI runs format check → lint → typecheck → test → build, per package.
- [ ] The lint step fails on warnings (clippy through `CARGO_BUILD_WARNINGS=deny`).
- [ ] `oxlint --type-check` and `tsc --noEmit` are not both running in the same job.

## Sources

> Checked 2026-11-07. Facts come from the pages cited below and recorded in `references/official/tooling/tooling-2026-11-07.md`; the hook-runner choice, editor settings, and CI order are this package's convention.

| Claim | Source |
|---|---|
| EditorConfig properties and `root = true` | https://editorconfig.org/ |
| `* text=auto` and `eol` attribute behavior | https://git-scm.com/docs/gitattributes |
| lefthook configuration surface, `jobs` added in 1.10.0 | https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration.md, https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/jobs.md |
| `stage_fixed` is pre-commit only | https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/stage_fixed.md |
| `glob` accepts a list since 1.10.10 | https://raw.githubusercontent.com/evilmartians/lefthook/master/docs/configuration/glob.md |
| lefthook npm latest 2.2.2 | https://registry.npmjs.org/lefthook |
| `oxc.oxc-vscode` id, `source.fixAll.oxc`, `oxc.typeAware` | https://oxc.rs/docs/guide/usage/linter/editors.html |
| Prettier reads `.editorconfig` values; `--check` exit behavior | https://prettier.io/docs/options, https://prettier.io/docs/cli |
| lefthook over husky, hook scope, editor recommendation set, and the CI check order | this package's convention |
