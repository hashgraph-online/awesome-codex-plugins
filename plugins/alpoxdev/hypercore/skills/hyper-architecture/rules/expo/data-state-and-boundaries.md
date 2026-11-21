# Data, State, and Boundaries

Read when changing server state, client state, persistence, or the direction of a dependency. This file owns state ownership, the runtime boundaries, the transport contract, and the offline rule.

## Separate state by owner

- **Server state**: remote cache, request status, invalidation, retries. Keep it in a query/data layer; do not mirror it wholesale into global client state.
- **Feature/UI state**: transient interaction state owned by the smallest screen/feature that coordinates it.
- **Form state**: input, validation, dirty/submission lifecycle local to the form workflow.
- **Persisted device state**: a deliberate storage schema with versioning/migration and failure handling.
- **Session secrets**: minimal values behind a secure-storage adapter, never a generic persistence store.

Choose libraries from installed project evidence and requirements; this skill does not mandate TanStack Query, Zustand, Redux, or a form/schema library.

## Runtime boundaries

TypeScript types do not validate runtime data. Validate API responses, deep links, push payloads, persisted records, environment values, and native-module results at their entry boundary. Convert transport DTOs to domain models when semantics differ. Normalize network/auth/domain errors before presentation.

Feature application code depends on ports such as `AuthRepository` or a narrow API module, not directly on screen globals. Infrastructure implements those ports. Avoid speculative repository layers for trivial calls; add abstraction where substitution, testing, mapping, caching, or platform divergence is real.

## Transport

`expo/fetch` is installed as `globalThis.fetch` since SDK 56 and is WinterTC-compliant with `AbortSignal.timeout` and `AbortSignal.any`. Do not add a second fetch polyfill on top of it; opting out requires `EXPO_PUBLIC_USE_RN_FETCH=1`, which is a deliberate migration decision rather than a default. When mocking network in tests, mock at the fetch boundary and assert against `expo/fetch` semantics such as abort and timeout behavior rather than a different implementation's.

Centralize base URL, headers, auth refresh, cancellation, timeout, and error normalization. Never log tokens or sensitive payloads. Define retry only for safe/idempotent operations and handle app background/network transitions intentionally.

## Persistence APIs

The `expo-file-system` and `expo-sqlite` APIs split synchronous and asynchronous writes, which a storage adapter must respect:

- `File.write()` is async in SDK 58; the synchronous path is `File.writeSync()`. An adapter that drops the returned promise silently loses writes.
- `File.copy()` and `File.move()` became async in SDK 56.
- `expo-sqlite` no longer supports libSQL: `syncLibSQL()`, `libSQLOptions`, and the `useLibSQL` plugin property are removed or inert.
- `File.md5` is deprecated in favor of `File.digest()`.

If offline persistence is required, define source of truth, conflict policy, queue idempotency, schema migration, encryption needs, and recovery. Do not claim offline-first behavior from caching alone.

## Configuration

Read public environment variables through one validated config module. `EXPO_PUBLIC_*` is bundled client-visible data. Server secrets and signing credentials must remain outside the app bundle.

Three inlining constraints are architecture rules/expo, not style preferences:

- Only static dot access such as `process.env.EXPO_PUBLIC_API_URL` is replaced at build time. Computed access (`process.env['EXPO_PUBLIC_API_URL']`) and destructuring such as `const { EXPO_PUBLIC_X } = process.env` are not.
- Code inside `node_modules` is not rewritten, so a library cannot read the app's public variables through its own module.
- Inlined values are recorded in the transform cache, so changing one invalidates cached output. A stale value therefore indicates a stale cache rather than a missing variable.

Fail early for required config in the appropriate build/runtime path without leaking values.

## Sources

> Claims checked 2026-11-04. These statements restate the package's official snapshot, `references/official/expo/expo-react-native-2026-11-04.md`, which cites https://docs.expo.dev/guides/environment-variables/, https://expo.dev/changelog/sdk-56, https://expo.dev/changelog/sdk-58, and https://docs.expo.dev/versions/v58.0.0/sdk/filesystem/.
