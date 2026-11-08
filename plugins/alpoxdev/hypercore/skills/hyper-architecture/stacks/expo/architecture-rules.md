# Expo Architecture Rules

Read before classifying any finding or enforcing a rule. This file owns the rule classes, the authority order, the blocking gates, and the migration policy.

## Rule classes

- **Official**: behavior documented by Expo or React Native and applicable to the installed versions.
- **Safety**: blocking local policy for secrets, runtime input, permissions, native effects, and data loss.
- **Hypercore convention**: scalable default that may be adapted to evidenced project conventions.

Order: user/project authority, installed project evidence, applicable official behavior, safety policy, then Hypercore convention. Safety findings still require an explicit resolution.

## Target dependency direction

```text
src/app (route composition)
  -> src/widgets (optional cross-feature sections)
    -> src/features/<domain> (product capabilities)
      -> src/entities/<entity> (optional shared domain concepts)
        -> src/shared (domain-agnostic UI and infrastructure)
```

Dependencies point right/downward; lower layers never import routes, widgets, or feature screens. Prefer composition in `app`/`widgets` over feature-to-feature imports. Cross-module access uses a deliberately small public API.

## Blocking gates

Block or fix touched work that:

1. Places server credentials or private keys in client code, `EXPO_PUBLIC_*`, app config output, logs, or unencrypted storage.
2. Trusts deep-link params, persisted data, push payloads, or API responses without runtime validation at the boundary.
3. Requests a permission at runtime without corresponding native configuration and user-facing purpose text where required.
4. Runs `prebuild` on committed native directories, EAS publication, signing, or store actions without explicit authority.
5. Introduces native dependencies incompatible with the installed Expo SDK/New Architecture without evidence. SDK 55 through 58 have no architecture opt-out, so an incompatible library must be replaced, patched, or reported; diagnose with `npx expo-doctor` and React Native Directory rather than looking for a flag to flip.
6. Creates route/feature/shared dependency cycles or imports platform-only modules from an unsafe universal module.
7. Claims Android/iOS support after testing only web or Expo Go when native behavior changed. Expo Go also requires a signed-in Expo account in the CLI and the app and ships one SDK version from the stores, so a run must name the SDK it targeted and never stands in for config-plugin or native permission evidence.
8. Uses a removed, deprecated, or superseded API from the dated reference: `InteractionManager`, the `Modal` `animated` prop, the `StatusBar` appearance props, `Touchable` root export, `NativeMethods`, boolean `keyboardShouldPersistTaps`, `freezeOnBlur`, the `initialRouteName` navigator prop, `prebuild --clean` as a break-glass command, `expo-sqlite` libSQL entry points, `File.md5`, `AppMetrics`, or `@expo/vector-icons`.
9. Imports `@react-navigation/*` directly in application code, or uses `react-native/Libraries/*` deep imports or `*Properties` type aliases under the Strict TypeScript API.
10. Plans an SDK 58 upgrade for a project with committed `ios/` and a customized `AppDelegate.swift` without checking the iOS 27 scene-lifecycle migration. Prebuild now generates `SceneDelegate.swift` and `UIApplicationSceneManifest`, and `UIWindow` is created by the scene delegate.

## Scalable default

```text
src/
  app/                  # Expo Router route graph only
  widgets/              # optional cross-feature screen sections
  features/<domain>/    # feature-owned UI, application logic, data, state
  entities/<entity>/    # optional cross-feature domain concepts
  shared/
    api/                # transport, auth injection, error normalization
    config/             # validated public runtime/build config
    observability/      # logging, analytics, crash-reporting ports
    storage/            # secure/non-secure adapters
    testing/            # shared test harness
    theme/              # tokens and theme composition
    ui/                 # reusable presentation primitives
    lib/                # focused framework-independent utilities
  server/               # server-only helpers behind API routes and middleware
  generated/            # generated code; never hand-edit
assets/                 # Expo static assets
app.config.ts           # root native/build config
```

Add folders only when they own real code. A small app may begin with `app`, `features`, and `shared`; do not create empty architecture theater.

A `server/` layer becomes reachable by default on SDK 58: Expo Router projects use `web.output: "server"` when `web.output` is unset, so `+api.ts` routes and `+middleware.ts` exist unless the project opts into `"static"`. Decide that hosting model explicitly and keep privileged code behind the server boundary either way.

## Migration policy

Use vertical slices. Move one route/feature, update imports/tests, run checks, then continue. Avoid repo-wide moves when aliases, generated route types, native config, tests, or ownership remain uncertain. Preserve public behavior unless the request says otherwise.

## Completion gate

All critical Official and Safety findings must pass. Convention differences may ship only when explicitly justified by existing project evidence. Run `rules/expo/testing-and-validation.md` and report both platform coverage and skipped native checks.
