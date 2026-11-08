# Testing and Type Checking

> `astro check` is the type gate and needs both `@astrojs/check` and `typescript`; components render through the Container API under Vitest, and end-to-end tests run Playwright against `astro preview`.

Rules here are labelled `official` when an opened page in the dated snapshot states them, and `hypercore-default` when this package chose the default.

## 1. Type checking

`official` — `astro dev` and `astro build` do not type-check. `astro check` does and exits 1 on errors; the docs call it "intended to be used in CI workflows" (L-26, L-28).

```json
{
  "scripts": {
    "dev": "astro dev",
    "build": "astro check && astro build",
    "preview": "astro preview",
    "sync": "astro sync",
    "test": "vitest run"
  }
}
```

Rules:

- `official` — `astro check` requires both `@astrojs/check` and `typescript`: "The `@astrojs/check` and `typescript` packages are required for this command to work."
- `official` — `astro check` rejects TypeScript 7.0. The CLI logs that it does not currently support 7.0, asks for TypeScript 6 instead, and notes that `astro check` will be deprecated in a future Astro release.
- `official` — `astro check` accepts `--watch`, `--minimumFailingSeverity`, `--minimumSeverity`, and `--noSync`.
- `official` — `astro sync` generates `.astro/types.d.ts` and runs automatically inside dev, build, and check.
- `hypercore-default` — Pin `typescript` to 6.x while `astro check` is the type gate. Latest 7.x is not a valid pin for this setup, and the 7.x path through `@astrojs/ts-content-mapper` is experimental at 0.2.0.
- `hypercore-default` — Run `astro check && astro build` as the build script, so a type error cannot ship as a successful build.

## 2. tsconfig

`official` — `tsconfig.json` extends `astro/tsconfigs/base`, `strict`, or `strictest` (L-26).

| Template | Adds |
|---|---|
| `base` | `target`/`module` ESNext, `moduleResolution: "Bundler"`, `allowImportingTsExtensions`, `verbatimModuleSyntax`, `isolatedModules`, `noEmit`, `jsx: "preserve"`, includes `.astro/types.d.ts` and `**/*`, excludes `dist` |
| `strict` | `strict` plus the base settings |
| `strictest` | `strict` plus `noUnusedLocals`, `noUnusedParameters`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitReturns`, `noImplicitOverride`, `noFallthroughCasesInSwitch` |

Rules:

- `hypercore-default` — Use `astro/tsconfigs/strictest` for a new project, and `strict` for a brownfield migration that cannot absorb the extra checks in one change. Record which one the project uses.
- `official` — The `base` template needs `strictNullChecks: true` and `allowJs: true` for the content layer to type-check.
- `official` — TypeScript 7.1+ support is experimental through `@astrojs/ts-content-mapper`, which registers `contentMappers: [{ package: '@astrojs/ts-content-mapper', extensions: ['.astro'] }]` and needs `tsc --noEmit --runExternalCode`.

## 3. Vitest and the Container API

`official` — Use `getViteConfig()` from `astro/config` (L-25):

```ts
import { getViteConfig } from 'astro/config';

export default getViteConfig({
  test: {
    include: ['src/**/*.test.ts'],
  },
});
```

Rules:

- `official` — `getViteConfig(testConfig, inlineAstroConfig?)` takes an optional second argument that overrides the Astro config for tests (4.8+).
- `official` — Astro requires at least Vitest 3.2, or 4.1 beta 5, for `getViteConfig()` since 6.0. The current Vitest line is 5.x.
- `official` — Render a component with the Container API (L-27):

```ts
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import Card from '../components/card.astro';

const container = await AstroContainer.create();
const html = await container.renderToString(Card, {
  props: { title: 'Hello' },
  slots: { default: 'Body' },
});
```

- `official` — `AstroContainer.create({ streaming?, renderers? })`, `renderToString(Component, { slots, props, request, params, locals })`, and `renderToResponse()` are the supported entry points.
- `official` — The Container API is still labelled experimental and "subject to breaking changes, even in minor or patch releases". Do not build a long-lived test harness on it without recording that risk.
- `official` — In 7.0, `getContainerRenderer()` moved from the integration package root to `@astrojs/react/container-renderer` (same for preact, solid-js, svelte, vue, and mdx).
- `hypercore-default` — Test the rendered HTML contract (headings, links, form actions, ARIA attributes) rather than internal component state; that is what the Container API can actually assert.

## 4. End-to-end tests

`official` — Playwright is the documented end-to-end tool, with `webServer: { command: 'npm run preview' }` and `baseURL: 'http://localhost:4321/'` (L-25).

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  webServer: { command: 'npm run preview', port: 4321 },
  use: { baseURL: 'http://localhost:4321/' },
});
```

