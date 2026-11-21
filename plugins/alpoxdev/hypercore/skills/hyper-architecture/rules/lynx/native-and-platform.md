# Lynx Native and Platform

> Read when touching native modules, host app integration, the engine dependency, `engineVersion`, or the web target. The `engineVersion` gate in this file blocks deployment, not just review.

## `engineVersion` is a deployment constraint

`engineVersion` declares the oldest engine a bundle can run on. A bundle that declares N runs on an engine of N or newer and **fails fatally with error 10204 on anything older**. There is no degradation path, no fallback, and no runtime warning that a build would catch.

That makes it the hardest constraint in a Lynx deployment:

- It is not a build setting. The build succeeds regardless.
- It is not versioned with the bundle in a way the host can negotiate. The host either satisfies it or the screen dies.
- `pluginReactLynx` defaults it to `'3.2'`. That default is a floor, not a target; leaving it alone is safe, but it also forbids newer CSS and APIs that a higher value would unlock.

### Blocking review rule

**A change that raises `engineVersion` cannot merge until the lowest engine version of every host that loads the bundle is recorded with its evidence.** Accept evidence in this order:

1. The host dependency in this repository: an iOS `Podfile` line `pod 'Lynx', '<version>'`, an Android Gradle `org.lynxsdk.lynx:lynx:<version>`, or a HarmonyOS `@lynx/primjs` dependency.
2. A release-train document or app-version matrix the repository points at.
3. A named person's confirmation with the app version it applies to, recorded in the config comment.

If none of those exist, the bundler cannot verify the floor. Keep `engineVersion` at its current value, report the missing evidence, and do not raise it to unlock a feature. Silently raising it passes review and then kills the screen on the oldest shipped host, which is the worst failure shape: it reproduces on exactly the users who cannot update.

```ts
pluginReactLynx({
  // Lowest engine on a shipping host: 3.9 (Android app 24.x pins org.lynxsdk.lynx:lynx:3.9.0).
  engineVersion: '3.9',
})
```

The same reasoning applies to every engine-gated feature: `!important` and the `flex` shorthand change at 3.9, `FetchBundle` lazy-bundle loading at 3.9 and later, Trace from 3.4, WebAssembly from 3.8 on Android only. Using one of them is a decision about the host floor.

## Native modules

Native modules are registered by the host app and called from the bundle.

| Platform | Registration |
|---|---|
| Android | `LynxEnv.inst().registerModule(...)` |
| iOS | `[globalConfig registerModule:...]` |

Rules:

- Native modules can be used only from Background Thread Scripting. `NativeModules.X` in a render body or at module top level throws on the main thread. This is a blocking gate in `rules/lynx/threading.md`.
- Native module access funnels through one adapter under `src/shared/native/`. Every call site goes through it, so the thread and the error handling are decided once.
- The host decides what exists. A bundle cannot assume a module; call it defensively or check availability once and cache the answer.
- Host permissions — camera, location, storage — are not Lynx concepts. The bundle can do only what the host's native modules and `fetch` service permit. There is no Lynx-level permission model beyond the module validator.

### Module call authorization

From SDK 3.5 the host can install a per-`LynxView` validator that sees `(moduleName, methodName, params)` and returns allow or deny; denying raises a JS error.

```kotlin
// Android
lynxViewBuilder.registerModuleAuthValidator(object : LynxModule.AuthValidator {
  override fun validate(module: String, method: String, params: JSONObject): Boolean =
    allowed[module]?.contains(method) == true
})
```

```objc
// iOS
[config registerMethodAuth:^BOOL(NSString *module, NSString *method, NSDictionary *params) {
  return [self allowedModule:module method:method params:params];
}];
```

Available on Android and iOS; HarmonyOS support was pending at the time the documentation was read. Treat the validator as the seam for "this screen must not call the wallet module" and record which modules each surface may reach.

## Host data contract

`initData` and `globalProps` are host inputs, not local state. Their platform entry points and typing live in `rules/lynx/ui-and-data.md`; this file owns only the boundary rule: a frontend change that adds a field to `initData` is a host contract change, so it ships with the host change or behind a check for absence. A bundle deployed before its host would read `undefined`.

## Host app integration

| Platform | Dependency | Notes |
|---|---|---|
| iOS | CocoaPods `pod 'Lynx', '<version>'`, plus `PrimJS`; optionally `LynxService`, `XElement`, `SDWebImage`, `SDWebImageWebPCoder` | Version must satisfy every bundle's `engineVersion` |
| Android | Maven `org.lynxsdk.lynx:lynx`, `:lynx-jssdk`, `:lynx-trace`, `:primjs`; optionally `:lynx-service-image`, `:lynx-service-log`, `:lynx-service-http` | Gradle version is the floor for `engineVersion` |
| HarmonyOS | `@lynx/primjs` artifacts | Engine APIs differ; verify separately |
| Windows | CMake plus LynxSDK | Not verified by this package |
| Web | `@lynx-js/web-core` and `<lynx-view>` | See below |

`LynxView` is itself a native view: it works full-screen or embedded. The host sets size constraints and Lynx lays out the `<page>` inside. When the loader shows a splash, a skeleton, or a native header around the view, that chrome is host code and its layout must match what the bundle assumes — a bundle that expects the full screen while the host gives it 60% height produces a layout that looks like a CSS bug.

