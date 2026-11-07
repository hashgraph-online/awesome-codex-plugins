# 성능

> 프로덕션 빌드를 먼저 측정하고, 클라이언트 번들 밖으로 작업을 옮기고, 이미지와 폰트 무게를 줄인 뒤에야 빌드 병렬화를 건드립니다.

이 파일의 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다. 규칙 순서는 흔한 영향 순이며 측정으로 매긴 순위가 아닙니다.

## 1. Measure first

성능 작업은 프로덕션 빌드에서 합니다. 개발 서버 타이밍과 개발 모드 렌더는 근거가 아닙니다.

| 목표 | 명령 또는 도구 |
|---|---|
| 프로덕션 빌드 | `astro build` |
| 빌드 단계 타이밍 | `astro build --timings` (7.4) |
| 측정 전 타입 검사 | `astro check` |
| 프로덕션 미리보기 | `astro preview` |
| 랩 Core Web Vitals | `astro preview`에 대한 `lhci autorun`, 또는 preview URL에 대한 Lighthouse |
| 필드 Core Web Vitals | 배포된 사이트의 실제 사용자 측정 |
| 번들 구성 | `dist/_astro/` 아래 클라이언트 자산과 선택한 번들 시각화 도구 |

`official` — `astro build --timings`는 빌드 단계 타이밍을 보고합니다. 빌드 시간, 전송 바이트, LCP, INP, CLS 중 어느 수치가 움직였는지 기록합니다.

## 2. Rules

