# Lynx Testing

> test를 추가하거나 검토하고, test runner를 바꾸고, Lynx 변경을 검증됐다고 주장하기 전에 읽습니다.

## Template이 제공하는 것

공식 ReactLynx TypeScript template은 Rstest를 실행합니다.

```ts
// rstest.config.ts
import { withLynxConfig } from '@lynx-js/react/testing-library/rstest-config';
import { defineConfig } from '@rstest/core';

export default defineConfig({
  extends: withLynxConfig(),
});
```

`withLynxConfig()`는 app의 실제 `lynx.config.ts`를 재사용하므로 test가 build와 같은 alias, plugin, `engineVersion`을 봅니다. Test가 app config를 상속하면 안 될 때는 `withDefaultConfig()`가 대안입니다. Template은 `jsdom`과 `@testing-library/jest-dom`도 설치합니다.

`package.json` script는 `build: rspeedy build`, `dev: rspeedy dev`, `preview: rspeedy preview`, `test: rstest run`입니다.

## Testing library

`@lynx-js/react/testing-library`는 `@lynx-js/react` package 안에 `./testing-library` export로 들어 있습니다. React Testing Library를 그대로 반영하며 `render`, `fireEvent`, `screen`을 제공하고, `@lynx-js/testing-environment`로 dual thread를 한 process에서 emulation합니다.

Runner 둘을 지원합니다.

| Runner | 설정 |
|---|---|
| Rstest | `@lynx-js/react/testing-library/rstest-config`의 `withDefaultConfig()` 또는 `withLynxConfig()`를 `extends`에 |
| Vitest | `@lynx-js/react/testing-library/plugins`의 `vitestTestingLibraryPlugin()`을 `plugins`에 |

App test에는 실제 build config를 재사용하는 Rstest와 `withLynxConfig()`를 선호합니다. Vitest는 repository가 이미 그것을 표준으로 삼았을 때만 씁니다.

## Event

Attribute 의미와 맞는 typed event 이름으로 발생시킵니다.

```ts
fireEvent(element, new Event('bindEvent:tap'));
fireEvent(element, new Event('catchEvent:tap'));
fireEvent(element, new Event('capture-bind:tap'));
fireEvent(element, new Event('capture-catch:tap'));

// 흔한 경우의 shorthand
fireEvent.tap(element);
```

Element PAPI를 JSDOM에서 emulation하므로 `@testing-library/jest-dom` matcher가 동작합니다. 그 말은 test가 JavaScript와 element 의미를 증명하고 native rendering은 증명하지 않는다는 뜻입니다. 통과한 test가 device에서 `<list>`가 정확히 recycle되는 것을 증명하지는 않습니다.

## 무엇을 test하는가

화면 또는 feature마다 다음을 둡니다.

1. 주어진 `initData`에서 초기 tree를 확인하는 render test.
2. 화면이 실제로 binding한 handler를 발생시키는 event test.
3. 없거나 일부만 있는 `initData`, 갱신된 `initData`, `globalProps`가 `null` 또는 `{}`인 경우의 host data test.
4. `main-thread:` handler가 있으면 그 handler의 thread test. Directive는 binding을 통해서만 적용되므로 handler를 직접 호출하지 말고 보이는 결과를 확인합니다.
5. `item-key`와 `key`가 일치하고 주어진 data로 row가 render되는지 확인하는 list test.

감추지 말고 밝혀야 하는 test 한계입니다.

- Dual-thread emulation은 JavaScript emulation입니다. PrimJS/JSC 동작 차이, bytecode load, 실제 main-thread timing bug를 증명하지 않습니다.
- Test는 `engineVersion` 호환성을 증명할 수 없습니다. 그건 host version 사실이고 unit test가 아니라 host와 대조해 확인합니다.
- Native module은 test 환경에 없습니다. `NativeModules`가 아니라 `src/shared/native/`의 adapter를 mock합니다. 그래야 mock이 app이 실제로 쓰는 경계에 놓입니다.

