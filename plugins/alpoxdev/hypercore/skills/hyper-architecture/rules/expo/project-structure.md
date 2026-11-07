# Project Structure

Read when choosing or changing folders, module ownership, imports, aliases, or a migration order. This file owns the scale profiles, the feature and shared boundaries, and the import direction.

## 1. Choose structure from evidence

Inspect app size, team boundaries, route root, aliases, workspace layout, generated files, native-directory ownership, server/API routes, tests, and current imports. Do not replace a coherent brownfield structure merely to match this rule.

Use the smallest profile that preserves clear ownership:

| Profile | Use when | Start with |
|---|---|---|
| Compact | Prototype or small product with few independent domains | `app`, `features`, `shared` |
| Product | Multiple flows, data sources, persisted state, or several contributors | Full app structure below |
| Platform | Multiple apps, shared packages, native modules, or independently released libraries | Product structure inside `apps/mobile` plus workspace `packages/*` |

Promote a folder only after it has a distinct owner or dependency rule. Empty directories and one-file abstraction layers are not scalability.

## 2. Recommended product structure

```text
.
├── app.config.ts                 # dynamic Expo/native/build configuration
├── eas.json                      # EAS profiles; no client secrets
├── metro.config.js               # .js, .ts, or .mts; only evidenced customization
├── package.json
├── tsconfig.json
├── assets/                       # fonts, icons, images, animations
├── scripts/                      # deterministic project automation
├── src/
│   ├── app/                      # Expo Router route graph only
│   │   ├── _layout.tsx           # root providers and navigation shell
│   │   ├── +not-found.tsx
│   │   ├── (public)/
│   │   │   └── sign-in.tsx
│   │   ├── (app)/
│   │   │   ├── _layout.tsx
│   │   │   ├── (tabs)/
│   │   │   │   ├── _layout.tsx
│   │   │   │   └── index.tsx
│   │   │   └── profile/[id].tsx
│   │   ├── +middleware.ts        # optional server middleware (app root)
│   │   └── api/                  # Expo Router +api routes; server output is the SDK 58 default
│   │       └── health+api.ts
│   ├── features/                 # independently changeable product capabilities
│   │   ├── auth/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── model/            # feature types, state, domain logic
│   │   │   ├── screens/
│   │   │   ├── schemas/
│   │   │   ├── test/             # feature-wide fixtures/integration tests
│   │   │   └── index.ts          # intentionally small public API
│   │   └── profile/
│   ├── entities/                 # optional concepts shared across features
│   │   └── user/
│   │       ├── model/
│   │       ├── ui/
│   │       └── index.ts
│   ├── widgets/                  # optional cross-feature screen sections
│   │   └── account-summary/
│   ├── shared/                   # domain-agnostic reusable infrastructure
│   │   ├── api/                  # transport, auth injection, error mapping
│   │   ├── config/               # validated public app configuration
│   │   ├── constants/            # stable global constants only
│   │   ├── hooks/                # truly cross-feature hooks
│   │   ├── lib/                  # focused pure utilities by concern
│   │   ├── observability/        # logging, analytics, crash reporting ports
│   │   ├── storage/              # secure/cache/preferences adapters
│   │   ├── testing/              # render wrappers, factories, native mocks
│   │   ├── theme/                # tokens and theme composition
│   │   ├── types/                # rare domain-agnostic shared types
│   │   └── ui/                   # design-system primitives
│   ├── server/                   # optional server-only API-route support
│   └── generated/                # generated code; never hand-edit
└── ios/ / android/               # present only when project ownership requires
```

This is a destination map, not a requirement to create every directory. A normal app should omit `entities`, `widgets`, `server`, `generated`, or native directories until they own real code.

## 3. Layer ownership

### `src/app`

Contains route modules, layouts, route groups, navigation options, URL/deep-link parameter adaptation, and optional `+api` entrypoints. A route imports a feature screen/use-case and remains thin. Reusable components, queries, stores, storage, and business logic stay outside the route tree because files there participate in routing.

### `src/features/<domain>`

A feature owns one product capability such as auth, checkout, profile editing, or notifications. Organize first by feature, then by technical concern inside that feature. Prefer colocating a component's styles, tests, stories, and platform variants beside the component.

Use this expanded shape only when needed:

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

Do not create parallel root folders such as global `screens`, `services`, `stores`, and `components` for feature-owned code. Those buckets become cross-domain dumping grounds. A global screen folder is acceptable only as an evidenced brownfield convention; new scalable work should colocate screens with their feature.

### `src/entities`

Use only when a stable domain concept is reused by multiple independent features and is more than a transport DTO. Entities must not know routes or feature workflows. Do not create an entity for every API response.

### `src/widgets`

Use only for reusable page sections that compose multiple features/entities, such as an account dashboard header. Widgets may depend on features, entities, and shared code; features must not depend on widgets.

### `src/shared`

Shared means domain-agnostic and reusable across at least two owners, not merely convenient. Group `lib` and infrastructure by concern (`date`, `validation`, `network`) rather than placing unrelated files directly in them. `shared/ui` contains primitives; product-specific composites stay with features/widgets.

### `src/server`

Use only when Expo Router API routes or middleware exist. Server-only database, secret, and privileged code must not be exported through client-safe barrels or imported by native routes/features. Add lint/import boundaries when server code is present.

