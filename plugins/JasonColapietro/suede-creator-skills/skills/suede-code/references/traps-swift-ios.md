# Swift and iOS Traps

Swift and SwiftUI failure catalog plus the native contract drift checks that catch a client and server disagreeing about a payload.

## Swift / iOS Traps

Check on every Swift file in the diff. iOS ships on a release cycle with no hot-fix: a crash here is live for days.

- **Force operations (`!`, `try!`, `as!`):** each crashes when the optional is nil or the cast fails. Flag unless the failure case is provably eliminated immediately above. `try!` on anything that throws at runtime (decoding, file I/O) is P1.
- **Retain cycles in closures:** an escaping closure that strongly captures `self` inside a stored property, `Task`, Combine sink, or callback leaks the owner. Require `[weak self]` (or `[unowned self]` only when lifetime is provably bound).
- **UI work off the main thread:** mutating `@State`, `@Published`, or UIKit views from a background context is undefined behavior. Flag observable or UI mutation inside `Task.detached`, a URLSession callback, or a background queue with no hop to `@MainActor` / `DispatchQueue.main`.
- **Actor and concurrency misuse:** actor-isolated state mutated across a suspension point without re-checking invariants (reentrancy); `nonisolated` used to silence a warning rather than because access is truly isolation-free; `@MainActor` work awaited from a path that should already be on main.
- **Codable fragility:** a non-optional property decoding a field the server may omit or send null fails the whole decode and drops the response. Match optionality to the real API contract; flag `decode` on fields the backend does not guarantee.
- **SwiftUI identity and lifecycle:** `ForEach` over a non-stable `id` (index, or a value that changes) loses state and breaks animations; `onAppear` used for one-time work re-fires on re-insertion; `@StateObject` vs `@ObservedObject` confusion (owning vs observing) re-creates or prematurely releases models.
- **Leaked resources:** unbounded image/data caches; URLSession tasks not cancelled on disappearance; observers or timers added with no matching removal.

Pair with iOS / Native Contract Drift below: crash risk here, contract break there.

## iOS / Native Contract Drift

Check on any API route, response shape, auth header, or shared type that iOS or other native consumers depend on:

- **Response shape change:** field renamed, field removed, field type changed (string → number, nullable → required), or new required field added without a default. Flag any change to an API route's return value that is not purely additive and backward-compatible.
- **Route path or method change:** endpoint renamed, HTTP method changed (POST → PUT), or path parameters reordered. iOS has no hot-reload: a renamed route is a hard crash until the app ships an update.
- **Auth header or token format change:** changes to how `Authorization`, `X-Session-Token`, or similar headers are validated server-side. If the server changes the expected format, the iOS app gets 401s on every request.
- **Error response shape change:** iOS likely pattern-matches on `{ error: string }` or `{ code: number }`. Changing the error envelope silently breaks native error handling with no visible failure on the web surface.
- **New required query param or body field:** adding a required field that old app versions don't send causes the new server to reject requests from users who haven't updated yet.
- **Shared type drift:** TypeScript types in `types/`, `shared/`, or `lib/` consumed by both web and a native build step. A field rename or removal here breaks both surfaces simultaneously.

Blast radius note: identify which iOS version is currently in production. If the app hasn't shipped an update in >2 weeks, assume the old contract is live for the majority of users and treat breaking changes as P0.
