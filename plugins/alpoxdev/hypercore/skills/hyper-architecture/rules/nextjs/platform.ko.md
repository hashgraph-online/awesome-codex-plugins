# Platform and Environment

> `next.config.*`, env handling, route segment config, Proxy, deployment-sensitive setup 규칙입니다.

---

## Environment Variables

- `.env*` files는 `src/` 내부가 아니라 project root에 둡니다.
- Non-`NEXT_PUBLIC_` env vars는 server-only입니다.
- `NEXT_PUBLIC_` values는 build time에 browser bundles로 inline됩니다.
- client에 runtime values가 필요하면 runtime-public env var처럼 가장하지 말고 server path를 통해 노출합니다.
- Next runtime 밖 code가 env loading이 필요하면 `@next/env`를 사용합니다.

## Runtime Env Rule

Server code는 dynamic rendering 중 runtime env values를 읽을 수 있습니다. runtime server env와 build-time inlined client env를 혼동하지 않습니다.

## Cache Components and Route Segment Config

- Cache Components는 Next.js 16.4부터 권장 기본값입니다. `cacheComponents: true`와 `partialPrefetching: true` 두 플래그로 켭니다. `cacheComponents` 없이 `partialPrefetching`만 두면 설정 검증에서 예외가 나고, `partialPrefetching`을 비워 두면 경고가 남습니다.
- `cacheComponents`는 Next.js 16에서 Cache Components, PPR, `useCache`, `dynamicIO` 동작을 묶는 unified switch입니다.
- `cacheComponents`가 켜지면 v16에서 `dynamic`, `dynamicParams`, `revalidate`, `fetchCache` route segment options가 제거됩니다. 대신 Cache Components model을 씁니다. `dynamicParams`는 Cache Components를 켜지 않은 앱에서 그대로 유효합니다.
- 현재 route segment options:

| 옵션 | 타입 | 기본값 |
|---|---|---|
| `dynamicParams` | `boolean` | `true` |
| `runtime` | `'nodejs' \| 'edge' (deprecated)` | `'nodejs'` |
| `preferredRegion` | `'auto' \| 'global' \| 'home' \| string \| string[] (deprecated)` | `'auto'` |
| `maxDuration` | `number` | 배포 플랫폼이 정함 |
| `ensureStatic` (Cache Components 전용) | `'auto' \| 'shell' \| 'prefetch' \| 'navigation' \| false` | `'auto'` |

- `ensureStatic`은 App Shell, per-link prefetch, 완전한 route 중 어디까지 static이어야 하는지 정합니다. layout에 걸면 하위 모든 route에 적용되고, 하위 세그먼트는 더 엄격한 값만 쓸 수 있으며, 함께 렌더링되는 parallel slot은 같은 값을 써야 합니다. dynamic route의 `'navigation'`에는 `generateStaticParams`가 필요합니다.
- `instant`(v16.3 stable)는 Instant Navigation 검증을, `prefetch`(v16.3 stable)는 세그먼트별 prefetch 방식을 `'partial'`과 `'force-disabled'`로 설정합니다. 둘 다 Cache Components가 필요하고 Client Component에서는 export할 수 없습니다.
- `runtime` 기본값은 `'nodejs'`이고 `'edge'`는 deprecated입니다. route 파일에서 `runtime: 'edge'`를 포함한 `runtime` export를 제거합니다. Cache Components에서는 `runtime = 'nodejs'`까지 제거합니다. Cache Components가 Node.js runtime을 요구하고 이 세그먼트 설정을 거부하기 때문입니다.
- Deployment platforms는 `maxDuration`을 사용할 수 있으므로 execution limits를 바꾸는 변경은 문서화합니다.

## Proxy

