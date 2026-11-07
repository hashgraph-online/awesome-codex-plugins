# TypeScript Setup Baseline

> TypeScript target이 이미 가진 tooling을 감지하고, oxlint와 Prettier로 옮기며, type checker와 compiler option, package manager를 고정합니다.

규칙은 `## Sources`에 열거한 페이지가 그대로 진술할 때 `official`, 이 패키지가 기본값을 골랐을 때 `hypercore-default`, stack 자체 toolchain이 두 번째 linter를 요구할 때 `official` 기반 `exception`입니다. 모든 규칙은 복사할 template과 대상 file 이름을 밝힙니다. 기본 template은 `assets/templates/setup/typescript/`에 있습니다.

## 1. Detect first

`hypercore-default` — 아무 file도 쓰기 전에 기존 설정을 읽습니다. 다른 tool을 유지하겠다는 결정이 이미 기록된 project는 그 결정이 이깁니다. 옮기지 않고 보고합니다.

| 찾을 것 | 의미 |
|---|---|
| `.eslintrc*`, `eslint.config.{js,mjs,cjs,ts}` | ESLint 사용 중(legacy 또는 flat config) |
| `biome.json`, `biome.jsonc` | Biome 사용 중 |
| `.oxlintrc.json`, `oxlint.config.ts` | oxlint 이미 사용 중 |
| `.prettierrc*`, `prettier.config.*`, `package.json`의 `"prettier"` | Prettier 이미 설정됨 |
| `tsconfig.json`, `tsconfig.*.json` | 적용 중인 compiler option |
| `package.json` → `scripts.lint`, `scripts.format`, `scripts.typecheck` | CI가 실제로 실행하는 명령 |
| `packageManager`, `devEngines`, `engines`, `.nvmrc`, `.node-version` | runtime과 package manager 고정 값 |
| `AGENTS.md`, `CONTRIBUTING.md`, config 주석 | 현재 tool을 유지한다는 기록된 결정 |

config file만이 아니라 script를 함께 읽습니다. 쓰이지 않는 ESLint config를 두고 다른 tool로 lint하는 repository도 있습니다.

## 2. Target standard

