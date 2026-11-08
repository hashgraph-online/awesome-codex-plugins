# 렌더링과 아일랜드

> Astro는 기본이 정적이고, 요청 데이터가 필요할 때만 라우트를 온디맨드로 만들며, `client:*` 지시어와 이유가 있을 때만 프레임워크 JavaScript를 보냅니다.

이 파일의 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. The rendering model

`official` — `output`은 `'static'` 또는 `'server'`만 받고 기본값은 `'static'`입니다. `'server'`는 "does not bring any additional functionality. It only switches the default rendering behavior."라고 문서가 밝힙니다(L-17, L-09).

| 설정 | 의미 |
|---|---|
| `output: 'static'`(기본) | 선택 해제하지 않는 한 모든 라우트가 빌드 시점에 렌더됩니다 |
| `output: 'server'` | 선택하지 않는 한 모든 라우트가 요청 시점에 렌더됩니다 |
| `export const prerender = false` | `'static'` 아래에서 이 라우트가 요청 시점에 렌더됩니다 |
| `export const prerender = true` | `'server'` 아래에서 이 라우트가 빌드 시점에 렌더됩니다 |

규칙:

- `official` — `prerender`는 정적으로 분석 가능해야 합니다. 런타임에 계산한 값은 지원되지 않습니다.
- `official` — 온디맨드 라우트에는 어댑터가 필요합니다. `server:defer` 서버 아일랜드와 라이브 컬렉션도 마찬가지입니다.
- `official` — 5.0에서 `output: 'hybrid'`가 제거되면서 `'static'`이 그 동작을 흡수했으므로, 정적 사이트도 개별 라우트를 서버 렌더링으로 선택할 수 있습니다(L-03).
- `hypercore-default` — `'static'`에서 시작해 필요한 라우트에만 `prerender = false`를 붙입니다. 대부분의 라우트가 동적일 때만 사이트를 `'server'`로 바꾸고, 그 사실을 변경 설명에 적습니다.

## 2. Adapters

`official` — 공식 어댑터는 Node, Netlify, Vercel, Cloudflare입니다(L-09, L-54).

```js
import node from '@astrojs/node';

export default defineConfig({
  adapter: node({ mode: 'standalone' }),
});
```

- `official` — `@astrojs/node`는 `mode: 'standalone' | 'middleware'`와 `staticHeaders`, `bodySizeLimit`, `experimentalDisableStreaming`을 받습니다.
- `official` — 온디맨드 라우트의 HTML은 기본적으로 스트리밍됩니다.
- `official` — 응답 헤더는 페이지 수준(`Astro.response.headers`, `Astro.redirect`)에서만 수정할 수 있고, 자식 컴포넌트는 설정할 수 없습니다.
- `hypercore-default` — 서버 기능을 권하기 전에 어댑터를 확인하고 보고에 어댑터 이름을 적습니다. 프로젝트에 없는 어댑터를 전제로 한 권고는 틀린 권고입니다.

## 3. Server islands

`official` — `<Component server:defer />`는 컴포넌트를 별도 `/_server_islands/...` 라우트로 분리하고, 주입된 스크립트가 그것을 가져옵니다(L-18).

```astro
---
import Avatar from '../components/avatar.astro';
---

<Avatar server:defer>
  <p slot="fallback">Loading…</p>
</Avatar>
```

규칙:

- `official` — prop은 직렬화할 수 있어야 합니다. 함수와 순환 참조는 경계를 넘지 못합니다.
- `official` — prop은 암호화된 쿼리 문자열로 이동하고 대략 2048바이트를 넘으면 POST로 넘어가며, 그러면 캐싱이 깨집니다.
- `official` — prop은 빌드마다 다른 키로 암호화됩니다. 롤링 배포나 다중 리전 배포에서는 `astro create-key`와 `ASTRO_KEY`를 씁니다.
- `official` — `slot="fallback"`은 정적 페이지에 들어갈 자리 표시 마크업을 제공합니다.
- `hypercore-default` — 조각 하나만 쿠키나 개인화를 필요로 하면 페이지 전체를 온디맨드로 바꾸지 말고 서버 아일랜드를 씁니다.

## 4. Client islands

`official` — 프레임워크 컴포넌트는 기본적으로 정적 HTML로 렌더되고, `client:*` 지시어가 하이드레이션합니다(L-19, L-58).

| 지시어 | 하이드레이션 시점 | 쓰는 곳 |
|---|---|---|
| `client:load` | 페이지 로드 즉시 | 첫 페인트에 필요한 상호작용 |
| `client:idle` | 브라우저가 유휴일 때 | 접힌 영역 아래의 보조 컨트롤 |
| `client:visible` | 컴포넌트가 뷰포트에 들어올 때 | 페이지 아래쪽 콘텐츠 |
| `client:media={QUERY}` | 미디어 쿼리가 맞을 때 | 모바일 전용이나 데스크톱 전용 위젯 |
| `client:only={FRAMEWORK}` | 클라이언트 전용, 서버 렌더 없음 | 서버에서 렌더할 수 없는 컴포넌트 |

규칙:

- `official` — 서버 렌더를 건너뛰는 것은 `client:only`뿐이고, 프레임워크 이름을 요구합니다.
- `official` — 하이드레이션 컴포넌트에 넘기는 prop도 서버 아일랜드와 같은 직렬화 제약을 받습니다. 함수는 넘지 못합니다.
- `official` — 프레임워크를 섞을 수 있는 것은 `.astro` 파일뿐입니다. React 컴포넌트가 Svelte 컴포넌트를 렌더할 수 없습니다.
- `hypercore-default` — 상호작용을 만족하는 가장 좁은 지시어를 씁니다. 접힌 영역 아래 아일랜드는 `client:visible`이나 `client:idle`, 첫 페인트에 상호작용이 필요할 때만 `client:load`, 컴포넌트가 정말 서버에서 렌더될 수 없을 때만 `client:only`입니다.
- `hypercore-default` — 추가한 지시어마다 변경에 이유를 적습니다. 아일랜드 지시어는 기본값이 아니라 성능 결정입니다.

