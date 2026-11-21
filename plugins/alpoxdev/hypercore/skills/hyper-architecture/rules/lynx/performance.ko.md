# Lynx 성능

> Lynx app의 시작 시간, first screen, jank, scroll 부드러움, bundle 크기, build 무게를 다루는 요청에서 읽습니다. DevTool Trace로 먼저 측정하고, lever 하나를 바꾸고, production build에서 다시 측정합니다.

## 먼저 측정

Trace capture 없는 Lynx 성능 주장은 추측입니다. 순서대로 쓰는 측정 도구입니다.

| 질문 | 도구 | Command |
|---|---|---|
| Frame budget이 어디로 가는가 | Lynx DevTool Trace | USB로 DevTool desktop app, Trace panel |
| 어느 module이 어느 layer에 있는가 | Rsdoctor module graph | `RSDOCTOR=true rspeedy build` |
| 각 layer에 무엇이 있는가 | 읽을 수 있는 중간 산출물 | `DEBUG=rspeedy rspeedy build` |
| 출시 artifact가 얼마나 큰가 | output 검사 | `du -sh dist/*.lynx.bundle` |

Trace는 DevTool 통합이 필요하고 engine 3.4부터 Android, iOS, HarmonyOS에서 지원됩니다. Frame label은 16 ms 미만이 초록, 16 ms 이상 32 ms 미만이 주황, 32 ms 이상이 빨강이고(Android `Choreographer#doFrame`), scroll 중 dropped-frame 구간을 국소화합니다.

Rsdoctor module graph는 module마다 `layer` field를 담습니다. `react:main-thread` 또는 `react:background`이며 "왜 이 module이 main-thread bundle에 있는가"에 바로 답합니다.

Before 수치를 command와 함께 변경에 기록합니다. 여기서 측정할 수 없는 경우(device 없음, DevTool session 없음, production build 없음)는 측정하지 못했다고 보고하며 개선으로 주장하지 않습니다.

## IFR: Instant First-Frame Rendering

IFR은 bundle이 동기로 load되고 first-screen data가 이미 있을 때 main thread에서 첫 frame을 동기로 render합니다.

실패하는 경우는 팀이 가장 먼저 만나는 두 가지입니다.

- Bundle이 비동기로 load되어 main thread가 load 시점에 render할 것이 없습니다.
- First screen이 network data에 의존해 background thread가 fetch하기 전에는 render할 것이 없습니다.

실제 data로 IFR을 얻는 공인된 방법은 host `initialData`와 `useInitData()`입니다. Host가 이미 data를 갖고 template과 함께 주입하며 main thread가 그 값으로 first screen을 render합니다.

IFR은 first-screen 속성입니다. 모든 화면을 IFR로 만들려 하지 않습니다. Entry 화면을 IFR로 만들고 이후 화면은 정상 load에 맡깁니다.

## `firstScreenSyncTiming`

`'immediately' | 'jsReady' | 'manual'`, default는 `'immediately'`입니다. First screen 이후 main thread(Lepus)가 background thread에 제어를 넘기는 시점을 정합니다.

Handover 이후 main-thread runtime은 data 갱신에 더 이상 반응하지 못하고, 갱신은 비동기로 전달됩니다. 그래서 이 값은 "first screen이 정적이고 빠르게 유지되어야 한다"와 "가능한 한 빨리 상호작용해야 한다" 사이의 knob입니다.

- `'immediately'` — 가장 빠른 handover, 이른 상호작용, 이후 data에 대한 main-thread 반응 없음.
- `'jsReady'` — background JS가 준비될 때까지 기다립니다.
- `'manual'` — app이 `markFirstScreenSyncReady()`를 호출할 때 넘깁니다.

이 값을 바꾸면 체감 시작 시간이 바뀝니다. 변경을 유지하기 전에 양쪽을 측정합니다.

## Main-thread bundle을 작게

Build는 entry마다 `main-thread.js`와 `background.js`를 만들고, `main-thread.js`가 first-frame critical path에 있습니다. 그곳의 kilobyte마다 첫 paint가 늦어지고, 같은 kilobyte가 `background.js`에 있으면 상호작용이 늦어집니다.

영향 순서대로 lever입니다.

