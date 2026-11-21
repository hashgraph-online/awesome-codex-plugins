# Packaging, Signing, and Updates

> Pick one packager, flip the fuses before signing, sign and notarize every release, and ship updates through the packager's own update path.

Rules are labelled `official` when a page in `references/official/electron/electron-2026-11-08.md` states them, and `hypercore-default` when this package chose the default.

## 1. One packager

| Packager | Build tool it pairs with | Config | Updates |
|---|---|---|---|
| electron-builder 26.x | electron-vite (every surveyed electron-vite app) | `electron-builder.yml` | `electron-updater` |
| Electron Forge 8.x | `@electron-forge/plugin-vite` | `forge.config.ts` | Electron's built-in `autoUpdater` (`update-electron-app`, a static-storage publisher, or an update server) |

- `hypercore-default` — A repository uses one packager. Two packaging configs (`electron-builder.yml` and `forge.config.*`) in one target is a finding; keep the one the release scripts call.
- `official` — Forge 8 promoted the Vite plugin to stable, targets Vite 8, and renamed `electron-forge publish` to `electron-forge release` (`publish` remains a deprecated alias). Its documentation site still shows the older "experimental" banner; the 8.0.1 release notes are newer.
- `official` — electron-builder's default documentation URLs now describe the unreleased v27. A project on 26.x reads `https://www.electron.build/v26/docs/…`; v27 renames keys and ships `electron-builder migrate-schema`.
- `official` — The packaged `main` entry differs per tool: electron-vite writes `out/main/index.js`, Forge writes `.vite/build/main.cjs`. `package.json` `main` must match the tool that builds.

## 2. Fuses

- `official` — Flip fuses at package time, before code signing: Forge's `FusesPlugin` or electron-builder's `electronFuses` key, both passing `@electron/fuses` options. The hardened set is in `rules/electron/security.md` §6; Forge's template already flips six of them.
- `official` — Playwright's `_electron.launch` times out when `EnableNodeCliInspectArguments` is off. Run end-to-end tests against an unpackaged build or a test-only package, never by turning the fuse back on in the release build.

## 3. Signing and notarization

- `official` — macOS auto-update (Squirrel.Mac) requires a signed app, and `safeStorage` needs a stable signature to avoid Keychain prompts after updates.
- `official` — electron-builder signs, notarizes, and staples in one run with `mac: { hardenedRuntime: true, notarize: true, entitlements, entitlementsInherit }`; Electron needs at least `com.apple.security.cs.allow-jit`. Credentials come from the environment (`APPLE_API_KEY`, `APPLE_API_KEY_ID`, `APPLE_API_ISSUER` for CI, or `APPLE_ID` with an app-specific password and `APPLE_TEAM_ID`; `CSC_LINK` and `CSC_KEY_PASSWORD` for the certificate).
- `hypercore-default` — Signing credentials live only in CI secrets. They never appear in the repository, in `electron-builder.yml`, or in a `VITE_` variable. Signing, notarizing, and publishing a release are authority-gated actions this guide never runs without an explicit request.

## 4. Updates

- `official` — Electron's built-in `autoUpdater` supports macOS and Windows only; Linux updates come from the package source. `update.electronjs.org` needs a public GitHub repository, GitHub Releases, and a signed macOS build.
- `official` — `electron-updater` is a separate package from electron-builder: install it as an app dependency, configure `publish`, and call `autoUpdater.checkForUpdatesAndNotify()`; do not call `setFeedURL`, because the build writes `app-update.yml`. macOS needs the `zip` target next to `dmg`; Squirrel.Windows is not supported (use NSIS).
- `official` — electron-builder's implicit CI publishing is deprecated and removed in v27; pass `--publish always|onTag|onTagOrDraft|never` explicitly.
- `hypercore-default` — The update check runs in main, after the first window is shown, and reports status to the renderer through one push channel (`updates.onStatus`). Guard it with `app.isPackaged`.

## 5. What goes into the package

- `official` — electron-vite bundles renderer dependencies and, by default (`build.externalizeDeps`), leaves `dependencies` external for main and preload. Put renderer-only libraries (React, TanStack, Tailwind) in `devDependencies` so electron-builder does not copy them into `app.asar` a second time. Since electron-vite 5 the `externalizeDepsPlugin` and `bytecodePlugin` plugins are deprecated in favour of `build.externalizeDeps` and `build.bytecode`.
- `official` — `asarUnpack` lists files that must live outside `app.asar` (native addons, binaries a child process executes); everything else stays packed so ASAR integrity covers it.
- `official` — electron-vite's `build.bytecode` protects main and preload source only in production, needs `sandbox: false` for a bytecode preload, and is bound to the V8 version and CPU architecture. Do not trade the renderer sandbox for preload bytecode.

## Review gate

1. Two packagers are configured, or `package.json` `main` does not match the build tool's output.
2. Fuses are flipped after signing, missing from the release config, or relaxed to make tests pass.
3. A signing or notarization credential sits in the repository or in renderer-visible configuration.
4. `electron-updater` uses `setFeedURL`, or the macOS build lacks the `zip` target while expecting updates.
5. A sandboxed preload was given up for bytecode protection.
6. A 26.x project follows v27 documentation keys.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Forge 8 stable Vite plugin, `release` rename, and the stale banner | https://github.com/electron/forge/releases/tag/v8.0.1, https://www.electronforge.io/config/plugins/vite |
| Forge fuses plugin and template fuse set | https://www.electronforge.io/config/plugins/fuses, https://github.com/electron/forge/tree/main/packages/template/vite/tmpl |
| Fuses flipped before signing | https://www.electronjs.org/docs/latest/tutorial/fuses |
| electron-builder v26 config, `asarUnpack`, `electronFuses`, and v27 docs drift | https://www.electron.build/v26/docs/configuration |
| electron-builder signing and notarization | https://www.electron.build/v26/docs/code-signing-mac |
| `electron-updater` setup, targets, and providers; explicit `--publish` | https://www.electron.build/v26/docs/auto-update, https://www.electron.build/v26/docs/publish |
| Built-in `autoUpdater` platforms, signing, and `update.electronjs.org` | https://www.electronjs.org/docs/latest/api/auto-updater, https://www.electronjs.org/docs/latest/tutorial/updates |
| electron-vite `externalizeDeps`, `bytecode`, and the deprecated plugins | https://electron-vite.org/guide/dependency-handling, https://electron-vite.org/guide/source-code-protection, https://github.com/alex8088/electron-vite/blob/master/CHANGELOG.md |
| Playwright launch timeout with the inspect fuse off | https://playwright.dev/docs/api/class-electron |
| One packager per repository, CI-only credentials, update check after first window | this package's convention, not an official Electron requirement |