## 5. Framework integrations

`official` — 프레임워크 지원은 통합으로 들어옵니다. `@astrojs/react`, `@astrojs/preact`, `@astrojs/svelte`, `@astrojs/vue`, `@astrojs/solid-js`, `@astrojs/alpinejs`입니다(L-19).

- `official` — 통합과 프레임워크 자체 패키지를 함께 설치합니다. 통합이 프레임워크 런타임을 묶어 주지는 않습니다.
- `hypercore-default` — 정적 마크업에는 `.astro` 컴포넌트를 먼저 씁니다. 프레임워크 통합은 그 컴포넌트 모델이 런타임 비용을 정당화할 때만 추가합니다.
- `hypercore-default` — 프레임워크 통합이 여럿인 프로젝트에서는 새로 추가하기 전에 하나로 충분한지 확인합니다. 통합마다 하이드레이션 런타임이 붙습니다.

## 6. Client-side scripts

`official` — Astro의 `<script>`는 번들되고, TypeScript로 컴파일되며, 페이지마다 중복이 제거되고, `type="module"`이 붙고, 작으면 인라인됩니다(L-29, L-58).

| 속성 | 효과 |
|---|---|
| 기본 | 번들, 중복 제거, 처리됨 |
| `is:inline` | 작성한 그대로 두고 번들하지 않음 |
| `define:vars` | `is:inline`을 함축하므로 번들되지 않고 인스턴스마다 실행됨 |

규칙:

- `official` — `define:vars`는 `is:inline`을 함축합니다. 번들이나 중복 제거를 기대하지 않습니다.
- `hypercore-default` — 번들이 로드되기 전에 실행해야 하거나 처리가 필요 없는 경우가 아니면 `is:inline`보다 번들되는 `<script>`를 씁니다.

## 7. What not to do

- 어댑터가 없는 프로젝트에 Actions, 세션, 서버 아일랜드, 라이브 컬렉션, 라우트 캐싱을 추가하지 않습니다.
- 라우트 하나를 동적으로 만들려고 사이트 전체를 `output: 'server'`로 바꾸지 않습니다.
- 자식 컴포넌트 안에서 응답 헤더를 설정하지 않습니다.
- 하이드레이션 아일랜드나 서버 아일랜드에 함수, 클래스 인스턴스, 순환 구조를 넘기지 않습니다.
- `client:*`가 컴포넌트를 서버에서 렌더한다고 기대하지 않습니다. 서버 렌더는 지시어가 없을 때 일어납니다.

## Checklist

- [ ] `output`과 어댑터를 기록했고, 손댄 모든 라우트에 `prerender` 결정이 명시돼 있습니다.
- [ ] `prerender` 값을 정적으로 분석할 수 있습니다.
- [ ] 온디맨드 라우트, 서버 아일랜드, 라이브 컬렉션 뒤에 어댑터가 있습니다.
- [ ] 각 `client:*` 지시어가 상호작용을 만족하는 가장 좁은 것이고 이유가 적혀 있습니다.
- [ ] 직렬화할 수 없는 prop이 하이드레이션이나 서버 아일랜드 경계를 넘지 않습니다.
- [ ] 캐싱이 중요한 곳에서 서버 아일랜드 prop이 POST 대체를 피할 만큼 작습니다.
- [ ] 응답 헤더를 페이지 수준에서 설정합니다.
- [ ] 프레임워크 컴포넌트를 `.astro` 파일 안에서만 섞습니다.

## Sources

> Checked 2026-11-07. 사실은 2026-11-07에 해당 페이지를 연 Astro 조사 레인에서 나왔고, 레인 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `output`은 `'static'`과 `'server'`만 받고 `'server'`는 기본값만 바꿉니다 (L-17, L-09) | https://docs.astro.build/en/reference/configuration-reference/ |
| `prerender` 선택과 해제는 정적으로 분석 가능해야 합니다 (L-09, L-07) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| 5.0에서 `output: 'hybrid'`가 제거되고 `'static'`이 흡수했습니다 (L-03) | https://docs.astro.build/en/guides/upgrade-to/v5/ |
| 온디맨드 라우트, 서버 아일랜드, 라이브 컬렉션의 어댑터 요구 (L-09, L-18, L-10) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| 공식 어댑터와 Node 어댑터 옵션 (L-09, L-54) | https://docs.astro.build/en/guides/integrations-guide/node/ |
| HTML 스트리밍 기본값과 페이지 수준 전용 응답 헤더 (L-09) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| 서버 아일랜드, `server:defer`, fallback slot, 암호화된 props, 2048바이트 POST 대체 (L-18) | https://docs.astro.build/en/guides/server-islands/ |
| 서버 아일랜드 prop 암호화 키와 `astro create-key` (L-18, L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| `client:*` 지시어, 기본 정적 렌더링, 직렬화 가능한 props, `.astro` 전용 혼합 (L-19, L-58) | https://docs.astro.build/en/reference/directives-reference/ |
| 프레임워크 통합과 그 패키지 (L-19) | https://docs.astro.build/en/guides/framework-components/ |
| 번들되는 스크립트, `is:inline`, `define:vars`의 인라인 함축 (L-29, L-58) | https://docs.astro.build/en/guides/client-side-scripts/ |
