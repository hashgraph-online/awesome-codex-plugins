# Lynx Project Structure

> folder, entry file, `source.entry`, output target, bundle과 native host 사이의 경계를 고르거나 바꿀 때 읽습니다.

## Template tree

`@lynx-js/create-lynx@0.2.1`의 공식 ReactLynx TypeScript template은 정확히 이 형태를 제공합니다.

```text
.
├── lynx.config.ts          # Rspeedy config, pluginReactLynx, type-check plugin
├── package.json            # scripts: build, dev, preview, test
├── rstest.config.ts        # withLynxConfig()를 extends
├── tsconfig.json           # strict, isolatedModules, project reference
├── tsconfig.node.json      # lynx.config.ts와 rstest.config.ts를 compile
└── src/
    ├── tsconfig.json       # jsx react-jsx, jsxImportSource @lynx-js/react
    ├── index.tsx           # 유일한 root.render 호출 지점
    ├── App.tsx
    ├── App.css
    ├── lynx-env.d.ts       # GlobalProps augmentation
    ├── assets/
    ├── lib/
    ├── useFlappy.ts
    └── __tests__/index.test.tsx
```

Root `tsconfig.json`은 자체 file이 없습니다. `tsconfig.node.json`과 `./src`에 대한 `references`를 나열하고 `files: []`를 둡니다. Program이 둘입니다. 하나는 config와 test용, 하나는 source용입니다. 이 분리를 유지합니다. Source program에는 `jsxImportSource`가 필요하고 config program에는 `node16` resolution이 필요합니다.

## Entry file

`src/index.tsx`는 tree를 mount하는 유일한 지점입니다.

```tsx
import { root } from '@lynx-js/react';

import { App } from './App.js';

root.render(<App />);

if (import.meta.webpackHot) {
  import.meta.webpackHot.accept();
}
```

틀리기 쉬운 두 가지입니다.

- Source가 `.tsx`인데도 local import에 `.js`가 붙습니다. Source program은 `moduleResolution: "Bundler"`로 해석하지만, extension을 유지하면 template과 같아지고 나중에 resolution이 바뀌어도 견딥니다.
- `import.meta.webpackHot`이 동작하는 이유는 Rspeedy가 Rspack 기반이라 webpack HMR surface가 존재하기 때문입니다. Vite API로 바꾸지 않습니다.

App이 하는 모든 일은 entry 밖에 둡니다. Feature file의 두 번째 `root.render`는 두 번째 tree를 만들어 bundle 하나에 root 하나라는 전제를 깨뜨립니다.

## `source.entry`

`source.entry`는 string, module array, record를 받습니다. Default는 `'./src/index.js'`이므로 TypeScript project는 반드시 명시합니다.

```ts
// entry 하나
source: { entry: './src/index.tsx' }

// 한 target에 entry 여럿
source: { entry: { main: './src/index.tsx', settings: './src/settings.tsx' } }

// 여러 module로 조립한 entry 하나
source: { entry: ['./src/polyfills.ts', './src/index.tsx'] }
```

Entry마다 `[name].lynx.bundle`이 생깁니다. Host가 실제로 분리된 화면을 별도 bundle로 load할 때 entry를 나눕니다. Bundle 크기를 줄이려고 나누지 않습니다. 그 일은 `rules/lynx/performance.md`의 lazy loading이 맡습니다.

## Output 배치

Production:

```text
dist/
├── [name].lynx.bundle          # 두 JS layer와 style을 한 artifact에 담음
├── async/[name].lynx.bundle    # lazy bundle
└── static/
    ├── js/[id].[hash].js
    ├── image/
    └── svg/
```

Development는 `dist/.rspeedy/[name]/` 아래에 읽을 수 있는 중간 산출물을 추가합니다. `background.js`, `main-thread.js`, `[name].css`, `tasm.json`, `debug-metadata.json`입니다. 이 skill이 검토하는 artifact 경계는 그 두 JS file입니다. `DEBUG=rspeedy rspeedy build`가 production 조사용으로 이들을 유지합니다.

`.lynx.bundle`은 두 layer를 담은 하나의 binary artifact입니다. 그래서 `engineVersion` 실수가 build 실패가 아니라 배포 실패가 됩니다. Bundle은 정상이고 host가 너무 오래된 것입니다.

## Web target

Web output은 opt-in입니다. `environments`의 default는 `{ lynx: {} }`입니다.

```ts
export default defineConfig({
  environments: { lynx: {}, web: {} },
});
```

Web build는 `dist/main.web.bundle`을 만들고 `@lynx-js/web-core`로 embed합니다.

```tsx
import '@lynx-js/web-core/client';

export const App = () => (
  <lynx-view style={{ height: '100vh', width: '100vw' }} url="/main.web.bundle" />
);
```

`lynx-view`는 `url`(필수), `globalProps`, `initData`, `pixelRatio`/`width`/`height`를 담는 `browser-config`, `transform-vw`, `transform-vh`, 그리고 `nativeModulesMap` property와 `onNativeModulesCall`을 받습니다. Bundle URL과 모든 native module URL은 network 입력으로 다룹니다.

`@lynx-js/web-core`는 engine이 4.2인데 0.26.7이고 production 준비 상태에 대한 서술을 찾지 못했습니다. Web target은 사용 가능하지만 production에 대해서는 미검증으로 보고하고 권장하지 않습니다.

## Host embedding 경계

`LynxView` 자체가 native view입니다. Host가 크기 제약을 정하고 Lynx가 그 안의 `<page>`를 배치합니다. Repository에서 경계를 명시적으로 유지합니다.

