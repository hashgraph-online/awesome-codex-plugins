# 프로젝트 구조와 라우팅

> Astro에서 프레임워크 법칙은 `src/pages/`뿐이고 나머지 폴더는 라벨을 붙인 팀 관례이며, 모든 라우트는 빌드 시점에 렌더되는지 요청 시점에 렌더되는지 밝혀야 합니다.

이 파일의 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다.

## 1. Folder ownership

Astro는 `src/pages/`를 예약하고 `src/`의 나머지는 사용자 몫으로 둡니다. 문서는 `src/components`, `src/layouts`, `src/styles`를 "a common convention ... but it is not required"라고 부릅니다(L-05).

| 경로 | 소유 | 라벨 |
|---|---|---|
| `src/pages/` | 라우트와 엔드포인트만 | `official` |
| `src/layouts/` | 페이지 셸, `<html>` 래퍼, 공유 `<head>` | `hypercore-default` |
| `src/components/` | 재사용 UI, 아일랜드, `.astro` 조각 | `hypercore-default` |
| `src/styles/` | 레이아웃이 import하는 전역 CSS와 토큰 | `hypercore-default` |
| `src/lib/` | 프레임워크에 중립적인 도우미 | `hypercore-default` |
| `src/lib/server/` | `client:*` 아일랜드에 절대 닿으면 안 되는 서버 전용 모듈 | `hypercore-default` |
| `src/actions/` | `src/actions/index.ts`에서 다시 export하는 Action 정의 | `official`(경로), `hypercore-default`(도메인 분할) |
| `src/content.config.ts` | 콘텐츠 컬렉션 정의 | `official` |
| `src/live.config.ts` | 라이브 컬렉션 정의 | `official` |
| `src/middleware.ts` 또는 `src/middleware/index.ts` | 요청 미들웨어 | `official` |
| `src/fetch.ts` | 고급 라우팅용 커스텀 워커 진입점 | `official` |
| `src/env.d.ts` | `App.Locals`와 `ImportMeta` 확장 | `official` |
| `public/` | 출력 루트로 그대로 복사되는 파일 | `official` |

규칙:

- `official` — `src/pages/`에는 라우트만 둡니다. 그곳에 둔 도우미, 타입, fixture는 라우팅되는 URL이 되거나 빌드 오류가 됩니다.
- `official` — `public/`의 파일은 그대로 복사되고 절대 최적화되지 않습니다. 소스 CSS와 JS는 `src/`에 둡니다.
- `hypercore-default` — 서버 전용 코드는 `src/lib/server/`에 두고 클라이언트 import 경로를 열지 않습니다. 그래야 아일랜드가 비밀 값을 브라우저 번들로 끌어오지 못합니다.
- `hypercore-default` — `src/actions/`는 도메인별로 나누고(`src/actions/billing.ts`) `src/actions/index.ts`에서 다시 export합니다. `server` 객체가 노출하는 것만 호출할 수 있습니다.
- `hypercore-default` — `src/content/config.ts`를 만들지 않습니다. 레거시 컬렉션은 6.0에서 제거됐고 현재 파일은 `src/content.config.ts`입니다.
- `hypercore-default` — `dist/`나 `.astro/`에 손으로 쓰지 않습니다. `.astro/types.d.ts`는 `astro sync`가 소유합니다.

## 2. File-based routing

`official` — `src/pages` 아래의 `.astro` 페이지와 `.js`/`.ts` 엔드포인트가 라우트가 되고, `.md`와 `.mdx` 페이지도 라우트로 렌더됩니다(L-06, L-05).

| 파일 | URL |
|---|---|
| `src/pages/index.astro` | `/` |
| `src/pages/about.astro` | `/about` |
| `src/pages/blog/index.astro` | `/blog` |
| `src/pages/blog/[slug].astro` | `/blog/:slug` |
| `src/pages/docs/[...path].astro` | `/docs/*` (rest 파라미터) |
| `src/pages/rss.xml.ts` | `/rss.xml` (엔드포인트) |
| `src/pages/404.astro` | 빌드 시 `404.html` |

규칙:

