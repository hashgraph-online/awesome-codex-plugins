# 프로젝트 구조와 소유권

> Tauri v2 애플리케이션의 renderer/Rust 경계를 도입하거나 검토할 때 이 규칙을 사용합니다. 먼저 날짜가 있는 근거를 읽습니다: [Tauri v2 근거](../../references/official/tauri/tauri-v2-2026-11-04.ko.md), [TanStack + Vite + React 근거](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md).

## 결정 요약

React에는 보편적인 directory layout이 없습니다. 이 스킬은 Tauri의 frontend/Rust 분리, TanStack Router의 file routing 계약, React의 colocation 지침, Redux가 문서화한 feature-folder pattern을 종합해 **규모에 따라 확장하는 route/page/module 구조**를 사용합니다. 이 layout은 Hypercore 규약이며, framework에 구성된 path와 이미 확립된 repository 규약이 우선합니다.

| 관심사 | 기본 소유자 | 분류 |
|---|---|---|
| Frontend와 native code | repository-top JavaScript project(보통 `src/`)와 `src-tauri/`의 Rust/config 분리 | Tauri 공식 문서의 일반 구조 |
| URL hierarchy와 route lifecycle | `src/routes/`와 생성된 `src/routeTree.gen.ts` | TanStack Router 공식 사실 |
| Routed screen composition | route가 더 이상 trivial하지 않을 때 `src/pages/<screen>/` | Hypercore 규약 |
| Business/domain capability | `src/modules/<domain>/` | feature-folder 사례를 반영한 Hypercore 규약 |
| 재사용 가능한 business-agnostic UI | `src/components/` | Hypercore 규약 |
| Tauri renderer adapter | `src/platform/tauri/` | native 경계를 강제하는 Hypercore 규약 |
| App bootstrap과 전역 composition | `src/main.tsx`, `src/router.tsx`, `src/app/` | Hypercore 규약 |
| Cross-cutting non-UI primitive | 목적이 드러나는 child를 가진 `src/shared/` | Hypercore 규약 |

TanStack Router가 file-based routing을 소유합니다. TanStack Query는 asynchronous cache와 freshness를 소유합니다. `pages/`, `modules/`, `components/` folder는 이 소유권을 바꾸지 않습니다.

## Template이 아니라 근거에 따라 확장하기

현재 code가 정당화하는 가장 작은 tier를 선택합니다.

| Tier | 사용하는 경우 | 지금 추가할 것 |
|---|---|---|
| Compact | Route가 몇 개뿐이고 각 UI와 domain logic이 작음 | Bootstrap, Router file, `routes/`, typed Tauri adapter, generated tree |
| Standard | Screen이 여러 개이거나 한 domain에 재사용 UI/data/model behavior가 있음 | 필요에 따라 `pages/`, `modules/`, `components/`, `app/`, 좁은 `shared/` child 추가 |
| Large | Domain과 team이 여러 개이거나 독립 application shell이 있음 | Module public API와 dependency 검사 강화; 두 application이 stable shared contract를 필요로 할 때만 workspace package 추출 |

아래에 표시된 빈 tier나 child를 미리 만들지 않습니다. 관찰 가능한 압력이 생길 때 code를 승격합니다.

- Route component가 screen composition이 되거나 page-only UI가 커지거나 독립적으로 test할 screen boundary가 필요하면 **page**를 만듭니다.
- 한 domain이 함께 변경되는 UI, query, mutation, validation/model, orchestration 중 둘 이상을 소유하면 **module**을 만듭니다.
- 독립적인 page/module 소유자 둘 이상이 같은 business-agnostic UI contract를 필요로 하면 shared **component**를 만듭니다.
- 책임을 하나의 이름으로 설명할 수 있고 소유자가 둘 이상일 때만 shared library를 만듭니다.

## Compact Layout

작은 애플리케이션은 framework 계약상 이점이 있는 부분을 flat하게 유지합니다.

```text
src/
├── main.tsx                 # 유일한 React bootstrap
├── router.tsx               # QueryClient 하나, typed context, router 하나
├── routeTree.gen.ts         # 생성물, 수동 편집 금지
├── routes/
│   ├── __root.tsx
│   └── index.tsx
└── platform/
    └── tauri/
        └── desktop-api.ts   # 좁고 typed된 IPC facade
```

Trivial page component를 route file에 유지해도 됩니다. File 하나를 한 단계 더 깊이 옮기기 위해 `pages/`, `modules/`, `components/`를 만들지 않습니다.

## Standard Layout

Compact layout에 실제 소유권 압력이 생긴 뒤 권장하는 target입니다. 현재 file이 없는 optional directory는 모두 생략합니다.

