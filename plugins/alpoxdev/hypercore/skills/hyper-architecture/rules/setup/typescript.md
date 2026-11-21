# TypeScript Setup Baseline

> Detect the tooling a TypeScript target already has, migrate it to oxlint plus Prettier, and pin the type checker, the compiler options, and the package manager.

Rules are `official` when an opened page listed under `## Sources` states them, `hypercore-default` when this package chose the default, and `official`-backed `exception` where a stack's own toolchain requires a second linter. Every rule names the template it copies and the destination file name. The base templates are in `assets/templates/setup/typescript/`.

## 1. Detect first

`hypercore-default` — Read the existing configuration before writing any file. A project that already records a decision to keep another tool wins; report it instead of migrating.

| Look for | Meaning |
|---|---|
| `.eslintrc*`, `eslint.config.{js,mjs,cjs,ts}` | ESLint in use (legacy or flat config) |
| `biome.json`, `biome.jsonc` | Biome in use |
| `.oxlintrc.json`, `oxlint.config.ts` | oxlint already in use |
| `.prettierrc*`, `prettier.config.*`, `"prettier"` in `package.json` | Prettier already configured |
| `tsconfig.json`, `tsconfig.*.json` | Compiler options in force |
| `package.json` → `scripts.lint`, `scripts.format`, `scripts.typecheck` | What CI actually runs |
| `packageManager`, `devEngines`, `engines`, `.nvmrc`, `.node-version` | Runtime and package manager pins |
| `AGENTS.md`, `CONTRIBUTING.md`, a config comment | A recorded decision to keep the current tool |

Read the scripts, not only the config files: a repository can carry an unused ESLint config and lint with something else.

## 2. Target standard

