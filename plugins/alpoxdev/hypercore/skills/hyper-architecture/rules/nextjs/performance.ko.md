# 성능

> 프로덕션 빌드를 측정하고, 정적 출력 작업을 클라이언트 번들 밖으로 옮기며, 캐시 수명을 프리렌더 가능 범위에 둡니다.

이 파일의 규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술한 경우 `official`, 이 패키지가 기본값으로 고른 경우 `hypercore-default`로 표시합니다. 규칙 순서는 흔한 영향 순이며 측정으로 매긴 순위가 아닙니다.

## Measure first

성능 작업은 프로덕션 빌드에서 합니다. 개발 서버 타이밍과 개발 모드 렌더는 근거가 아닙니다.

| 목표 | 명령 또는 도구 |
|---|---|
| 프로덕션 빌드 | `next build` (Turbopack이 기본 번들러) |
| 타입 검사 | `tsc --noEmit`. Turbopack은 타입 검사를 하지 않습니다 |
| 번들 구성 | `next analyze`, 또는 `.next/diagnostics/analyze`에 쓰는 `next analyze --output` |
| 빌드 시 분석 데이터 | `next build --analyze` |
| 빌드 간 번들 비교 | `next analyze export --snapshot <name>` (16.4에 추가된 JSONL) |
| 필드 Core Web Vitals | 앱의 `useReportWebVitals` |
| 랩 Core Web Vitals | 프로덕션 배포에 대한 `lhci autorun` |

`next build`는 더 이상 JS 번들 크기를 출력하지 않고(16.0.0에서 제거), `@next/bundle-analyzer`는 Webpack 빌드에서만 유효합니다. 런타임 설정으로 잰 LCP와 랩 Lighthouse 점수는 다른 수치이므로 어느 쪽이 움직였는지 기록합니다.

## Rules

1. `official` — 정적 마크업만 만드는 작업(구문 강조, 마크다운 파싱, 차트 렌더링)은 Server Component로 옮깁니다. 문서의 예시는 클라이언트 Prism을 서버 Shiki로 바꾸면서 해당 부분의 클라이언트 JS를 0으로 만듭니다. 서버에서 번들하지 않아야 하는 패키지는 `serverExternalPackages`로 처리합니다.
2. `official` — 새 작업에는 `cacheComponents: true`와 `partialPrefetching: true`를 함께 켭니다. `partialPrefetching`만 켜면 설정 검증에서 실패하고, 두지 않으면 경고가 기록됩니다.
3. `official` — Cache Components를 켜면 `experimental.ppr`, `experimental_ppr` 세그먼트 export, 모든 `runtime` 세그먼트 export(`runtime = 'nodejs'` 포함)를 제거합니다. PPR은 이제 기본 동작이고 Cache Components는 Node.js 런타임을 요구합니다.
4. `official` — 모든 `use cache` 범위에 명시적 `cacheLife`를 붙이고, 출력이 프리렌더된다고 가정하기 전에 프로필을 프리렌더 기준선과 대조합니다. `revalidate: 0`이나 5분 미만의 `expire`는 런타임 동적 구멍이 되고, 30초 미만의 `stale`은 프리렌더에서 제외되며, 30초에서 5분 사이의 `stale`은 프리렌더되지만 App Shell에서는 빠집니다. 프리셋 중 `seconds`만 여기에 걸립니다.
5. `official` — `use cache` 범위는 async로 두고, `cookies()`와 `headers()` 값은 캐시 범위 안에서 읽지 말고 인자로 넘깁니다. 캐시된 함수가 읽는 외부 스코프 값은 캐시 키의 일부가 됩니다.
6. `official` — 캐시하지 않는 읽기와 요청 시점 API 접근은 `<Suspense>`로 감싸거나 해당 세그먼트에 `loading.tsx`를 둡니다. `loading.js`는 `page.js`, `not-found.js`, 중첩 layout을 감싸지만 같은 세그먼트의 `layout.js`, `template.js`, `error.js`는 감싸지 않습니다. `layout.js`의 fetch를 `page.js`로 옮기는 것이 즉시 내비게이션을 지키는 방법입니다.
7. `official` — 반응형 `next/image`에는 모두 `sizes`를 붙입니다. 없으면 브라우저가 `100vw`로 가정해 필요보다 큰 파일을 내려받습니다. 기본 `quality`는 75이고 `formats` 기본값은 `['image/webp']`이므로 AVIF는 의도적으로 추가합니다.
8. `official` — LCP 이미지는 `loading="eager"`나 `fetchPriority="high"`를 씁니다. Next.js 16부터 `priority`는 `preload`로 대체되어 폐기됐고, `preload`는 `loading`이나 `fetchPriority`와 함께 쓰지 않습니다.
9. `official` — 모든 폰트는 `display: 'swap'`과 함께 `next/font`로 제공합니다. 자체 호스팅되어 외부 요청이 사라집니다. 가변 폰트는 `'100 900'` 같은 굵기 범위를 받습니다.
10. `official` — `next/script`는 기본값인 `afterInteractive`를 유지하고, `beforeInteractive`는 루트 layout의 사이트 전역 중요 스크립트에만 씁니다. App Router에서는 `worker` 전략을 쓰지 않습니다.
11. `official` — Server Action 안의 read-your-own-writes에는 `updateTag`, 그 밖에는 `revalidateTag`를 씁니다. Server Action 밖의 `updateTag`는 유효하지 않습니다. 오래된 데이터 불만은 번들이 아니라 캐시 최신성 결함입니다.
12. `official` — `reactCompiler`(16.0.0부터 안정 최상위 옵션)를 `compilationMode: 'annotation'`과 뜨거운 컴포넌트의 `"use memo"`로 켭니다. 이 컴파일러의 목표는 연쇄 재렌더와 비싼 계산을 건너뛰는 갱신 성능이지 초기 로드가 아닙니다. Next.js는 JSX나 React Hook이 있는 파일에만 적용하므로 빌드 비용이 국소적입니다. 아래 React Compiler 규칙도 함께 봅니다.
13. `official` — Server Component에서 Route Handler를 fetch하지 않습니다. 컴포넌트가 직접 할 수 있는 일에 서버 왕복이 하나 붙습니다.
14. `hypercore-default` — `experimental.optimizePackageImports`에는 분석기가 크다고 지목한 패키지만 추가합니다. 이 옵션은 아직 experimental이고 기본 목록이 `lucide-react`, `date-fns`, `lodash-es`, `rxjs`, `@mui/material`, `recharts`, `@headlessui/react`, `react-icons/*`, `@tabler/icons-react`, `effect`를 이미 덮습니다.
15. `hypercore-default` — 랩 Lighthouse만 믿지 말고 `useReportWebVitals`로 필드 Core Web Vitals를 수집합니다. 게이트는 75백분위에서 LCP 2.5초 이하, INP 200밀리초 이하, CLS 0.1 이하이며 모바일과 데스크톱을 따로 보고합니다.

