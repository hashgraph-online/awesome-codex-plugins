# Lynx Native와 Platform

> Native module, host app integration, engine dependency, `engineVersion`, web target을 다룰 때 읽습니다. 이 파일의 `engineVersion` gate는 검토가 아니라 배포를 막습니다.

## `engineVersion`은 배포 제약입니다

`engineVersion`은 bundle이 실행될 수 있는 가장 오래된 engine을 선언합니다. N을 선언한 bundle은 N 이상 engine에서 실행되고 **그보다 오래된 engine에서는 fatal error 10204로 실패합니다**. 성능 저하 경로도, fallback도, build가 잡아 주는 runtime 경고도 없습니다.

그래서 Lynx 배포에서 가장 단단한 제약입니다.

- Build 설정이 아닙니다. Build는 값과 무관하게 성공합니다.
- Host가 협상할 수 있는 형태로 bundle에 version이 실리지 않습니다. Host가 만족하거나 화면이 죽습니다.
- `pluginReactLynx`의 default는 `'3.2'`입니다. 이 default는 하한이지 target이 아닙니다. 그대로 두면 안전하지만 더 높은 값이 열어 줄 새 CSS와 API도 함께 막습니다.

### Blocking review 규칙

**`engineVersion`을 올리는 변경은 bundle을 load하는 모든 host의 최저 engine version이 증거와 함께 기록되기 전까지 merge할 수 없습니다.** 증거는 이 순서로 받습니다.

1. 이 repository의 host dependency. iOS `Podfile`의 `pod 'Lynx', '<version>'` 줄, Android Gradle의 `org.lynxsdk.lynx:lynx:<version>`, HarmonyOS의 `@lynx/primjs` dependency입니다.
2. Repository가 가리키는 release-train 문서나 app version matrix.
3. 적용되는 app version과 함께 기록한 담당자 확인. Config 주석에 남깁니다.

셋 다 없으면 bundler가 하한을 검증할 수 없습니다. `engineVersion`을 현재 값으로 두고 빠진 증거를 보고하며, 기능을 쓰려고 올리지 않습니다. 말없이 올리면 검토를 통과하고 나서 가장 오래된 출시 host에서 화면이 죽습니다. 업데이트할 수 없는 사용자에게만 재현되는 최악의 실패 형태입니다.

```ts
pluginReactLynx({
  // 출시 host의 최저 engine: 3.9 (Android app 24.x가 org.lynxsdk.lynx:lynx:3.9.0 고정).
  engineVersion: '3.9',
})
```

같은 논리가 engine-gated 기능 전부에 적용됩니다. 3.9의 `!important`와 `flex` shorthand 변경, 3.9 이상의 `FetchBundle` lazy bundle loading, 3.4부터의 Trace, 3.8부터 Android 전용인 WebAssembly입니다. 이 중 하나를 쓰는 것은 host 하한에 대한 결정입니다.

## Native module

Native module은 host app이 등록하고 bundle이 호출합니다.

| Platform | 등록 |
|---|---|
| Android | `LynxEnv.inst().registerModule(...)` |
| iOS | `[globalConfig registerModule:...]` |

규칙입니다.

- Native module은 Background Thread Scripting에서만 쓸 수 있습니다. Render body나 module top level의 `NativeModules.X`는 main thread에서 throw합니다. `rules/lynx/threading.md`의 blocking gate입니다.
- Native module 접근은 `src/shared/native/` 아래 하나의 adapter로 모읍니다. 모든 호출 지점이 그곳을 지나므로 thread와 오류 처리를 한 번에 정합니다.
- 무엇이 존재하는지는 host가 정합니다. Bundle은 module 존재를 가정할 수 없습니다. 방어적으로 호출하거나 한 번 확인해 결과를 cache합니다.
- Camera, location, storage 같은 host permission은 Lynx 개념이 아닙니다. Bundle은 host의 native module과 `fetch` service가 허용하는 일만 할 수 있습니다. Module validator 외에 Lynx 수준 permission model은 없습니다.

### Module 호출 권한

SDK 3.5부터 host는 `(moduleName, methodName, params)`를 보고 허용 또는 거부를 반환하는 per-`LynxView` validator를 설치할 수 있습니다. 거부하면 JS error가 발생합니다.

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

