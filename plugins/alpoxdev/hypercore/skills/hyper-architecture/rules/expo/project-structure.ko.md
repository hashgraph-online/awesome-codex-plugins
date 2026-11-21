# Project Structure

folder, module ownership, import, alias, migration 순서를 고르거나 바꿀 때 읽습니다. 이 파일은 scale profile, feature/shared 경계, import 방향을 소유합니다.

## 1. 근거로 구조 선택

App 규모, team boundary, route root, alias, workspace layout, generated file, native-directory ownership, server/API route, test, 현재 import를 조사합니다. 이 규칙에 맞추기 위해 일관된 brownfield 구조를 교체하지 않습니다.

명확한 ownership을 유지하는 가장 작은 profile을 사용합니다.

| Profile | 사용 시점 | 시작 구조 |
|---|---|---|
| Compact | 독립 domain이 적은 prototype/small product | `app`, `features`, `shared` |
| Product | 여러 flow/data source/persisted state 또는 여러 contributor | 아래 full app structure |
| Platform | 여러 app/shared package/native module/독립 release library | `apps/mobile` 내부 Product 구조 + workspace `packages/*` |

Folder는 별도 owner나 dependency rule이 생긴 뒤 승격합니다. 빈 directory와 one-file abstraction layer는 scalability가 아닙니다.

## 2. 권장 product structure

```text
.
├── app.config.ts                 # dynamic Expo/native/build config
├── eas.json                      # EAS profile; client secret 금지
├── metro.config.js               # .js, .ts, .mts 중 하나. 근거가 있는 customization만
├── package.json
├── tsconfig.json
├── assets/                       # font, icon, image, animation
├── scripts/                      # deterministic project automation
├── src/
│   ├── app/                      # Expo Router route graph only
│   │   ├── _layout.tsx           # root provider/navigation shell
│   │   ├── +not-found.tsx
│   │   ├── (public)/
│   │   │   └── sign-in.tsx
│   │   ├── (app)/
│   │   │   ├── _layout.tsx
│   │   │   ├── (tabs)/
│   │   │   │   ├── _layout.tsx
│   │   │   │   └── index.tsx
│   │   │   └── profile/[id].tsx
│   │   ├── +middleware.ts        # 선택적 server middleware (app root)
│   │   └── api/                  # Expo Router +api route. server output이 SDK 58 기본
│   │       └── health+api.ts
│   ├── features/                 # 독립적으로 변경 가능한 product capability
│   │   ├── auth/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── model/            # feature type/state/domain logic
│   │   │   ├── screens/
│   │   │   ├── schemas/
│   │   │   ├── test/             # feature-wide fixture/integration test
│   │   │   └── index.ts          # 의도적으로 작은 public API
│   │   └── profile/
│   ├── entities/                 # optional cross-feature domain concept
│   │   └── user/
│   │       ├── model/
│   │       ├── ui/
│   │       └── index.ts
│   ├── widgets/                  # optional cross-feature screen section
│   │   └── account-summary/
│   ├── shared/                   # domain-agnostic reusable infrastructure
│   │   ├── api/                  # transport/auth injection/error mapping
│   │   ├── config/               # validated public app config
│   │   ├── constants/            # stable global constant only
│   │   ├── hooks/                # truly cross-feature hook
│   │   ├── lib/                  # concern별 focused pure utility
│   │   ├── observability/        # logging/analytics/crash-reporting port
│   │   ├── storage/              # secure/cache/preferences adapter
│   │   ├── testing/              # render wrapper/factory/native mock
│   │   ├── theme/                # token/theme composition
│   │   ├── types/                # 드문 domain-agnostic shared type
│   │   └── ui/                   # design-system primitive
│   ├── server/                   # API route와 middleware 뒤의 server-only 지원
│   └── generated/                # generated code; hand-edit 금지
└── ios/ / android/               # project ownership이 요구할 때만
```

이는 모든 directory를 생성하라는 요구가 아니라 destination map입니다. 실제 code owner가 생기기 전에는 `entities`, `widgets`, `server`, `generated`, native directory를 생략합니다.

## 3. Layer ownership

### `src/app`

Route module, layout, route group, navigation option, URL/deep-link parameter adaptation, optional `+api` entrypoint만 둡니다. Route는 feature screen/use-case를 import하며 얇게 유지합니다. 이 tree의 파일은 routing에 참여하므로 reusable component/query/store/storage/business logic은 밖에 둡니다.