Rules:

- `official` — Test against `astro preview`, not the dev server, so the test sees the production build.
- `hypercore-default` — Keep one smoke test per route family (static page, on-demand page, endpoint, Action) so a rendering-mode change cannot pass unnoticed.

## 5. Lint and format for `.astro`

`official` — Oxlint lints framework files "by linting only their `<script>` blocks", and its compatibility matrix says for Astro: "No template linting yet" (L-43, L-44).

- `official` — Oxlint ships an `astro` env for Astro globals.
- `official` — Prettier formats `.astro` with `prettier-plugin-astro`: install `prettier` and `prettier-plugin-astro`, set `"plugins": ["prettier-plugin-astro"]`, and map `*.astro` to `"parser": "astro"`.
- `official` — Oxfmt treats `.astro` as Prettier-backed, not native: it needs `@astrojs/compiler-rs` installed and the `astro` option enabled, and Oxfmt does not bundle the compiler.
- `hypercore-default` — Do not claim template or accessibility linting for `.astro` from oxlint. If template linting is required, it needs a different tool and a stated decision.
- `hypercore-default` — Format `.astro` with `prettier-plugin-astro`, not a JSX parser.

```json
{
  "plugins": ["prettier-plugin-astro"],
  "overrides": [{ "files": "*.astro", "options": { "parser": "astro" } }]
}
```

## 6. What not to do

- Do not run `astro build` as the only check; it does not type-check.
- Do not install `@astrojs/check` without `typescript`, or pin TypeScript 7.x while `astro check` is the gate.
- Do not hand-edit `.astro/types.d.ts`.
- Do not claim oxlint lints `.astro` templates.
- Do not format `.astro` with a JSX parser.
- Do not run end-to-end tests against the dev server when the point is the production build.

## Checklist

- [ ] `astro check` runs in CI and in the build script.
- [ ] `@astrojs/check` and `typescript` are both installed, and TypeScript is pinned to 6.x.
- [ ] `tsconfig.json` extends `astro/tsconfigs/strictest` or `strict`, and the choice is recorded.
- [ ] Component tests use `getViteConfig()` and the Container API, with the experimental risk noted.
- [ ] End-to-end tests run against `astro preview` on the documented port.
- [ ] `.astro` formatting uses `prettier-plugin-astro`.
- [ ] No report claims `.astro` template linting from oxlint.
- [ ] `astro sync` generated `.astro/types.d.ts` rather than a manual edit.

## Sources

> Checked 2026-11-07. Facts come from the Astro research lane, which opened these pages on 2026-11-07; lane source ids are kept in parentheses.

| Claim | Source |
|---|---|
| `astro dev` and `astro build` do not type-check; `astro check` does and is CI-intended (L-26, L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| `@astrojs/check` and `typescript` are both required (L-51) | https://docs.astro.build/en/reference/cli-reference/ |
| `astro check` rejects TypeScript 7.0 and announces future deprecation (L-51) | https://raw.githubusercontent.com/withastro/astro/main/packages/astro/src/cli/check/index.ts |
| `@astrojs/check` peer range `typescript ^5 || ^6` (L-52) | https://registry.npmjs.org/@astrojs/check |
| `astro check` flags and `astro sync` (L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| tsconfig templates and their compiler options (L-26) | https://docs.astro.build/en/guides/typescript/ |
| `@astrojs/ts-content-mapper` registration and `--runExternalCode` (L-53) | https://raw.githubusercontent.com/withastro/astro/main/packages/language-tools/ts-content-mapper/README.md |
| `getViteConfig()` signature and the inline config override (L-25) | https://docs.astro.build/en/guides/testing/ |
| Vitest minimum for `getViteConfig()` since 6.0 (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| Container API entry points and its experimental status (L-27) | https://docs.astro.build/en/reference/container-reference/ |
| `getContainerRenderer()` path move in 7.0 (L-01) | https://docs.astro.build/en/guides/upgrade-to/v7/ |
| Playwright `webServer` and `baseURL` guidance (L-25) | https://docs.astro.build/en/guides/testing/ |
| Oxlint lints only `<script>` blocks and has no `.astro` template linting (L-43, L-44) | https://oxc.rs/compatibility.html |
| Oxlint `astro` env (L-47) | https://oxc.rs/docs/guide/usage/linter/config-file-reference.html |
| `prettier-plugin-astro` install, plugins entry, and parser override (L-40) | https://docs.astro.build/en/editor-setup/ |
| Oxfmt's Prettier-backed `.astro` handling and `@astrojs/compiler-rs` requirement (L-45, L-46) | https://oxc.rs/docs/guide/usage/formatter/language-support |
