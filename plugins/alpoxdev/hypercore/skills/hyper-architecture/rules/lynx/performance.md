# Lynx Performance

> Read when the request is about startup time, first screen, jank, scroll smoothness, bundle size, or build weight in a Lynx app. Measure first with DevTool Trace, change one lever, re-measure on a production build.

## Measure first

A Lynx performance claim without a Trace capture is a guess. The measurement tools, in the order to reach for them:

| Question | Tool | Command |
|---|---|---|
| Where does the frame budget go? | Lynx DevTool Trace | DevTool desktop app over USB, Trace panel |
| Which module is in which layer? | Rsdoctor module graph | `RSDOCTOR=true rspeedy build` |
| What is in each layer? | readable intermediates | `DEBUG=rspeedy rspeedy build` |
| How big is the shipped artifact? | output inspection | `du -sh dist/*.lynx.bundle` |

Trace requires DevTool integration and is supported from engine 3.4 on Android, iOS, and HarmonyOS. Frame labels read green under 16 ms, orange from 16 to 32 ms, red at 32 ms or more (Android `Choreographer#doFrame`), which localizes dropped-frame segments during a scroll.

Rsdoctor's module graph carries a `layer` field per module — `react:main-thread` or `react:background` — so it answers "why is this in the main-thread bundle" directly.

Record the before number in the change, with the command that produced it. A measurement that cannot run here (no device, no DevTool session, no production build) is reported as not measured, never as a gain.

## IFR: Instant First-Frame Rendering

IFR renders the first frame synchronously on the main thread when the bundle loads synchronously and the first-screen data is already present.

It fails in exactly the two cases teams hit first:

- The bundle is loaded asynchronously, so the main thread has nothing to render at load time.
- The first screen depends on network data, so there is nothing to render until the background thread fetches it.

The sanctioned way to get IFR with real data is host `initialData` plus `useInitData()`: the host already has the data, injects it with the template, and the main thread renders the first screen from it.

IFR is a first-screen property. Do not try to make every screen IFR; make the entry screen IFR and let later screens load normally.

## `firstScreenSyncTiming`

`'immediately' | 'jsReady' | 'manual'`, default `'immediately'`. It controls when the main thread (Lepus) hands control to the background thread after the first screen.

After the handover the main-thread runtime can no longer respond to data updates; they are forwarded asynchronously. So this is the knob for "first screen must stay static and fast" versus "interactive as soon as possible":

- `'immediately'` — fastest handover, earliest interactivity, no main-thread responsiveness to later data.
- `'jsReady'` — waits until the background JS is ready.
- `'manual'` — the app calls `markFirstScreenSyncReady()` when it decides.

Changing this value changes perceived startup. Measure both ends before keeping a change.

## Keep the main-thread bundle small

The build emits `main-thread.js` and `background.js` per entry, and `main-thread.js` sits on the first-frame critical path. Every kilobyte there delays the first paint; the same kilobyte in `background.js` delays interactivity instead.

Levers, in order of impact:

1. **Background-only marking.** Code reachable only from background-only code is inferred and dropped from the main-thread bundle. An inline arrow handler or a function passed as a prop through a component breaks the inference and drags its imports into the main-thread layer. Write the directive where inference cannot see it.
2. **`optimizeBundleSize`** — default `false`, with `mainThread` and `background` sub-flags. Turn on at least `mainThread` in production.
3. **`extractStr`** — default `false`; merges duplicate string literals across the JS and Lepus layers. Cheap win on text-heavy screens.
4. **`__BACKGROUND__`** — a compile-time boolean that removes the dead branch per layer, for a module that legitimately needs different implementations.

Verify with Rsdoctor's layer attribution after each change rather than trusting the flag names.

## List recycling

`<list>` is the only virtualized feed. It recycles nodes, and the recycling breaks quietly when the contract is wrong:

- The viewport must be a fixed size. A `<list>` sized by its content has no viewport to virtualize against.
- `item-key` must equal the `key` used to build the row. A mismatch recycles the wrong node.
- `reuse-identifier` groups structurally identical items. Two loops that render different shapes must not share a group; two that render the same shape should.
- `recyclable={false}` on a row that must never be reused.

A jank report during scroll usually lands on one of these, or on a row whose component does heavy work in `useEffect` — which fires even when no UI node exists, so an expensive effect runs for rows the user has not seen.

## Lazy bundles and code splitting

```tsx
const Detail = lazy(() => import('./Detail.js'));

<Suspense fallback={<Loading />}>
  <Detail />
</Suspense>
```

Each lazy component gets its own bundle, and therefore its own CSS scope: global CSS does not cross a bundle boundary. A style that worked before splitting can stop applying, which looks like a regression in the split screen.

- Standalone producers use `experimental_isLazyBundle`.
- Loader selection between `FetchBundle` and `QueryComponent` follows `engineVersion`; `FetchBundle` needs 3.9 or later. `REACT_LAZY_BUNDLE_FETCHER` overrides it.
- A Consumer older than 0.115.0 cannot load a lazy bundle built with 0.115.0 or later. That is a second version floor beside `engineVersion`, and it is easy to miss.

