# Lynx Threading

> handler, effect, native 호출, cross-thread 호출, shared module을 쓰거나 검토하기 전에 읽습니다. 이 파일은 dual-thread model, directive 규칙, thread 사이를 넘을 수 있는 값을 소유합니다.

## 두 thread, 두 engine

Lynx는 application code를 두 thread에서 두 개의 분리된 JavaScript engine으로 실행합니다.

| | Main thread | Background thread |
|---|---|---|
| Engine | PrimJS (QuickJS 기반, Lynx 유지) | Android는 PrimJS, iOS는 기본적으로 JavaScriptCore |
| 최대 문법 | ES2019 (ES10) | ES2015 (ES6) |
| 실행 내용 | First screen render, patch 적용, layout, main-thread script | Component lifecycle, 모든 사용자 code, state, effect, native 호출 |
| 배포 형태 | PrimJS bytecode (text script보다 약 4배 빠르게 load) | Script |
| Polyfill | — | iOS에만 주입 |

SWC가 build 시점에 transpile하므로 문법 상한은 build 사안이고, 실행 분리는 design 사안입니다.

표에서 따라오는 규칙입니다. **Component lifecycle 관리와 사용자 code 실행은 background thread에서만 일어납니다.** Main thread는 first screen을 render하고 patch를 적용하며 main-thread script를 실행합니다. 그러나 component body 자체는 두 thread에서 실행됩니다. Main thread가 first screen 중에 그 component를 render하기 때문입니다. 이 한 가지 사실이 Lynx bug의 대부분을 만듭니다.

검토자가 알아야 하는 결과입니다.

- Component body의 `console.log`는 두 번 출력됩니다.
- Component body의 `lynx.getJSModule(...)`은 main thread에서 "not a function"으로 throw합니다.
- Module top level의 `NativeModules` 읽기는 같은 이유로 오류입니다. Background-only code 안이 아니며, 그 module은 main-thread layer에서도 평가됩니다.

이들은 `useEffect`, event handler, `'background only'` function에 둡니다.

## Directive

### `'background only'`

첫 statement가 `'background only';`인 function은 background thread에서만 실행됩니다. Main-thread 출력에서 compiler가 그 body를 `{}`로 바꿉니다.

기본적으로 background-only인 것:

- `bind*` 또는 `catch*`로 binding된 event handler.
- `useEffect`와 `useLayoutEffect` callback.
- `ref` callback과 `useImperativeHandle`.
- Directive를 단 function.
- `background-only` marker package를 import하는 module.

규칙입니다.

1. Background-only code는 background-only code에서만 호출할 수 있습니다.
2. Module top level이나 render body에서 호출하면 오류입니다.
3. Background-only code에서만 도달 가능한 code는 background-only로 추론되어 main-thread bundle에서 제거될 수 있습니다.
4. 추론이 볼 수 없어 directive를 직접 써야 하는 경우가 둘입니다. Component를 거쳐 prop으로 전달되는 event handler와 custom hook 안의 callback입니다.

`import 'background-only'`는 poison marker입니다. 이 module이 main-thread 환경에 bundle되면 throw합니다. Main thread에 절대 닿으면 안 되는 module에 붙입니다.

문서 전체에 두 표기가 나타납니다. Directive page의 공백 표기 `'background only'`와 bundle-size 및 quick-start page의 hyphen 표기입니다. 현재 compiler가 어느 쪽을 받는지는 **미확인**입니다. Function directive에는 directive page를 따르고, hyphen 표기는 두 번째 API가 아니라 문서 불일치로 다룹니다.

### `'main thread'`

첫 statement가 `'main thread';`인 function은 main thread에서 동기로 실행됩니다. 단, `main-thread:` 접두 attribute로 binding될 때만 그렇습니다.

```tsx
function handleTap(this: MainThread.Element) {
  'main thread';
  this.setStyleProperty('opacity', 0.5);
}

<view main-thread:bindtap={handleTap} />
```

접두는 background variant를 그대로 반영합니다. `main-thread:bindtap`, `main-thread:catchtap`, `main-thread:capture-bindtap`, `main-thread:capture-catchtap`, `main-thread:bindscroll`, `main-thread:global-bindscroll`, `main-thread:ref`입니다.

제약이며 모두 blocking입니다.