1. **Background-only 표시.** Background-only code에서만 도달하는 code는 추론되어 main-thread bundle에서 제거됩니다. Inline arrow handler나 component를 거쳐 prop으로 전달되는 function은 추론을 깨고 그 import를 main-thread layer로 끌고 옵니다. 추론이 볼 수 없는 곳에는 directive를 씁니다.
2. **`optimizeBundleSize`** — default `false`이고 `mainThread`와 `background` sub-flag가 있습니다. Production에서 최소한 `mainThread`를 켭니다.
3. **`extractStr`** — default `false`. JS layer와 Lepus layer의 중복 string literal을 병합합니다. Text가 많은 화면에서 싼 이득입니다.
4. **`__BACKGROUND__`** — layer별로 죽은 branch를 제거하는 compile-time boolean입니다. 한 module이 layer별로 다른 구현을 정당하게 가져야 할 때 씁니다.

각 변경 후 flag 이름을 믿지 말고 Rsdoctor의 layer 귀속으로 확인합니다.

## List recycling

`<list>`가 유일한 virtualized feed입니다. Node를 recycle하고, 계약이 틀리면 조용히 깨집니다.

- Viewport가 고정 크기여야 합니다. 내용에 따라 크기가 정해지는 `<list>`는 virtualize할 viewport가 없습니다.
- `item-key`가 row를 만들 때 쓴 `key`와 같아야 합니다. 어긋나면 잘못된 node를 recycle합니다.
- `reuse-identifier`가 구조가 같은 item을 묶습니다. 형태가 다른 두 loop는 group을 공유하면 안 되고, 형태가 같은 두 loop는 공유해야 합니다.
- 절대 재사용하면 안 되는 row에는 `recyclable={false}`를 둡니다.

Scroll 중 jank 보고는 대개 이 중 하나에, 또는 `useEffect`에서 무거운 일을 하는 row에 떨어집니다. `useEffect`는 UI node가 없어도 실행되므로 사용자가 보지 않은 row에도 비싼 effect가 돕니다.

## Lazy bundle과 code splitting

```tsx
const Detail = lazy(() => import('./Detail.js'));

<Suspense fallback={<Loading />}>
  <Detail />
</Suspense>
```

Lazy component마다 자기 bundle이 생기고 따라서 자기 CSS scope가 생깁니다. Global CSS는 bundle 경계를 넘지 않습니다. Split 전에 동작하던 style이 split 후 적용되지 않을 수 있고, 이는 split된 화면의 regression처럼 보입니다.

- 독립 생산자는 `experimental_isLazyBundle`을 씁니다.
- `FetchBundle`과 `QueryComponent` 중 loader 선택은 `engineVersion`을 따릅니다. `FetchBundle`은 3.9 이상이 필요합니다. `REACT_LAZY_BUNDLE_FETCHER`가 이를 덮습니다.
- 0.115.0 이전 Consumer는 0.115.0 이후로 build한 lazy bundle을 load할 수 없습니다. `engineVersion` 옆의 두 번째 version 하한이며 놓치기 쉽습니다.

`splitChunks`는 별도 Rspeedy lever이고 default는 `false`입니다. 예전 `performance.chunkSplit`은 top-level `splitChunks`로 대체되어 obsolete입니다.

## Cross-thread traffic

`runOnMainThread`와 `runOnBackground`는 비동기이고 argument를 JSON으로 marshal합니다. Item별 또는 frame별 사용은 매끄러운 animation을 stutter로 바꿉니다. 호출마다 직렬화와 왕복 비용을 치르기 때문입니다.

- Event가 도착한 곳에서 일을 끝냅니다. Background로 넘겼다가 되돌아오지 말고 `main-thread:`로 binding해 그곳에서 처리합니다.
- `NodesRef.invoke()`와 `.exec()`로 native 작업을 batch합니다.
- Item별 호출 대신 `setNativeProps` batch 하나를 선호합니다.
- Payload를 작게 유지합니다. Frame마다 큰 객체 graph를 직렬화하는 것이 정상적인 app의 scroll jank 흔한 원인입니다.

## 그 밖의 lever

- **Gesture와 scroll에 Main Thread Script** — Animation이 손가락을 늦게 따라오게 만드는 event -> background -> render thread hop을 제거합니다.
- **External Bundle** — 한 번 build해 여러 app에서 load합니다. `@lynx-js/react-umd`와 `externalsPresets.reactlynx`가 필요합니다. App별 최적화가 아니라 platform 전략입니다.
- **Image** — Source에서 압축하고 크기가 맞는 asset을 쓰며, first screen에 필요 없는 큰 asset을 main bundle에서 분리합니다.
- **React Compiler** — 선택 사항이고 target은 `'17'`이며 `react-compiler-runtime@rc`, `@rsbuild/plugin-babel`, `babel-plugin-react-compiler@rc`가 필요합니다. 문서는 IFR과 초기 background render를 다소 해칠 수 있다고 경고하므로, 시작 시간보다 re-render 효율이 중요할 때 켭니다.
- **Production monitoring** — `lynx.performance`와 `PerformanceObserver`, `__lynx_timing_flag` node attribute, ActualFMP용 `__lynx_timing_actual_fmp`입니다. 권장 최소 production 집합은 `metric.fcp`와 `pipeline.loadBundle`에 업무상 중요한 flag를 더한 것입니다.