- `official` — `[param]`은 한 세그먼트를, `[...rest]`는 나머지 경로를 매칭합니다. 서로 바꿔 쓸 수 없습니다.
- `official` — 라우트 우선순위는 예약 라우트, 세그먼트가 많은 쪽, 정적 우선 동적, 명명 파라미터 우선 rest, 프리렌더 동적 우선 온디맨드 동적, 엔드포인트 우선 페이지, 파일 라우트 우선 리다이렉트 순으로 정해집니다(L-06). 이 순서에 조용히 기대지 말고, 두 라우트가 함께 매칭될 수 있으면 하나의 이름을 바꿉니다.
- `official` — 예약 접두사는 `_astro/`, `_server_islands/`, `_actions/`입니다. 이들과 충돌하는 페이지를 만들지 않습니다.
- `official` — `src/pages/404.astro`는 `404.html`을 만듭니다. `src/pages/500.astro`는 온디맨드 렌더링에서만 동작하고 `error` prop을 받습니다(L-37).

## 3. Dynamic routes and `getStaticPaths()`

`official` — 프리렌더 동적 라우트는 `{ params, props? }`를 돌려주는 `getStaticPaths()`를 export합니다(L-06, L-07).

```astro
---
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map((post) => ({
    params: { slug: post.id },
    props: { post },
  }));
}

const { post } = Astro.props;
---
```

규칙:

- `official` — 파라미터는 디코드되지 않습니다. 세그먼트에 인코딩된 문자가 들어올 수 있으면 `decodeURI()`를 호출합니다.
- `official` — `paginate()`는 페이지네이션 컬렉션에 `page` prop을 제공합니다.
- `official` — `routePattern`(5.14+)은 `getStaticPaths` 안에서 파일의 패턴을 노출합니다.
- `official` — 온디맨드 라우트는 `getStaticPaths()`를 export하면 안 되고, 따라서 그 `props`도 받을 수 없습니다.
- `official` — `getStaticPaths()` 안의 `Astro`는 폐기됐습니다. `Astro.site` 대신 `import.meta.env.SITE`를 씁니다.
- `hypercore-default` — `getStaticPaths()`에 요청 시점 네트워크 호출을 두지 않습니다. 이 함수는 빌드 시점에만 돌고, 느린 호출은 모든 빌드를 느리게 합니다.

## 4. Endpoints

`official` — 엔드포인트는 `src/pages` 아래에서 메서드 함수나 `ALL`을 export하고 `satisfies APIRoute`로 타입을 붙이는 `.js` 또는 `.ts` 파일입니다(L-08).

```ts
import type { APIRoute } from 'astro';

export const GET: APIRoute = ({ params, request }) => {
  return new Response(JSON.stringify({ slug: params.slug }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
```

규칙:

- `official` — 응답이 HTML이 아니면 페이지보다 엔드포인트를 씁니다. `Response`를 돌려주는 페이지는 라우터가 추론할 수 없는 라우트입니다.
- `official` — 파일 확장자가 붙은 URL(`sitemap.xml.ts`)은 뒤에 슬래시가 없을 때만 매칭됩니다.
- `hypercore-default` — 엔드포인트 안에서 권한을 확인합니다. 엔드포인트도 공개 URL입니다.

## 5. Redirects, rewrites, and error pages

- `official` — 리다이렉트는 `astro.config.*`에 설정합니다. `redirects: { '/old': '/new' }` 또는 `status`를 지정하는 객체 형태를 씁니다. 외부 절대 URL도 허용되고, 정적 빌드는 `<meta http-equiv="refresh">`를 출력합니다(L-06, L-17).
- `official` — 파일 라우트가 리다이렉트보다 우선합니다. 옛 경로에 페이지가 있으면 리다이렉트는 실행되지 않습니다.
- `official` — `Astro.rewrite('/path')`와 `context.rewrite()`는 브라우저 URL을 유지하고 미들웨어를 포함한 전체 렌더 단계를 다시 돕니다. 대상이 없으면 404를 돌려줍니다.
- `official` — 트래픽만 옮기려는 리다이렉트는 매 요청마다 `Astro.redirect()`를 호출하는 페이지가 아니라 설정에 둡니다.

## 6. Naming

`hypercore-default` — 폴더와 파일은 kebab-case를 씁니다(`src/components/blog-card.astro`, `src/lib/server/session.ts`). 프레임워크가 요구하는 이름(`src/content.config.ts`, `src/middleware.ts`, `src/env.d.ts`, `src/fetch.ts`)은 정확한 표기를 유지합니다.