- `proxy.ts`는 `app` 또는 `pages`와 같은 level인 project root 또는 `src/` root에 둡니다.
- Proxy는 routes render 전에 실행되며 app render code 앞의 network boundary입니다.
- Proxy보다 먼저 `redirects`, `rewrites`, headers, cookies, render-time logic을 검토합니다.
- Proxy에는 explicit matcher와 narrow scope가 있어야 합니다. matcher가 없으면 `_next/static`, `_next/image`, public assets를 포함한 모든 request에서 실행됩니다.
- Matcher values는 Next.js가 build time에 분석할 수 있도록 static constants여야 합니다.
- Proxy 안에서 shared modules 또는 globals에 의존하지 않습니다.
- broad matcher에서는 API routes, metadata, static surfaces, image optimization, public assets가 Proxy를 우회해야 하는지 확인합니다.
- negative matcher로 제외해도 `_next/data` 요청에는 Proxy가 실행됩니다.
- Proxy에서는 `revalidateTag`를 호출할 수 없습니다.
- Server Functions는 사용된 route로 가는 POST requests입니다. matcher 변경은 Proxy coverage를 조용히 제거할 수 있으므로 auth/authz는 Server Function 또는 DAL 안에도 있어야 합니다.

## Important Proxy Note

기존 `middleware` file convention은 deprecated이며 `proxy`로 renamed되었습니다. 새 작업에서 `middleware.ts`를 추가하지 않습니다. migration이 필요하면 official `npx @next/codemod@canary middleware-to-proxy .` codemod를 사용합니다. Proxy는 Node.js runtime이 기본이고 `runtime` config option을 거부하므로, 설정하면 예외가 납니다.

## `next.config.*`

Config changes는 명시적이고 의도적이어야 합니다. 다음 변경은 특히 검토합니다:

- `typedRoutes`
- `cacheComponents`와 `partialPrefetching`(함께 켬)
- `experimental` 아래 `serverActions`: `allowedOrigins`와 `bodySizeLimit`
- `cacheLife`와 `cacheHandlers`
- `experimental.authInterrupts`와 `experimental.instantInsights`
- route segment config strategy, 특히 `cacheComponents` 하위의 v16 removed options
- redirect and rewrite rules/nextjs
- output and deployment settings

## Server Action Deployment Settings

- `experimental.serverActions.allowedOrigins`는 `Origin` host를 `x-forwarded-host` 또는 `host`와 비교합니다. `*`는 한 라벨, `**`는 한 개 이상 라벨과 맞고, 포트는 그대로 적어야 하며 partial replacement는 지원하지 않습니다.
- `Origin` 헤더가 아예 없는 요청은 거절되지 않고 경고와 함께 통과합니다.
- `experimental.serverActions.bodySizeLimit` 기본값은 1MB이고 multipart overhead를 포함한 raw request body에 적용됩니다.
- action ID는 최대 14일마다 회전하므로 인스턴스 사이에서 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`를 고정하고 rolling deploy를 씁니다.

## Recommended Platform Checks

- route-safety가 중요한 TypeScript App Router projects에서는 `typedRoutes: true`를 고려합니다.
- multi-proxy 또는 reverse-proxy deployments에서는 Server Action origin configuration 필요성을 확인합니다.
- deployment-sensitive settings는 PR 또는 final report에 문서화합니다.

## Review Checklist

- `.env*` handling이 Next.js behavior와 일치
- Client code가 `NEXT_PUBLIC_` env vars만 봄
- Cache Components와 removed v16 route segment config options가 우발적으로 섞이지 않음
- `cacheComponents`와 `partialPrefetching`이 함께 켜져 있음
- `runtime` export를 설정하지 않고 제거함
- Proxy가 진짜 필요하고 statically matched이며 scope가 좁음
- Server Action origin, body 크기, 암호화 키 설정이 의도적임
- `next.config.*` changes가 의도적이고 설명됨

## Sources

> 확인 2026-11-04. `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/ensureStatic`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/instant`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/prefetch`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/partialPrefetching`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`, `https://nextjs.org/docs/app/api-reference/file-conventions/proxy`, `https://nextjs.org/docs/app/guides/server-actions`, `https://nextjs.org/docs/app/guides/environment-variables`를 확인했습니다. 날짜가 붙은 스냅숏은 `references/official/nextjs/current-docs-2026-11-04.md`입니다.