### `src/features/<domain>`

Feature는 auth, checkout, profile editing, notification 같은 하나의 product capability를 소유합니다. 먼저 feature별로 나누고 그 안에서 technical concern으로 나눕니다. Component style/test/story/platform variant는 component 옆에 colocate합니다.

필요할 때만 다음 expanded shape를 사용합니다.

```text
features/profile/
├── api/
│   ├── profile.dto.ts
│   ├── profile.mapper.ts
│   └── profile.queries.ts
├── components/
│   └── avatar-editor/
│       ├── avatar-editor.tsx
│       ├── avatar-editor.test.tsx
│       └── avatar-editor.ios.tsx
├── hooks/
├── model/
│   ├── profile.types.ts
│   ├── profile.state.ts
│   └── update-profile.ts
├── screens/
│   └── profile-screen.tsx
├── schemas/
│   └── profile.schema.ts
└── index.ts
```

Feature-owned code를 위한 global `screens`, `services`, `stores`, `components` root folder를 병렬로 만들지 않습니다. 이런 bucket은 cross-domain dumping ground가 됩니다. Global screen folder는 근거가 있는 brownfield convention일 때만 허용하고 새 scalable work는 screen을 feature와 colocate합니다.

### `src/entities`

독립된 여러 feature가 안정적인 domain concept을 공유하고 transport DTO 이상의 의미가 있을 때만 사용합니다. Entity는 route/feature workflow를 알지 못합니다. API response마다 entity를 만들지 않습니다.

### `src/widgets`

Account dashboard header처럼 여러 feature/entity를 조합하는 reusable page section에만 사용합니다. Widget은 feature/entity/shared에 의존할 수 있지만 feature는 widget에 의존하지 않습니다.

### `src/shared`

Shared는 단지 편리한 code가 아니라 domain-agnostic이고 둘 이상의 owner가 재사용하는 code입니다. `lib`/infrastructure는 unrelated file을 root에 두지 말고 `date`, `validation`, `network` 같은 concern별로 묶습니다. `shared/ui`는 primitive만 두고 product-specific composite는 feature/widget에 둡니다.

### `src/server`

Expo Router API route나 middleware가 있을 때만 사용합니다. Server-only database/secret/privileged code를 client-safe barrel로 export하거나 native route/feature에서 import하지 않습니다. Server code가 있으면 lint/import boundary를 추가합니다.

SDK 58에서는 이 layer가 기본 구성에 들어옵니다. Expo Router 프로젝트는 `web.output`이 없으면 `"server"`를 쓰므로, `"static"`과 선택적 `apiRoutes: true`를 고르지 않는 한 `+api.ts` handler와 `+middleware.ts`가 실행됩니다. 앱이 세 형태 중 무엇을 의도하는지 기록합니다. Server layer의 존재 여부, HTML을 미리 만들어 둘지 요청마다 render할지, 배포가 어디서 돌아야 하는지가 여기서 갈립니다. `expo-server`가 `StatusError` 같은 runtime helper를 제공합니다.

## 4. Dependency rule

```text
app -> widgets -> features -> entities -> shared
api route -> server -> shared/server-safe modules
```

Layer는 오른쪽 layer만 import할 수 있습니다. Same-layer cross-import는 public API가 필요하고 cycle을 만들면 안 됩니다. Feature-to-feature import보다 `app`/`widgets` composition을 선호합니다. 두 feature가 behavior를 공유할 때:

1. Reuse가 incidental하면 caller에 orchestration을 유지합니다.
2. 독립적 의미가 있는 stable domain concept은 `entities`로 이동합니다.
3. Domain-agnostic capability는 `shared`로 이동합니다.
4. 여러 feature 조합이 필요하면 widget/application coordinator를 만듭니다.

각 feature/entity/widget의 `index.ts`는 supported public symbol만 export합니다. Recursive `export *` barrel과 다른 module private path import를 금지합니다. Internal file은 자기 barrel을 거치지 않고 직접 import합니다.

## 5. Cross-cutting placement

