# Lynx Project Structure

> Read when choosing or changing folders, entry files, `source.entry`, output targets, or the boundary between the bundle and the native host.

## Template tree

The official ReactLynx TypeScript template from `@lynx-js/create-lynx@0.2.1` ships exactly this shape:

```text
.
├── lynx.config.ts          # Rspeedy config, pluginReactLynx, type-check plugin
├── package.json            # scripts: build, dev, preview, test
├── rstest.config.ts        # extends withLynxConfig()
├── tsconfig.json           # strict, isolatedModules, project references
├── tsconfig.node.json      # compiles lynx.config.ts and rstest.config.ts
└── src/
    ├── tsconfig.json       # jsx react-jsx, jsxImportSource @lynx-js/react
    ├── index.tsx           # the only root.render call site
    ├── App.tsx
    ├── App.css
    ├── lynx-env.d.ts       # GlobalProps augmentation
    ├── assets/
    ├── lib/
    ├── useFlappy.ts
    └── __tests__/index.test.tsx
```

The root `tsconfig.json` holds no files of its own; it lists `references` to `tsconfig.node.json` and `./src` and sets `files: []`. Two separate programs, one for config and tests, one for source. Keep that split: the source program needs `jsxImportSource`, the config program needs `node16` resolution.

## Entry file

`src/index.tsx` is the only place that mounts a tree:

```tsx
import { root } from '@lynx-js/react';

import { App } from './App.js';

root.render(<App />);

if (import.meta.webpackHot) {
  import.meta.webpackHot.accept();
}
```

Two details that are easy to get wrong:

- The local import carries `.js` even though the source is `.tsx`. The source program resolves with `moduleResolution: "Bundler"`, but keeping the extension matches the template and survives a later resolution change.
- `import.meta.webpackHot` works because Rspeedy is Rspack-based; the webpack HMR surface is present. Do not replace it with a Vite API.

Everything the app does belongs outside the entry. A second `root.render` in a feature file creates a second tree and breaks the assumption that one bundle has one root.

## `source.entry`

`source.entry` accepts a string, an array of modules, or a record. The default is `'./src/index.js'`, so a TypeScript project must state it.

```ts
// one entry
source: { entry: './src/index.tsx' }

// several entries in one target
source: { entry: { main: './src/index.tsx', settings: './src/settings.tsx' } }

// one entry assembled from several modules
source: { entry: ['./src/polyfills.ts', './src/index.tsx'] }
```

Each entry produces its own `[name].lynx.bundle`. Use several entries when the host loads genuinely different screens as separate bundles, not to reduce a single app's bundle size — that is lazy loading's job, in `rules/lynx/performance.md`.

## Output layout

Production:

```text
dist/
├── [name].lynx.bundle          # both JS layers plus styles in one artifact
├── async/[name].lynx.bundle    # lazy bundles
└── static/
    ├── js/[id].[hash].js
    ├── image/
    └── svg/
```

Development adds readable intermediates under `dist/.rspeedy/[name]/`: `background.js`, `main-thread.js`, `[name].css`, `tasm.json`, `debug-metadata.json`. Those two JS files are the artifact boundary this skill reviews; `DEBUG=rspeedy rspeedy build` keeps them for a production investigation.

A `.lynx.bundle` is one binary artifact holding both layers. That is why an `engineVersion` mistake is a deployment failure rather than a build failure: the bundle is valid, the host is too old.

## Web target

The web output is opt-in. `environments` defaults to `{ lynx: {} }`.

```ts
export default defineConfig({
  environments: { lynx: {}, web: {} },
});
```

The web build emits `dist/main.web.bundle`, embedded through `@lynx-js/web-core`:

```tsx
import '@lynx-js/web-core/client';

export const App = () => (
  <lynx-view style={{ height: '100vh', width: '100vw' }} url="/main.web.bundle" />
);
```

`lynx-view` accepts `url` (required), `globalProps`, `initData`, `browser-config` with `pixelRatio`/`width`/`height`, `transform-vw`, and `transform-vh`, plus the `nativeModulesMap` property and `onNativeModulesCall`. Treat the bundle URL and every native-module URL as network input.

`@lynx-js/web-core` is at 0.26.7 while the engine is 4.2, and no production-readiness statement was found. Report a web target as available but unverified for production rather than recommending it.

## Host embedding boundary

`LynxView` is itself a native view. The host decides its size constraints; Lynx lays out the `<page>` inside. Keep the boundary explicit in the repository:

