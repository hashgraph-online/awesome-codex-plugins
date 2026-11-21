# Performance

> Measure a packaged build, keep the main process free, load only what the first window needs, and treat the renderer bundle as a separate budget.

Rules are labelled `official` when a page in the dated snapshot states them, and `hypercore-default` when this package chose the default. The order is typical impact, not a measured ranking.

## Measure first

| Goal | Command or tool |
|---|---|
| Cold start to first visible window | packaged build, timestamp `app` `ready` and the window `ready-to-show` in main, logged once |
| Main-process blocking | `contentTracing` recording (Perfetto format since Electron 45), or `--inspect` on an unpackaged build |
| Renderer bundle composition | the renderer Vite build with a bundle analyzer (for example `rollup-plugin-visualizer`) |
| Renderer runtime | Chromium DevTools Performance panel in the window |
| Package size | size of `app.asar` and the installer the packager produces |
| Memory | `app.getAppMetrics()` per process after a fixed scenario |

Every number comes from a production build. The dev server serves unbundled modules and its startup says nothing about the shipped app.

## Rules

1. `official` — Audit modules before requiring them: one transitive dependency can pull a large file into startup.
2. `official` — Do not load and run code too soon. Defer work that the first window does not need (update checks, indexing, analytics) until after `ready-to-show`; `require` is expensive, especially on Windows.
3. `official` — Never block the main process. It hosts the UI thread and mediates OS events and windows; move long CPU or I/O work to a `utilityProcess` or a worker thread.
4. `official` — Never block the renderer. Use `requestIdleCallback` for small deferred work and Web Workers for long work.
5. `official` — Drop unnecessary polyfills: the Chromium version is fixed per Electron major. Set the Vite build target to that Chromium instead of a broad browser list.
6. `official` — Defer or parallelize network requests the first screen does not need.
7. `official` — Bundle the code so module loading is paid once. electron-vite bundles all three processes; keep main and preload bundled too when startup `require` cost shows in the trace.
8. `official` — Call `Menu.setApplicationMenu(null)` before `ready` when the app ships no default menu, so Electron skips building one.
9. `hypercore-default` — Create the `BrowserWindow` with `show: false` and show it on `ready-to-show`, so the user never sees a blank frame.
10. `hypercore-default` — Split renderer routes with the router plugin's `autoCodeSplitting` and keep heavy feature libraries (editors, charts) behind lazy routes.
11. `hypercore-default` — Keep IPC payloads small and batched. Stream large or frequent data through a `MessagePort` instead of many `invoke` calls, and do not send whole datasets on every change.
12. `hypercore-default` — Keep renderer-only packages in `devDependencies` so they are bundled once and not also copied into `app.asar` (`rules/electron/packaging.md` §5).

## Do not

- Claim a startup gain from a dev-server run.
- Disable the sandbox or context isolation to save startup time.
- Add a V8 snapshot without measuring: the `LoadBrowserProcessSpecificV8Snapshot` fuse costs part of the time a snapshot saves, and the Performance tutorial has no snapshot recipe.
- Move work into the preload to make the renderer look faster; the preload blocks page load too.
- Retune the packager and the bundler in one change; one lever per measurement.

## Checklist

- [ ] Packaged-build start time, renderer bundle size, and `app.asar` size recorded before any change.
- [ ] Main-process trace checked for synchronous work before `ready-to-show`.
- [ ] Deferred work starts after the first window shows.
- [ ] Long CPU or I/O work lives in a utility process or worker.
- [ ] Build target matches the shipped Chromium.
- [ ] One lever per measurement, with before and after numbers from the same command.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| The eight performance recommendations, including the application-menu item | https://www.electronjs.org/docs/latest/tutorial/performance |
| `contentTracing` recordings as Perfetto protobuf in 45 | https://www.electronjs.org/docs/latest/breaking-changes |
| The V8 snapshot fuse and its startup cost | https://www.electronjs.org/docs/latest/tutorial/fuses |
| `utilityProcess` and `MessagePort` streams | https://www.electronjs.org/docs/latest/api/utility-process, https://www.electronjs.org/docs/latest/tutorial/message-ports |
| `ready-to-show` for showing a window without a blank frame | https://www.electronjs.org/docs/latest/api/browser-window |
| Router `autoCodeSplitting` | https://tanstack.com/router/latest/docs/framework/react/guide/automatic-code-splitting |
| electron-vite dependency handling | https://electron-vite.org/guide/dependency-handling |
| Show-on-ready, lazy feature routes, batched IPC, and `devDependencies` placement as defaults | this package's convention, not an official requirement |
