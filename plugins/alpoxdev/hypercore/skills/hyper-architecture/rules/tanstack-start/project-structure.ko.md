# Project Structure and Shared Folder Organization

> TanStack Start project shape, route-root discovery, generated route tree handling, Hypercore shared-folder grouping 규칙.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Start source와 route root는 `tanstackStart({ srcDirectory, router: { routesDirectory } })` 또는 defaults에서 도출 | Official | config가 다르면 `src/routes`를 hard-code하지 않음 |
| `src/router.tsx`가 `getRouter()`를 export하고 generated `routeTree.gen.ts`를 import | Official | `rules/tanstack-start/platform.md`와 함께 확인 |
| `routeTree.gen.ts`는 Start/Router tooling이 생성하며 git에 커밋해야 함 | Official + Safety policy | 일반 architecture work에서 수동 편집 금지, 생성 파일은 커밋 |
| `public/`, root `vite.config.ts`, `package.json`, `tsconfig.json`는 project-level surface로 유지 | Official/docs-derived | source folder 안의 app code처럼 이동하지 않음 |
| `src/modules`, `src/lib`, `src/db`, `src/server`, `src/integrations`, `src/config` 같은 shared folders | Hypercore convention | domain/runtime ownership을 nested folder로 표현 |
| server-only shared code는 compiler-recognized boundaries 뒤에 둠 | Safety policy | client-reachable secret/DB/privileged import 차단 |
| Server function wrapper와 server-only helper 분리 | Official + Safety policy + Hypercore convention | `.functions.ts` / `.server.ts` / schema split 적용 |

## Official Start Project Shape

기본 Start project shape는 source-rooted이며 route tree가 generated됩니다:

```text
src/
├── routes/
│   ├── __root.tsx
│   ├── index.tsx
│   └── example.tsx
├── router.tsx
├── routeTree.gen.ts
├── styles.css
└── types/
public/
vite.config.ts
package.json
tsconfig.json
```

해석:

- `src/routes`는 default route directory이며, config가 override하면 무조건적인 path가 아닙니다.
- `src/router.tsx`는 router creation을 담당하고 `getRouter()`를 export해야 합니다.
- `src/routeTree.gen.ts`는 generated file입니다. route 변경을 위해 수동 rewrite하지 않고, 커밋합니다. 공식 FAQ는 "Should I commit my `routeTree.gen.ts` file into git?"에 "Yes!"라고 답하며, generated route tree가 "part of your application's runtime, not a build artifact"라고 설명합니다 (Official).
- `public/`은 static assets용입니다.
- `vite.config.ts`에는 Start plugin과 route/source directory customization이 있습니다.

## Route Root Discovery

Folder structure를 강제하기 전에 Start plugin config를 확인합니다:

```ts
// vite.config.ts
import { tanstackStart } from '@tanstack/react-start/plugin/vite'

export default defineConfig({
  plugins: [
    tanstackStart({
      srcDirectory: 'src',
      router: {
        routesDirectory: 'routes',
      },
    }),
  ],
})
```

위 예시는 Start의 Vite plugin(`@tanstack/react-start/plugin/vite`)을 사용합니다. Vite는 공식 번들러 통합 둘 중 하나이고, 다른 하나는 Rsbuild이며 자체 plugin entry `@tanstack/react-start/plugin/rsbuild`를 가집니다 (Official). Vite를 당연하게 가정하지 말고 프로젝트 번들러에 맞는 plugin path를 사용합니다.

Default route root는 `src/routes`입니다. `srcDirectory` 또는 `router.routesDirectory`가 custom이면 config에서 실제 route root를 도출하고 review에 보고합니다.

## Route-Local Nested Organization

특정 route에만 존재하는 route-local organization은 route 근처에 둡니다. 기본 route folder는 얇게 유지합니다:

```text
<route-root>/<page>/
├── index.tsx                    # page UI
├── route.tsx                    # layout/beforeLoad/loader when needed
├── -components/
├── -hooks/
└── -sections/
```

`-functions/`는 domain module로 만들 필요가 없는 route-only server action에만 사용합니다:

```text
<route-root>/<page>/
└── -functions/
│   ├── <resource>.functions.ts  # createServerFn wrappers; static import 가능
│   ├── <resource>.server.ts     # DB/secret/filesystem/server-only helper
│   └── schemas.ts               # route-local client-safe validation/types
```