1. `official` — 기본값은 클라이언트 JavaScript 0입니다. `client:*` 지시어가 없으면 프레임워크 컴포넌트는 HTML로 렌더됩니다. 아일랜드 지시어가 전송 바이트에 가장 큰 레버이므로 하나하나 근거를 댑니다.
2. `official` — 콘텐츠 이미지는 `astro:assets`의 `<Image />`와 `<Picture />`를 씁니다. `alt`는 필수이고, 로컬 이미지는 `width`/`height`가 추론되며, 출력에는 `loading="lazy"`, `decoding="async"`, CLS를 막는 명시적 크기가 붙습니다.
3. `official` — LCP 이미지에 `priority`를 붙입니다. `loading="eager" decoding="sync" fetchpriority="high"`가 추가됩니다(5.10+). 모든 이미지에 `priority`를 붙이지 않습니다.
4. `official` — 반응형 세트에는 `layout: 'constrained' | 'full-width' | 'fixed' | 'none'`과 `image.responsiveStyles`, `image.breakpoints`를 씁니다(5.10+). `public/` 이미지는 절대 최적화되거나 반응형이 되지 않습니다.
5. `official` — 원격 이미지 최적화에는 `image.domains` 또는 `image.remotePatterns`가 필요하고, 리다이렉트 대상도 함께 매칭돼야 합니다.
6. `official` — 폰트는 Fonts API로 자체 호스팅합니다. `fonts: [{ provider: fontProviders.local() | fontsource() | google(), name, cssVariable, weights, styles, subsets, fallbacks, formats }]`를 선언하고 `astro:assets`의 `<Font cssVariable="..." preload />`를 출력합니다. 폰트는 내려받아 자체 호스팅되고 `_astro/fonts`에 복사되며 긴 캐시로 제공됩니다.
7. `official` — 첫 화면 위 폰트만 preload합니다. 모든 폰트에 preload를 걸면 LCP 리소스와 경쟁합니다.
8. `official` — `prefetch: true`를 켜고 다음에 갈 가능성이 높은 링크에 `data-astro-prefetch`를 붙입니다. 전략은 `tap`, `hover`, `viewport`, `load`이고, `prefetchAll: true`는 모든 내부 링크를 프리페치하며 `data-astro-prefetch="false"`로 해제합니다. 데이터 절약 모드와 느린 연결은 `tap`으로 낮춥니다.
9. `official` — `astro:transitions`의 `<ClientRouter />`는 그 라우터가 더하는 기능이 필요할 때만 씁니다. 브라우저 네이티브 문서 간 뷰 전환은 Astro JavaScript가 필요 없으므로, 페이지 전환만 원하는 사이트는 라우터를 싣지 않습니다.
10. `official` — `build.inlineStylesheets`는 `'always' | 'auto' | 'never'`를 받고 기본값은 `'auto'`이며 Vite의 4kB `assetsInlineLimit` 아래 스타일시트를 인라인합니다. `'always'`로 강제하기 전에 측정합니다. 요청 수를 HTML 무게와 맞바꿉니다.
11. `official` — `build.concurrency`는 기본값 1로 둡니다. 문서는 "In most cases, you should not change the default value of 1"이라고 하고, 이 옵션은 마이너 릴리스에서 깨질 수 있습니다.
12. `official` — `experimental.parallelPrerender`(7.4)는 여러 CPU 코어를 쓰고, 스스로 프리렌더하는 어댑터(`@astrojs/cloudflare`)에서는 무시됩니다. `--timings`가 프리렌더가 빌드를 지배한다고 보여 줄 때만 씁니다.
13. `official` — `experimental.incrementalBuild`(7.2)는 `cacheKey`를 돌려주는 변경 없는 `getStaticPaths` 페이지의 출력을 재사용합니다. 첫 빌드가 아니라 반복 빌드에 도움이 됩니다.
14. `official` — 라우트 캐싱에는 provider가 필요합니다. `cache: { provider: memoryCache({ max }) }`를 두고 `Astro.cache.set({ maxAge, swr, tags })` 또는 선언적 `routeRules`를 씁니다. `memoryCache()`는 단일 인스턴스 배포용 LRU이고 `X-Astro-Cache: HIT|MISS|STALE`을 추가합니다. provider 없이 `Astro.cache`를 쓰면 "Cache is not enabled."를 던집니다.
15. `official` — Astro의 `<script>` 태그는 번들되고, TypeScript로 컴파일되며, 페이지마다 중복이 제거되고, 작으면 인라인됩니다. `is:inline`은 선택 해제이고, `define:vars`는 `is:inline`을 함축하므로 그 스크립트는 번들되지 않고 인스턴스마다 실행됩니다.
16. `hypercore-default` — 첫 변경 전에 기준선을 기록합니다. `astro build --timings`와 `astro preview`에 대한 Lighthouse 한 번을 모바일과 데스크톱으로 따로 잽니다. 측정마다 레버 하나만 바꿉니다.
17. `hypercore-default` — 75백분위에서 LCP 2.5초 이하, INP 200밀리초 이하, CLS 0.1 이하로 게이트합니다. 모바일과 데스크톱은 별도 수치로 보고합니다.
18. `hypercore-default` — 접힌 영역 아래에는 `client:load`보다 `client:visible`이나 `client:idle`을 먼저 씁니다. `client:only`는 서버에서 렌더할 수 없는 컴포넌트에만 씁니다. 지시어 변경은 성능 변경이므로 전후 수치가 필요합니다.
19. `hypercore-default` — 조각 하나가 개인화될 때 페이지를 온디맨드 렌더링으로 바꾸지 말고 서버 아일랜드를 먼저 씁니다. 온디맨드 렌더링은 정적 페이지에 없던 요청 시점 작업을 더합니다.
20. `hypercore-default` — 라이브 컬렉션은 라우트 캐싱과 함께 씁니다. 캐싱 없는 라이브 컬렉션은 방문자마다 업스트림 요청을 만듭니다.

## 3. Island hydration choice

| 증상 | 레버 |
|---|---|
| 정적 페이지의 큰 전송 JS | `client:*` 지시어를 제거하거나 좁힘 |
| 첫 페인트의 느린 상호작용 | 필요한 위젯에만 `client:load` 유지 |
| 로드 후 긴 메인 스레드 작업 | 접힌 영역 아래 아일랜드를 `client:idle` 또는 `client:visible`로 이동 |
| 정적 마크업에 프레임워크 런타임 전송 | 컴포넌트를 `.astro`로 전환 |
| 작은 위젯 하나 때문에 두 번째 프레임워크 통합 | `.astro`로 충분한지 먼저 확인 |

## 4. Do not

- 개발 서버에서 성능을 읽지 않습니다.
- 프로덕션 빌드의 전후 수치 없이 개선을 주장하지 않습니다.
- 모든 이미지에 `priority`를 붙이거나, 최적화가 필요한 콘텐츠에 `public/` 이미지를 쓰지 않습니다.
- 모든 폰트 굵기를 preload하지 않습니다.
- 네이티브 문서 간 전환만 원하는 사이트에 `<ClientRouter />`를 싣지 않습니다.
- `build.concurrency`, `experimental.parallelPrerender`, `experimental.incrementalBuild`를 한 번에 바꾸지 않습니다.
- 측정된 이유와 마이너 릴리스에서 바뀔 수 있다는 메모 없이 `experimental.*` 플래그를 켜지 않습니다.
- `memoryCache()`를 다중 인스턴스 캐시로 취급하지 않습니다. 프로세스 내 LRU입니다.