`official` — 새 repository에서 JS/TS linter는 oxlint 하나입니다. 내장 rule 872개를 갖고 `.oxlintrc.json`, `.oxlintrc.jsonc`, `oxlint.config.ts`, `oxlint.config.mts` 중 하나를 읽으며 config file은 directory당 하나입니다(https://oxc.rs/docs/guide/usage/linter.html, https://oxc.rs/docs/guide/usage/linter/config.html).

`official` — formatter는 Prettier 3.9.x입니다. oxfmt는 0.77.0이고 여전히 0.x이며 Prettier plugin을 지원하지 않고 기본 `printWidth`도 달라서 보고 대상으로만 남깁니다(https://oxc.rs/docs/guide/usage/formatter/migrate-from-prettier.html, https://registry.npmjs.org/oxfmt).

`official` — linter에서 layout rule을 끌 필요가 없습니다. oxlint에는 `indent`, `max-len`, `quotes`, `semi`, `comma-dangle`, `space-before-function-paren` rule이 없어 Prettier를 위해 끌 것이 없습니다(https://oxc.rs/docs/guide/usage/linter/rules.html).

| 복사 | 대상 | 목적 |
|---|---|---|
| `assets/templates/setup/typescript/oxlintrc.json` | `.oxlintrc.json` | React가 아닌 package의 linter config |
| `assets/templates/setup/typescript/oxlintrc.react.json` | `.oxlintrc.json` | React, Next.js, Expo package의 linter config |
| `assets/templates/setup/typescript/prettierrc.json` | `.prettierrc.json` | formatter config |
| `assets/templates/setup/typescript/prettierignore` | `.prettierignore` | build output과 생성 file |
| `assets/templates/setup/typescript/tsconfig.base.json` | `tsconfig.base.json` | 상속할 strict compiler 기준선 |

`official` — `plugins` 배열은 항상 전부 적습니다. 이 field는 기본 집합(`eslint`, `typescript`, `unicorn`, `oxc`)을 덮어쓰므로 빠뜨린 plugin은 조용히 꺼집니다(https://oxc.rs/docs/guide/usage/linter/config.html).

`hypercore-default` — category는 `correctness: error`, `suspicious: warn`, `perf: warn`에서 시작합니다. `style`, `restriction`, `nursery`는 끈 상태로 두고 `nursery`는 semver 보증 밖입니다(https://oxc.rs/docs/guide/usage/linter/versioning.html).

`hypercore-default` — 내부 module graph가 있는 repository에는 `import/no-cycle`을 `maxDepth: 3`으로 넣습니다. 문서가 드는 multi-file analysis 사례입니다(https://oxc.rs/docs/guide/usage/linter/multi-file-analysis.html).

`official` — ignore는 별도 `.eslintignore`가 아니라 config 안 `ignorePatterns`에 둡니다. oxlint는 hidden file도 자동으로 무시하지 않습니다(https://oxc.rs/docs/guide/usage/linter/ignore-files.html).

## 3. Migration

### ESLint → oxlint

`official` — `npx @oxlint/migrate [flat-config]`는 severity, option, override, globals, root ignore를 보존합니다. `--type-aware`는 type-aware rule을 옮기고 `--js-plugins=false`는 JS plugin 이전을 건너뜁니다(https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html).

`official` — legacy `.eslintrc.*`는 먼저 `@eslint/migrate-config`를 거쳐야 합니다. oxlint migrator는 flat config를 읽습니다(https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html).

`hypercore-default` — 이전 순서는 다음과 같습니다.

1. migrator를 실행하고 생성된 `.oxlintrc.json`을 `assets/templates/setup/typescript/oxlintrc.json`과 비교합니다.
2. 합칩니다. 교체하지 않습니다. project가 `error`로 둔 rule은 template이 `warn`이어도 `error`로 남습니다.
3. `oxlint`가 같거나 적은 finding을 낸 뒤에 ESLint config와 dependency를 지웁니다.
4. `scripts.lint`를 `oxlint`로 바꾸고, 대응 oxlint rule이 꺼져 있는 곳에서만 `eslint-disable` 주석을 지웁니다.

`official` — hybrid mode는 예외입니다. `eslint-plugin-oxlint`가 oxlint가 이미 덮는 ESLint rule을 끄고, script는 `oxlint && eslint`이며(반대 순서 금지) flat config 배열에서 `...oxlint.configs['flat/recommended']`가 마지막이어야 합니다(https://github.com/oxc-project/eslint-plugin-oxlint).

`official` — `oxlint`와 `oxlint-tsgolint`는 함께 고정하고 같은 변경에서 올립니다. type-aware linting은 semver 보증 밖이고 `oxlint-tsgolint`로만 동작합니다(https://oxc.rs/docs/guide/usage/linter/type-aware-linting.html, https://oxc.rs/docs/guide/usage/linter/versioning.html).

`official` — type-aware linting은 root `options.typeAware` 또는 `--type-aware`로 선택합니다. CI에서 `tsc --noEmit`과 함께 돌리기보다 `options.typeCheck`를 쓰고, type check가 이미 통과하는 곳에서만 켭니다(https://oxc.rs/docs/guide/usage/linter/type-aware-linting.html).

### Biome → oxlint + Prettier

`hypercore-default` — Biome는 lint와 format을 합쳐 둡니다. 둘로 나눕니다. `biome migrate prettier`(또는 수동 복사)로 formatting block을 `.prettierrc.json`에 옮기고, lint block은 아래 표대로 `.oxlintrc.json`으로 옮깁니다. 이 snapshot에는 공식 Biome → oxlint migrator가 없으므로 rule 단위로 옮기고 대응이 없는 rule을 기록합니다.

| Biome group | oxlint 대상 |
|---|---|
| `correctness` / `suspicious` | `categories.correctness`, `categories.suspicious` |
| `performance` / `complexity` | `categories.perf` |
| `style`(formatting) | linter가 아니라 Prettier |
| `nursery` | 끈 상태 유지 |
| `a11y` | `jsx-a11y` plugin(React 전용) |

`hypercore-default` — 분리 뒤 `biome.json`, `@biomejs/biome`, `biome` script를 같은 변경에서 제거합니다. Biome를 유지하려면 그 결정을 `AGENTS.md`나 `CONTRIBUTING.md`에 적어야 하며, 없으면 이전합니다.

## 4. Per-stack overrides

template은 평범한 TypeScript package에서 그대로 동작합니다. 아래 각 stack은 한 가지만 바꿉니다.

| Stack | Linter | Formatter | Type check | 비고 |
|---|---|---|---|---|
| nextjs | `oxlint`(`react`, `nextjs`, `jsx-a11y` plugin 추가) | Prettier | `tsc --noEmit` | Next.js 16에서 `next lint`가 제거되고 `next build`가 더는 lint하지 않으므로 `lint` script를 직접 겁니다 |
| tanstack-start | `oxlint` | Prettier | `tsc --noEmit` | 생성 file `routeTree.gen.ts`를 lint와 format에서 제외 |
| vite | `oxlint` | Prettier | `tsc --noEmit` | TanStack Router를 쓰면 여기서도 `routeTree.gen.ts`가 생성됨 |
| tauri(frontend) | `oxlint` | Prettier | `tsc --noEmit` | `src-tauri` crate는 `rules/setup/rust.md`를 따름 |
| expo | `oxlint && eslint` | Prettier | `tsc --noEmit` | `exception`: `eslint-config-expo`는 대체 불가 |
| lynx | `oxlint` | Prettier | `tsc --noEmit`(`@rsbuild/plugin-type-check` 경유) | DOM 전용 `react/*` rule을 끔. `<view>`/`<text>`는 DOM element가 아님 |
| astro | `oxlint`(`<script>` block만) | Prettier + `prettier-plugin-astro` | `astro check` | `exception`: TypeScript 6.x 고정, `astro check`가 7.0을 거부 |
| hono | `oxlint` | Prettier | `tsc --noEmit` | Node service이므로 `moduleResolution`은 `"bundler"` 대신 `"nodenext"` |

### nextjs

`official` — Next.js 16은 `next lint`를 제거했고 `next build`는 lint를 실행하지 않으며 Next config의 `eslint` option도 사라졌습니다. 문서가 드는 경로는 ESLint를 직접 쓰는 것입니다(https://nextjs.org/docs/app/guides/upgrading/version-16). `assets/templates/setup/typescript/oxlintrc.react.json`을 `.oxlintrc.json`으로 복사하고 `nextjs` plugin을 넣으며 기본 ignore인 `.next/**`, `out/**`, `build/**`, `next-env.d.ts`를 `ignorePatterns`에 옮깁니다(https://nextjs.org/docs/app/api-reference/config/eslint).

`hypercore-default` — oxlint를 먼저 씁니다. oxlint의 `nextjs` plugin이 덮지 못하는 rule이 있을 때만 `eslint-config-next`를 hybrid chain에 남깁니다. `eslint-plugin-oxlint` 없이 둘을 함께 넣지 않습니다.

### tanstack-start and vite

`hypercore-default` — `routeTree.gen.ts`는 route source file에서 생성됩니다. `ignorePatterns`와 `.prettierignore`에 넣고 손대거나 format하지 않습니다.

`hypercore-default` — 두 stack 모두 `src/routeTree.gen.ts`를 제외하고 나머지는 기본 template을 그대로 씁니다.

### tauri

`hypercore-default` — webview frontend는 Vite app입니다. `oxlintrc.react.json`을 `.oxlintrc.json`으로, `prettierrc.json`을 `.prettierrc.json`으로 복사합니다. Rust 쪽은 `src-tauri` crate이며 `rules/setup/rust.md`를 따릅니다. frontend의 `lint` script는 `cargo` 명령을 실행하지 않고 Rust 검사는 별도 script에 둡니다.

### expo (exception)

`official` 기반 `exception` — `eslint-config-expo`는 oxlint로 대체할 수 없습니다. Expo 전용 rule과 React Native global이 그 ESLint config에 있고, 유일한 대체 경로인 JS plugin은 oxlint가 alpha로 문서화합니다(https://docs.expo.dev/guides/using-eslint/, https://oxc.rs/docs/guide/usage/linter/js-plugins.html).

`hypercore-default` — script는 `"lint": "oxlint && eslint"`이고 flat config에서 `eslint-plugin-oxlint`가 마지막입니다. `assets/templates/setup/typescript/oxlintrc.react.json`을 `.oxlintrc.json`으로 복사하고 `ignorePatterns`에 `android/**`, `ios/**`, `.expo/**`를 더합니다. `npx expo lint`는 `lint` script만 실행하므로 이 설정을 그대로 씁니다.

### lynx

`official` — Lynx에는 자사 ESLint plugin이 없고 ReactLynx template에도 linter가 없으며 Oxlint에는 Lynx plugin이 없습니다(https://lynxjs.org/llms.txt, https://oxc.rs/docs/guide/usage/linter/config-file-reference.html).

`hypercore-default` — `oxlintrc.react.json`을 `.oxlintrc.json`으로 복사하고 `src/**/*.tsx`에서 `react/no-unknown-property`를 `off`로 둡니다. Lynx element와 attribute(`<view>`, `<text>`, `bindtap`, `item-key`)는 DOM property가 아닙니다(https://oxc.rs/docs/guide/usage/linter/rules/react/no-unknown-property.html). Prettier는 `.ts`/`.tsx`를 그대로 format합니다. scaffold의 Rslint template은 유지 결정이 기록되지 않았을 때만 교체하고, 기록됐으면 `"lint": "oxlint && rslint"`로 둡니다.

### astro

`official` — `astro check`는 `@astrojs/check`와 `typescript`를 모두 요구하고 TypeScript 7.0을 거부합니다. "astro check does not currently support TypeScript 7.0. To continue using astro check, install TypeScript 6 instead"를 기록합니다(https://docs.astro.build/reference/cli-reference/).

`official` 기반 `exception` — `astro check`가 type gate인 동안 `typescript`를 `~6.0.3`으로 고정합니다. TypeScript 7은 실험적 `@astrojs/ts-content-mapper` 경로와 `tsc --noEmit --runExternalCode`를 요구합니다.

`official` — Oxlint는 `.astro` file의 `<script>` block만 lint하고 호환성 표는 Astro에 "No template linting yet"을 적습니다. Astro global용 `astro` env는 있습니다(https://oxc.rs/compatibility.html, https://oxc.rs/docs/guide/usage/linter/config-file-reference.html).

`official` — Prettier에는 `prettier-plugin-astro`와 `*.astro`를 `parser: "astro"`로 매핑하는 override가 필요합니다. plugin은 `plugins` 배열이 전체 plugin 목록인 `.prettierrc.json`에서 읽힙니다(https://github.com/withastro/prettier-plugin-astro).

`hypercore-default` — Astro의 `tsconfig.json`은 `astro/tsconfigs/strictest`를 상속합니다. 그 file을 `tsconfig.base.json`으로 덮지 않고, Astro가 없는 형제 package에만 씁니다. `format`과 `format:check`는 plugin을 통해 `.astro`를 자동으로 포함합니다.

### hono

`hypercore-default` — Hono는 Node에서 돌므로 기본 template의 `moduleResolution: "bundler"`를 `"nodenext"`로 바꿉니다. TS 7은 `node`/`node10`/`classic` resolution을 아예 제거했으므로 Node service에서 `nodenext`가 유일한 지원 선택입니다(https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).

## 5. Compiler options

`official` — TypeScript 7.0.2가 stable입니다. `strict` 기본값이 `true`, `module` 기본값이 `esnext`, `types` 기본값이 `[]`, `rootDir` 기본값이 `./`, `noUncheckedSideEffectImports` 기본값이 `true`입니다(https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).

`official` — TypeScript 7은 `target: es5`, `downlevelIteration`, `moduleResolution: node`/`node10`/`classic`, `module: amd`/`umd`/`systemjs`/`none`, `baseUrl`, `esModuleInterop: false`, `allowSyntheticDefaultImports: false`, `alwaysStrict: false`에서 hard error를 냅니다(https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).

`official` — `noUncheckedIndexedAccess`와 `exactOptionalPropertyTypes`는 `strict`에 포함되지 않아 직접 켜야 하며, 둘 다 현재 option reference에 남아 있습니다(https://www.typescriptlang.org/tsconfig/).

`hypercore-default` — `tsconfig.base.json`은 `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, `isolatedModules`, `noEmit`을 담습니다. 같은 block을 반복하지 말고 상속(`"extends": "../tsconfig.base.json"`)하며, TS 7에서 기본값이 바뀐 `types`와 `rootDir`은 필요한 package에서 직접 선언합니다.

`hypercore-default` — framework가 생성한 `tsconfig.json`과 다투지 않습니다. Next.js 16은 여전히 `target: ES2017`과 자체 `plugins` 배열을 냅니다. file을 다시 쓰지 말고 strict 추가분만 위에 얹습니다(https://raw.githubusercontent.com/vercel/next.js/canary/packages/create-next-app/templates/app-tw/ts/tsconfig.json).

## 6. Package scripts

`hypercore-default` — lint할 source tree가 있는 모든 package는 아래 네 script를 정의하고, `rules/setup/repo.md`의 CI 순서가 이 이름으로 호출합니다.

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

`official` — `prettier --check .`는 format이 필요한 file이 있으면 non-zero로 끝나며 이것이 CI 형태입니다. `--write`는 local 전용입니다(https://prettier.io/docs/cli).

`hypercore-default` — stack별 script 차이는 다음과 같습니다.

| Stack | `lint` | `typecheck` |
|---|---|---|
| nextjs | `oxlint` | `tsc --noEmit` |
| expo | `oxlint && eslint` | `tsc --noEmit` |
| lynx | `oxlint` | `tsc --noEmit` |
| astro | `oxlint` | `astro check` |
| hono | `oxlint` | `tsc --noEmit` |
| 나머지 | `oxlint` | `tsc --noEmit` |

`hypercore-default` — repository 전체 `prettier --write .`는 새 project이거나 `전체 수정`일 때만, 다른 변경 없이 단독 단계로 실행합니다. 그 밖에는 이번에 손댄 file만 format합니다.

## 7. Package manager and runtime pinning

`official` — `packageManager`는 `name@x.y.z` 형식이고 `name`은 `yarn`, `npm`, `pnpm` 중 하나입니다. hash 접미사는 선택이지만 "strongly recommended as a security practice"입니다. `devEngines.packageManager`(`name`, `version`, `onFail`)는 Corepack이 검증하고 `packageManager`가 없을 때 쓰입니다(https://nodejs.org/api/corepack.html).

`official` — Corepack은 Node 14.19.0부터 25.0.0 미만까지 Node에 포함됩니다. Node 25 이상에서는 직접 설치해야 하므로 Corepack으로 고정한 repository는 Node 24 이하를 고정하거나 CI에서 Corepack을 설치합니다(https://nodejs.org/api/corepack.html).

`hypercore-default` — 세 층을 모두 고정하고 서로 맞춥니다.

```json
{
  "packageManager": "pnpm@9.15.4",
  "engines": { "node": ">=22.12.0" },
  "devEngines": {
    "packageManager": { "name": "pnpm", "version": "^9.15.0", "onFail": "error" }
  }
}
```

`hypercore-default` — `.node-version`(또는 `.nvmrc`)에 `engines.node`와 같은 major를 적습니다. 둘 다 runtime이 강제하지 않는 관례 file이므로 CI가 version을 계속 확인해야 합니다. 2026-11-07 기준 현재 LTS는 Node 26.13.0입니다(https://nodejs.org/dist/index.json).

## 8. React Compiler

`hypercore-default` — React Compiler를 켜면 compiler의 lint 신호를 oxlint rule 집합과 분리해 둡니다. oxlint의 `react-hooks` rule은 compiler의 memoization validator가 아니고 compiler 진단은 build plugin이 보고합니다. 단순 `oxlint` 실행 결과로 compiler 위반을 주장하지 않습니다.

`official` — Lynx는 compiler 연동을 `@rsbuild/plugin-babel`을 통한 `react-compiler-runtime@rc`와 `babel-plugin-react-compiler@rc` 설치로 문서화하고, first frame rendering을 조금 해칠 수 있다고 적습니다(https://lynxjs.org/react/react-compiler.html). 이는 build plugin 설정이지 oxlint rule이 아닙니다.

## Checklist

- [ ] 쓰기 전에 기존 lint, format, type config와 script, 기록된 tool 결정을 읽었습니다.
- [ ] linter는 `oxlint`이고, expo만 `oxlint && eslint`에 `eslint-plugin-oxlint` 마지막이라는 문서화된 예외입니다.
- [ ] formatter는 Prettier 3.9.x이고 oxfmt는 채택하지 않았습니다.
- [ ] `.oxlintrc.json`의 `plugins`를 전부 적었습니다.
- [ ] ignore가 `ignorePatterns`에 있고 생성 file(`routeTree.gen.ts`, `next-env.d.ts`)이 제외됐습니다.
- [ ] warning 실패 정책(`--deny-warnings` 또는 `--max-warnings`)을 의도적으로 정했습니다.
- [ ] `tsconfig.base.json`을 복사하지 않고 상속하며, TS 7 기본값이 build를 깨뜨릴 package에서 `types`/`rootDir`을 선언했습니다.
- [ ] 어떤 `tsconfig.json`에도 제거된 TS 7 flag가 없습니다.
- [ ] Astro는 TypeScript 6.x를, 나머지 stack은 7.0.2를 씁니다.
- [ ] `lint`, `format`, `format:check`, `typecheck` script가 있고 CI에서 그 순서로 실행됩니다.
- [ ] `packageManager`, `engines.node`, `.node-version`이 일치하고 Node 25 이상 repository는 Corepack을 직접 설치합니다.
- [ ] repository 전체 format은 새 project이거나 `전체 수정`일 때만 실행했습니다.

## Sources

> 확인 2026-11-07. `references/official/tooling/tooling-2026-11-07.md`에 기록된 페이지, Astro와 Lynx lane ledger, 아래 인용한 oxlint, Prettier, Next.js, Expo, TypeScript, Node 페이지에서 사실을 가져왔습니다.

| Claim | Source |
|---|---|
| oxlint 1.92.0, config 탐색, `plugins`가 기본 집합을 대체, category | https://oxc.rs/docs/guide/usage/linter/config.html |
| 최상위 config key, `env` 목록, `overrides` field, 최상위 `ignore` 없음 | https://oxc.rs/docs/guide/usage/linter/config-file-reference.html |
| 선택 plugin 이름 목록과 Lynx plugin 부재 | https://oxc.rs/docs/guide/usage/linter/plugins.html |
| rule 872개, `.astro`는 script block만 lint | https://oxc.rs/docs/guide/usage/linter.html |
| Astro template linting 불가 | https://oxc.rs/compatibility.html |
| Prettier를 위해 끌 layout rule 없음 | https://oxc.rs/docs/guide/usage/linter/rules.html |
| `ignorePatterns` 권장, hidden file 자동 무시 없음 | https://oxc.rs/docs/guide/usage/linter/ignore-files.html |
| `@oxlint/migrate` 동작과 legacy config 선행 조건 | https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html |
| hybrid `oxlint && eslint`, plugin은 마지막 | https://github.com/oxc-project/eslint-plugin-oxlint |
| `oxlint-tsgolint` 경유 type-aware, `typeCheck`가 `tsc --noEmit` 대체 | https://oxc.rs/docs/guide/usage/linter/type-aware-linting.html |
| type-aware는 semver 보증 밖 | https://oxc.rs/docs/guide/usage/linter/versioning.html |
| `import/no-cycle` multi-file analysis | https://oxc.rs/docs/guide/usage/linter/multi-file-analysis.html |
| JS plugin은 alpha | https://oxc.rs/docs/guide/usage/linter/js-plugins.html |
| `react/no-unknown-property` rule | https://oxc.rs/docs/guide/usage/linter/rules/react/no-unknown-property.html |
| oxlint 1.92.0, oxfmt 0.77.0, Prettier 3.9.10 | https://registry.npmjs.org/oxlint, https://registry.npmjs.org/oxfmt, https://registry.npmjs.org/prettier |
| oxfmt는 Prettier 호환이나 drop-in 아님, `printWidth` 100 | https://oxc.rs/docs/guide/usage/formatter/migrate-from-prettier.html |
| `prettier --check` 종료 의미, `--write` | https://prettier.io/docs/cli |
| Prettier 기본값과 `.editorconfig` 반영 | https://prettier.io/docs/options |
| `prettier-plugin-astro` plugin과 `*.astro` parser override | https://github.com/withastro/prettier-plugin-astro |
| Next.js 16의 `next lint`와 `eslint` option 제거 | https://nextjs.org/docs/app/guides/upgrading/version-16 |
| `eslint-config-next` flat config와 기본 ignore | https://nextjs.org/docs/app/api-reference/config/eslint |
| Next.js 16 app-router tsconfig 값 | https://raw.githubusercontent.com/vercel/next.js/canary/packages/create-next-app/templates/app-tw/ts/tsconfig.json |
| Expo ESLint config, `npx expo lint`, `eslint-config-expo` 대체 불가 | https://docs.expo.dev/guides/using-eslint/ |
| Lynx에 자사 ESLint plugin과 template linter 없음 | https://lynxjs.org/llms.txt |
| Lynx React Compiler 연동 | https://lynxjs.org/react/react-compiler.html |
| `astro check`가 `@astrojs/check`와 `typescript`를 요구하고 TS 7.0을 거부 | https://docs.astro.build/reference/cli-reference/ |
| Astro `tsconfig` strictest preset 내용 | https://docs.astro.build/guides/typescript/ |
| TypeScript 7.0.2 기본값과 제거 flag | https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ |
| `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` 직접 설정 | https://www.typescriptlang.org/tsconfig/ |
| `packageManager`, `devEngines`, Corepack 포함 범위 | https://nodejs.org/api/corepack.html |
| Node 26.13.0이 현재 LTS | https://nodejs.org/dist/index.json |
| oxlint, Prettier, TS 7, Expo 예외, Astro TS 6 고정, package manager 규칙 정리 | 위 페이지를 바탕으로 한 이 패키지의 convention |