| Concern | Owner | Where it lives |
|---|---|---|
| Engine dependency version | host app | iOS `pod 'Lynx', '<version>'`; Android `org.lynxsdk.lynx:lynx`; HarmonyOS `@lynx/primjs` artifacts |
| Bundle artifact | frontend build | `dist/[name].lynx.bundle` |
| `initData` and its updates | host app | `LynxView.loadTemplate(meta.initialData)`, `setInitialData`, `MetaData(new TemplateData(...))`, later `updateData`/`updateMetaData` |
| `globalProps` | host app | `lynx.__globalProps`; may be absent or `{}` |
| Native modules | host app registers, bundle calls | `LynxEnv.inst().registerModule(...)`, `[globalConfig registerModule:...]` |
| Module call authorization | host app | per-`LynxView` validator from SDK 3.5 |

When the host lives in the same repository, the engine version in the host dependency must be the value that bounds `engineVersion`. When it does not, record the host floor in the config next to `engineVersion` with its source. A frontend-only repository cannot verify the floor by itself and must say so.

## Folder ownership

For a growing app, keep the entry thin and organize by feature. The official template's flat `src/` is fine for a demo; once there are three or more screens, feature folders beat a global `components/` bucket.

```text
src/
├── index.tsx             # root.render only
├── App.tsx               # top-level composition
├── app/                  # screen composition per route
├── features/<domain>/    # feature components, hooks, host-data mapping
├── shared/
│   ├── ui/               # primitives, no native call
│   ├── native/           # the only NativeModules adapters
│   ├── lynx/             # thread helpers and MainThreadRef utilities
│   └── lib/              # focused utilities
└── types/                # InitData, GlobalProps, IntrinsicElements augmentation
```

Rules that keep this honest:

- A feature imports only `shared`. Two features coordinating is composition in `app/`.
- `shared/native/` is the only folder allowed to import `NativeModules`. Every call there is background-thread only.
- `shared/lynx/` holds the wrapper that pairs `runOnMainThread` with its main-thread function so the pairing is reviewed once.
- Files directly under `src/` stay limited to the entry, the root component, and its styles.

This layout is hypercore-default, not an official Lynx requirement.

## Naming

Follow the project's existing convention. For a new structure prefer kebab-case file names and named exports, except where the framework requires otherwise. A main-thread handler file states the interaction it serves (`header-scroll.main-thread.ts`), because the thread is part of what the file is.

## Checklist

- [ ] The entry is `src/index.tsx`-style, mounts once, and holds no feature logic.
- [ ] `source.entry` is stated explicitly when the project is TypeScript.
- [ ] Every extra entry maps to a screen the host loads separately, not to a size workaround.
- [ ] Production output was inspected as `[name].lynx.bundle` plus `static/`, not as plain JS.
- [ ] The web target is opt-in and reported as available but unverified for production.
- [ ] The engine version in the host project bounds `engineVersion` in `lynx.config.ts`, or the missing host evidence is recorded.
- [ ] `initData`, `globalProps`, and native modules have a named owner on the host side.
- [ ] Features import only `shared`; no feature-to-feature import exists.
- [ ] `NativeModules` appears only under `shared/native/`.

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation, the `@lynx-js/create-lynx` 0.2.1 tarball, and npm registry metadata read on 2026-11-07.

| Claim | Source |
|---|---|
| Template file set, the entry file, and the `.js` extension on a `.tsx` import | https://registry.npmjs.org/@lynx-js%2Fcreate-lynx/-/create-lynx-0.2.1.tgz |
| `source.entry` accepted forms, default value, and multi-entry behavior | https://lynxjs.org/llms-full.txt (Rspeedy `source.entry` page) |
| Production and development output layout, and `DEBUG=rspeedy rspeedy build` | https://lynxjs.org/rspeedy/output.md, https://lynxjs.org/guide/performance/analysis-performance/analysis-bundle-size.md |
| `environments` defaulting to `{ lynx: {} }`, `dist/main.web.bundle`, and `lynx-view` attributes | https://lynxjs.org/guide/start/integrate-with-existing-apps.md, https://lynxjs.org/llms-full.txt (lynx-view page) |
| CocoaPods, Maven, and HarmonyOS host dependencies, `initData` injection, and native module registration | https://lynxjs.org/guide/start/integrate-with-existing-apps.md, https://lynxjs.org/guide/use-data-from-host-platform.md, https://lynxjs.org/guide/use-native-modules.md |
| `@lynx-js/web-core` 0.26.7 registry state with no production-readiness statement | https://registry.npmjs.org/@lynx-js%2Fweb-core |
| Folder ownership, the `shared/native/` boundary, and the naming convention | this package's convention, not an official Lynx requirement |
