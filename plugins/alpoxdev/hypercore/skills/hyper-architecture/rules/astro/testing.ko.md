# 테스트와 타입 검사

> `astro check`가 타입 게이트이고 `@astrojs/check`와 `typescript`가 모두 필요하며, 컴포넌트는 Vitest 아래 Container API로 렌더하고, 종단 테스트는 `astro preview`에 대한 Playwright로 돌립니다.

이 파일의 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. Type checking

`official` — `astro dev`와 `astro build`는 타입 검사를 하지 않습니다. `astro check`가 하고 오류가 있으면 종료 코드 1을 내며, 문서는 이를 "intended to be used in CI workflows"라고 부릅니다(L-26, L-28).

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

규칙:

- `official` — `astro check`는 `@astrojs/check`와 `typescript`를 모두 요구합니다. "The `@astrojs/check` and `typescript` packages are required for this command to work."
- `official` — `astro check`는 TypeScript 7.0을 거부합니다. CLI는 현재 7.0을 지원하지 않는다고 기록하고 TypeScript 6을 설치하라고 하며, `astro check`가 향후 Astro 릴리스에서 폐기될 것이라고 알립니다.
- `official` — `astro check`는 `--watch`, `--minimumFailingSeverity`, `--minimumSeverity`, `--noSync`를 받습니다.
- `official` — `astro sync`가 `.astro/types.d.ts`를 생성하고 dev, build, check 안에서 자동으로 돕니다.
- `hypercore-default` — `astro check`가 타입 게이트인 동안 `typescript`를 6.x로 고정합니다. 최신 7.x는 이 구성에 유효한 고정값이 아니고, `@astrojs/ts-content-mapper`를 거치는 7.x 경로는 0.2.0 실험 단계입니다.
- `hypercore-default` — 빌드 스크립트를 `astro check && astro build`로 둡니다. 타입 오류가 성공한 빌드로 나가지 못하게 됩니다.

## 2. tsconfig

`official` — `tsconfig.json`은 `astro/tsconfigs/base`, `strict`, `strictest`를 extends합니다(L-26).

| 템플릿 | 추가되는 것 |
|---|---|
| `base` | `target`/`module` ESNext, `moduleResolution: "Bundler"`, `allowImportingTsExtensions`, `verbatimModuleSyntax`, `isolatedModules`, `noEmit`, `jsx: "preserve"`, `.astro/types.d.ts`와 `**/*` 포함, `dist` 제외 |
| `strict` | `strict`와 base 설정 |
| `strictest` | `strict`와 `noUnusedLocals`, `noUnusedParameters`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitReturns`, `noImplicitOverride`, `noFallthroughCasesInSwitch` |

규칙:

- `hypercore-default` — 새 프로젝트에는 `astro/tsconfigs/strictest`, 추가 검사를 한 번에 흡수할 수 없는 브라운필드 마이그레이션에는 `strict`를 씁니다. 프로젝트가 어느 쪽을 쓰는지 기록합니다.
- `official` — 콘텐츠 계층이 타입 검사되려면 `base` 템플릿에 `strictNullChecks: true`와 `allowJs: true`가 필요합니다.
- `official` — TypeScript 7.1+ 지원은 `@astrojs/ts-content-mapper`를 통한 실험이고, 이 패키지는 `contentMappers: [{ package: '@astrojs/ts-content-mapper', extensions: ['.astro'] }]`를 등록하며 `tsc --noEmit --runExternalCode`를 요구합니다.

## 3. Vitest and the Container API

`official` — `astro/config`의 `getViteConfig()`를 씁니다(L-25).

```ts
import { getViteConfig } from 'astro/config';

export default getViteConfig({
  test: {
    include: ['src/**/*.test.ts'],
  },
});
```

규칙:

- `official` — `getViteConfig(testConfig, inlineAstroConfig?)`의 두 번째 인자는 선택이며 테스트용으로 Astro 설정을 덮어씁니다(4.8+).
- `official` — 6.0부터 `getViteConfig()`를 쓰려면 Vitest 3.2 이상 또는 4.1 베타 5 이상이 필요합니다. 현재 Vitest 계열은 5.x입니다.
- `official` — 컴포넌트는 Container API로 렌더합니다(L-27).

```ts
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import Card from '../components/card.astro';