```text
.
├── package.json
├── index.html
├── vite.config.ts
├── tsconfig.json
├── public/                              # 의도적으로 공개하는 정적 입력만
├── src/
│   ├── main.tsx                         # 유일한 root, app provider를 render
│   ├── router.tsx                       # module-owned QueryClient/context/router
│   ├── routeTree.gen.ts                 # Router plugin 생성물, 수동 편집 금지
│   ├── app/                             # application-wide composition만
│   │   ├── providers.tsx                # main.tsx가 사용하는 provider composition
│   │   ├── app-shell.tsx                # 필요할 때 global chrome/error boundary
│   │   └── styles/                      # global style과 design token
│   ├── routes/                          # URL과 route-lifecycle adapter
│   │   ├── __root.tsx
│   │   ├── index.tsx
│   │   ├── (workspace)/                 # URL에 영향을 주지 않는 조직 group
│   │   │   └── settings.tsx             # thin route -> SettingsPage
│   │   ├── _unlocked.tsx                # optional pathless layout
│   │   └── -route-support/               # generation에서 제외된 route-local helper만
│   ├── pages/                           # routed screen composition
│   │   └── settings/
│   │       ├── settings-page.tsx
│   │       ├── settings-page.test.tsx
│   │       └── parts/                   # 탐색성이 좋아질 때 page-only UI
│   ├── modules/                         # 응집된 business/domain capability
│   │   └── settings/
│   │       ├── ui/                      # module-owned reusable UI
│   │       ├── queries/                 # queryOptions factory
│   │       ├── mutations/               # mutation option과 invalidation policy
│   │       ├── model/                   # schema, domain type, pure state rule
│   │       ├── services/                # 필요할 때 domain orchestration
│   │       └── index.ts                 # 의도적으로 좁힌 public API
│   ├── components/                      # cross-module business-agnostic UI
│   │   └── ui/                          # Button, Dialog, Field, domain policy 없음
│   ├── platform/
│   │   └── tauri/                       # renderer-side typed IPC/plugin adapter
│   │       ├── desktop-api.ts
│   │       └── settings.ts
│   ├── shared/                          # cross-cutting non-UI primitive
│   │   ├── config/                      # public renderer configuration parsing
│   │   ├── hooks/                       # 실제 cross-domain hook
│   │   ├── lib/                         # date/, result/처럼 목적이 있는 folder
│   │   └── test/                        # 실제 공유될 때 test builder
│   └── assets/                          # import되는 renderer asset
├── src-tauri/
│   ├── Cargo.toml
│   ├── build.rs
│   ├── tauri.conf.json                  # 사람이 소유하는 v2 configuration
│   ├── capabilities/                    # 사람이 소유하는 capability manifest
│   ├── permissions/                     # 사용하는 경우 app-command permission
│   ├── icons/
│   └── src/
│       ├── main.rs                      # 얇은 desktop binary entry
│       ├── lib.rs                       # application setup과 registration
│       ├── commands/                    # Tauri command transport boundary
│       ├── domain/                      # 필요할 때 native domain type/policy
│       ├── services/                    # 필요할 때 native use case
│       ├── infrastructure/              # filesystem/keychain/network adapter
│       └── state/                       # 필요할 때 managed Tauri state
├── frontend-build-output/               # 생성물, 정확한 path가 frontendDist와 일치
└── src-tauri/target/                    # 생성된 Cargo output
```

`main.tsx`는 유일한 React bootstrap이며 provider composition을 render합니다. `router.tsx`는 해당 provider가 사용하는 정확한 `QueryClient`, 좁은 renderer dependency, typed router context, router를 소유합니다. Route file은 발견 가능하고 얇게 유지하며, page는 module을 조합하고, module은 domain behavior를 소유하며, shared UI와 primitive는 domain-agnostic하게 유지합니다.

## Folder 계약

### `routes/`: 전체 feature가 아니라 URL과 lifecycle

Route file은 `createFileRoute`, params/search validation, `loaderDeps`, loader/beforeLoad wiring, pending/error/not-found 선택, 하나의 page import를 소유할 수 있습니다. Domain model, 넓은 component tree, raw Tauri call, shared query policy의 기본 위치가 되어서는 안 됩니다.

Router naming을 의도적으로 사용합니다.

- `(group)/`은 URL이나 component tree를 바꾸지 않고 route file을 정리합니다.
- `_layout.tsx`는 pathless layout을 만들므로 component nesting을 바꿉니다.
- `-name`은 file/folder를 generation에서 제외합니다. 작은 route-exclusive helper에만 사용합니다.
- `route.tsx`, `index.tsx`, `$param`, configured token은 설치된 Router plugin 설정을 따릅니다.

