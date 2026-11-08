# Platform Setup

> Router, env, alias, 운영 인접 설정 규칙

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| `src/router.tsx`가 fresh-instance `getRouter()` export | Official | missing setup 차단 |
| server/client env boundary | Safety policy | secret leak 차단 |
| non-trivial app runtime env validation | Hypercore convention + Safety policy | warn 또는 `src/config/env.ts` scaffold 추가 |
| Vite version-aware path alias | Hypercore convention | touched code에서 수정 |
| Nitro(`nitro/vite`) 기반 hosting, Vite 8, Node ≥22.12 | Official | 삭제된 plugin 또는 Vite 7 안내 차단 |
| 설치된 `@tanstack/*` 버전을 공식 공급망 권고의 영향·패치 범위와 대조 | Safety policy | install 또는 upgrade 전에 확인 |

---

## Dependency Safety

- **Safety policy.** install 또는 upgrade 전에 설치된 `@tanstack/*` 버전을 공식 권고의 영향·패치 범위와 대조합니다. 선례는 권고 [`GHSA-g7cv-rxg3-hmpx`](https://github.com/TanStack/router/security/advisories/GHSA-g7cv-rxg3-hmpx)(2026-05-11 게시, critical)입니다. `@tanstack/*` 패키지의 악성 버전이 배포되어 install 시점에 클라우드 자격증명, GitHub 토큰, SSH 키를 수집했습니다. 이 스냅샷들이 고정한 패키지 중 `@tanstack/cli`만 영향을 받지 않았습니다.
- **Official.** 권고가 기록한 영향 → 패치 범위입니다. 이 표는 provenance로만 쓰고, 권위 있는 범위 확인은 권고 원문에서 합니다.

| 패키지 | 악성 버전 | 패치 버전 |
|---|---|---|
| `@tanstack/react-router` | 1.169.5, 1.169.8 | 1.169.9 |
| `@tanstack/react-start` | 1.167.68, 1.167.71 | 1.167.72 |
| `@tanstack/router-cli` | 1.166.46, 1.166.49 | 1.166.50 |
| `@tanstack/router-plugin` | 1.167.38, 1.167.41 | 1.167.42 |
| `@tanstack/start-client-core` | 1.168.5, 1.168.8 | 1.168.9 |
| `@tanstack/start-plugin-core` | 1.169.23, 1.169.26 | 1.169.27 |
| `@tanstack/start-server-core` | 1.167.33, 1.167.36 | 1.167.37 |
| `@tanstack/zod-adapter` | 1.166.12, 1.166.15 | 1.166.16 |

- 특정 버전을 이 파일에서 "안전하다"고 적지 않습니다. 권고의 postmortem은 현재 배포된 모든 TanStack 패키지 버전이 설치해도 안전하다고 밝혔고, 권위 있는 범위 확인은 이 파일이 아니라 권고와 npm advisory database에 있습니다.
- 영향을 받은 버전을 설치한 호스트가 있으면 그 호스트를 침해 가능 상태로 보고, 호스트에서 접근 가능한 자격증명(AWS, GCP, Kubernetes, Vault, GitHub, npm, SSH)을 교체합니다. 페이로드가 install lifecycle script로 실행됐기 때문입니다.

## Release Status

- **Official.** Start는 v1 stable입니다. `@tanstack/react-start` 1.169.0(2026-10-12 게시)이 첫 stable release입니다. 원문: "TanStack Start is stable. If you're upgrading from a release candidate, follow `Migrate from the Release Candidate`." stable line은 1.169.x이고 `@tanstack/react-router`는 1.170.x에서 따로 움직입니다.
- **Official.** Release Candidate 프로젝트를 올릴 때는 API 세 개를 제거하고 동작 영역 네 곳을 확인합니다. `@tanstack/nitro-v2-vite-plugin`은 `nitro/vite`의 `nitro()`로, `useSession`은 iron-session 같은 session library로, `.inputValidator()`는 `.validator()`로, Vite 7은 Vite 8로 바뀝니다. 동작 영역은 Errors, Responses, Requests and middleware이며 각 내용은 `references/official/tanstack-start/tanstack-start-2026-11-04.md`에 기록했습니다.
- **Official.** Start는 Vite로 빌드할 때 Vite 8을 요구합니다(`peerDependencies.vite`가 `>=8.0.0`이고 "Vite 7 is no longer supported"). `@tanstack/react-start@1.169.4`는 `engines.node`로 `>=22.12.0`을 선언합니다. version bump나 새 scaffold를 제안하기 전에 두 조건을 확인합니다.
- stable이 되었다고 동작을 추측해도 되는 것은 아닙니다. Router와 Start는 patch release에서도 BREAKING 변경을 싣기 때문에, API가 확정됐다고 가정하지 말고 날짜가 박힌 snapshot을 다시 확인합니다.

---

## Router 설정

- `src/router.tsx`는 반드시 `getRouter()`를 export해야 합니다
- `getRouter()`는 호출할 때마다 새로운 router instance를 생성해서 반환해야 합니다
- `scrollRestoration`, preload 기본값, cache 설정 같은 router-wide 동작은 여기서 설정합니다

---

## Environment 규칙

- 새 TanStack Start env scaffold에서는 `src/env/`, `src/env.ts`, `src/env.d.ts`를 만들지 않습니다.
- env 코드는 `src/config/` 아래에 유지하고, canonical validation module은 `src/config/env.ts`입니다.
- TanStack Start/Vite 프로젝트에서는 `@t3-oss/env-core`와 `zod`를 사용하고 `createEnv`로 scaffold합니다.
- 프로젝트가 Vite `envPrefix`를 명시적으로 바꾸지 않았다면 client 변수는 `clientPrefix: "VITE_"`로 설정합니다.
- `VITE_*` 변수는 client에 노출되므로 secret, token, private API key, password, database URL을 담으면 안 됩니다.
- 서버 전용 env는 `process.env`에 두고 server boundary 뒤에서 접근하며 `server`에 나열합니다.
- client-safe env는 `import.meta.env`에서 가져오고 `client`에 나열하며 public prefix를 사용합니다.
- 명시적인 build-time coverage가 필요하면 `runtimeEnvStrict`를 우선 사용하고, framework/runtime이 전체 env object를 안정적으로 제공할 때만 `runtimeEnv`를 사용합니다.
- shared config file이 server/client 양쪽에서 import될 수 있으면 `isServer: typeof window === "undefined"`를 포함합니다.
- env는 module scope가 아니라 request 안에서 읽습니다. `process.env` 접근은 `.handler()`, middleware `.server()`, server-route handler 같은 per-request callback 안에 둡니다. Cloudflare Workers와 다른 edge SSR runtime은 env를 request 시점에 주입하므로 module scope에서 읽으면 서버에서도 `undefined`가 되고, client에서는 secret이 bundle에 inline될 위험이 있습니다.
- 프로젝트에 문서화된 예외가 없으면 새 validation module에는 `emptyStringAsUndefined: true`를 설정합니다.
- 서버 변수 이름 자체가 client bundle에 노출되면 안 되는 경우에도 schema split은 `src/config/` 아래(예: `env.server.ts`, `env.client.ts`)에서 수행하고 `src/env/` 아래에는 만들지 않습니다.

Canonical starter shape:

```ts
// src/config/env.ts
import { createEnv } from "@t3-oss/env-core"
import * as z from "zod"

export const env = createEnv({
  server: {
    DATABASE_URL: z.url(),
  },
  clientPrefix: "VITE_",
  client: {
    VITE_PUBLIC_APP_URL: z.url(),
  },
  runtimeEnvStrict: {
    DATABASE_URL: process.env.DATABASE_URL,
    VITE_PUBLIC_APP_URL: import.meta.env.VITE_PUBLIC_APP_URL,
  },
  isServer: typeof window === "undefined",
  emptyStringAsUndefined: true,
})
```

---

## Path Alias 규칙

- path alias는 암묵적으로 가정하지 말고 명시적으로 설정합니다
- Vite 8+: `resolve.tsconfigPaths: true` 우선(Vite 자체 옵션이고 기본값은 `false`입니다)
- Vite 7 이하: `vite-tsconfig-paths` 사용
- TanStack Start 프로젝트는 반드시 첫 번째 갈래입니다. Start 1.169+는 Vite 8을 요구하므로 `vite-tsconfig-paths` 갈래는 Start가 아닌 Vite 7 프로젝트에만 해당합니다
- 저장소 전체에서 하나의 canonical alias 규칙을 유지합니다

---

## 운영 인접 패턴

- health/readiness endpoint는 server route로 허용됩니다
- sitemap/robots 생성은 prerender 설정 또는 server route를 사용할 수 있습니다
- integration/LLMO용 machine-readable endpoint는 명시적으로 필요할 때 허용됩니다
- observability hook, metrics, Sentry류 연동은 페이지 로직이 아니라 operations/platform 문서에 둡니다

---

## Server Entry

- `src/server.ts`는 선택 사항입니다. 없으면 Start가 내장 entry를 쓰고, 그 entry가 request를 렌더하며 잡히지 않은 error를 HTTP response로 바꿉니다. error 처리만을 위해 custom entry를 추가하지 않습니다.
- custom entry가 필요하면 `createServerEntry`가 callback 전체를 request context 안에 두고, `createStartHandler(...)`가 원래 error를 다시 던져 `handleStartError(error)`가 helper state를 적용한 response를 만들 수 있게 합니다.
- request ID나 database handle처럼 request마다 달라지는 값은 `handler.fetch(request, { context })`로 넘기고, `@tanstack/react-router`의 `Register` interface에 `server.requestContext`를 보강해 type을 붙입니다. type 등록은 runtime 값을 만들지 않습니다. 이 context는 global middleware, request/function middleware, server route, server function, router에 전달됩니다.

## Hosting과 Deployment

- **Official.** 배포는 삭제된 `@tanstack/nitro-v2-vite-plugin`이 아니라 `nitro/vite` plugin의 Nitro로 합니다. `vite.config.ts`에서 `tanstackStart()`와 함께 `nitro/vite`의 `nitro()`를 추가합니다. Nitro는 Vite Environments API와 통합되어 Start의 기반 build tool로 동작합니다.
- **Official.** 공식 hosting partner는 Cloudflare(`@cloudflare/vite-plugin`과 `wrangler`), Netlify(`@netlify/vite-plugin-tanstack-start`), Railway(Nitro)입니다. 다른 provider도 지원되지만 partner는 아닙니다.
- **Official.** Node + Nitro에서 srvx `FastResponse`가 문서화된 처리량 선택지입니다. 이것은 배포 tuning 선택이지 아키텍처 요구사항이 아닙니다.
- hosting 설정을 page나 route code에 적지 않습니다. 배포 설정은 `vite.config.ts`, provider 설정 파일, operations 문서에 둡니다.

## 리뷰 체크리스트

- `getRouter()`가 존재하고 새 instance를 반환함
- env 사용이 typed이고 경계가 안전하며 module scope가 아니라 request 단위로 읽음
- alias 설정이 사용 중인 Vite 버전과 맞음
- hosting 안내가 `nitro/vite`를 가리키고 삭제된 plugin을 언급하지 않음
- 운영 endpoint가 내부 앱 RPC와 섞이지 않음

## Sources

> Safety policy 사실은 공식 권고 <https://github.com/TanStack/router/security/advisories/GHSA-g7cv-rxg3-hmpx>와 그 postmortem <https://tanstack.com/blog/npm-supply-chain-compromise-postmortem>에서 왔습니다. stable release 상태, Vite 8 요구, 삭제된 API, hosting partner는 <https://tanstack.com/start/latest/docs/framework/react/overview.md>, <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>, <https://tanstack.com/start/latest/docs/framework/react/guide/hosting.md>, <https://tanstack.com/start/latest/docs/framework/react/guide/environment-variables.md>, <https://registry.npmjs.org/@tanstack/react-start/latest>, <https://vite.dev/config/shared-options.md>에서 확인했습니다. 공식 사실 검증일 2026-11-04. 나머지는 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 위임합니다. 저장소 로컬 링크 확인 2026-11-04.