const container = await AstroContainer.create();
const html = await container.renderToString(Card, {
  props: { title: 'Hello' },
  slots: { default: 'Body' },
});
```

- `official` — 지원 진입점은 `AstroContainer.create({ streaming?, renderers? })`, `renderToString(Component, { slots, props, request, params, locals })`, `renderToResponse()`입니다.
- `official` — Container API는 여전히 실험으로 표시되고 "subject to breaking changes, even in minor or patch releases"입니다. 그 위험을 기록하지 않고 오래 유지할 테스트 하네스를 만들지 않습니다.
- `official` — 7.0에서 `getContainerRenderer()`가 통합 패키지 루트에서 `@astrojs/react/container-renderer`로 이동했습니다(preact, solid-js, svelte, vue, mdx도 같습니다).
- `hypercore-default` — 내부 컴포넌트 상태가 아니라 렌더된 HTML 계약(제목, 링크, form action, ARIA 속성)을 검사합니다. Container API가 실제로 단정할 수 있는 것이 그것입니다.

## 4. End-to-end tests

`official` — 문서화된 종단 도구는 Playwright이고, `webServer: { command: 'npm run preview' }`와 `baseURL: 'http://localhost:4321/'`를 씁니다(L-25).

```ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  webServer: { command: 'npm run preview', port: 4321 },
  use: { baseURL: 'http://localhost:4321/' },
});
```

규칙:

- `official` — 개발 서버가 아니라 `astro preview`로 시험합니다. 테스트가 프로덕션 빌드를 보게 됩니다.
- `hypercore-default` — 라우트 계열(정적 페이지, 온디맨드 페이지, 엔드포인트, Action)마다 스모크 테스트를 하나씩 두어 렌더링 모드 변경이 조용히 지나가지 않게 합니다.

## 5. Lint and format for `.astro`

`official` — Oxlint는 프레임워크 파일을 "by linting only their `<script>` blocks" 방식으로 lint하고, 호환성 표는 Astro에 대해 "No template linting yet"이라고 적습니다(L-43, L-44).

- `official` — Oxlint는 Astro 전역을 위한 `astro` env를 제공합니다.
- `official` — Prettier는 `prettier-plugin-astro`로 `.astro`를 포맷합니다. `prettier`와 `prettier-plugin-astro`를 설치하고 `"plugins": ["prettier-plugin-astro"]`를 설정하며 `*.astro`를 `"parser": "astro"`에 매핑합니다.
- `official` — Oxfmt는 `.astro`를 네이티브가 아니라 Prettier 기반으로 처리합니다. `@astrojs/compiler-rs`가 설치돼 있고 `astro` 옵션이 켜져야 하며, Oxfmt는 컴파일러를 묶지 않습니다.
- `hypercore-default` — oxlint로 `.astro` 템플릿이나 접근성 lint를 한다고 주장하지 않습니다. 템플릿 lint가 필요하면 다른 도구와 기록된 결정이 필요합니다.
- `hypercore-default` — `.astro`는 JSX 파서가 아니라 `prettier-plugin-astro`로 포맷합니다.

```json
{
  "plugins": ["prettier-plugin-astro"],
  "overrides": [{ "files": "*.astro", "options": { "parser": "astro" } }]
}
```

## 6. What not to do

- `astro build`만 유일한 검사로 돌리지 않습니다. 타입 검사를 하지 않습니다.
- `typescript` 없이 `@astrojs/check`만 설치하거나, `astro check`가 게이트인데 TypeScript 7.x를 고정하지 않습니다.
- `.astro/types.d.ts`를 손으로 고치지 않습니다.
- oxlint가 `.astro` 템플릿을 lint한다고 주장하지 않습니다.
- `.astro`를 JSX 파서로 포맷하지 않습니다.
- 프로덕션 빌드가 목적인데 종단 테스트를 개발 서버에 돌리지 않습니다.

## Checklist

- [ ] CI와 빌드 스크립트에서 `astro check`가 돕니다.
- [ ] `@astrojs/check`와 `typescript`가 모두 설치돼 있고 TypeScript는 6.x로 고정돼 있습니다.
- [ ] `tsconfig.json`이 `astro/tsconfigs/strictest` 또는 `strict`를 extends하고 그 선택을 기록했습니다.
- [ ] 컴포넌트 테스트가 `getViteConfig()`와 Container API를 쓰고 실험 위험을 적었습니다.
- [ ] 종단 테스트가 문서화된 포트의 `astro preview`를 상대로 돕니다.
- [ ] `.astro` 포맷이 `prettier-plugin-astro`를 씁니다.
- [ ] oxlint로 `.astro` 템플릿 lint를 한다고 주장하는 보고가 없습니다.
- [ ] `.astro/types.d.ts`를 손으로 고치지 않고 `astro sync`가 생성했습니다.

## Sources

> Checked 2026-11-07. 사실은 2026-11-07에 해당 페이지를 연 Astro 조사 레인에서 나왔고, 레인 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `astro dev`와 `astro build`는 타입 검사를 하지 않고 `astro check`가 하며 CI용입니다 (L-26, L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| `@astrojs/check`와 `typescript`가 모두 필요합니다 (L-51) | https://docs.astro.build/en/reference/cli-reference/ |
| `astro check`가 TypeScript 7.0을 거부하고 향후 폐기를 알립니다 (L-51) | https://raw.githubusercontent.com/withastro/astro/main/packages/astro/src/cli/check/index.ts |
| `@astrojs/check`의 peer 범위 `typescript ^5 || ^6` (L-52) | https://registry.npmjs.org/@astrojs/check |
| `astro check` 플래그와 `astro sync` (L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| tsconfig 템플릿과 각 컴파일러 옵션 (L-26) | https://docs.astro.build/en/guides/typescript/ |
| `@astrojs/ts-content-mapper` 등록과 `--runExternalCode` (L-53) | https://raw.githubusercontent.com/withastro/astro/main/packages/language-tools/ts-content-mapper/README.md |
| `getViteConfig()` 시그니처와 인라인 설정 덮어쓰기 (L-25) | https://docs.astro.build/en/guides/testing/ |
| 6.0부터 `getViteConfig()`에 필요한 Vitest 최소 버전 (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| Container API 진입점과 실험 상태 (L-27) | https://docs.astro.build/en/reference/container-reference/ |
| 7.0의 `getContainerRenderer()` 경로 이동 (L-01) | https://docs.astro.build/en/guides/upgrade-to/v7/ |
| Playwright `webServer`와 `baseURL` 안내 (L-25) | https://docs.astro.build/en/guides/testing/ |
| Oxlint는 `<script>` 블록만 lint하고 `.astro` 템플릿 lint가 없습니다 (L-43, L-44) | https://oxc.rs/compatibility.html |
| Oxlint `astro` env (L-47) | https://oxc.rs/docs/guide/usage/linter/config-file-reference.html |
| `prettier-plugin-astro` 설치, plugins 항목, parser override (L-40) | https://docs.astro.build/en/editor-setup/ |
| Oxfmt의 Prettier 기반 `.astro` 처리와 `@astrojs/compiler-rs` 요구 (L-45, L-46) | https://oxc.rs/docs/guide/usage/formatter/language-support |