## Checklist

- [ ] `astro build --timings`와 `astro preview`에 대한 Lighthouse 한 번으로 기준선을 기록했습니다.
- [ ] 상호작용이 필요 없는 프레임워크 JavaScript가 클라이언트 번들에 없는지 확인했습니다.
- [ ] 모든 `client:*` 지시어에 이유와 가장 좁은 값이 있습니다.
- [ ] 콘텐츠 이미지가 크기와 함께 `astro:assets`를 쓰고, LCP 이미지 하나만 `priority`를 답니다.
- [ ] 반응형 이미지가 `layout`과 `image.responsiveStyles`를 쓰고, `public/` 이미지가 최적화된다고 기대하지 않습니다.
- [ ] 폰트가 Fonts API에서 오고, 첫 화면 위 폰트만 preload합니다.
- [ ] 프리페치 전략이 내비게이션 패턴과 맞고, 뷰 전환은 추가 기능이 필요할 때만 라우터를 씁니다.
- [ ] 측정이 다른 말을 하지 않는 한 `build.concurrency`가 1입니다.
- [ ] 라우트 캐싱에 provider가 있고 라이브 컬렉션이 캐시됩니다.
- [ ] 측정마다 레버 하나만 바꾸고 전후 수치를 기록했습니다.

## Sources

> Checked 2026-11-07. 사실과 URL은 2026-11-07에 각 페이지를 연 Astro 조사 레인에서 가져왔고, 레인 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| 기본 클라이언트 JS 0, 지시어 없이 프레임워크 컴포넌트가 HTML로 렌더 (L-19) | https://docs.astro.build/en/guides/framework-components/ |
| `astro build --timings` (L-28, L-50) | https://docs.astro.build/en/reference/cli-reference/ |
| `<Image />`/`<Picture />`, 필수 `alt`, 추론 크기, lazy/async 기본값 (L-20, L-21) | https://docs.astro.build/en/reference/modules/astro-assets/ |
| LCP 이미지용 `priority` 속성 (L-21) | https://docs.astro.build/en/reference/modules/astro-assets/ |
| `layout` 값, `image.responsiveStyles`, `image.breakpoints`, `public/` 제외 (L-20, L-17) | https://docs.astro.build/en/guides/images/ |
| 원격 최적화용 `image.domains`와 `image.remotePatterns` (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| Fonts API provider, `<Font cssVariable preload />`, `_astro/fonts` 캐싱 (L-24, L-42) | https://docs.astro.build/en/guides/fonts/ |
| 프리페치 전략, `prefetchAll`, 선택 해제, 데이터 절약 하향 (L-22) | https://docs.astro.build/en/guides/prefetch/ |
| `<ClientRouter />`, `transition:persist`, Astro JS가 필요 없는 네이티브 문서 간 전환 (L-23) | https://docs.astro.build/en/guides/view-transitions/ |
| `build.inlineStylesheets` 값과 4kB `assetsInlineLimit` 기본값 (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| `build.concurrency` 기본값과 변경 주의 (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| `experimental.parallelPrerender`와 Cloudflare 어댑터 예외 (L-34, L-50) | https://docs.astro.build/en/reference/experimental-flags/parallel-prerender/ |
| `experimental.incrementalBuild`와 `cacheKey` (L-35, L-50) | https://docs.astro.build/en/reference/experimental-flags/incremental-build/ |
| 라우트 캐싱 provider, `routeRules`, `memoryCache()` LRU, `X-Astro-Cache` (L-30, L-31) | https://docs.astro.build/en/guides/caching/ |
| 번들되는 스크립트, `is:inline`, `define:vars`의 인라인 함축 (L-29, L-58) | https://docs.astro.build/en/guides/client-side-scripts/ |
| 75백분위 Core Web Vitals 임계값과 기기별 보고 | https://web.dev/articles/vitals |
| 랩 하네스로서의 Lighthouse CI | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