`splitChunks` is a separate Rspeedy lever and defaults to `false`. The older `performance.chunkSplit` is obsolete in favor of top-level `splitChunks`.

## Cross-thread traffic

`runOnMainThread` and `runOnBackground` are asynchronous and marshal their arguments as JSON. Per-item or per-frame use turns a smooth animation into a stutter, because each call pays serialization and a round trip.

- Do the work where the event arrives: bind with `main-thread:` and handle it there instead of forwarding to the background thread and back.
- Batch native work with `NodesRef.invoke()` and `.exec()`.
- Prefer one `setNativeProps` batch over per-item calls.
- Keep the payload small; a large object graph serialized per frame is the common cause of scroll jank in an otherwise correct app.

## Other levers

- **Main Thread Script for gestures and scroll** — removes the event → background → render thread hops that make an animation lag the finger.
- **External Bundle** — build once, load across apps; needs `@lynx-js/react-umd` and `externalsPresets.reactlynx`. A platform play, not a per-app optimization.
- **Images** — compress at source, use correctly sized assets, and split large non-first-screen assets out of the main bundle.
- **React Compiler** — optional, target `'17'`, requires `react-compiler-runtime@rc`, `@rsbuild/plugin-babel`, and `babel-plugin-react-compiler@rc`. The docs warn it can slightly hurt IFR and the initial background render, so enable it when re-render efficiency matters more than startup.
- **Production monitoring** — `lynx.performance` with `PerformanceObserver`, the `__lynx_timing_flag` node attribute, and `__lynx_timing_actual_fmp` for ActualFMP. The recommended minimum production set is `metric.fcp` plus `pipeline.loadBundle` plus business-critical flags.

## Procedure

1. Name the metric and the tool. "First screen slow" becomes `metric.fcp` measured in Trace, or bundle size from `dist/`.
2. Record the before number with its command.
3. Change one lever from this file.
4. Re-measure with the same command on a production build.
5. Keep the change only when the number improves and the type check, tests, and build still pass. Otherwise revert it.
6. At most three levers per run; list the rest as next steps.

## Checklist

- [ ] The metric, the tool, and the before number are recorded before any change.
- [ ] The re-measurement used the same command on a production build.
- [ ] IFR was checked against its two failure modes: async bundle load and network-dependent first content.
- [ ] `firstScreenSyncTiming` was left at its default unless a measurement justified a change.
- [ ] `main-thread.js` size was checked in a development build or with `RSDOCTOR=true`.
- [ ] `optimizeBundleSize` and `extractStr` were considered for production.
- [ ] Every `<list>` has a fixed viewport, matching `item-key`/`key`, and correct `reuse-identifier` grouping.
- [ ] A lazy split was checked for the CSS scope it breaks.
- [ ] `FetchBundle` use is matched by `engineVersion` 3.9 or later and the Consumer 0.115.0 floor.
- [ ] Cross-thread calls are batched, not per-item or per-frame.
- [ ] No gain is claimed without a before and after number from the same measurement.

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation read on 2026-11-07.

| Claim | Source |
|---|---|
| IFR conditions and the async-bundle and network-data failure modes | https://lynxjs.org/guide/interaction/ifr.md |
| `firstScreenSyncTiming` values, default, and post-handover behavior | https://lynxjs.org/llms-full.txt (pluginReactLynx option pages) |
| `main-thread.js` on the critical path, `optimizeBundleSize`, `extractStr`, and the layer field | https://lynxjs.org/guide/performance/analysis-performance/analysis-bundle-size.md, https://lynxjs.org/llms-full.txt |
| `__BACKGROUND__` removing the dead branch | https://lynxjs.org/api/react/Document.built-in-macros.md |
| `<list>` recycling contract and fixed viewport | https://lynxjs.org/api/elements/built-in/list.md |
| Lazy bundles, per-bundle CSS scope, `experimental_isLazyBundle`, `FetchBundle` at 3.9, and the Consumer 0.115.0 floor | https://lynxjs.org/react/code-splitting.md |
| `splitChunks` default `false` and the obsolete `performance.chunkSplit` | https://lynxjs.org/llms-full.txt |
| Cross-thread marshaling and batching guidance | https://lynxjs.org/react/main-thread-script.md, https://lynxjs.org/llms.txt |
| Main Thread Script for gestures, `External Bundle`, images, React Compiler, and monitoring flags | https://lynxjs.org/react/best-practices.md, https://lynxjs.org/rspeedy/external-bundle.md, https://lynxjs.org/react/react-compiler.md, https://lynxjs.org/llms-full.txt |
| Trace support from engine 3.4 and the frame color thresholds | https://lynxjs.org/guide/devtool/trace.md, https://lynxjs.org/guide/performance/analysis-performance/analysis-fluency.md |
| `RSDOCTOR=true` and `DEBUG=rspeedy` build modes | https://lynxjs.org/guide/performance/analysis-performance/analysis-bundle-size.md, https://lynxjs.org/rspeedy/output.md |