## 절차

1. Metric과 도구를 명시합니다. "First screen이 느리다"를 Trace로 측정한 `metric.fcp`나 `dist/`의 bundle 크기로 바꿉니다.
2. Command와 함께 before 수치를 기록합니다.
3. 이 file의 lever 하나를 바꿉니다.
4. 같은 command로 production build에서 다시 측정합니다.
5. 수치가 개선되고 type check, test, build가 여전히 통과할 때만 유지합니다. 아니면 되돌립니다.
6. 실행당 lever는 최대 3개이고 나머지는 next step으로 남깁니다.

## Checklist

- [ ] 변경 전에 metric, 도구, before 수치를 기록했습니다.
- [ ] 재측정이 같은 command로 production build에서 이뤄졌습니다.
- [ ] IFR의 두 실패 조건, 즉 비동기 bundle load와 network 의존 first content를 확인했습니다.
- [ ] 측정이 변경을 정당화하지 않았으면 `firstScreenSyncTiming`을 default로 두었습니다.
- [ ] Development build 또는 `RSDOCTOR=true`로 `main-thread.js` 크기를 확인했습니다.
- [ ] Production에 `optimizeBundleSize`와 `extractStr`을 검토했습니다.
- [ ] 모든 `<list>`에 고정 viewport, 일치하는 `item-key`/`key`, 올바른 `reuse-identifier` grouping이 있습니다.
- [ ] Lazy split이 깨뜨리는 CSS scope를 확인했습니다.
- [ ] `FetchBundle` 사용이 `engineVersion` 3.9 이상과 Consumer 0.115.0 하한에 맞습니다.
- [ ] Cross-thread 호출이 item별이나 frame별이 아니라 batch입니다.
- [ ] 같은 측정의 before와 after 수치 없이 개선을 주장하지 않았습니다.

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서를 인용합니다.

| Claim | Source |
|---|---|
| IFR 조건과 비동기 bundle 및 network data 실패 조건 | https://lynxjs.org/guide/interaction/ifr.md |
| `firstScreenSyncTiming` 값, default, handover 이후 동작 | https://lynxjs.org/llms-full.txt (pluginReactLynx option page) |
| Critical path의 `main-thread.js`, `optimizeBundleSize`, `extractStr`, layer field | https://lynxjs.org/guide/performance/analysis-performance/analysis-bundle-size.md, https://lynxjs.org/llms-full.txt |
| `__BACKGROUND__`의 죽은 branch 제거 | https://lynxjs.org/api/react/Document.built-in-macros.md |
| `<list>` recycling 계약과 고정 viewport | https://lynxjs.org/api/elements/built-in/list.md |
| Lazy bundle, bundle별 CSS scope, `experimental_isLazyBundle`, 3.9의 `FetchBundle`, Consumer 0.115.0 하한 | https://lynxjs.org/react/code-splitting.md |
| `splitChunks` default `false`와 obsolete `performance.chunkSplit` | https://lynxjs.org/llms-full.txt |
| Cross-thread marshal과 batch 지침 | https://lynxjs.org/react/main-thread-script.md, https://lynxjs.org/llms.txt |
| Gesture용 Main Thread Script, `External Bundle`, image, React Compiler, monitoring flag | https://lynxjs.org/react/best-practices.md, https://lynxjs.org/rspeedy/external-bundle.md, https://lynxjs.org/react/react-compiler.md, https://lynxjs.org/llms-full.txt |
| Engine 3.4부터의 Trace와 frame 색 구간 | https://lynxjs.org/guide/devtool/trace.md, https://lynxjs.org/guide/performance/analysis-performance/analysis-fluency.md |
| `RSDOCTOR=true`와 `DEBUG=rspeedy` build mode | https://lynxjs.org/guide/performance/analysis-performance/analysis-bundle-size.md, https://lynxjs.org/rspeedy/output.md |