On SDK 58 this layer is reachable by default: an Expo Router project uses `web.output: "server"` when `web.output` is unset, so `+api.ts` handlers and `+middleware.ts` run unless the project sets `"static"` (optionally with `apiRoutes: true`). Record which of those three shapes the app intends, because it decides whether the server layer exists at all, whether HTML is prerendered or rendered per request, and where the deployment must run. `expo-server` supplies the runtime helpers such as `StatusError` for privileged code.

## 4. Dependency rule

```text
app -> widgets -> features -> entities -> shared
api route -> server -> shared/server-safe modules
```

A layer may import only layers to its right. Same-layer cross-imports require a public API and must not form cycles. Prefer composition in `app`/`widgets` over feature-to-feature imports. When two features share behavior:

1. Keep orchestration in the caller if reuse is incidental.
2. Move a stable domain concept to `entities` if it has independent meaning.
3. Move domain-agnostic capability to `shared`.
4. Create a widget/application coordinator when multiple features must be composed.

Each feature/entity/widget `index.ts` exports only supported public symbols. Never use recursive `export *` barrels or import another module's private path. Internal files import directly rather than routing back through their own barrel.

## 5. Cross-cutting placement

| Concern | Preferred location | Avoid |
|---|---|---|
| Query keys, DTOs, mappers | owning feature `api/`; transport base in `shared/api` | one global `services/` containing every endpoint |
| Local feature store | feature `model/` or `state/` | one global store for unrelated state |
| Secure storage/session | `shared/storage` adapter; auth orchestration in feature | direct SecureStore calls throughout UI |
| Design primitives | `shared/ui` | feature-specific card/forms promoted prematurely |
| Analytics/logging | typed ports in `shared/observability`; event calls near owner | provider SDK imports scattered across features |
| Localization | shared i18n runtime; translation namespaces owned by feature | one huge unowned translation module |
| Tests | colocated unit tests; feature `test/` for wider scenarios; `shared/testing` for harness | a detached test tree that mirrors all source paths |
| Platform variants | beside common module as `.ios`, `.android`, `.native`, `.web` | large `Platform.OS` branches and duplicate feature trees |
| Generated API/types | `src/generated` or workspace package with generator ownership | manual edits or mixing generated and authored files |

## 6. Monorepo profile

```text
.
├── apps/
│   └── mobile/                    # complete Expo app and app-specific features
├── packages/
│   ├── api-client/                # generated or platform-neutral client
│   ├── domain/                    # pure shared domain rules/expo, when genuinely shared
│   ├── ui/                        # cross-app primitives with explicit RN compatibility
│   ├── config/                    # lint/TypeScript/test presets
│   └── native-*/                  # intentionally owned Expo/native modules
└── package.json / workspace file
```

Do not move code to `packages/*` merely because it might be reused. Extract only after a second consumer or an independent release/test boundary exists. Packages expose explicit entrypoints, declare peer/runtime dependencies, avoid importing app internals, and document native/platform compatibility. Keep app routes and app-specific feature orchestration inside `apps/mobile`.

## 7. Naming and configuration

Follow evidenced project naming; for a new structure prefer kebab-case files and folders, named exports except framework-required defaults, and `@/* -> src/*` when supported by the actual config. An alias change must update TypeScript, Metro/Babel if applicable, Jest, lint/import rules/expo, and all callsites. Root Expo/config files stay at the app root.

Metro config may be `metro.config.js`, `metro.config.ts`, or `metro.config.mts`. YAML configs and `.es6` extensions were removed with Metro 0.87 and are broken in this generation.

Metro monorepo behavior is automatic, including autolinking module resolution from SDK 55. Do not add or retain `watchFolders`, `resolver.nodeModulesPath`, `resolver.extraNodeModules`, or `resolver.disableHierarchicalLookup`; these are legacy workarounds that now conflict with the default resolution.

## 8. Placement decision

For every new module, decide in order:

1. Is it a route/layout/API-route entry? Put it in `app`.
2. Is it owned by one product capability? Put it in that feature.
3. Does it compose multiple capabilities into a reusable section? Consider a widget.
4. Is it a stable domain concept shared by independent features? Consider an entity.
5. Is it truly domain-agnostic infrastructure or UI? Put it in a focused shared area.
6. Is it privileged server-only code? Put it behind the server boundary.
7. Is it shared by separate apps/packages with an actual independent boundary? Extract to a workspace package.

If ownership is unclear, keep the module close to its only caller. Premature sharing is harder to reverse than local duplication.

## 9. Migration and validation

Move one vertical feature at a time. Update routes, public exports, aliases, tests, mocks, and persisted/import contracts in the same slice. Check dependency cycles and forbidden imports after every move. Preserve generated/native outputs and user changes. Delete obsolete code only after the replacement and callers are verified.

## Sources

> Claims checked 2026-11-04. The Expo-specific statements restate this package's official snapshot, `references/official/expo/expo-react-native-2026-11-04.md`, which cites https://docs.expo.dev/router/reference/src-directory/, https://docs.expo.dev/router/web/api-routes/, https://docs.expo.dev/guides/monorepos/, and https://reactnative.dev/blog/2026/08/11/react-native-0.87. The layering and scale profiles are Hypercore convention and rest on no external source.