Android와 iOS에서 사용할 수 있고, 문서를 읽은 시점에 HarmonyOS 지원은 대기 중이었습니다. Validator를 "이 화면은 wallet module을 호출하면 안 된다"의 seam으로 삼고, 화면별로 허용 module을 기록합니다.

## Host data 계약

`initData`와 `globalProps`는 local state가 아니라 host 입력입니다. Platform별 진입점과 typing은 `rules/lynx/ui-and-data.md`가 소유하고, 이 파일은 경계 규칙만 소유합니다. `initData`에 field를 추가하는 frontend 변경은 host 계약 변경이므로 host 변경과 함께 배포하거나 부재를 확인하는 code 뒤에 둡니다. Host보다 먼저 배포된 bundle은 `undefined`를 읽습니다.

## Host app integration

| Platform | Dependency | 비고 |
|---|---|---|
| iOS | CocoaPods `pod 'Lynx', '<version>'`와 `PrimJS`, 선택적으로 `LynxService`, `XElement`, `SDWebImage`, `SDWebImageWebPCoder` | Version이 모든 bundle의 `engineVersion`을 만족해야 함 |
| Android | Maven `org.lynxsdk.lynx:lynx`, `:lynx-jssdk`, `:lynx-trace`, `:primjs`, 선택적으로 `:lynx-service-image`, `:lynx-service-log`, `:lynx-service-http` | Gradle version이 `engineVersion`의 하한 |
| HarmonyOS | `@lynx/primjs` artifact | Engine API가 다르므로 별도 검증 |
| Windows | CMake와 LynxSDK | 이 패키지에서 미검증 |
| Web | `@lynx-js/web-core`와 `<lynx-view>` | 아래 참고 |

`LynxView` 자체가 native view이며 full-screen이나 embed 모두 가능합니다. Host가 크기 제약을 정하고 Lynx가 그 안의 `<page>`를 배치합니다. Loader가 splash, skeleton, native header로 view를 감싸면 그 chrome은 host code이고 그 배치는 bundle의 가정과 맞아야 합니다. Bundle이 전체 화면을 기대하는데 host가 height 60%를 주면 CSS bug처럼 보이는 layout이 나옵니다.

Engine version은 platform별로 함께 release되지만 host dependency는 따로 나아갑니다. Android를 3.9, iOS를 4.0에 고정하는 것은 정상이며, 둘 다 load하는 bundle의 실효 하한은 둘 중 낮은 값입니다.

## Engine release model

- 글을 쓰는 시점의 문서상 stable engine은 4.2이고 2026-10-27에 release됐습니다. 4.2.0은 Android Gradle, iOS pod, Harmony에서 PrimJS 4.2.1을 고정합니다.
- 3.8부터 격월 cadence가 월간으로 바뀌었습니다. 공개 계획은 이미 한 번 밀렸습니다. 4.2는 2026/09 계획이었고 2026-10-27에 나왔습니다. 계획을 의도로 보고, 의존할 일정으로 보지 않습니다.
- Platform 하한은 iOS 10과 Android 5.0(API 21) 이상입니다. macOS가 권장 개발 OS이고 Windows와 Linux host는 engine project가 "아직 검증하거나 보장하지 않음"으로 적습니다.

`@lynx-js/types`는 engine major 선을 따르고(engine이 4.2일 때 4.4.2 관측), `@lynx-js/react`는 자체 0.129.x 선을 씁니다. `@lynx-js/react` minor를 engine minor에 묶는 공개 matrix가 없으므로 짝을 주장하지 말고 설치 version을 읽습니다.

## Web target 상태

`@lynx-js/web-core`가 Lynx web platform을 제공합니다. `.lynx.bundle`을 `<lynx-view>` custom element 안에서 render합니다.

- 관측된 registry 상태는 0.26.7이고 engine은 4.2입니다.
- 문서는 통합 경로를 전부 주지만 **production 준비에 대한 서술이 없고**, `enableSSR`이 존재해 default `false`인데도 SSR guide를 찾지 못했습니다.
- Web target은 사용 가능하지만 production에 대해 미검증으로 다룹니다. 하나의 codebase를 caveat 없이 web과 native에 동시에 출시하는 수단으로 제시하지 않습니다.