- 바깥 변수를 capture하면 `JSON.stringify()`로 직렬화됩니다. 모든 capture가 JSON-serializable해야 합니다.
- Capture한 변수는 read-only입니다. 변경은 state 변화가 아니며 `useMainThreadRef`를 씁니다.
- Main-thread function은 중첩할 수 없습니다.
- Class constructor, getter, setter는 main-thread function이 될 수 없습니다.
- Main-thread function은 TTI 이후에만 실행되므로 first-screen load 중에는 실행되지 않습니다.
- `event.currentTarget`과 `event.target`은 `setStyleProperty`, `invoke` 같은 method를 가진 `MainThread.Element` 객체입니다. Background handler가 받는 plain JSON과 다릅니다.
- `stopPropagation()`은 main-thread script 안에서만 동작합니다. Background thread에서는 `catch`/`capture` attribute 이름이 그 수단입니다.

`useMainThreadRef` 외의 React hook을 `'main thread'` function 안에서 호출할 수 있는지는 **미확인**입니다. 문서는 `useMainThreadRef`가 component top level에서 호출하는 hook이라 적고 main-thread function이 중첩될 수 없다고만 적으며, 일반 hook 규칙은 언급하지 않습니다. 규칙을 만들지 말고 문서에 있는 제약만 주장합니다.

## Cross-thread 호출

```ts
// background thread에서
runOnMainThread(() => {
  'main thread';
  element.setStyleProperty('transform', 'translateX(0)');
})(args);

// main thread에서
runOnBackground(updateState)(payload);
```

양방향 모두 비동기이며 argument를 marshal합니다. 동기 반환을 가정하지 않고, frame마다 또는 list item마다 호출하지 않습니다. 대신 batch하고, event가 이미 도착한 곳에서 일을 끝내는 main-thread handler를 선호합니다.

## Main-thread state

Main thread에서 읽거나 쓰는 state는 `useMainThreadRef()`에 둡니다.

```tsx
const offsetRef = useMainThreadRef<number>(0);

// Event type 이름은 @lynx-js/types에서 가져옵니다. 지어낸 alias 대신 형태를 유지합니다.
function onScroll(e) {
  'main thread';
  offsetRef.current = e.detail.scrollTop;
  headerRef.current?.setStyleProperty('opacity', String(1 - offsetRef.current / 120));
}
```

`MainThreadRef.current`는 main-thread function에서만 읽고 쓸 수 있습니다. `useMainThreadRef`는 다른 hook처럼 component top level에서 호출합니다. Background handler에서 읽으면 쓸 만한 값이 없고, main thread에서 쓴 React state는 background tree를 다시 render하지 않습니다.

## Shared module

Shared runtime으로 import한 module은 두 thread에서 호출할 수 있습니다.

```ts
import { clamp } from './math.js' with { runtime: 'shared' };
```

Import한 function이 자동으로 main-thread function이 되지는 않습니다. `MainThreadRef`를 건드리는 shared function은 여전히 directive와 `main-thread:` binding이 필요합니다. Shared module은 순수 계산에만 씁니다.

## Bundle 분리 macro

`__BACKGROUND__`와 `__MAIN_THREAD__`는 compile-time boolean이고 layer별로 죽은 branch가 제거됩니다.

```ts
const showToast = __BACKGROUND__ ? realImplementation : () => {};
```

한 module이 layer별로 다른 동작을 정당하게 가져야 할 때, 예를 들어 main thread에서 no-op이어야 하는 logger에 씁니다. Directive를 대체하지는 않습니다. Main-thread 경로에 background-only API를 참조하는 branch가 남으면 runtime에서 실패합니다.

## Thread 사이를 넘을 수 있는 값

| 항목 | Background에서 main | Main에서 background |
|---|---|---|
| JSON-serializable 값 | 가능, `runOnMainThread` 또는 capture로 | 가능, `runOnBackground`로 |
| Function | `main-thread:`로 binding된 `'main thread'` function만 | `runOnBackground`에 넘기는 background-only function만 |
| DOM 유사 node handle | 불가 | `MainThread.Element`는 main thread에만 존재 |
| Class instance, Map, Set, Date 객체 | 미확인. 불가로 보고 plain JSON으로 변환 | 같음 |
| `MainThreadRef` | 불가 | 불가. Main-thread local |
| Native module 객체 | 불가 | 불가. Native module은 background-only |

안전한 default는 JSON입니다. `JSON.stringify`와 `JSON.parse`를 거쳐 unchanged로 돌아오지 않는 값은 thread 사이로 보내지 않습니다.

## API 분리

공식 agent brief 기준 background-only:

```text
lynx.getJSModule, NativeModules, lynx.createSelectorQuery, lynx.getElementById,
lynx.reload, lynx.performance.addTimingListener/removeTimingListener/removeAllTimingListener,
fetch, setTimeout/clearTimeout, setInterval/clearInterval, requestAnimationFrame/cancelAnimationFrame,
GlobalEventEmitter
```