이 shape는 Hypercore convention입니다. TanStack Router는 flat, directory, mixed route structures를 공식 지원하므로 flat route files를 official TanStack usage로 invalid라고 말하지 않습니다. Router의 `routeFileIgnorePrefix` 기본값은 `-`이며 (Official), `-components`, `-hooks`, `-functions` 같은 route-local folders는 route file로 처리되지 않는 co-location 용도로 적합합니다. 이 공식 기본값이 이 스킬의 `-hooks/`, `-components/`, `-functions/` 관례를 뒷받침합니다. Hypercore가 만들어 낸 규칙이 아니라 이 prefix가 해당 folder를 route tree 밖에 두기 때문입니다. 같은 문서는 `routeFilePrefix`, `routeFileIgnorePrefix`, `routeFileIgnorePattern`을 File Naming Conventions 가이드에서 쓰는 token과 겹치게 설정하지 말라고 경고합니다. 겹치면 예기치 않은 동작이 생길 수 있습니다 (Official).

Page UI composition과 route-specific orchestration은 route-local folders를 사용합니다. Publishing-only static pages에 empty folders를 강제하지 않습니다. Server function은 기본적으로 `src/modules/<domain>/<feature>/`에 두고, route-only action일 때만 route-local `-functions/`를 예외적으로 사용합니다.

Server function을 route-local exception으로 둘지 domain module로 승격할지는 reuse와 domain 범위로 판단합니다:

| 상황 | 위치 |
|---|---|
| 진짜 단일 route의 임시/고유 action만 사용 | `<route-root>/<page>/-functions/<resource>.functions.ts` |
| domain noun이 있거나 query key/cache/auth/permission이 필요 | `src/modules/<domain>/<feature>/<resource>.functions.ts` |
| 같은 route group의 여러 child route가 공유 | 기본은 `src/modules/<domain>/<feature>/`; 해당 route group과 분리할 수 없을 때만 parent `-functions/` |
| 서로 다른 route tree 또는 app-wide hook이 공유 | `src/modules/<domain>/<feature>/<resource>.functions.ts` |
| DB, secret, filesystem, privileged SDK helper | `*.server.ts` 또는 `src/db/<domain>/*.server.ts` |
| Zod schema, DTO, query key, formatter처럼 client-safe reuse | route-local `schemas.ts`, `src/modules/<domain>/<feature>/*.schemas.ts`, 또는 `src/lib/<domain>/...` |

## Shared Nested Folder Grouping

Routes를 가로질러 공유되는 code는 route root 밖에 두고, touched shared code를 추가하거나 재구성할 때는 nested logical grouping을 사용해야 합니다. 명시적 project exception을 기록하지 않는 한 `src/lib/foo.ts`, `src/modules/foo.ts`, `src/config/foo.ts` 같은 새 direct leaf file을 만들지 않습니다. Domain ownership, runtime boundary, dependency direction을 보여주는 `src/modules/<domain>/<feature>/foo.ts`, `src/lib/<domain>/foo.ts`, `src/db/<domain>/foo.server.ts`, `src/integrations/<provider>/client.server.ts` 같은 ownership folder를 사용합니다.

이 shared-folder shape는 Hypercore 또는 repo-local convention으로 label합니다(official TanStack requirement 아님). TanStack 공식 문서가 특정 `src/modules`, `src/lib`, `src/integrations` grouping을 요구하지 않기 때문입니다.

Naming decision:

- Domain-owned feature code는 `src/modules/<domain>/<feature>/`를 사용합니다. Server functions, server-only helpers, feature hooks, feature components, schemas, query keys, DTOs를 함께 담아도 좁은 service wrapper처럼 오해되지 않기 때문입니다.
- `src/services/`는 기본 domain layer로 사용하지 않습니다. Hooks, schemas, query keys, UI support가 RPC wrapper 옆에 함께 있을 때 이름이 너무 좁고 애매해집니다.
- External SDK/client adapters는 `src/integrations/<provider>/`를 사용합니다. Domain modules가 provider를 orchestration할 수는 있지만 provider-specific client가 domain workflow를 소유하지는 않습니다.

