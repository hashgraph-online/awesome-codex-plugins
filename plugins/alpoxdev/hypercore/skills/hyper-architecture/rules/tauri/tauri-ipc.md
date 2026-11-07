# Tauri IPC Boundary

> Read when adding, reviewing, or testing communication between the React/TanStack frontend and Tauri Rust in this skill.

## Evidence and terms

**Official fact.** Tauri commands are invoked from the frontend and may return a value or an error; events carry one-way notifications; channels send ordered data from Rust to the frontend. See the [Tauri v2 evidence ledger](../../references/official/tauri/tauri-v2-2026-11-04.md), [Calling Rust from the Frontend](https://v2.tauri.app/develop/calling-rust/), and [Calling the Frontend from Rust](https://v2.tauri.app/develop/calling-frontend/). The linked pages were accessed on 2026-11-04 as evidence, not as immutable API contracts; recheck the ledger and current official docs before version-sensitive changes.

**Project convention.** A *native adapter* is the only frontend module that imports `invoke`, `listen`, `Channel`, or another `@tauri-apps/api/*` native API. It owns marshaling, runtime validation, error normalization, and cancellation semantics. Routes, route loaders, components, and presentational hooks call domain/query helpers, never native APIs directly.

**Safety policy.** IPC is a privilege boundary, not an internal shortcut. A Rust command must treat every frontend argument and every event-originated value as untrusted input.

---

## Ownership and typed contracts

Use one explicit frontend adapter per native domain. Keep request/response DTOs close to the adapter and use the same named fields at the boundary; do not expose a generic `invoke<T>()` helper to application code.

```text
src/platform/tauri/settings/
  settings.dto.ts             # input/output schemas and TypeScript types
  settings.native.ts          # the only invoke/listen implementation
src/modules/settings/
  queries/settings.queries.ts # TanStack Query option factories
  mutations/settings.ts       # writes and invalidation policy
src-tauri/src/
  commands/
    mod.rs
    settings.rs           # command handlers and boundary validation
  dto/
    settings.rs           # serializable request/response/error DTOs
```

Adapt the paths to an existing project structure rather than creating parallel folders. The invariant is ownership, not this exact tree.

```ts
// src/platform/tauri/settings/settings.native.ts
import { invoke } from '@tauri-apps/api/core'
import { z } from 'zod'

export const readSettingsOutput = z.object({ theme: z.enum(['light', 'dark']) })
export type Settings = z.infer<typeof readSettingsOutput>

export async function readSettings(): Promise<Settings> {
  const output = await invoke<unknown>('settings_read')
  return readSettingsOutput.parse(output)
}
```

- **Convention:** use descriptive command names grouped by domain (for example, `settings_read` and `settings_update`), and pass a named object for multi-field input. Keep the exact Rust/JS naming rule explicit; do not depend on implicit case conversion.
- **Convention:** parse untrusted external payloads at the frontend boundary when a malformed value could otherwise reach application state. Rust remains the enforcing side even if the frontend validates first.
- **Convention:** return stable, serializable response DTOs rather than Rust persistence, OS, or plugin types. Do not return `any`, throw stringly errors, or leak `std::io::Error` text.
- **Safety policy:** do not place tokens, filesystem paths requiring authorization, capability decisions, or privileged defaults in a frontend DTO.

Define structured errors with a small public code set. Map internal failures to safe messages and attach a correlation ID or diagnostic cause only when the product's approved observability policy permits it.

```rust
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct NativeError {
    pub code: String,
    pub message: String,
}

type CommandResult<T> = Result<T, NativeError>;
```

**Safety policy:** `code` is for program flow, `message` is safe for users, and neither field contains secrets, raw SQL, local paths, authorization state, or backend response bodies. Log protected diagnostics on the native side only under the project's approved logging policy.

---

## Rust command modules and state

Register commands from small domain modules through one visible composition point. Handlers should deserialize into request DTOs, validate shape and limits, authorize the operation for the current app/session context, call a domain service, and map errors to the public DTO. Keep OS, plugin, and database work behind service interfaces rather than embedding it in `#[tauri::command]` handlers.

```rust
// src-tauri/src/commands/settings.rs
#[tauri::command]
pub async fn settings_update(
    input: UpdateSettingsInput,
    state: tauri::State<'_, AppState>,
) -> CommandResult<SettingsDto> {
    input.validate()?;
    state.authorize_settings_write()?;
    state.settings.update(input).await.map_err(NativeError::from)
}
```

**Official fact.** Tauri managed state is registered with the application and can be accessed by commands as `State`. See [State Management](https://v2.tauri.app/develop/state-management/) (accessed 2026-11-04; see the evidence ledger caveat above).

- **Convention:** define `AppState` ownership and synchronization deliberately. Use `Mutex`, `RwLock`, atomics, or message passing according to the data and platform API; do not use mutable global state.
- **Safety policy:** never hold a blocking mutex, `std::sync` guard, database transaction, or other exclusive guard across `.await`. Minimize lock duration, define lock ordering where multiple locks exist, and move blocking work off the async executor according to the project runtime design.
- **Safety policy:** mutable managed state must have an explicit concurrency invariant (single writer, keyed lock, actor, transaction, or equivalent) and tests for competing operations when the command mutates durable or security-sensitive data.
- **Convention:** command handlers translate domain errors once. They do not retry indefinitely, silently coerce invalid input, or make authorization decisions from a frontend-supplied role.

---

## Choose commands, events, or channels

| Need | Use | Contract |
|---|---|---|
| Request with one final success/error result | command via adapter | Typed input, typed output, structured error; caller owns pending UI. |
| Best-effort notification or lifecycle signal | event | Named payload schema, explicit producer/consumer, and listener cleanup. Do not use it as an authorization decision or a request/response protocol. |
| Ordered multi-value progress or stream from Rust | `Channel<T>` | Typed item schema, completion/error behavior, bounded production, and consumer lifecycle. |

**Official fact.** Tauri's event system communicates events between frontend and Rust, while channels are intended for ordered data sent from Rust to the frontend. Events are implemented with commands internally, so the event API is itself gated by the event permissions (`core:event:*`) rather than by capability alone. See [Events](https://v2.tauri.app/develop/calling-frontend/), [Channels](https://v2.tauri.app/develop/calling-rust/#channels), and [IPC concept](https://v2.tauri.app/concept/inter-process-communication/) (accessed 2026-11-04; see the evidence ledger caveat above).

**Official fact.** Channels and large invoke responses have a version floor. Before Tauri `2.11.6`, large channel responses were stored in an app-wide queue under a monotonic `u32` identifier, and `plugin:__TAURI_CHANNEL__|fetch` returned an entry based only on a renderer-supplied header while bypassing the normal ACL rejection path. Any webview that could call `window.__TAURI_INTERNALS__.invoke` could guess identifiers and read or drain another webview's payload ([GHSA-w28w-mhc8-qvjv](https://github.com/tauri-apps/tauri/security/advisories/GHSA-w28w-mhc8-qvjv), High, no workaround). From `2.11.6`, entries are bound to their owning webview, identifiers are random, foreign and unknown identifiers answer identically, and stale entries are purged when the owning webview closes; `2.12.0` stops queueing large payloads for a closed webview.

**Safety policy:** a Tauri app with more than one webview, or any channel that carries sensitive native data, MUST run `2.11.6` or newer. Do not mitigate by filtering payloads in JavaScript; the queue is native state, so the upgrade is the fix.

**Safety policy:** never send credentials, tokens, or authorization decisions through a channel or event. Channel scoping protects payloads from other webviews in the same app, not from a compromised renderer that legitimately owns the channel.

**Convention:** prefer a command for a mutation's authoritative result and use an event/channel only for subsequent progress or invalidation. Do not make a route wait for an event that may have fired before subscription. Do not use an event as a secret-bearing transport.

For every event listener, retain and invoke the unlisten function during the owning lifecycle cleanup. Subscribe once per stable owner; do not register listeners during render or in a query function.

```ts
useEffect(() => {
  let unlisten: (() => void) | undefined
  let disposed = false

  void listen<Progress>('export-progress', (event) => {
    if (!disposed) updateProgress(event.payload)
  }).then((stop) => {
    if (disposed) stop()
    else unlisten = stop
  })

  return () => {
    disposed = true
    unlisten?.()
  }
}, [updateProgress])
```

**Safety policy:** validate event/channel payloads before they mutate trusted frontend state. Ensure completion, window closure, route teardown, and React Strict Mode re-mounts cannot leave duplicate listeners or a producer with no consumer.

**Official fact:** Tauri `2.12.0` removes a webview's Rust-side and JavaScript-side event listeners from the backend registry when that webview is destroyed, and stops queueing channel payloads for a closed webview. This removes a leak that previously forced manual `unlisten()` before closing a window; it does not remove the cleanup obligation for listeners that outlive a component, a route, or a re-mount while the webview stays alive.

---

## TanStack Query and cancellation

TanStack Query passes an `AbortSignal` to a query function. Aborting that signal cancels the query's client-side consumption, but it does **not** automatically cancel a Rust command already accepted by Tauri. Do not claim cancellation support merely because a query is no longer observed.

```ts
export function settingsQueryOptions() {
  return queryOptions({
    queryKey: ['settings'],
    queryFn: async ({ signal }) => {
      signal.throwIfAborted()
      const settings = await readSettings()
      signal.throwIfAborted()
      return settings
    },
  })
}
```

- **Convention:** use the signal to prevent stale UI work before and after an adapter call, and let Query manage cache invalidation.
- **Safety policy:** for expensive, destructive, or long-running native work, design an explicit job ID plus a command/channel/event lifecycle and a cooperative native cancellation command. Define idempotency, ownership, cleanup, and the outcome when cancellation races completion.
- **Convention:** query functions are reads. Route loaders/components use query options and mutations; they do not invoke native commands directly. A mutation invalidates or updates the relevant query keys only after its authoritative command result.

---

## IPC review gates

Block the change until every applicable gate is satisfied:

1. **Boundary gate:** no route, component, loader, or shared UI utility directly imports a Tauri native API; a typed domain adapter owns it.
2. **Contract gate:** each command has named input/output DTOs, frontend parsing where needed, Rust validation, structured public errors, and an explicit serialization/naming rule.
3. **Authority gate:** the Rust command validates and authorizes untrusted input independently of UI visibility, cached state, or frontend claims.
4. **Lifecycle gate:** every event/channel has an owner, payload schema, cleanup path, completion behavior, and no duplicate subscription on re-mount.
5. **Concurrency gate:** managed mutable state has a documented synchronization invariant; no lock or transaction crosses `.await`.
6. **Cancellation gate:** native work is not described as abortable unless an explicit cooperative native protocol implements and tests it.
7. **Security gate:** the custom command's capability/permission/scope review required by [security.md](security.md) is complete before exposing the adapter.
8. **Version gate:** the app runs Tauri `2.11.6` or newer whenever a channel or large invoke response crosses the boundary, and the adapter does not claim remediation that the installed version does not provide.

Do not bypass a failed gate with a type assertion, a broad catch, a frontend-only check, or an event-based workaround.

## Sources

> Links checked 2026-11-04.

| Claim | Source |
|---|---|
| Commands, events, channels, and managed `State` in the frontend-to-Rust IPC surface | [tauri-v2-2026-11-04.md](../../references/official/tauri/tauri-v2-2026-11-04.md); <https://v2.tauri.app/develop/calling-rust/>; <https://v2.tauri.app/develop/calling-frontend/>; <https://v2.tauri.app/develop/state-management/> |
| Events are implemented as commands and are gated by the event permissions | <https://v2.tauri.app/concept/inter-process-communication/> |
| The `2.11.6` channel and large-response scoping fix, and the `2.12.0` listener and queue reclamation | <https://github.com/tauri-apps/tauri/security/advisories/GHSA-w28w-mhc8-qvjv>; <https://github.com/tauri-apps/tauri/releases/tag/tauri-v2.12.0>; <https://github.com/tauri-apps/tauri/releases/tag/tauri-v2.11.6> |
| Query passes an `AbortSignal` that does not cancel a Rust command Tauri already accepted | [tanstack-vite-react-2026-11-04.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.md); <https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation>; [tauri-v2-2026-11-04.md](../../references/official/tauri/tauri-v2-2026-11-04.md) |
| DTO/error shape, listener cleanup, and managed-state concurrency requirements | This file's convention and safety policy; no external source |