| Concern | 소유자 | 위치 |
|---|---|---|
| Engine dependency version | host app | iOS `pod 'Lynx', '<version>'`; Android `org.lynxsdk.lynx:lynx`; HarmonyOS `@lynx/primjs` artifact |
| Bundle artifact | frontend build | `dist/[name].lynx.bundle` |
| `initData`와 그 갱신 | host app | `LynxView.loadTemplate(meta.initialData)`, `setInitialData`, `MetaData(new TemplateData(...))`, 이후 `updateData`/`updateMetaData` |
| `globalProps` | host app | `lynx.__globalProps`; 없거나 `{}`일 수 있음 |
| Native module | host app이 등록하고 bundle이 호출 | `LynxEnv.inst().registerModule(...)`, `[globalConfig registerModule:...]` |
| Module 호출 권한 | host app | SDK 3.5부터의 per-`LynxView` validator |

Host가 같은 repository에 있으면 host dependency의 engine version이 `engineVersion`을 제한하는 값입니다. 없으면 host 하한을 출처와 함께 config의 `engineVersion` 옆에 기록합니다. Frontend만 있는 repository는 하한을 스스로 검증할 수 없으므로 그 사실을 밝혀야 합니다.

## Folder 소유권

App이 커지면 entry를 얇게 두고 feature로 구성합니다. 공식 template의 평평한 `src/`는 demo에 충분합니다. 화면이 셋 이상이 되면 전역 `components/` bucket보다 feature folder가 낫습니다.

```text
src/
├── index.tsx             # root.render 전용
├── App.tsx               # 최상위 composition
├── app/                  # route별 화면 composition
├── features/<domain>/    # feature component, hook, host data mapping
├── shared/
│   ├── ui/               # primitive, native 호출 없음
│   ├── native/           # NativeModules adapter 전용
│   ├── lynx/             # thread helper와 MainThreadRef utility
│   └── lib/              # 국소 utility
└── types/                # InitData, GlobalProps, IntrinsicElements augmentation
```

이 구조를 정직하게 유지하는 규칙입니다.

- Feature는 `shared`만 import합니다. 두 feature의 협력은 `app/`에서 composition으로 표현합니다.
- `shared/native/`만 `NativeModules`를 import할 수 있습니다. 그곳의 모든 호출은 background-thread 전용입니다.
- `shared/lynx/`에 `runOnMainThread`와 그 main-thread function을 짝지어 두는 wrapper를 두어 pairing을 한 번만 검토합니다.
- `src/` 바로 아래 file은 entry, root component, 그 style로 제한합니다.

이 배치는 hypercore-default이며 공식 Lynx 요구가 아닙니다.

## Naming

Project의 기존 관례를 따릅니다. 새 구조에는 kebab-case file 이름과 named export를 선호하며 framework가 다르게 요구하는 곳은 예외입니다. Main-thread handler file은 맡은 상호작용을 이름에 담습니다(`header-scroll.main-thread.ts`). Thread가 그 file의 정체성 일부이기 때문입니다.

## Checklist

- [ ] Entry가 `src/index.tsx` 형태이고 한 번만 mount하며 feature logic을 담지 않습니다.
- [ ] Project가 TypeScript이면 `source.entry`를 명시했습니다.
- [ ] 추가 entry가 크기 우회가 아니라 host가 따로 load하는 화면에 대응합니다.
- [ ] Production output을 plain JS가 아니라 `[name].lynx.bundle`과 `static/`으로 확인했습니다.
- [ ] Web target이 opt-in이고 production 미검증으로 보고됐습니다.
- [ ] Host project의 engine version이 `lynx.config.ts`의 `engineVersion`을 제한하거나, host 증거 부재를 기록했습니다.
- [ ] `initData`, `globalProps`, native module의 host 쪽 소유자가 명시됐습니다.
- [ ] Feature가 `shared`만 import하고 feature-to-feature import가 없습니다.
- [ ] `NativeModules`가 `shared/native/` 아래에만 나타납니다.

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서, `@lynx-js/create-lynx` 0.2.1 tarball, npm registry metadata를 인용합니다.

| Claim | Source |
|---|---|
| Template file 집합, entry file, `.tsx` import에 붙는 `.js` extension | https://registry.npmjs.org/@lynx-js%2Fcreate-lynx/-/create-lynx-0.2.1.tgz |
| `source.entry` 허용 형태, default 값, multi-entry 동작 | https://lynxjs.org/llms-full.txt (Rspeedy `source.entry` page) |
| Production과 development output 배치, `DEBUG=rspeedy rspeedy build` | https://lynxjs.org/rspeedy/output.md, https://lynxjs.org/guide/performance/analysis-performance/analysis-bundle-size.md |
| `environments`의 `{ lynx: {} }` default, `dist/main.web.bundle`, `lynx-view` attribute | https://lynxjs.org/guide/start/integrate-with-existing-apps.md, https://lynxjs.org/llms-full.txt (lynx-view page) |
| CocoaPods, Maven, HarmonyOS host dependency, `initData` 주입, native module 등록 | https://lynxjs.org/guide/start/integrate-with-existing-apps.md, https://lynxjs.org/guide/use-data-from-host-platform.md, https://lynxjs.org/guide/use-native-modules.md |
| `@lynx-js/web-core` 0.26.7 registry 상태와 production 준비 서술 부재 | https://registry.npmjs.org/@lynx-js%2Fweb-core |
| Folder 소유권, `shared/native/` 경계, naming 관례 | 공식 Lynx 요구가 아니라 이 패키지의 관례 |