`official` — oxlint is the only JS/TS linter in a greenfield repository; it ships 872 built-in rules and reads `.oxlintrc.json`, `.oxlintrc.jsonc`, `oxlint.config.ts`, or `oxlint.config.mts`, one config file per directory (https://oxc.rs/docs/guide/usage/linter.html, https://oxc.rs/docs/guide/usage/linter/config.html).

`official` — Prettier 3.9.x is the formatter. oxfmt is 0.77.0 and still 0.x; it does not support Prettier plugins and its default `printWidth` differs, so it stays a report-only item (https://oxc.rs/docs/guide/usage/formatter/migrate-from-prettier.html, https://registry.npmjs.org/oxfmt).

`official` — Do not disable layout rules in the linter: oxlint has no `indent`, `max-len`, `quotes`, `semi`, `comma-dangle`, or `space-before-function-paren` rules, so there is nothing to turn off for Prettier (https://oxc.rs/docs/guide/usage/linter/rules.html).

| Copy | To | Purpose |
|---|---|---|
| `assets/templates/setup/typescript/oxlintrc.json` | `.oxlintrc.json` | Linter config for a non-React package |
| `assets/templates/setup/typescript/oxlintrc.react.json` | `.oxlintrc.json` | Linter config for React, Next.js, and Expo packages |
| `assets/templates/setup/typescript/prettierrc.json` | `.prettierrc.json` | Formatter config |
| `assets/templates/setup/typescript/prettierignore` | `.prettierignore` | Build output and generated files |
| `assets/templates/setup/typescript/tsconfig.base.json` | `tsconfig.base.json` | Strict compiler baseline to extend |

`official` — Spell out the full `plugins` array every time: the field overwrites the default set (`eslint`, `typescript`, `unicorn`, `oxc`), so an omitted plugin is silently disabled (https://oxc.rs/docs/guide/usage/linter/config.html).

`hypercore-default` — Categories start at `correctness: error`, `suspicious: warn`, `perf: warn`. `style`, `restriction`, and `nursery` stay off; `nursery` is outside the semver guarantee (https://oxc.rs/docs/guide/usage/linter/versioning.html).

`hypercore-default` — `import/no-cycle` with `maxDepth: 3` goes in any repository with an internal module graph; it is the documented multi-file analysis case (https://oxc.rs/docs/guide/usage/linter/multi-file-analysis.html).

`official` — Ignores live in `ignorePatterns` inside the config, not in a separate `.eslintignore`; oxlint also does not auto-ignore hidden files (https://oxc.rs/docs/guide/usage/linter/ignore-files.html).

## 3. Migration

### ESLint → oxlint

`official` — `npx @oxlint/migrate [flat-config]` preserves severities, options, overrides, globals, and root ignores; `--type-aware` migrates type-aware rules and `--js-plugins=false` opts out of JS plugin migration (https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html).

`official` — A legacy `.eslintrc.*` must pass through `@eslint/migrate-config` first; the oxlint migration reads flat config (https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html).

`hypercore-default` — Migration steps, in order:

1. Run the migrator and diff the generated `.oxlintrc.json` against `assets/templates/setup/typescript/oxlintrc.json`.
2. Merge, never replace: a rule the project set to `error` stays `error` even when the template has `warn`.
3. Delete the ESLint config and its dependencies once `oxlint` reports the same or fewer findings.
4. Replace `scripts.lint` with `oxlint`, and delete `eslint-disable` comments only where the equivalent oxlint rule is not enabled.

`official` — Hybrid mode exists but is the exception: `eslint-plugin-oxlint` disables the ESLint rules oxlint already covers, the script is `oxlint && eslint` (never the reverse), and `...oxlint.configs['flat/recommended']` must be last in the flat config array (https://github.com/oxc-project/eslint-plugin-oxlint).

`official` — Pin `oxlint` and `oxlint-tsgolint` together and upgrade them in the same change; type-aware linting is excluded from semver and only runs through `oxlint-tsgolint` (https://oxc.rs/docs/guide/usage/linter/type-aware-linting.html, https://oxc.rs/docs/guide/usage/linter/versioning.html).

`official` — Type-aware linting is opt-in via root `options.typeAware` or `--type-aware`. Prefer `options.typeCheck` over running both it and `tsc --noEmit` in CI, and enable it only where the type check is already green (https://oxc.rs/docs/guide/usage/linter/type-aware-linting.html).

### Biome → oxlint + Prettier

`hypercore-default` — Biome merges lint and format. Split it: run `biome migrate prettier` (or hand-copy the formatting block) into `.prettierrc.json`, then translate the lint block into `.oxlintrc.json` following the table below. There is no official Biome → oxlint migrator in this snapshot; translate rule by rule and record any rule that has no equivalent.

| Biome group | oxlint target |
|---|---|
| `correctness` / `suspicious` | `categories.correctness`, `categories.suspicious` |
| `performance` / `complexity` | `categories.perf` |
| `style` (formatting) | Prettier, not the linter |
| `nursery` | leave off |
| `a11y` | `jsx-a11y` plugin (React only) |

`hypercore-default` — After the split, `biome.json`, `@biomejs/biome`, and the `biome` scripts come out in the same change. A repository that keeps Biome needs that decision written in `AGENTS.md` or `CONTRIBUTING.md`; otherwise migrate.

## 4. Per-stack overrides

The template works unchanged for a plain TypeScript package. Each stack below changes one thing.

| Stack | Linter | Formatter | Type check | Notes |
|---|---|---|---|---|
| nextjs | `oxlint` (add `react`, `nextjs`, `jsx-a11y` plugins) | Prettier | `tsc --noEmit` | `next lint` was removed in Next.js 16 and `next build` no longer lints; wire the `lint` script yourself |
| tanstack-start | `oxlint` | Prettier | `tsc --noEmit` | Exclude the generated `routeTree.gen.ts` from lint and format |
| vite | `oxlint` | Prettier | `tsc --noEmit` | `routeTree.gen.ts` is generated here too when TanStack Router is used |
| tauri (frontend) | `oxlint` | Prettier | `tsc --noEmit` | The `src-tauri` crate follows `rules/setup/rust.md` |
| electron | `oxlint` | Prettier + `prettier-plugin-tailwindcss` | `tsc --noEmit -p` per process tsconfig | Separate `tsconfig.node.json` (main, preload) and `tsconfig.web.json` (renderer); exclude `out/**`, `dist/**`, `release/**`, and `routeTree.gen.ts` |
| expo | `oxlint && eslint` | Prettier | `tsc --noEmit` | `exception`: `eslint-config-expo` cannot be replaced |
| lynx | `oxlint` | Prettier | `tsc --noEmit` (via `@rsbuild/plugin-type-check`) | Turn off DOM-only `react/*` rules; `<view>`/`<text>` are not DOM elements |
| astro | `oxlint` (`<script>` blocks only) | Prettier + `prettier-plugin-astro` | `astro check` | `exception`: pin TypeScript 6.x, `astro check` refuses 7.0 |
| hono | `oxlint` | Prettier | `tsc --noEmit` | Node service: `moduleResolution: "nodenext"` instead of `"bundler"` |

### nextjs

`official` — Next.js 16 removed `next lint`, `next build` no longer runs linting, and the `eslint` option in the Next config is gone; the documented path is ESLint directly (https://nextjs.org/docs/app/guides/upgrading/version-16). Copy `assets/templates/setup/typescript/oxlintrc.react.json` to `.oxlintrc.json`, add the `nextjs` plugin, and carry the default ignores `.next/**`, `out/**`, `build/**`, `next-env.d.ts` into `ignorePatterns` (https://nextjs.org/docs/app/api-reference/config/eslint).

`hypercore-default` — Use oxlint first; keep `eslint-config-next` in the hybrid chain only for a rule oxlint's `nextjs` plugin does not cover. Never add both without `eslint-plugin-oxlint`.

### tanstack-start and vite

`hypercore-default` — `routeTree.gen.ts` is generated from route source files; it goes into `ignorePatterns` and `.prettierignore`, and nobody hand-edits or formats it.

`hypercore-default` — `src/routeTree.gen.ts` is excluded in both stacks; everything else uses the base template unchanged.

### tauri

`hypercore-default` — The webview frontend is a Vite app: copy `oxlintrc.react.json` to `.oxlintrc.json` and `prettierrc.json` to `.prettierrc.json`. The Rust side is the `src-tauri` crate and follows `rules/setup/rust.md`; the `lint` script of the frontend must not run `cargo` commands, and the Rust checks live in their own script.

### electron

`hypercore-default` — Copy `oxlintrc.react.json` to `.oxlintrc.json` and `prettierrc.json` to `.prettierrc.json`. The main and preload processes run in Node and the renderer runs in Chromium, so keep two tsconfig files: `tsconfig.node.json` for `src/main/**`, `src/preload/**`, and `src/shared/**` with `types: ["node"]`, and `tsconfig.web.json` for `src/renderer/**` and `src/shared/**` with the DOM lib and no Node types. Set `"typecheck": "tsc --noEmit -p tsconfig.node.json && tsc --noEmit -p tsconfig.web.json"`; electron-vite, like Vite, only transpiles and never type checks.

`official` — With Tailwind CSS v4, `prettier-plugin-tailwindcss` must be the last Prettier plugin and needs `tailwindStylesheet` pointing at the renderer's CSS entry, for example `"tailwindStylesheet": "./src/renderer/src/main.css"` (https://github.com/tailwindlabs/prettier-plugin-tailwindcss).

`hypercore-default` — Add the build outputs `out/**`, `dist/**`, and `release/**` and the generated `src/renderer/src/routeTree.gen.ts` to `ignorePatterns` and `.prettierignore`.

### expo (exception)

`official`-backed `exception` — `eslint-config-expo` cannot be replaced by oxlint: Expo-specific rules and React Native globals ship in that ESLint config, and the only replacement path is JS plugins, which oxlint documents as alpha (https://docs.expo.dev/guides/using-eslint/, https://oxc.rs/docs/guide/usage/linter/js-plugins.html).

`hypercore-default` — The script is `"lint": "oxlint && eslint"`, with `eslint-plugin-oxlint` last in the flat config. Copy `assets/templates/setup/typescript/oxlintrc.react.json` to `.oxlintrc.json` and add `android/**`, `ios/**`, `.expo/**` to `ignorePatterns`. `npx expo lint` only runs the `lint` script, so it picks this up unchanged.

### lynx

`official` — Lynx ships no first-party ESLint plugin and the ReactLynx template ships no linter; Oxlint has no Lynx plugin (https://lynxjs.org/llms.txt, https://oxc.rs/docs/guide/usage/linter/config-file-reference.html).

`hypercore-default` — Copy `oxlintrc.react.json` to `.oxlintrc.json` and set `react/no-unknown-property` to `off` for `src/**/*.tsx`, because Lynx elements and attributes (`<view>`, `<text>`, `bindtap`, `item-key`) are not DOM properties (https://oxc.rs/docs/guide/usage/linter/rules/react/no-unknown-property.html). Prettier formats `.ts`/`.tsx` unchanged. Replace the scaffold's Rslint template only when the project has not recorded a decision to keep it; when it has, keep `"lint": "oxlint && rslint"`.

### astro

`official` — `astro check` needs both `@astrojs/check` and `typescript`, and it refuses TypeScript 7.0: it logs "astro check does not currently support TypeScript 7.0. To continue using astro check, install TypeScript 6 instead" (https://docs.astro.build/reference/cli-reference/).

`official`-backed `exception` — Pin `typescript` to `~6.0.3` while `astro check` is the type gate. TypeScript 7 needs the experimental `@astrojs/ts-content-mapper` route and `tsc --noEmit --runExternalCode`.

`official` — Oxlint lints `.astro` files only through their `<script>` blocks and the compatibility matrix lists "No template linting yet" for Astro; an `astro` env exists for Astro globals (https://oxc.rs/compatibility.html, https://oxc.rs/docs/guide/usage/linter/config-file-reference.html).

`official` — Prettier needs `prettier-plugin-astro` plus an override mapping `*.astro` to `parser: "astro"`; the plugin is loaded in a `.prettierrc.json` whose `plugins` array is the full plugin list (https://github.com/withastro/prettier-plugin-astro).

`hypercore-default` — The Astro `tsconfig.json` extends `astro/tsconfigs/strictest`; do not copy `tsconfig.base.json` over it, use it only for a sibling package without Astro. `format` and `format:check` gain `.astro` automatically through the plugin.

### hono

`hypercore-default` — Hono runs on Node, so the base template's `moduleResolution: "bundler"` becomes `"nodenext"`. Node 7 removed `node`/`node10`/`classic` resolution outright, so `nodenext` is the only supported choice for a Node service (https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).

## 5. Compiler options

`official` — TypeScript 7.0.2 is stable. It makes `strict` default `true`, `module` default `esnext`, `types` default `[]`, `rootDir` default `./`, and `noUncheckedSideEffectImports` default `true` (https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).

`official` — TypeScript 7 hard-errors on `target: es5`, `downlevelIteration`, `moduleResolution: node`/`node10`/`classic`, `module: amd`/`umd`/`systemjs`/`none`, `baseUrl`, `esModuleInterop: false`, `allowSyntheticDefaultImports: false`, and `alwaysStrict: false` (https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).

`official` — `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` are not part of `strict` and must be opted into; both still exist in the current option reference (https://www.typescriptlang.org/tsconfig/).

`hypercore-default` — `tsconfig.base.json` carries `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, `isolatedModules`, and `noEmit`. Extend it (`"extends": "../tsconfig.base.json"`) rather than repeating the block, and declare `types` and `rootDir` explicitly in the package that needs them, because both defaults changed in TS 7.

`hypercore-default` — Do not fight a framework's generated `tsconfig.json`. Next.js 16 still ships `target: ES2017` and its own `plugins` array; layer the strict extras on top instead of rewriting the file (https://raw.githubusercontent.com/vercel/next.js/canary/packages/create-next-app/templates/app-tw/ts/tsconfig.json).

## 6. Package scripts

`hypercore-default` — Every package that has a lintable source tree defines these four scripts, and the CI order in `rules/setup/repo.md` calls them by name:

```json
{
  "scripts": {
    "lint": "oxlint",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "typecheck": "tsc --noEmit"
  }
}
```

`official` — `prettier --check .` exits non-zero when a file needs formatting, which is the CI form; `--write` is local only (https://prettier.io/docs/cli).

`hypercore-default` — Per-stack script deltas:

| Stack | `lint` | `typecheck` |
|---|---|---|
| nextjs | `oxlint` | `tsc --noEmit` |
| electron | `oxlint` | `tsc --noEmit -p tsconfig.node.json && tsc --noEmit -p tsconfig.web.json` |
| expo | `oxlint && eslint` | `tsc --noEmit` |
| lynx | `oxlint` | `tsc --noEmit` |
| astro | `oxlint` | `astro check` |
| hono | `oxlint` | `tsc --noEmit` |
| all others | `oxlint` | `tsc --noEmit` |

`hypercore-default` — A repository-wide `prettier --write .` runs only in a new project or under `전체 수정`, as its own step with no other change in it. Otherwise format only the touched files.

## 7. Package manager and runtime pinning

`official` — `packageManager` must be `name@x.y.z` with `name` in `yarn`, `npm`, `pnpm`; the hash suffix is optional but "strongly recommended as a security practice". `devEngines.packageManager` (`name`, `version`, `onFail`) is validated by Corepack and used when `packageManager` is missing (https://nodejs.org/api/corepack.html).

`official` — Corepack ships inside Node from 14.19.0 up to but excluding 25.0.0; on Node ≥25 it must be installed explicitly, so a Corepack-pinned repository either pins Node ≤24 or installs Corepack in CI (https://nodejs.org/api/corepack.html).

`hypercore-default` — Pin all three layers and keep them consistent:

```json
{
  "packageManager": "pnpm@9.15.4",
  "engines": { "node": ">=22.12.0" },
  "devEngines": {
    "packageManager": { "name": "pnpm", "version": "^9.15.0", "onFail": "error" }
  }
}
```

`hypercore-default` — Add `.node-version` (or `.nvmrc`) with the same major as `engines.node`; both are convention files that no runtime enforces, so CI must still check the version. Node 26.13.0 is the current LTS on 2026-11-07 (https://nodejs.org/dist/index.json).

## 8. React Compiler

`hypercore-default` — When React Compiler is enabled, keep the compiler's own lint signal separate from the oxlint rule set: oxlint's `react-hooks` rules are not the compiler's memoization validator, and the compiler's diagnostics are reported by its build plugin. Do not claim a compiler violation from a plain `oxlint` run.

`official` — Lynx documents the compiler integration as installing `react-compiler-runtime@rc` plus `babel-plugin-react-compiler@rc` through `@rsbuild/plugin-babel`, and notes it can slightly hurt first-frame rendering (https://lynxjs.org/react/react-compiler.html). This is a build-plugin setting, not an oxlint rule.

## Checklist

- [ ] Existing lint, format, type configs, scripts, and any recorded tool decision were read before writing.
- [ ] The linter is `oxlint`, except expo, where `oxlint && eslint` with `eslint-plugin-oxlint` last is the documented exception.
- [ ] The formatter is Prettier 3.9.x; oxfmt is not adopted.
- [ ] `plugins` is spelled out in full in `.oxlintrc.json`.
- [ ] Ignores are in `ignorePatterns`, and generated files (`routeTree.gen.ts`, `next-env.d.ts`) are excluded.
- [ ] Failure-on-warning policy is deliberate (`--deny-warnings` or `--max-warnings`), not accidental.
- [ ] `tsconfig.base.json` is extended, not copy-pasted, and `types`/`rootDir` are declared where TS 7 defaults would break the build.
- [ ] No removed TS 7 flag appears in any `tsconfig.json`.
- [ ] Astro pins TypeScript 6.x; every other stack uses 7.0.2.
- [ ] `lint`, `format`, `format:check`, and `typecheck` scripts exist and run in that CI order.
- [ ] `packageManager`, `engines.node`, and `.node-version` agree, and a repository on Node ≥25 installs Corepack explicitly.
- [ ] The repository-wide format pass ran only for a new project or under `전체 수정`.

## Sources

> Checked 2026-11-07. Facts come from the pages recorded in `references/official/tooling/tooling-2026-11-07.md`, from the Astro and Lynx lane ledgers, and from the oxlint, Prettier, Next.js, Expo, TypeScript, and Node pages cited below.

| Claim | Source |
|---|---|
| oxlint 1.92.0, config discovery, full `plugins` array replaces defaults, categories | https://oxc.rs/docs/guide/usage/linter/config.html |
| Top-level config keys, `env` list, `overrides` fields; no top-level `ignore` | https://oxc.rs/docs/guide/usage/linter/config-file-reference.html |
| Optional plugin names and no Lynx plugin | https://oxc.rs/docs/guide/usage/linter/plugins.html |
| 872 rules, `.astro` script-block-only linting | https://oxc.rs/docs/guide/usage/linter.html |
| Astro template linting is not available | https://oxc.rs/compatibility.html |
| No layout rules to disable for Prettier | https://oxc.rs/docs/guide/usage/linter/rules.html |
| `ignorePatterns` recommended, hidden files not auto-ignored | https://oxc.rs/docs/guide/usage/linter/ignore-files.html |
| `@oxlint/migrate` behavior and legacy-config prerequisite | https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html |
| Hybrid `oxlint && eslint`, plugin must be last | https://github.com/oxc-project/eslint-plugin-oxlint |
| Type-aware linting via `oxlint-tsgolint`, `typeCheck` replacing `tsc --noEmit` | https://oxc.rs/docs/guide/usage/linter/type-aware-linting.html |
| Type-aware outside semver guarantees | https://oxc.rs/docs/guide/usage/linter/versioning.html |
| Doc-based `import/no-cycle` multi-file analysis | https://oxc.rs/docs/guide/usage/linter/multi-file-analysis.html |
| JS plugins are alpha | https://oxc.rs/docs/guide/usage/linter/js-plugins.html |
| `react/no-unknown-property` rule | https://oxc.rs/docs/guide/usage/linter/rules/react/no-unknown-property.html |
| oxlint latest 1.92.0, oxfmt latest 0.77.0, Prettier latest 3.9.10 | https://registry.npmjs.org/oxlint, https://registry.npmjs.org/oxfmt, https://registry.npmjs.org/prettier |
| oxfmt is Prettier-compatible but not drop-in, `printWidth` 100 | https://oxc.rs/docs/guide/usage/formatter/migrate-from-prettier.html |
| `prettier --check` exit semantics, `--write` | https://prettier.io/docs/cli |
| Prettier defaults and `.editorconfig` feeding | https://prettier.io/docs/options |
| `prettier-plugin-astro` plugin plus `*.astro` parser override | https://github.com/withastro/prettier-plugin-astro |
| Next.js 16 removed `next lint` and the `eslint` config option | https://nextjs.org/docs/app/guides/upgrading/version-16 |
| `eslint-config-next` flat config and default ignores | https://nextjs.org/docs/app/api-reference/config/eslint |
| Next.js 16 app-router tsconfig values | https://raw.githubusercontent.com/vercel/next.js/canary/packages/create-next-app/templates/app-tw/ts/tsconfig.json |
| Expo ESLint config, `npx expo lint`, `eslint-config-expo` cannot be replaced | https://docs.expo.dev/guides/using-eslint/ |
| Lynx has no first-party ESLint plugin or linter in the template | https://lynxjs.org/llms.txt |
| Lynx React Compiler integration | https://lynxjs.org/react/react-compiler.html |
| `astro check` requires `@astrojs/check` and `typescript`, refuses TS 7.0 | https://docs.astro.build/reference/cli-reference/ |
| Astro `tsconfig` strictest preset contents | https://docs.astro.build/guides/typescript/ |
| TypeScript 7.0.2 defaults and removed flags | https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ |
| `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` opt-in | https://www.typescriptlang.org/tsconfig/ |
| `packageManager`, `devEngines`, Corepack shipping range | https://nodejs.org/api/corepack.html |
| Node 26.13.0 is the current LTS | https://nodejs.org/dist/index.json |
| oxlint, Prettier, TS 7, Expo exception, Astro TS 6 pin, and package-manager rules restated | this package's convention built on the pages above |