파일 명명 규칙(kebab-case 파일명, hook과 component 명명, TypeScript style)은 [`rules/tanstack-start/conventions.ko.md`](conventions.ko.md)가 소유하고, 이 파일은 folder shape와 placement를 소유합니다. 파일을 추가할 때 두 규칙을 함께 적용합니다.

권장 Hypercore shape 예시:

```text
src/
├── lib/
│   ├── auth/
│   │   ├── session.ts
│   │   └── permissions.ts
│   └── cache/
│       └── query-keys.ts
├── modules/
│   ├── billing/
│   │   └── invoices/
│   │       ├── invoices.functions.ts   # createServerFn wrappers; client/loader static import 가능
│   │       ├── invoices.server.ts      # handler 내부에서만 import하는 server-only logic
│   │       ├── invoices.schemas.ts     # shared validation schemas / serializable DTOs
│   │       ├── invoices-query-keys.ts  # TanStack Query keys if shared across routes
│   │       ├── hooks/
│   │       └── components/
│   └── users/
│       └── profile/
│           ├── profile.functions.ts
│           ├── profile.server.ts
│           └── profile.schemas.ts
├── db/
│   ├── core/
│   │   └── client.server.ts
│   └── users/
│       └── user-repository.server.ts
├── integrations/
│   └── stripe/
│       ├── client.server.ts
│       └── webhook.schemas.ts
├── server/
│   ├── auth/
│   │   └── middleware.ts
│   └── csrf/
│       └── start.ts
└── config/
    └── env.ts                    # platform/env validation entrypoint exception
```

Shared folder 책임:

| Folder | 목적 | Runtime boundary |
|---|---|---|
| `src/modules/<domain>/<feature>/` | domain feature ownership, cross-route server functions, query/mutation entrypoints, reusable feature hooks/components | `.functions.ts`는 static import 가능; privileged helper는 `.server.ts` |
| `src/lib/<domain>/` | cross-feature client-safe 또는 isomorphic helpers, formatters, permissions, low-level query key primitives | secret/DB import 금지. 필요하면 module `.server.ts` 또는 `src/db`로 split |
| `src/db/<domain>/` | DB client, repositories, ORM-specific mapping | 기본 server-only. route/client import 금지 |
| `src/integrations/<provider>/` | external SDK/client adapters, webhook schemas, provider-specific mapping | secret-bearing client는 `.server.ts`; domain workflow는 modules에서 orchestrate |
| `src/server/<area>/` | request middleware, server entry helpers, auth/session request utilities | server-only 또는 request-runtime only |
| `src/config/<area>/` | env/runtime config, feature flags, deployment config | public/private split 명확화 |

Direct leaf exception은 좁게 둡니다. `src/router.tsx`, generated `src/routeTree.gen.ts`, root `src/start.ts` 또는 `src/config/env.ts`처럼 framework/platform entrypoint로 이미 정해진 파일은 유지할 수 있습니다. 새 domain/shared code는 nested folder가 기본입니다.

## Server Function File Placement

다음 상황에서는 nested grouping을 선호합니다:

- 새 touched shared code가 그대로라면 `src/modules`, `src/lib`, `src/db`, `src/server`, `src/integrations`, `src/config` 아래 direct file로 놓이게 됨
- shared folder에 서로 다른 책임의 files가 세 개 이상 있음
- domain logic, provider integration, schemas, DTOs, query keys, permissions가 섞여 있음
- server-only helper와 client-safe helper가 혼동되기 쉬움
- route-local `-functions/`가 reusable domain module logic으로 커지고 있음
- 관련 없는 helpers가 나란히 있어 imports가 모호해짐

TanStack Start 공식 file organization guidance는 큰 앱에서 server function wrapper와 server-only helper를 분리합니다. Hypercore는 이를 nested domain folder 안에 적용합니다:

```text
src/modules/users/profile/
├── profile.functions.ts      # createServerFn wrappers; route loader/component/hook에서 static import
├── profile.server.ts         # DB/secret/filesystem access; handler 내부에서만 import
├── profile.schemas.ts        # validator schema, serializable DTO
└── profile-query-keys.ts     # client-safe query keys
```

규칙:

