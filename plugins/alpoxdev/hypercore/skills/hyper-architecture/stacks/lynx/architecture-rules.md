# Lynx Architecture Rules

> Read before classifying a finding or enforcing a rule. This file owns the rule classes, the authority order, the blocking gates, and the target shape.

## Rule classes

- **Official**: behavior documented by Lynx, ReactLynx, or Rspeedy for the installed versions.
- **hypercore-default**: this package's stricter default, adoptable or replaceable by a recorded project decision.
- **hypercore-only**: kept as an alias of `hypercore-default` where an older file already uses that label.

Order: user and project authority, installed project evidence (manifest, `lynx.config.ts`, `tsconfig.json`), applicable official behavior, then hypercore-default.

## Target shape

```text
src/index.tsx            root.render, the only entry mount point
src/App.tsx              root component and top-level composition
src/app/                 screen-level composition per route or tab
src/features/<domain>/   feature-owned components, state, and host-data mapping
src/shared/
  ui/                    presentation primitives with no native call
  native/                the only place allowed to hold NativeModules adapters
  lynx/                  thread helpers: runOnMainThread wrappers, MainThreadRef helpers
  lib/                   focused framework-independent utilities
src/types/               InitData, GlobalProps, and IntrinsicElements augmentation
```

Dependencies point downward: `app` -> `features` -> `shared`. Features never import each other; shared never imports a feature or the entry. This layout is hypercore-default. The official template ships `src/index.tsx`, `src/App.tsx`, `src/App.css`, and `src/__tests__/` only, so a small project may legitimately stay flat.

## Blocking gates

Block or fix touched work that:

1. **Declares an `engineVersion` above the lowest engine version the shipping host runs.** A bundle whose `engineVersion` is higher than the host engine fails fatally with error 10204 instead of degrading, so the value is a deployment constraint. `pluginReactLynx` defaults to `'3.2'`, which is a floor, not a target. Read the host floor from the host project and record it next to the config.
2. **Reaches a background-only API from code that also runs on the main thread.** `NativeModules`, `lynx.getJSModule`, `lynx.createSelectorQuery`, `lynx.getElementById`, `lynx.reload`, `fetch`, timers, `requestAnimationFrame`, and `GlobalEventEmitter` belong to the background thread. A component body runs on both threads, so such a call there throws on the main thread.
3. **Binds a handler with `main-thread:` without the `'main thread';` directive**, or captures a value that is not JSON-serializable, or mutates a captured variable, or nests another main-thread function.
4. **Assumes a synchronous cross-thread result.** `runOnMainThread` and `runOnBackground` both return promises and marshal their arguments.
5. **Uses `useLayoutEffect` for measurement.** It is an alias of `useEffect` in ReactLynx, so it cannot run synchronously after layout. Use `main-thread:bindlayoutchange` with `e.detail.height` and `e.detail.width`.
6. **Renders a virtualized feed as a plain list of views.** Use `<list>` with fixed viewport dimensions, `list-type`, `span-count`, `scroll-orientation`, and one `<list-item>` per record whose `item-key` matches its `key`.
7. **Runs a build as type checking.** Rspeedy does not type check; a green `rspeedy build` with `pluginTypeCheck()` absent is unverified for types.
8. **Ships without `isolatedModules: true` or without `jsxImportSource: "@lynx-js/react"`.**
9. **Uses `document`, `window`, `<Link>`, `NavLink`, or the History API.** Lynx has no DOM and no History API; routing is memory-based.
10. **Scaffolds a new project with `create-rspeedy`.** It is a deprecation shim over `@lynx-js/create-lynx`; use `npm create @lynx-js/lynx@latest` for new projects and accept the old command only in existing repositories.

## Scalable default

- One entry, one `root.render`. A second entry exists only for a genuinely separate surface such as a web target with its own `source.entry`.
- Thread intent is visible at the call site: a file that exports main-thread handlers says so in its name and its first statement.
- Native module access funnels through `src/shared/native/`; no other file imports `NativeModules`.
- Host data is typed through `useInitData()` and `useGlobalProps()`, and the `InitData`/`GlobalProps` interfaces are augmented once under `src/types/`.
- `main-thread.js` and `background.js` are treated as two reviewable artifacts, not one bundle.

## Migration policy

Use vertical slices per screen or feature. Move one screen's handlers and native calls, update its tests, run type check and tests, then continue. Never re-cut the thread boundary across a whole app in one change; a whole-app directive pass hides regressions because a mis-split handler fails only when the main thread runs it.

## Completion gate

All blocking gates pass or are reported with the file and the failing gate. hypercore-default differences ship only with a stated reason. Verification evidence is the type-check and test output plus a production build; a performance claim additionally needs its before/after numbers.

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation and npm registry metadata read on 2026-11-07.

| Claim | Source |
|---|---|
| `engineVersion` default and the fatal 10204 failure on an older host engine | https://lynxjs.org/guide/compatibility.md, https://lynxjs.org/rspeedy/plugin.md |
| Dual-thread execution model, background-only APIs, and the both-threads component body | https://lynxjs.org/react/thinking-in-reactlynx.md, https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md |
| `'main thread'` capture rules and `runOnMainThread`/`runOnBackground` promises | https://lynxjs.org/react/main-thread-script.md, https://lynxjs.org/api/react/Document.directives.md |
| `useLayoutEffect` as an alias of `useEffect` and `main-thread:bindlayoutchange` | https://lynxjs.org/react/lifecycle.md, https://lynxjs.org/api/react/index.md |
| `<list>` attributes and fixed viewport sizing | https://lynxjs.org/api/elements/built-in/list.md |
| No type checking in the build; `isolatedModules` requirement | https://lynxjs.org/rspeedy/typescript.md |
| Memory routing and no History API | https://lynxjs.org/react/routing/react-router.md, https://lynxjs.org/react/routing/tanstack-router.md |
| `create-rspeedy` deprecation in favor of `@lynx-js/create-lynx` | https://registry.npmjs.org/create-rspeedy, https://registry.npmjs.org/@lynx-js%2Fcreate-lynx |
| Folder layout, native-wrapper boundary, and the two-artifact review habit | this package's convention, not an official Lynx requirement |
