# Lynx Threading

> Read before writing or reviewing any handler, effect, native call, cross-thread call, or shared module. This file owns the dual-thread model, the directive rules, and what may cross threads.

## Two threads, two engines

Lynx runs application code on two threads with two separate JavaScript engines.

| | Main thread | Background thread |
|---|---|---|
| Engine | PrimJS (QuickJS-based, Lynx maintained) | PrimJS on Android; JavaScriptCore on iOS by default |
| Max syntax | ES2019 (ES10) | ES2015 (ES6) |
| What runs | First-screen render, patch application, layout, main-thread scripts | Component lifecycle, all user code, state, effects, native calls |
| Ships as | PrimJS bytecode (loads roughly four times faster than text scripts) | Script |
| Polyfills | — | Injected on iOS only |

SWC transpiles at build time, so the syntax ceilings are build concerns; the execution split is a design concern.

The rule that follows from the table: **component lifecycle management and user code execution only happen on the background thread.** The main thread renders the first screen, applies patches, and runs main-thread scripts. But a component body itself runs on both threads, because the main thread renders it during first screen. That single fact produces most Lynx bugs.

Consequences a reviewer must know:

- `console.log` in a component body prints twice.
- `lynx.getJSModule(...)` in a component body throws "not a function" on the main thread.
- A module top-level `NativeModules` read is an error for the same reason: it is not inside background-only code, and the module also evaluates in the main-thread layer.

Put those in `useEffect`, an event handler, or a `'background only'` function.

## Directives

### `'background only'`

A function whose first statement is `'background only';` runs only on the background thread. In the main-thread output the compiler replaces its body with `{}`.

Background-only by default:

- Event handlers bound with `bind*` or `catch*`.
- `useEffect` and `useLayoutEffect` callbacks.
- `ref` callbacks and `useImperativeHandle`.
- Functions carrying the directive.
- Modules importing the `background-only` marker package.

Rules:

1. Background-only code may only be called from background-only code.
2. Calling it at module top level or in a render body is an error.
3. Code reachable only from background-only code is inferred as background-only and can be dropped from the main-thread bundle.
4. Two cases need the directive written by hand because inference cannot see them: an event handler passed as a prop through a component, and a callback inside a custom hook.

`import 'background-only'` is a poison marker: the module throws if it is ever bundled into a main-thread environment. Use it on a module that must never reach the main thread.

Both spellings appear across the documentation — the space form `'background only'` in the directive page and the hyphen form in the bundle-size and quick-start pages. Which one the compiler accepts today is **unverified**; follow the directive page for function directives and treat any hyphen form as a doc inconsistency rather than a second API.

### `'main thread'`

A function whose first statement is `'main thread';` runs synchronously on the main thread, but only when it is bound with a `main-thread:` prefixed attribute.

```tsx
function handleTap(this: MainThread.Element) {
  'main thread';
  this.setStyleProperty('opacity', 0.5);
}

<view main-thread:bindtap={handleTap} />
```

The prefixes mirror the background variants: `main-thread:bindtap`, `main-thread:catchtap`, `main-thread:capture-bindtap`, `main-thread:capture-catchtap`, `main-thread:bindscroll`, `main-thread:global-bindscroll`, and `main-thread:ref`.

Constraints, all blocking:

- Captured outer variables are serialized with `JSON.stringify()`, so every capture must be JSON-serializable.
- Captured variables are read-only. Mutating one is not a state change; use `useMainThreadRef`.
- Main-thread functions cannot be nested.
- A class constructor, getter, or setter cannot be a main-thread function.
- Main-thread functions run only after TTI, so they cannot run during first-screen load.
- `event.currentTarget` and `event.target` are `MainThread.Element` objects with methods such as `setStyleProperty` and `invoke`, not plain JSON like a background handler receives.
- `stopPropagation()` works only inside a main-thread script; on the background thread the `catch`/`capture` attribute naming is the mechanism.

Whether React hooks other than `useMainThreadRef` may be called inside a `'main thread'` function is **unverified**. The documentation states that `useMainThreadRef` is a hook called at component top level and that main-thread functions cannot be nested, but it never states a general hook rule. Do not invent one; assert only the documented constraints.

## Cross-thread calls

```ts
// from the background thread
runOnMainThread(() => {
  'main thread';
  element.setStyleProperty('transform', 'translateX(0)');
})(args);

// from the main thread
runOnBackground(updateState)(payload);
```

Both directions are asynchronous and marshal their arguments. Never assume a synchronous return, and never call one per frame or per list item. Batch instead, and prefer a main-thread handler that does the work where the event already arrives.

## Main-thread state

State read or written on the main thread lives in `useMainThreadRef()`:

```tsx
const offsetRef = useMainThreadRef<number>(0);

// The event type name comes from @lynx-js/types; keep the shape, not an invented alias.
function onScroll(e) {
  'main thread';
  offsetRef.current = e.detail.scrollTop;
  headerRef.current?.setStyleProperty('opacity', String(1 - offsetRef.current / 120));
}
```

`MainThreadRef.current` is readable and writable only in main-thread functions. `useMainThreadRef` is called at component top level like any other hook. Reading it from a background handler gives nothing useful, and React state written on the main thread does not re-render the background tree.

## Shared modules

A module imported with the shared runtime can be called from both threads:

```ts
import { clamp } from './math.js' with { runtime: 'shared' };
```

Imported functions are not automatically main-thread functions. A shared function that touches a `MainThreadRef` still needs the directive and a `main-thread:` binding. Use shared modules for pure computation only.