`hypercore-default` — 컴포넌트 파일은 컴포넌트 하나를 export하고 파일 안에서는 그 이름을 PascalCase로 쓰되, 파일 이름 자체는 kebab-case로 둡니다.

## 7. Migration rules

- 파일을 옮길 때 공개 URL을 보존합니다. 같은 변경에서 리다이렉트를 함께 내보내지 않는 라우트 이름 변경은 호환성을 깨는 변경입니다.
- `prerender` 값을 보존합니다. `export const prerender = false`를 조용히 떨어뜨리는 파일 이동은 동적 페이지를 빌드 시점 페이지로 바꿉니다.
- `src/middleware.ts`를 `src/middleware/index.ts`로 나눌 때 미들웨어 순서를 보존합니다.
- 로컬 관례에 맞추려고 예약 파일의 이름을 바꾸지 않습니다. 프레임워크가 그 파일을 찾지 못하게 됩니다.

## Checklist

- [ ] `src/pages/`에 라우트와 엔드포인트만 있습니다.
- [ ] `src/pages/` 밖의 모든 폴더를 프레임워크 법칙이 아니라 팀 관례로 보고했습니다.
- [ ] 동적 라우트가 올바른 파라미터 형태를 쓰고, 온디맨드 라우트에 `getStaticPaths()`가 없습니다.
- [ ] 엔드포인트가 메서드를 export하고 `satisfies APIRoute`로 타입이 붙어 있습니다.
- [ ] 커스텀 not-found 페이지가 필요하면 `404.astro`가 있고, `500.astro`는 온디맨드 사이트에만 있습니다.
- [ ] `_astro/`, `_server_islands/`, `_actions/`와 충돌하는 파일이 없습니다.
- [ ] `dist/`와 `.astro/`를 손으로 고치지 않았습니다.
- [ ] 라우트 이동이 공개 URL을 유지했거나 리다이렉트를 함께 냈습니다.

## Sources

> Checked 2026-11-07. 사실은 2026-11-07에 해당 페이지를 연 Astro 조사 레인에서 나왔고, 레인 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| `src/pages/`만 예약되고 다른 폴더는 관례입니다 (L-05) | https://docs.astro.build/en/basics/project-structure/ |
| `public/` 파일은 그대로 복사되고 절대 최적화되지 않습니다 (L-05, L-20) | https://docs.astro.build/en/basics/project-structure/ |
| `.astro`, `.md`, `.mdx` 페이지와 `.js`/`.ts` 엔드포인트의 파일 기반 라우팅 (L-06, L-05) | https://docs.astro.build/en/guides/routing/ |
| `[param]`, `[...rest]`, 라우트 우선순위, 예약 라우트 (L-06) | https://docs.astro.build/en/guides/routing/ |
| `getStaticPaths()`, 디코드되지 않는 파라미터, `paginate()`, `routePattern` (L-06, L-07) | https://docs.astro.build/en/reference/routing-reference/ |
| 온디맨드 라우트는 `getStaticPaths()`를 쓸 수 없고 그 props도 받지 못합니다 (L-06) | https://docs.astro.build/en/guides/routing/ |
| `getStaticPaths()` 안의 `Astro` 폐기 (L-02) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
| 엔드포인트 메서드 export, `satisfies APIRoute`, 확장자 URL 매칭 (L-08) | https://docs.astro.build/en/guides/endpoints/ |
| `404.astro`는 `404.html`을 만들고 `500.astro`는 온디맨드 전용입니다 (L-37) | https://docs.astro.build/en/basics/astro-pages/ |
| 리다이렉트 설정, 외부 URL, `<meta http-equiv="refresh">` 대체, 파일 라우트 우선 (L-06, L-17) | https://docs.astro.build/en/guides/routing/ |
| `Astro.rewrite()`는 URL을 유지하고 미들웨어를 다시 돕니다 (L-06) | https://docs.astro.build/en/guides/routing/ |
| `astro sync`가 `.astro/types.d.ts`를 생성합니다 (L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| 레거시 콘텐츠 컬렉션이 6.0에서 제거됐고 현재 파일은 `src/content.config.ts`입니다 (L-02, L-10) | https://docs.astro.build/en/guides/upgrade-to/v6/ |
