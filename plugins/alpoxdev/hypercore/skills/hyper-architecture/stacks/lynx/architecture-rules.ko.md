# Lynx Architecture 규칙

> finding을 분류하거나 규칙을 적용하기 전에 읽습니다. 이 파일은 규칙 분류, 권한 순서, blocking gate, 목표 구조를 소유합니다.

## 규칙 분류

- **Official**: 설치 version에 적용되는 Lynx, ReactLynx, Rspeedy 공식 문서 동작.
- **hypercore-default**: 이 패키지의 더 엄격한 기본값. 채택하거나, 기록된 project 결정으로 대체할 수 있습니다.
- **hypercore-only**: 이전 file이 이미 그 label을 쓰는 곳에서 `hypercore-default`의 alias로 유지합니다.

우선순위는 사용자와 project 권한, 설치 project 증거(manifest, `lynx.config.ts`, `tsconfig.json`), 적용 가능한 공식 동작, hypercore-default입니다.

## 목표 구조

```text
src/index.tsx            root.render, 유일한 entry mount 지점
src/App.tsx              root component와 최상위 composition
src/app/                 route 또는 tab별 화면 composition
src/features/<domain>/   feature 소유 component, state, host data mapping
src/shared/
  ui/                    native 호출이 없는 presentation primitive
  native/                NativeModules adapter를 둘 수 있는 유일한 위치
  lynx/                  thread helper: runOnMainThread wrapper, MainThreadRef helper
  lib/                   framework에 독립적인 국소 utility
src/types/               InitData, GlobalProps, IntrinsicElements augmentation
```

Dependency는 아래로 향합니다. `app` -> `features` -> `shared`입니다. Feature끼리 import하지 않고, shared는 feature나 entry를 import하지 않습니다. 이 배치는 hypercore-default입니다. 공식 template은 `src/index.tsx`, `src/App.tsx`, `src/App.css`, `src/__tests__/`만 제공하므로 작은 project는 평평하게 유지해도 됩니다.

## Blocking gate

다음 touched work는 block하거나 수정합니다.

1. **출시 host가 실행하는 가장 낮은 engine version보다 높은 `engineVersion`을 선언함.** `engineVersion`이 host engine보다 높은 bundle은 성능을 낮추는 대신 fatal error 10204로 실패하므로 이 값은 배포 제약입니다. `pluginReactLynx`의 default는 `'3.2'`이며 이는 하한이지 target이 아닙니다. Host project에서 하한을 읽어 config 옆에 기록합니다.
2. **main thread에서도 실행되는 code가 background-only API에 닿음.** `NativeModules`, `lynx.getJSModule`, `lynx.createSelectorQuery`, `lynx.getElementById`, `lynx.reload`, `fetch`, timer, `requestAnimationFrame`, `GlobalEventEmitter`는 background thread 소속입니다. Component body는 두 thread에서 실행되므로 그 자리에서 호출하면 main thread에서 throw합니다.
3. **`'main thread';` directive 없이 `main-thread:`로 handler를 binding함**, 또는 JSON-serializable하지 않은 값을 capture함, 또는 capture한 변수를 변경함, 또는 main-thread function을 중첩함.
4. **Cross-thread 결과를 동기로 가정함.** `runOnMainThread`와 `runOnBackground`는 모두 promise를 반환하고 argument를 marshal합니다.
5. **측정에 `useLayoutEffect`를 씀.** ReactLynx에서는 `useEffect`의 alias이므로 layout 이후 동기 실행이 불가능합니다. `e.detail.height`와 `e.detail.width`를 읽는 `main-thread:bindlayoutchange`를 씁니다.
6. **virtualized feed를 view 목록으로 rendering함.** 고정 viewport 크기, `list-type`, `span-count`, `scroll-orientation`, 그리고 `key`와 일치하는 `item-key`를 가진 `<list-item>`을 갖춘 `<list>`를 씁니다.
7. **build를 type checking으로 취급함.** Rspeedy는 type check를 하지 않습니다. `pluginTypeCheck()` 없이 통과한 `rspeedy build`는 type에 대해 검증되지 않았습니다.
8. **`isolatedModules: true` 또는 `jsxImportSource: "@lynx-js/react"` 없이 출시함.**
9. **`document`, `window`, `<Link>`, `NavLink`, History API를 씀.** Lynx에는 DOM도 History API도 없고 routing은 memory 기반입니다.
10. **새 project를 `create-rspeedy`로 scaffold함.** `@lynx-js/create-lynx` 위의 deprecation shim입니다. 새 project는 `npm create @lynx-js/lynx@latest`를 쓰고, 기존 repository에서만 예전 command를 허용합니다.