Route-local support가 긴밀하게 결합된 file 몇 개를 넘어가면 `routes/`를 두 번째 source tree로 만들지 말고 screen composition을 `pages/`, domain behavior를 `modules/`로 이동합니다.

### `pages/`: routed screen composition

Page는 사용자가 보는 screen 하나 또는 밀접한 screen 묶음을 나타냅니다. Module UI, shared component, page-only part를 조합할 수 있습니다. URL 규약, raw IPC, 전역으로 재사용할 domain behavior, 두 번째 cache를 소유해서는 안 됩니다. Page-only code는 독립적인 다른 소유자가 생길 때까지 page 옆에 둡니다.

`pages/`는 `routes/`를 복제하지 않습니다. Route는 URL/lifecycle adapter이고 page는 render되는 screen composition입니다.

### `modules/`: 응집된 domain capability

`settings`, `documents`, `workspace`처럼 안정적인 domain 또는 capability 이름 하나를 사용합니다. Top-level `features/`와 `modules/`를 동시에 만들지 않습니다. Repository에 이미 확립된 용어가 있으면 보존하고, 그렇지 않으면 여기서는 `modules/`를 사용합니다.

Module은 필요한 segment만 추가합니다.

- `ui/`: module-owned reusable presentation
- `queries/`: Query option factory와 key
- `mutations/`: write와 정확한 invalidation/update policy
- `model/`: schema, type, pure domain state rule
- `services/`: component에 둘 수 없는 multi-step orchestration
- `index.ts`: 외부 소유자가 module을 import할 때 작은 public API

Component, route, query, user click마다 module 하나를 만들지 않습니다. Module은 taxonomy label이 아니라 응집된 change unit입니다.

### `components/`: promotion rule이 있는 shared UI

기본적으로 component를 소유 page 또는 module 옆에 둡니다. 독립적인 소유자 둘 이상이 같은 business-agnostic contract를 사용할 때만 `components/`로 승격합니다. `components/ui/`에는 `Button`, `Dialog`, `Field` 같은 primitive를 둘 수 있지만 page, module, Router route, Query key, Tauri adapter를 import하면 안 됩니다.

Global `components/`에 domain-specific `SettingsForm`, `DocumentToolbar`, 관련 없는 one-off UI를 쌓지 않습니다. 이들은 해당 module/page 아래에 유지합니다.

### `app/`, `platform/`, `shared/`

- `app/`은 provider, shell, top-level error handling, global style을 조합합니다. Business module이 이를 import하면 안 됩니다.
- `platform/tauri/`는 command name, invocation/plugin 선택, argument/result validation, normalized renderer error를 소유합니다. Page나 module UI를 import하지 않습니다.
- `shared/`는 business-agnostic non-UI primitive를 포함합니다. Generic `utils.ts`, `helpers.ts`, global `types.ts`보다 `shared/lib/date/`, `shared/lib/result/`를 선호합니다.
- `public/`과 `assets/`는 delivery 위치이지 domain 소유자가 아닙니다. 어느 쪽에도 secret을 저장하지 않습니다.

## 의존성 방향

Import를 단방향으로 유지합니다.

```text
main/app -> routes/router -> pages -> modules -> platform/tauri
                           \          \-> components -> shared
                            \-------------------------> shared

Tauri command -> native service/use case -> domain -> infrastructure adapter
```

실무 규칙:

1. Route는 page, loader에 필요한 module query factory, typed context contract를 import할 수 있지만 deep path로 module internals를 import하지 않습니다.
2. Page는 module과 shared component를 조합할 수 있지만 다른 page를 import하면 안 됩니다.
3. Module은 `components/`, `platform/tauri/`, `shared/`에 의존할 수 있습니다. Sibling module끼리는 deep import가 아니라 선언된 public API 또는 상위 page/app composition을 통해 상호작용합니다.
4. `components/`, `platform/`, `shared/`는 page나 module을 import하지 않습니다.
5. Renderer code는 `src-tauri/`의 file을 import하지 않습니다. Shared TypeScript type은 Rust validation/authorization을 우회하지 않습니다.
6. Rust command는 transport data를 validate/map하고 native service를 호출합니다. Infrastructure는 command, window, renderer module에 역으로 의존하지 않습니다.

Path alias는 이 경계를 보존할 때만 사용합니다. Alias가 금지된 upward/deep import를 숨겨서는 안 됩니다.

## 생성물, Public API, 사람 소유 File