Main thread에는 "rendering에 영향을 주지 않는 Lynx API만 제공하며 background thread API의 부분집합"입니다. `lynx.querySelector`와 `lynx.querySelectorAll`이 main-thread selector API입니다.

`lynx.beforePublishEvent`는 background thread에서 event를 가로챕니다. WebAssembly는 3.8부터 Android에서만, background thread에서만, JS API 전면 없이 사용할 수 있습니다.

## `useLayoutEffect` 대체

ReactLynx에는 layout 이후 동기 실행 hook이 없습니다. API index는 `useLayoutEffect`를 "이제 `useEffect`의 alias"라 적고 lifecycle page는 지원하지 않는다고 적습니다. 실제 문서 불일치이며, 어느 쪽이든 layout을 측정할 수 없습니다.

대신 `main-thread:bindlayoutchange`를 씁니다.

```tsx
function onLayoutChange(e) {
  'main thread';
  const { width, height } = e.detail;
  boxRef.current?.setStyleProperty('height', `${width * 0.5}`);
}

<view main-thread:ref={boxRef} main-thread:bindlayoutchange={onLayoutChange} />
```

## 검토 절차

1. Touched file의 모든 handler, effect, ref callback, module top level statement를 찾습니다.
2. 각각에 대해 실행 thread와 callee가 요구하는 thread를 밝힙니다.
3. `main-thread:` binding마다 directive, capture, read-only 사용, 중첩 부재를 확인합니다.
4. Cross-thread 호출마다 caller가 동기 결과를 가정하지 않는지 확인합니다.
5. Main-thread function에서 쓰는 shared function마다 `with { runtime: 'shared' }` import와 `MainThreadRef` 미접촉을 확인합니다.
6. Development build의 touched module에 대해 `main-thread.js`를 확인합니다. Background-only body가 그곳에서 `{}`여야 합니다.

## Checklist

- [ ] Render body나 module top level에 `NativeModules`, `fetch`, timer, `requestAnimationFrame`, selector query 호출이 없습니다.
- [ ] 모든 `main-thread:` binding에 `'main thread';`가 첫 statement로 있습니다.
- [ ] 모든 main-thread capture가 JSON-serializable이고 read-only입니다.
- [ ] Main-thread function이 다른 main-thread function 안에 중첩되지 않았습니다.
- [ ] Class constructor, getter, setter를 main-thread function으로 선언하지 않았습니다.
- [ ] Cross-thread 호출이 promise를 await하고 item별이 아니라 batch로 묶였습니다.
- [ ] Main-thread state가 React state가 아니라 `useMainThreadRef`에 있습니다.
- [ ] Shared runtime import가 순수하고, `MainThreadRef`를 건드리면 directive를 갖습니다.
- [ ] `__BACKGROUND__`/`__MAIN_THREAD__` branch가 죽은 쪽을 완전히 제거합니다.
- [ ] 측정에 `useLayoutEffect`를 쓰지 않았습니다.
- [ ] Development build의 `main-thread.js`에서 touched module의 background-only body가 `{}`로 보입니다.

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서를 인용합니다.

| Claim | Source |
|---|---|
| 두 engine, 문법 상한, bytecode load, polyfill 분리 | https://lynxjs.org/guide/scripting-runtime/index.md, https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md |
| Background-thread 전용 lifecycle과 사용자 code, 두 thread에서 실행되는 component body | https://lynxjs.org/react/introduction.md, https://lynxjs.org/react/thinking-in-reactlynx.md |
| `'background only'` 추론 규칙, 네 가지 예외, `{}` 치환 | https://lynxjs.org/api/react/Document.directives.md, https://lynxjs.org/react/thinking-in-reactlynx.md |
| `'main thread'` capture, read-only 규칙, 중첩 금지, TTI 시점, `MainThread.Element` | https://lynxjs.org/react/main-thread-script.md, https://lynxjs.org/api/react/Document.directives.md |
| `runOnMainThread`/`runOnBackground`의 비동기성, `useMainThreadRef`, shared runtime import | https://lynxjs.org/react/main-thread-script.md |
| `__BACKGROUND__`/`__MAIN_THREAD__` compile-time macro | https://lynxjs.org/api/react/Document.built-in-macros.md |
| Background-only API 허용 목록과 main thread의 `lynx.querySelector` | https://lynxjs.org/llms.txt, https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md |
| `useLayoutEffect` alias와 `main-thread:bindlayoutchange` | https://lynxjs.org/react/lifecycle.md, https://lynxjs.org/api/react/index.md |
| `stopPropagation`이 main-thread script에서만 동작 | https://lynxjs.org/react/introduction.md |