### React Compiler

컴파일러는 이 스택을 포함한 모든 React 스택에 적용되므로 아래 규칙도 여기에 해당합니다.

- `official` — React Compiler 1.x는 안정 버전이고 프로덕션 준비가 끝났습니다. 베타 단서를 붙여 도입을 미루지 않습니다.
- `official` — 컴파일러가 초기 로드를 개선한다고 주장하지 않습니다. 컴포넌트와 hook을 메모이즈할 뿐 모든 함수를 대상으로 하지 않고, 메모이제이션은 컴포넌트 사이에서 공유되지 않습니다.
- `official` — 컴파일러 lint 규칙(`react-hooks`의 `recommended`/`recommended-latest`, 또는 oxlint의 `react` 플러그인 동등 규칙)을 켜고, 보고는 "이 컴포넌트는 최적화되지 않는다"로 읽습니다. 빌드 실패로 읽지 않습니다. oxlint에서 `rules-of-hooks`는 `correctness`가 아니라 `pedantic`에 있으므로 선택한 카테고리를 확인합니다.
- `official` — 수동 `useMemo`, `useCallback`, `memo` 삭제는 그 파일에서 컴파일러가 실제로 도는 경우에만 허용합니다. 여기서는 `reactCompiler`가 켜진 경우입니다.
- `official` — 프로덕션용 컴파일러 설정에는 `panicThreshold: 'none'`을 두어 컴파일러가 감당하지 못하는 컴포넌트를 빌드 실패 대신 건너뛰게 합니다.

## Do not

- `next build` 출력에서 번들 크기를 읽지 않습니다. 그 표시는 16.0.0에서 제거됐습니다.
- Webpack 전용 기능이 이유가 아니면 `--webpack`을 추가하지 않습니다.
- `partialPrefetching`만 켜지 않고, `seconds` 프로필을 가진 `use cache` 범위가 프리렌더된다고 가정하지 않습니다.
- `preload`를 `loading="eager"`나 `fetchPriority="high"`와 조합하지 않고, 폐기된 `priority` prop을 남기지 않습니다.
- 반응형 이미지에서 `sizes`를 빼지 않고, 폰트를 외부 스타일시트로 제공하지 않습니다.
- `<Scripts />`와 Suspense 배치를 확인하기 전에 스트리밍을 hydration 실패 원인으로 지목하지 않습니다.
- 분석기가 문제 패키지를 지목하기 전에 `experimental.optimizePackageImports`를 조정하지 않습니다.
- Meta 수치(로드 최대 12% 개선, 상호작용 2.5배)를 보장으로 인용하지 않습니다. 한 배포에서 나온 공급자 보고입니다.

## Checklist