Engine versions across platforms are released together but the host dependencies advance independently. Pinning Android to 3.9 and iOS to 4.0 is normal; the effective floor is the lower of the two for any bundle both load.

## Engine release model

- Documented stable engine at the time of writing: 4.2, released 2026-10-27. 4.2.0 pins PrimJS 4.2.1 across Android Gradle, the iOS pod, and Harmony.
- The project moved from a bi-monthly to a monthly cadence starting with 3.8. The published plan has already slipped once — 4.2 was planned for 2026/09 and landed 2026-10-27 — so treat the plan as intent, not as a schedule to depend on.
- Platform floor: iOS 10 and Android 5.0 (API 21) or newer. macOS is the recommended development OS; Windows and Linux hosts are "not yet verified or guaranteed" by the engine project.

`@lynx-js/types` tracks the engine major line (4.4.2 observed while the engine was 4.2) while `@lynx-js/react` has its own 0.129.x line. No published matrix ties a `@lynx-js/react` minor to an engine minor, so read the installed versions instead of asserting a pairing.

## Web target status

`@lynx-js/web-core` provides the Lynx web platform. It renders a `.lynx.bundle` inside a `<lynx-view>` custom element.

- Registry state observed: 0.26.7, while the engine is 4.2.
- The documentation gives a full integration path but **no production-readiness statement**, and no SSR guide was found even though `enableSSR` exists and defaults to `false`.
- Treat a web target as available but unverified for production. Do not present it as a way to ship one codebase to web and native without the caveat.

`<lynx-view>` attributes: `url` (required), `globalProps`, `initData`, `browser-config` with `pixelRatio`/`width`/`height`, `transform-vw`, `transform-vh`; properties `nativeModulesMap` and `onNativeModulesCall`. The bundle URL and every module URL are network resources, so treat both as untrusted input.

## Supply chain

A `.lynx.bundle` is a binary artifact containing both JS layers, loaded by a host that enforces `engineVersion`. Three consequences:

- Sign or checksum the bundle at the distribution layer; the format does not carry a signature.
- Serve it over TLS from a host you control. A replaced bundle runs with the native module access the validator allows.
- Keep the validator's allow-list narrow enough that a replaced bundle gains little.

## Checklist

- [ ] `engineVersion` is at or below the lowest engine on a shipping host, with the evidence recorded next to it.
- [ ] Any raised `engineVersion` names the feature that needs it and the host evidence that permits it.
- [ ] No native call reaches `NativeModules` outside the adapter under `src/shared/native/`.
- [ ] No native call appears in a render body or at module top level.
- [ ] The adapter handles a missing module rather than assuming the host registered it.
- [ ] Module-call authorization is considered for any privileged module, and the platform gap is stated.
- [ ] A new `initData` field ships with its host change or an absence check.
- [ ] Host dependencies pin a version that satisfies every bundled `engineVersion`.
- [ ] Embedded-host sizing and surrounding chrome were checked against the bundle's layout assumptions.
- [ ] The web target is reported as available but unverified for production.
- [ ] Bundle distribution is over TLS from a controlled host, and the module allow-list stays narrow.

## Sources

> Checked 2026-11-07. These statements restate the package's dated snapshot, `references/official/lynx/lynx-2026-11-07.md`, which cites the Lynx documentation, the engine release feed, and npm registry metadata read on 2026-11-07.

| Claim | Source |
|---|---|
| `engineVersion` semantics, the fatal 10204 error on an older engine, and the `'3.2'` default | https://lynxjs.org/guide/compatibility.md, https://lynxjs.org/rspeedy/plugin.md |
| Native modules being background-thread only and the per-`LynxView` auth validator from SDK 3.5 | https://lynxjs.org/guide/use-native-modules.md |
| Registration APIs and host permission boundary | https://lynxjs.org/guide/use-native-modules.md, https://lynxjs.org/llms.txt |
| CocoaPods, Maven, and HarmonyOS dependencies; `LynxView` as an embeddable native view | https://lynxjs.org/guide/start/integrate-with-existing-apps.md, https://lynxjs.org/llms.txt |
| Engine 4.2.0 on 2026-10-27, PrimJS 4.2.1 pinning, and the monthly cadence with its slippage | https://github.com/lynx-family/lynx/releases.atom, https://lynxjs.org/blog/lynx-open-source-roadmap-2026.md, https://lynxjs.org/blog/lynx-3-8.md |
| iOS 10 and Android 5.0 platform floor; unverified Windows/Linux hosts | https://github.com/lynx-family/lynx/develop/README.md |
| `@lynx-js/web-core` 0.26.7 with no production-readiness statement; `lynx-view` attributes | https://registry.npmjs.org/@lynx-js%2Fweb-core, https://lynxjs.org/llms-full.txt |
| Engine-gated features: `!important` and `flex` at 3.9, Trace from 3.4, WebAssembly from 3.8 Android-only | https://lynxjs.org/blog/lynx-3-9.md, https://lynxjs.org/guide/devtool/trace.md, https://lynxjs.org/guide/scripting-runtime/index.md |
| The engine-version evidence requirement, the adapter boundary, and the supply-chain advice | this package's convention, not an official Lynx requirement |