## Type checking

Rspeedy는 type check를 하지 않습니다. "Type checking is not performed"가 문서화된 동작이므로 통과한 `rspeedy build`는 type에 대해 아무 말도 하지 않습니다.

명시적으로 연결합니다.

```ts
import { pluginTypeCheck } from '@rsbuild/plugin-type-check';

pluginTypeCheck({ enable: true });
```

공식 template은 이미 `@rsbuild/plugin-type-check`를 포함하고 `pluginTypeCheck()`를 호출합니다.

중요한 TypeScript 설정입니다.

- `isolatedModules: true`가 필요합니다. SWC가 file 단위로 compile하기 때문입니다.
- Source program에 `jsx: "react-jsx"`와 `jsxImportSource: "@lynx-js/react"`가 필요합니다.
- Source는 `moduleResolution: "Bundler"`, config program은 `node16`입니다.
- `strict`, `verbatimModuleSyntax`, `esModuleInterop`, `skipLibCheck`가 template default입니다.

`isolatedModules`가 켜져 있으므로 `export type { X }`와 `import type`은 style 선택이 아닙니다. 표시하지 않은 type re-export는 build를 실패시킵니다.

## Check 순서

1. Project 자체 command로 type check합니다(`tsc -b`로 referenced program을 검사하거나 repo가 정의한 script).
2. Unit과 component test에 `rstest run`을 실행합니다.
3. `rspeedy build`로 production bundle이 여전히 build되는지 확인합니다.
4. Threading, list, native module, `engineVersion`을 건드린 변경이면 device 또는 Lynx Explorer에서 실행합니다. Test suite가 이를 대신하지 못합니다.

실행하지 못한 단계와 이유를 보고합니다. 일어나지 않은 device 확인을 주장하지 않습니다.

## Checklist

- [ ] Test runner가 `withLynxConfig()`를 쓰는 Rstest이거나, 근거가 있는 Vitest입니다.
- [ ] `pluginTypeCheck()`가 설정됐고 type check가 check 순서에 들어 있습니다.
- [ ] `isolatedModules: true`와 `jsxImportSource: "@lynx-js/react"`가 있습니다.
- [ ] Touched 화면에 render test와 event test가 있습니다.
- [ ] Host data test가 없거나 일부만 있는 `initData`와 없는 `globalProps`를 다룹니다.
- [ ] Main-thread handler test가 직접 호출이 아니라 binding을 통해 확인합니다.
- [ ] List test가 `item-key`와 `key` 일치를 확인합니다.
- [ ] Native module을 `NativeModules`가 아니라 `src/shared/native/` adapter에서 mock합니다.
- [ ] 보고에 unit test가 증명할 수 없는 것(device 동작, engine 호환성, 실제 timing)을 밝혔습니다.

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서, `@lynx-js/create-lynx` 0.2.1 tarball, npm registry metadata를 인용합니다.

| Claim | Source |
|---|---|
| `@lynx-js/react/testing-library`, Rstest와 Vitest 설정, typed event 이름 | https://lynxjs.org/react/reactlynx-testing-library.md |
| `@lynx-js/testing-environment`의 dual thread emulation | https://registry.npmjs.org/@lynx-js%2Ftesting-environment, https://registry.npmjs.org/@lynx-js%2Freact |
| 제공되는 `rstest.config.ts`, template script, `@rstest/core` | https://registry.npmjs.org/@lynx-js%2Fcreate-lynx/-/create-lynx-0.2.1.tgz |
| Build에서 type check를 하지 않음, `pluginTypeCheck`, `isolatedModules` 요구 | https://lynxjs.org/rspeedy/typescript.md |
| JSDOM element PAPI emulation과 `jest-dom` matcher | https://lynxjs.org/react/reactlynx-testing-library.md |
| 경계 mock과 device 증거 요구 | 공식 Lynx 요구가 아니라 이 패키지의 관례 |