`<lynx-view>` attribute는 `url`(필수), `globalProps`, `initData`, `pixelRatio`/`width`/`height`를 담는 `browser-config`, `transform-vw`, `transform-vh`이고 property는 `nativeModulesMap`과 `onNativeModulesCall`입니다. Bundle URL과 모든 module URL은 network 자원이므로 둘 다 신뢰할 수 없는 입력으로 다룹니다.

## 공급망

`.lynx.bundle`은 두 JS layer를 담은 binary artifact이고 `engineVersion`을 강제하는 host가 load합니다. 세 가지 결과가 따릅니다.

- 배포 계층에서 bundle에 서명하거나 checksum을 붙입니다. Format 자체는 signature를 나르지 않습니다.
- 통제하는 host에서 TLS로 제공합니다. 교체된 bundle은 validator가 허용한 native module 접근으로 실행됩니다.
- 교체된 bundle이 얻는 것이 적도록 validator 허용 목록을 좁게 유지합니다.

## Checklist

- [ ] `engineVersion`이 출시 host의 최저 engine 이하이고 증거를 옆에 기록했습니다.
- [ ] 올린 `engineVersion`이 필요한 기능과 그것을 허용하는 host 증거를 함께 밝혔습니다.
- [ ] `src/shared/native/`의 adapter 밖에서 `NativeModules`에 닿는 native 호출이 없습니다.
- [ ] Render body나 module top level에 native 호출이 없습니다.
- [ ] Adapter가 host의 module 등록을 가정하지 않고 부재를 처리합니다.
- [ ] 권한이 있는 module에 module 호출 권한 검토를 했고 platform 격차를 밝혔습니다.
- [ ] 새 `initData` field가 host 변경과 함께 또는 부재 확인과 함께 배포됩니다.
- [ ] Host dependency version이 bundling된 모든 `engineVersion`을 만족합니다.
- [ ] Embed된 host의 크기와 주변 chrome을 bundle의 layout 가정과 대조했습니다.
- [ ] Web target을 사용 가능하지만 production 미검증으로 보고했습니다.
- [ ] Bundle 배포가 통제 host의 TLS를 거치고 module 허용 목록이 좁습니다.

## Sources

> 확인 2026-11-07. 이 서술은 이 패키지의 날짜가 있는 snapshot `references/official/lynx/lynx-2026-11-07.md`를 재진술한 것이며, 그 파일이 2026-11-07에 읽은 Lynx 문서, engine release feed, npm registry metadata를 인용합니다.

| Claim | Source |
|---|---|
| `engineVersion` 의미, 구형 engine에서의 fatal 10204, `'3.2'` default | https://lynxjs.org/guide/compatibility.md, https://lynxjs.org/rspeedy/plugin.md |
| Native module이 background-thread 전용이고 SDK 3.5부터의 per-`LynxView` auth validator | https://lynxjs.org/guide/use-native-modules.md |
| 등록 API와 host permission 경계 | https://lynxjs.org/guide/use-native-modules.md, https://lynxjs.org/llms.txt |
| CocoaPods, Maven, HarmonyOS dependency, embed 가능한 native view인 `LynxView` | https://lynxjs.org/guide/start/integrate-with-existing-apps.md, https://lynxjs.org/llms.txt |
| 2026-10-27의 engine 4.2.0, PrimJS 4.2.1 고정, 월간 cadence와 그 지연 | https://github.com/lynx-family/lynx/releases.atom, https://lynxjs.org/blog/lynx-open-source-roadmap-2026.md, https://lynxjs.org/blog/lynx-3-8.md |
| iOS 10과 Android 5.0 platform 하한, 미검증 Windows/Linux host | https://github.com/lynx-family/lynx/develop/README.md |
| `@lynx-js/web-core` 0.26.7과 production 준비 서술 부재, `lynx-view` attribute | https://registry.npmjs.org/@lynx-js%2Fweb-core, https://lynxjs.org/llms-full.txt |
| Engine-gated 기능: 3.9의 `!important`와 `flex`, 3.4부터의 Trace, 3.8부터 Android 전용 WebAssembly | https://lynxjs.org/blog/lynx-3-9.md, https://lynxjs.org/guide/devtool/trace.md, https://lynxjs.org/guide/scripting-runtime/index.md |
| Engine version 증거 요구, adapter 경계, 공급망 조언 | 공식 Lynx 요구가 아니라 이 패키지의 관례 |