| Path 또는 class | 소유자 | 규칙 |
|---|---|---|
| `src/routeTree.gen.ts` 또는 configured equivalent | `@tanstack/router-plugin/vite` | 수동 편집 금지, route source/config를 바꾸고 재생성 |
| configured frontend output | Vite build | Source/config를 고치고 rebuild하며 `frontendDist`를 `build.outDir`와 정렬 |
| `src-tauri/target/` | Cargo | Application source로 편집하거나 검토하지 않음 |
| mobile tooling이 만든 `src-tauri/gen/**` | Tauri generator | 관련 Tauri command로 재생성 |
| `tauri.conf.json`의 `app > appDirectoriesOverride` | Application team | Tauri와 해당 API를 쓰는 plugin의 `app_config_dir`, `app_data_dir`, `app_local_data_dir`, `app_cache_dir`, `app_log_dir` 및 `$APPCONFIG` 계열 path variable을 함께 옮긴다. 값을 바꾸면 persisted data, log path, asset scope를 다시 확인한다 |
| `src-tauri/tauri.conf.json`, capability, permission, Rust source | Application team | 의도적으로 검토·편집 |
| module `index.ts` | Module owner | 지원 surface만 export하고 모든 internal file을 그대로 노출하지 않음 |
| lockfile | Repository policy 아래 package manager | 선언된 dependency 작업을 통해서만 변경 |

## Brownfield 도입

1. `vite.config.*`, route directory/token, generated tree path, alias, Vite `build.outDir`, Tauri `devUrl`/`frontendDist`, package script, capability, permission, command registration을 inventory합니다.
2. Rename 전에 현재 folder를 책임에 mapping합니다. 현재 file이 각 boundary를 필요로 하지 않으면 `pages/`, `modules/`, `components/`를 동시에 추가하지 않습니다.
3. 용어 하나를 고릅니다. Repository가 일관되게 `features/`를 쓰면 보존하고 그곳에 `modules/` 계약을 적용합니다. 경쟁 folder를 만들지 않습니다.
4. Route/page/module seam 하나씩 이동하고 모든 direct import/test를 갱신하며 route tree를 재생성하고 navigation과 영향받은 Query/IPC behavior를 검증합니다.
5. Configuration은 마지막에 이동하며 migration 동안 resolved output/command path를 보존합니다.
6. 소유권이 명확해지면 멈춥니다. 작동하는 small app은 standard tree가 필요 없고 large app도 모든 FSD-style layer나 workspace package가 기본으로 필요하지 않습니다.

Folder migration을 Tauri v1 migration, permission 확대, dependency upgrade, workspace conversion, release 변경에 이용하지 않습니다.

## 검토 Gate

다음 조건이 있으면 구조를 거부하거나 교정합니다.

1. Router 생성물을 수동 편집하거나 route naming/group/exclusion semantics가 plugin configuration과 충돌합니다.
2. `routes/`에 넓은 feature 구현이 있고 `pages/`가 URL ownership을 복제하거나 `modules/`가 route file을 복제합니다.
3. 명시적이고 겹치지 않는 계약 없이 `features/`와 `modules/`가 함께 존재합니다.
4. Global `components/`, `hooks/`, `types/`, `utils/`, `services/`가 소유자 없는 dumping ground로 작동합니다.
5. Shared component에 domain policy가 있거나 page가 재사용 domain state를 소유하거나 module이 다른 module internals를 import합니다.
6. Raw Tauri call이 route/page/component에 있거나 renderer folder가 Rust implementation file을 import합니다.
7. 현재 소유자 없이 빈 folder/layer를 scaffold했거나 workspace/package extraction의 consumer가 하나뿐입니다.
8. `frontendDist`, generated route-tree path, human/generated ownership이 모호합니다.

## Sources

> 링크 확인 2026-11-04.

공식 제약:

- Tauri 프로젝트 구조: <https://v2.tauri.app/start/project-structure/>
- Tauri 애플리케이션 설정: <https://v2.tauri.app/reference/config/>
- Tauri Rust command / IPC: <https://v2.tauri.app/develop/calling-rust/>
- Tauri capability: <https://v2.tauri.app/security/capabilities/>
- TanStack Router file-based routing: <https://tanstack.com/router/latest/docs/framework/react/routing/file-based-routing>
- TanStack Router file naming: <https://tanstack.com/router/latest/docs/framework/react/routing/file-naming-conventions>
- TanStack Router context: <https://tanstack.com/router/latest/docs/framework/react/guide/router-context>
- TanStack Query overview: <https://tanstack.com/query/latest/docs/framework/react/overview>

Dependency나 framework mandate가 아닌 비교 조직 근거:

- React file-structure FAQ(legacy, 명시적으로 non-prescriptive): <https://legacy.reactjs.org/docs/faq-structure.html>
- Redux feature/domain folder 논의: <https://redux.js.org/faq/code-structure/>

Vendor mandate가 아닌 Hypercore layout 규약:

- `pages/`, `modules/`, `components/`, `platform/`, `shared/`, tier 표, promotion 규칙은 이 저장소의 규약이며 외부 출처가 없음