| Concern | 권장 위치 | 피할 것 |
|---|---|---|
| Query key, DTO, mapper | owning feature `api/`; transport base는 `shared/api` | 모든 endpoint를 담은 global `services/` |
| Local feature store | feature `model/` 또는 `state/` | unrelated state용 global store 하나 |
| Secure storage/session | `shared/storage` adapter; auth orchestration은 feature | UI 전반의 direct SecureStore call |
| Design primitive | `shared/ui` | feature-specific card/form의 성급한 승격 |
| Analytics/logging | `shared/observability` typed port; event call은 owner 근처 | provider SDK import 분산 |
| Localization | shared i18n runtime; translation namespace는 feature 소유 | 거대한 unowned translation module |
| Test | colocated unit test; 넓은 scenario는 feature `test/`; harness는 `shared/testing` | source 전체를 복제한 detached test tree |
| Platform variant | common module 옆 `.ios`, `.android`, `.native`, `.web` | 큰 `Platform.OS` branch/중복 feature tree |
| Generated API/type | `src/generated` 또는 generator-owned workspace package | manual edit/authored file 혼합 |

## 6. Monorepo profile

```text
.
├── apps/
│   └── mobile/                    # complete Expo app/app-specific feature
├── packages/
│   ├── api-client/                # generated/platform-neutral client
│   ├── domain/                    # 실제 shared pure domain rule
│   ├── ui/                        # 명시적 RN compatibility가 있는 cross-app primitive
│   ├── config/                    # lint/TypeScript/test preset
│   └── native-*/                  # intentionally owned Expo/native module
└── package.json / workspace file
```

재사용 가능성만으로 `packages/*`로 이동하지 않습니다. 두 번째 consumer 또는 독립 release/test boundary가 생긴 뒤 추출합니다. Package는 explicit entrypoint를 제공하고 peer/runtime dependency를 선언하며 app internals를 import하지 않고 native/platform compatibility를 문서화합니다. App route와 app-specific feature orchestration은 `apps/mobile`에 유지합니다.

## 7. Naming/configuration

근거가 있는 project naming을 따릅니다. 새 구조는 kebab-case file/folder, framework-required default 외 named export, 실제 config가 지원하면 `@/* -> src/*`를 선호합니다. Alias 변경은 TypeScript, 해당 시 Metro/Babel, Jest, lint/import rule, callsite를 함께 갱신합니다. Root Expo/config file은 app root에 둡니다.

Metro config는 `metro.config.js`, `metro.config.ts`, `metro.config.mts`를 쓸 수 있습니다. YAML config와 `.es6` extension은 Metro 0.87에서 제거되어 이 세대에서는 동작하지 않습니다.

Metro monorepo 동작은 SDK 55부터 autolinking module resolution을 포함해 자동입니다. `watchFolders`, `resolver.nodeModulesPath`, `resolver.extraNodeModules`, `resolver.disableHierarchicalLookup`은 추가하거나 유지하지 않습니다. 기본 resolution과 충돌하는 legacy 우회 설정입니다.

## 8. Placement decision

새 module마다 순서대로 판단합니다.

1. Route/layout/API-route entry인가? `app`.
2. 하나의 product capability가 소유하는가? 해당 feature.
3. 여러 capability를 reusable section으로 조합하는가? widget 고려.
4. 독립 feature가 공유하는 stable domain concept인가? entity 고려.
5. 실제 domain-agnostic infrastructure/UI인가? focused shared area.
6. Privileged server-only code인가? server boundary 뒤.
7. 실제 independent boundary가 있는 별도 app/package가 공유하는가? workspace package로 추출.

Ownership이 불명확하면 유일한 caller 가까이에 둡니다. Premature sharing은 local duplication보다 되돌리기 어렵습니다.

## 9. Migration/validation

한 번에 vertical feature 하나를 이동합니다. 같은 slice에서 route, public export, alias, test, mock, persisted/import contract를 갱신합니다. 이동마다 dependency cycle/forbidden import를 확인합니다. Generated/native output과 user change를 보존합니다. Replacement와 caller 검증 후에만 obsolete code를 삭제합니다.

## Sources

> 확인 2026-11-04. Expo 관련 서술은 이 패키지의 공식 snapshot `references/official/expo/expo-react-native-2026-11-04.md`를 재진술한 것이며, 그 파일이 다음 URL을 인용합니다: https://docs.expo.dev/router/reference/src-directory/, https://docs.expo.dev/router/web/api-routes/, https://docs.expo.dev/guides/monorepos/, https://reactnative.dev/blog/2026/08/11/react-native-0.87. Layering과 scale profile은 외부 출처에 기대지 않는 Hypercore convention입니다.