- [ ] 프로덕션 빌드에서 분석기 export와 CWV 측정으로 기준선을 기록했습니다.
- [ ] 정적 출력 라이브러리가 서버에서 돌고 클라이언트 번들에서 빠졌습니다.
- [ ] `cacheComponents`와 `partialPrefetching`이 모두 켜져 있고 `ppr`이나 `runtime` export가 남지 않았습니다.
- [ ] 모든 `use cache` 범위가 `cacheLife`를 밝히고 그 프로필이 프리렌더 기준선을 통과합니다.
- [ ] 캐시하지 않는 읽기가 실제로 감싸는 세그먼트의 `<Suspense>`나 `loading.tsx` 뒤에 있습니다.
- [ ] LCP 이미지가 `sizes`를 밝히고 `preload`나 `priority` 대신 `loading`/`fetchPriority`를 씁니다.
- [ ] 폰트는 `next/font`에서 오고, 스크립트는 루트 중요 스크립트가 아니면 `afterInteractive`입니다.
- [ ] 측정마다 레버 하나만 바꾸고 프로덕션 빌드의 전후 수치를 기록했습니다.

## Sources

> Checked 2026-11-07. 아래 사실과 URL은 성능 조사 레인의 Next.js와 React Compiler 항목에서 가져왔습니다. 레인은 2026-11-07에 각 페이지를 열었고 출처 id를 괄호에 남겼습니다.

| Claim | Source |
|---|---|
| Turbopack이 기본 번들러이고 타입 검사를 하지 않습니다 (L-06) | https://nextjs.org/docs/app/api-reference/turbopack |
| `next analyze`, `--output`, `next build --analyze`, 제거된 번들 크기 출력 (L-07) | https://nextjs.org/docs/app/api-reference/cli/next |
| `cacheComponents`와 `partialPrefetching` 조합, PPR 제거, runtime export 거부 (L-08) | https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents |
| Suspense 경계, blocking-route 인사이트, 동기 작업의 프리렌더 (L-09) | https://nextjs.org/docs/app/getting-started/caching |
| `use cache`의 async 요구, 캐시 키 구성, 런타임 API 규칙 (L-10) | https://nextjs.org/docs/app/api-reference/directives/use-cache |
| `cacheLife` 프리셋과 프리렌더 자격 기준선 (L-11) | https://nextjs.org/docs/app/api-reference/functions/cacheLife |
| `updateTag`와 `revalidateTag`의 구분 (L-13) | https://nextjs.org/docs/app/api-reference/functions/updateTag |
| `priority` 폐기, `sizes`, `quality`, `formats`, 이미지 크기 기본값 (L-14) | https://nextjs.org/docs/app/api-reference/components/image |
| `next/font` 자체 호스팅, `display: 'swap'`, 굵기 범위 (L-15) | https://nextjs.org/docs/app/api-reference/components/font |
| `next/script` 전략과 App Router에서의 `worker` 제약 (L-16) | https://nextjs.org/docs/app/api-reference/components/script |
| 정적 출력 작업의 Server Component 이전, `serverExternalPackages` (L-17) | https://nextjs.org/docs/app/guides/package-bundling |
| `useReportWebVitals`, 병렬 fetch, Server Component의 Route Handler fetch 금지 (L-18) | https://nextjs.org/docs/app/guides/production-checklist |
| `optimizePackageImports`의 experimental 상태와 기본 목록 (L-19) | https://nextjs.org/docs/app/api-reference/config/next-config-js/optimizePackageImports |
| `loading.js`의 적용 범위와 layout에서 page로의 fetch 이동 (L-20) | https://nextjs.org/docs/app/api-reference/file-conventions/loading |
| `staleTimes` 기본값 (L-21) | https://nextjs.org/docs/app/api-reference/config/next-config-js/staleTimes |
| `reactCompiler` 안정 최상위 옵션, SWC 패스, annotation 모드 (L-05) | https://nextjs.org/docs/app/api-reference/config/next-config-js/reactCompiler |
| React Compiler 1.0 안정성, Meta 수치, 갱신 성능 범위 (L-01, L-02) | https://react.dev/blog/2025/10/07/react-compiler-1, https://react.dev/learn/react-compiler/introduction |
| 컴파일러 선행 Babel 순서, `panicThreshold`, lint는 최적화 건너뜀 (L-03, L-04) | https://react.dev/learn/react-compiler/installation, https://react.dev/reference/react-compiler/configuration |
| 컴파일러 lint 규칙 이름과 프리셋 (L-65) | https://raw.githubusercontent.com/facebook/react/main/packages/eslint-plugin-react-hooks/README.md |
| oxlint `react` 플러그인 규칙 집합과 카테고리 매핑 (L-66) | https://oxc.rs/docs/guide/usage/linter/rules.html |
| 75백분위 기준 Core Web Vitals 임계값, 기기별 구분 (L-67) | https://web.dev/articles/vitals |
| CI 하네스로서의 Lighthouse CI (L-68) | https://raw.githubusercontent.com/GoogleChrome/lighthouse-ci/main/README.md |