- `.functions.ts`는 `createServerFn` exports만 두는 server RPC entrypoint입니다. Static import는 loader/component/hook에서 허용되지만 dynamic import는 피합니다.
- `.server.ts`는 DB, secrets, filesystem, privileged SDK를 포함할 수 있으며 client-reachable code에서 직접 import하지 않습니다.
- schema/type/query-key file은 client-safe로 유지합니다. server-only import를 섞지 않습니다.
- `index.ts` barrel은 safe exports와 server-only exports를 섞기 쉬우므로 `-functions/`와 `src/modules/<domain>/<feature>/`에서 만들지 않습니다.
- route-local `-functions/`가 여러 route에서 import되거나 domain noun/cache/auth/permission을 갖기 시작하면 `src/modules/<domain>/<feature>/`로 승격합니다.

## Boundary and Import Protection Notes

Folder name 자체는 runtime boundary를 강제하지 않습니다.

Privileged shared code에는 다음 중 하나 이상의 명시적 보호를 사용합니다:

- 적절한 경우 `.server.` file suffix
- `@tanstack/react-start/server-only` marker import
- server-only execution boundary용 `createServerOnlyFn`
- client-callable server RPC용 `createServerFn`
- 프로젝트가 더 강한 folder/package protection을 필요로 할 때 custom `importProtection` deny rules/tanstack-start

Route loader 또는 client-reachable module이 DB clients, secret env, filesystem access, privileged SDK wrappers를 직접 import하지 않게 합니다.

## Hard Rules

| 확인 | 규칙 |
|---|---|
| `tanstackStart()` config가 `srcDirectory` 또는 `routesDirectory`를 customize했는데 review가 `src/routes`를 가정 | 실제 route root를 도출할 때까지 차단 |
| 일반 architecture change에서 `routeTree.gen.ts`를 수동 편집 | 차단 |
| Shared `src/modules` / `src/lib` layout을 official TanStack law처럼 제시 | 차단 |
| touched shared root가 exception 없이 `src/modules/foo.ts`, `src/lib/foo.ts`, `src/integrations/foo.ts` 같은 direct leaf file을 추가하려 함 | 경고. logical nested folder로 이동 |
| touched shared folder가 mixed server/client 또는 domain boundaries를 flat layout에 숨김 | 경고. nested grouping 권장 |
| server function wrapper가 server-only helper와 같은 generic file 또는 mixed barrel에 섞임 | 경고. `.functions.ts`와 `.server.ts`로 split |
| server function을 dynamic import하거나 `functions/index.ts` barrel을 통해 가져옴 | 경고. static direct import 사용 |
| server-only shared code가 client-reachable이거나 import protection이 없음 | 차단 |

## Review Checklist

- [ ] 실제 source root와 route root를 Start config 또는 documented defaults에서 도출함.
- [ ] `src/router.tsx`와 generated `routeTree.gen.ts`의 역할을 유지함.
- [ ] Route-local folders는 route-specific logic/UI/server integration이 있을 때만 사용함.
- [ ] Publishing-only pages에 empty route-local folders를 강제하지 않음.
- [ ] 새 touched shared code는 explicit exception이 없는 한 `src/modules`, `src/lib`, `src/db`, `src/server`, `src/integrations`, `src/config` 바로 아래 direct leaf file을 만들지 않음.
- [ ] Shared folders는 boundaries를 명확히 할 때 nested `src/modules`, `src/lib`, `src/db`, `src/server`, `src/integrations`, `src/config` grouping을 사용함.
- [ ] Server functions가 route-local exception인지 domain module인지 reuse/domain 범위로 판단됨.
- [ ] Server function wrapper는 `.functions.ts`, privileged helper는 `.server.ts`, schema/query-key는 client-safe file로 분리됨.
- [ ] `functions/index.ts` 또는 mixed `src/modules/<domain>/<feature>/index.ts` barrel을 만들지 않음.
- [ ] Official Start facts, Safety policy, Hypercore conventions를 별도로 label함.
- [ ] Server-only shared modules에 명시적 import/runtime protection이 있음.

## Sources

> 출처 확인 2026-11-04. 이 파일은 이 패키지 자체의 snapshot(`references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, `references/official/tanstack-start/current-docs-2026-11-04.md`)에 담기지 않은 공식 사실을 주장하지 않습니다. 그 snapshot의 공식 사실은 거기 나열된 TanStack guide page에서 2026-11-04에 다시 검증했습니다. 저장소 로컬 링크 확인 2026-11-04.
