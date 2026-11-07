# Testing and Validation

Read before claiming completion. This file owns the risk depth, the check order, the required scenarios, and the completion record.

## Risk depth

Use `standard` depth for new architecture or material refactors; `thorough` when native modules, permissions, auth/secrets, offline data, EAS config, or platform divergence changes. Pair final-output checks with trajectory checks for installs, native generation, credentials, and publication gates.

## Check order

1. Run repository-defined format/lint/typecheck/tests from actual manifests.
2. Run focused unit/component tests for changed feature and boundary modules.
3. Run Expo diagnostics appropriate to the installed SDK (commonly `npx expo-doctor`). It checks dependency compatibility against React Native Directory, which is the only recovery path now that the New Architecture cannot be disabled.
4. For app-config/plugin changes, inspect resolved config (`npx expo config`) and native outputs/diffs when authorized. Record which command produced the resolved output, because `NODE_ENV` and therefore the loaded `.env` file follow the invoking command.
5. After changing `asyncRoutes`, Metro config, or Babel config, clear the cache with `npx expo start --clear` or `npx expo export --clear` before judging a result. A stale cache otherwise reads as a code failure.
6. For routing changes, exercise initial route, guard redirect, dynamic/deep-link params, back behavior from a deep link, and not-found behavior. Verify that a guard flipping to false leaves no stale history entry.
7. For native/platform changes, verify Android and iOS independently using the project's documented development-build/build path.

Do not invent scripts. If a native check cannot run because the host, credentials, simulator/device, package install, or authorization is unavailable, state the exact gap and use the strongest non-equivalent static check without claiming platform success.

`npx @expo/agent-cli@latest` (`status`, `dev`, `smoke`) and `npx expo command:ps` / `command:events` are optional diagnostics for an agent loop; they wrap Expo CLI, EAS CLI, and `expo-doctor` rather than replacing them, and they are experimental. Set `EXPO_NO_DEV_MENU=1` in CI-style runs so launch URLs suppress the dev menu.

## Testing floors

- `jest-expo` plus React Native Testing Library, per the installed versions.
- `expo-router/testing-library` requires `@testing-library/react-native` 14 or newer on Router 58.
- `renderRouter` returns a promise, and `testRouter` methods `navigate`, `push`, `replace`, `back`, `setParams`, and `dismissAll` are async; `canGoBack()` stays synchronous. Await them before asserting.
- Test files must not live under `app`/`src/app`; every file there is a route or layout. Use `__tests__` or a sibling directory.
- When mocking network, mock at the fetch boundary and assert `expo/fetch` behavior such as `AbortSignal.timeout` rather than a substitute implementation's.

## Required scenarios

- Happy path on the requested platforms.
- Invalid/missing runtime data and configuration.
- API timeout/offline/auth expiration where touched.
- Permission granted, denied, blocked, and fresh-install behavior where touched.
- Secure storage unavailable/corrupt/missing value, and reinstall persistence where it matters, since iOS Keychain can outlive an uninstall.
- Deep-link and malformed route params, including anchor and back behavior when `unstable_settings.anchor` is present or absent.
- Guard behavior: unauthenticated access redirects, an active screen losing access, and no redirect loop.
- Server-output behavior where touched: a `+api.ts` route answering its method, an unsupported method returning 405, and a thrown `StatusError` producing its status.
- Platform-specific module absence or differing lifecycle.
- Regression around moved imports, aliases, route types, and persisted schema.

## Architecture readback

Confirm route thinness, feature ownership, dependency direction, no cycles, no secret leakage, intentional state ownership, platform seams, and no orphaned files. Review generated/native diffs separately from authored source.

## Completion record

Record:

```text
Claim -> Risk -> Evidence -> Verification -> Result -> Caveat
```

Include installed versions, commands actually run, Android/iOS coverage, skipped checks, and one decision: `ship`, `iterate`, `caveated ship`, or `block`. Repair only observed failures and stop after two passes; never weaken checks to pass.

## Sources

> Claims checked 2026-11-04. These statements restate the package's official snapshot, `references/official/expo/expo-react-native-2026-11-04.md`, which cites https://docs.expo.dev/router/reference/testing/, https://docs.expo.dev/router/migrate/sdk-57-to-58/, https://docs.expo.dev/develop/unit-testing/, https://docs.expo.dev/guides/new-architecture/, https://docs.expo.dev/guides/environment-variables/, and https://expo.dev/changelog/sdk-58.
