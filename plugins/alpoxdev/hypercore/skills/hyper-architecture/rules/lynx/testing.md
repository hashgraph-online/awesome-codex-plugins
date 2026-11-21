# Lynx Testing

> Read before adding or reviewing tests, changing the test runner, or claiming a Lynx change is verified.

## What the template ships

The official ReactLynx TypeScript template runs Rstest.

```ts
// rstest.config.ts
import { withLynxConfig } from '@lynx-js/react/testing-library/rstest-config';
import { defineConfig } from '@rstest/core';

export default defineConfig({
  extends: withLynxConfig(),
});
```

`withLynxConfig()` reuses the app's real `lynx.config.ts`, so a test sees the same aliases, plugins, and `engineVersion` the build uses. `withDefaultConfig()` is the alternative when a test must not inherit app config. The template also installs `jsdom` and `@testing-library/jest-dom`.

`package.json` scripts: `build: rspeedy build`, `dev: rspeedy dev`, `preview: rspeedy preview`, `test: rstest run`.

## The testing library

`@lynx-js/react/testing-library` ships inside the `@lynx-js/react` package as the `./testing-library` export. It mirrors React Testing Library — `render`, `fireEvent`, `screen` — and abstracts the dual thread through `@lynx-js/testing-environment`, which emulates both threads in one process.

Two runners are supported:

| Runner | Setup |
|---|---|
| Rstest | `extends: withDefaultConfig()` or `withLynxConfig()` from `@lynx-js/react/testing-library/rstest-config` |
| Vitest | `plugins: [vitestTestingLibraryPlugin()]` from `@lynx-js/react/testing-library/plugins` |

Prefer Rstest with `withLynxConfig()` for app tests, because it reuses the real build config. Use Vitest only when the repository already standardizes on it.

## Events

Fire typed event names that match the attribute semantics:

```ts
fireEvent(element, new Event('bindEvent:tap'));
fireEvent(element, new Event('catchEvent:tap'));
fireEvent(element, new Event('capture-bind:tap'));
fireEvent(element, new Event('capture-catch:tap'));

// shorthand for the common case
fireEvent.tap(element);
```

The element PAPI is emulated on JSDOM, so `@testing-library/jest-dom` matchers work. That also means a test proves the JavaScript and element semantics, not the native rendering: a passing test does not prove that a `<list>` recycles correctly on a device.

## What to test

Per screen or feature:

1. A render test that asserts the initial tree from a given `initData`.
2. An event test that fires the handler the screen actually binds.
3. A host-data test for absent, partial, or updated `initData` and for `globalProps` being `null` or `{}`.
4. A thread test for any `main-thread:` handler: assert the visible effect of the handler rather than calling it directly, because the directive only applies through the binding.
5. A list test that asserts `item-key` and `key` agree and that rows render for the given data.

Testing limits to state rather than paper over:

- The dual-thread emulation is a JavaScript emulation. It does not prove PrimJS/JSC behavior differences, bytecode loading, or a real main-thread timing bug.
- A test cannot prove `engineVersion` compatibility. That is a host-version fact, verified against the host, not in a unit test.
- Native modules are not present in the test environment. Mock the adapter under `src/shared/native/`, not `NativeModules` directly, so the mock sits at the boundary the app actually uses.

## Type checking

Rspeedy does not type check. "Type checking is not performed" is the documented behavior, so a green `rspeedy build` says nothing about types.

Wire it explicitly:

```ts
import { pluginTypeCheck } from '@rsbuild/plugin-type-check';

pluginTypeCheck({ enable: true });
```

The official template already includes `@rsbuild/plugin-type-check` and calls `pluginTypeCheck()`.

TypeScript settings that matter:

- `isolatedModules: true` is required, because SWC compiles file by file.
- `jsxImportSource: "@lynx-js/react"` in the source program, with `jsx: "react-jsx"`.
- `moduleResolution: "Bundler"` for source, `node16` for the config program.
- `strict`, `verbatimModuleSyntax`, `esModuleInterop`, `skipLibCheck` are the template defaults.

Because `isolatedModules` is on, `export type { X }` and `import type` are not stylistic choices; a re-exported type that is not marked fails the build.

## Check order

1. Type check with the project's own command (`tsc -b` against the referenced programs, or the script the repo defines).
2. `rstest run` for unit and component tests.
3. `rspeedy build` to confirm the production bundle still builds.
4. A device or Lynx Explorer run when the change touches threading, lists, native modules, or `engineVersion`. A test suite cannot substitute for this.

Report a step that could not run and why. Do not claim a device check that did not happen.

## Checklist

- [ ] The test runner is Rstest with `withLynxConfig()`, or Vitest with an evidenced reason.
- [ ] `pluginTypeCheck()` is configured and the type check is part of the check order.
- [ ] `isolatedModules: true` and `jsxImportSource: "@lynx-js/react"` are present.
- [ ] Touched screens have a render test and an event test.
- [ ] Host-data tests cover absent and partial `initData` and absent `globalProps`.
- [ ] Main-thread handler tests assert through the binding, not by direct invocation.
- [ ] List tests assert `item-key` and `key` agreement.
- [ ] Native modules are mocked at the `src/shared/native/` adapter, not at `NativeModules`.
- [ ] The report names what a unit test cannot prove: device behavior, engine compatibility, and real timing.

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation, the `@lynx-js/create-lynx` 0.2.1 tarball, and npm registry metadata read on 2026-11-07.

| Claim | Source |
|---|---|
| `@lynx-js/react/testing-library`, its Rstest and Vitest setup, and the typed event names | https://lynxjs.org/react/reactlynx-testing-library.md |
| `@lynx-js/testing-environment` emulating the dual thread | https://registry.npmjs.org/@lynx-js%2Ftesting-environment, https://registry.npmjs.org/@lynx-js%2Freact |
| The shipped `rstest.config.ts`, template scripts, and `@rstest/core` | https://registry.npmjs.org/@lynx-js%2Fcreate-lynx/-/create-lynx-0.2.1.tgz |
| No type checking in the build; `pluginTypeCheck`; `isolatedModules` requirement | https://lynxjs.org/rspeedy/typescript.md |
| JSDOM element PAPI emulation and `jest-dom` matchers | https://lynxjs.org/react/reactlynx-testing-library.md |
| The boundary-mocking and device-evidence requirements | this package's convention, not an official Lynx requirement |