## 확장 가능한 기본값

- Entry 하나, `root.render` 하나. 두 번째 entry는 web target이 자체 `source.entry`를 갖는 것처럼 실제로 분리된 surface에만 존재합니다.
- Thread 의도가 호출 지점에서 보입니다. main-thread handler를 export하는 file은 이름과 첫 statement에서 그 사실을 밝힙니다.
- Native module 접근은 `src/shared/native/`로 모읍니다. 다른 file은 `NativeModules`를 import하지 않습니다.
- Host data는 `useInitData()`와 `useGlobalProps()`로 typing하고, `InitData`/`GlobalProps` interface는 `src/types/`에서 한 번만 augment합니다.
- `main-thread.js`와 `background.js`를 하나의 bundle이 아니라 검토 대상 두 artifact로 다룹니다.

## Migration 정책

화면 또는 feature 단위 vertical slice를 씁니다. 한 화면의 handler와 native 호출을 옮기고, 그 test를 갱신하고, type check와 test를 돌린 뒤 계속합니다. Thread 경계를 app 전체에서 한 번에 다시 긋지 않습니다. 잘못 나눈 handler는 main thread가 실행할 때만 실패하므로, 전면 directive 작업은 regression을 숨깁니다.

## 완료 gate

모든 blocking gate가 통과하거나 file과 실패 gate를 함께 보고합니다. hypercore-default 차이는 이유를 밝혀야 출시할 수 있습니다. 검증 증거는 type-check와 test 출력, production build입니다. 성능 주장에는 before/after 수치가 추가로 필요합니다.

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서와 npm registry metadata를 인용합니다.

| Claim | Source |
|---|---|
| `engineVersion` default와 구형 host engine에서의 fatal 10204 | https://lynxjs.org/guide/compatibility.md, https://lynxjs.org/rspeedy/plugin.md |
| Dual-thread 실행 model, background-only API, 두 thread에서 실행되는 component body | https://lynxjs.org/react/thinking-in-reactlynx.md, https://lynxjs.org/guide/scripting-runtime/main-thread-runtime.md |
| `'main thread'` capture 규칙과 `runOnMainThread`/`runOnBackground` promise | https://lynxjs.org/react/main-thread-script.md, https://lynxjs.org/api/react/Document.directives.md |
| `useLayoutEffect`가 `useEffect`의 alias라는 점과 `main-thread:bindlayoutchange` | https://lynxjs.org/react/lifecycle.md, https://lynxjs.org/api/react/index.md |
| `<list>` attribute와 고정 viewport 크기 | https://lynxjs.org/api/elements/built-in/list.md |
| Build에서 type check를 하지 않음, `isolatedModules` 요구 | https://lynxjs.org/rspeedy/typescript.md |
| Memory routing과 History API 부재 | https://lynxjs.org/react/routing/react-router.md, https://lynxjs.org/react/routing/tanstack-router.md |
| `create-rspeedy` deprecation과 `@lynx-js/create-lynx` | https://registry.npmjs.org/create-rspeedy, https://registry.npmjs.org/@lynx-js%2Fcreate-lynx |
| Folder 배치, native wrapper 경계, 두 artifact 검토 습관 | 공식 Lynx 요구가 아니라 이 패키지의 관례 |