## Bundle-split macros

`__BACKGROUND__` and `__MAIN_THREAD__` are compile-time booleans; the dead branch is removed per layer.

```ts
const showToast = __BACKGROUND__ ? realImplementation : () => {};
```

Use them when a single module legitimately needs different behavior per layer, such as a logger that must be a no-op on the main thread. They are not a substitute for the directive: a branch that still references a background-only API in the main-thread path fails at runtime.

## What may cross threads

| Item | Background to main | Main to background |
|---|---|---|
| JSON-serializable values | yes, via `runOnMainThread` or a capture | yes, via `runOnBackground` |
| Functions | only as a `'main thread'` function bound with `main-thread:` | only as a background-only function passed to `runOnBackground` |
| DOM-like node handles | no | `MainThread.Element` exists only on the main thread |
| Class instances, Map, Set, Date objects | unverified; assume no and convert to plain JSON | same |
| `MainThreadRef` | no | no; it is main-thread-local |
| Native module objects | no | no; native modules are background-only |

The safe default is JSON: if a value cannot survive `JSON.stringify` and `JSON.parse` unchanged, do not send it across.

## API split

Background-only, per the official agent brief:

```text
lynx.getJSModule, NativeModules, lynx.createSelectorQuery, lynx.getElementById,
lynx.reload, lynx.performance.addTimingListener/removeTimingListener/removeAllTimingListener,
fetch, setTimeout/clearTimeout, setInterval/clearInterval, requestAnimationFrame/cancelAnimationFrame,
GlobalEventEmitter
```

Main thread: "we only provide Lynx APIs in the main thread that do not affect rendering, which are a subset of the background thread APIs." `lynx.querySelector` and `lynx.querySelectorAll` are the main-thread selector APIs.

`lynx.beforePublishEvent` intercepts events on the background thread. WebAssembly is available from 3.8 on Android only, on the background thread only, without the full JS API surface.

## `useLayoutEffect` replacement

ReactLynx does not provide a synchronous-after-layout hook. The API index calls `useLayoutEffect` "an alias of `useEffect`" while the lifecycle page calls it unsupported — a real documentation inconsistency, and either way it cannot measure layout.

Use `main-thread:bindlayoutchange` instead:

```tsx
function onLayoutChange(e) {
  'main thread';
  const { width, height } = e.detail;
  boxRef.current?.setStyleProperty('height', `${width * 0.5}`);
}

<view main-thread:ref={boxRef} main-thread:bindlayoutchange={onLayoutChange} />
```

## Review procedure

1. Find every handler, effect, ref callback, and module top-level statement in the touched files.
2. For each, name the thread it runs on and the thread its callees require.
3. For each `main-thread:` binding, check the directive, the captures, read-only use, and no nesting.
4. For each cross-thread call, check that the caller does not assume a synchronous result.
5. For each imported shared function used from a main-thread function, check the `with { runtime: 'shared' }` import and that it touches no `MainThreadRef`.
6. Check `main-thread.js` in a development build for the touched module: background-only bodies must be `{}` there.

## Checklist

- [ ] No `NativeModules`, `fetch`, timer, `requestAnimationFrame`, or selector-query call in a render body or module top level.
- [ ] Every `main-thread:` binding has `'main thread';` as the first statement.
- [ ] Every main-thread capture is JSON-serializable and read-only.
- [ ] No main-thread function is nested inside another.
- [ ] No class constructor, getter, or setter is declared as a main-thread function.
- [ ] Cross-thread calls await their promise and are batched, not per-item.
- [ ] Main-thread state lives in `useMainThreadRef`, not in React state.
- [ ] Shared-runtime imports are pure and still carry a directive when they touch a `MainThreadRef`.
- [ ] `__BACKGROUND__`/`__MAIN_THREAD__` branches remove the dead side entirely.
- [ ] No `useLayoutEffect` is used for measurement.
- [ ] The development build's `main-thread.js` shows background-only bodies as `{}` for the touched module.

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation read on 2026-11-07.

| Claim | Source |
|---|---|
| Two engines, syntax ceilings, bytecode loading, and the polyfill split | https://lynxjs.org/guide/scripting-runtime/index.md, https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md |
| Background-thread-only lifecycle and user code; component bodies running on both threads | https://lynxjs.org/react/introduction.md, https://lynxjs.org/react/thinking-in-reactlynx.md |
| `'background only'` inference rules, the four exceptions, and the `{}` replacement | https://lynxjs.org/api/react/Document.directives.md, https://lynxjs.org/react/thinking-in-reactlynx.md |
| `'main thread'` captures, read-only rule, no nesting, TTI timing, `MainThread.Element` | https://lynxjs.org/react/main-thread-script.md, https://lynxjs.org/api/react/Document.directives.md |
| `runOnMainThread`/`runOnBackground` being async, `useMainThreadRef`, and shared-runtime imports | https://lynxjs.org/react/main-thread-script.md |
| `__BACKGROUND__`/`__MAIN_THREAD__` compile-time macros | https://lynxjs.org/api/react/Document.built-in-macros.md |
| The background-only API allow-list and `lynx.querySelector` on the main thread | https://lynxjs.org/llms.txt, https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md |
| `useLayoutEffect` alias and `main-thread:bindlayoutchange` | https://lynxjs.org/react/lifecycle.md, https://lynxjs.org/api/react/index.md |
| `stopPropagation` only in main-thread scripts | https://lynxjs.org/react/introduction.md |
