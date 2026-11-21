# Tauri v2 보안 경계

> Tauri capability, plugin permission, custom command, filesystem/network scope, remote content, updater, credential flow 또는 release configuration을 추가하거나 승인하기 전에 읽습니다.

## 근거, 권한, 분류

**공식 사실.** Tauri v2는 capability로 어떤 window/webview가 permission을 받을지 제한하고, permission은 command를 allow 또는 deny할 수 있으며, scope는 permission이 접근할 수 있는 대상을 제한합니다. [Tauri v2 근거 원장](../../references/official/tauri/tauri-v2-2026-11-04.ko.md), [Capabilities](https://v2.tauri.app/security/capabilities/), [Permissions](https://v2.tauri.app/security/permissions/), [Scopes](https://v2.tauri.app/security/scope/)를 참조합니다. 이 공식 페이지는 2026-11-04에 근거로 확인했으며 변경될 수 있습니다. 버전 의존 configuration 변경 전에는 원장과 최신 공식 문서를 다시 확인합니다.

**안전 정책.** WebView, 렌더링된 모든 JavaScript, navigation/deep-link input, IPC argument, event payload, local content 및 remote response를 형식이 잘못되거나 악의적일 수 있는 입력으로 취급합니다. frontend는 authorization authority가 아니며 browser origin 기대만으로 native 보안 경계가 되지 않습니다.

**프로젝트 규약.** 보안 결정은 `src-tauri/capabilities/`와 (app command용) `src-tauri/permissions/`의 명시적이고 검토 가능한 파일, 그리고 좁게 제한한 plugin configuration에 둡니다. 권한 있는 동작에 default, 넓은 plugin permission 또는 문서화되지 않은 inherited capability를 사용하지 않습니다.

이 규칙이 capability, credential, update publication, release, deployment, key rotation, destructive operation 또는 production write를 승인하지는 않습니다. gate 통과와 별도로 이 작업에는 명시적인 사용자 권한이 필요합니다.

---

## Command 측 신뢰 경계

capability는 WebView가 작업을 요청할 수 있는지 제어하지만 요청 자체를 안전하게 만들지는 않습니다. 모든 custom Rust command는 독립적으로 다음을 수행해야 합니다.

1. 크기가 제한된 타입 request DTO로 역직렬화합니다.
2. type, required field, size, format, enumeration value, path/URL canonicalization 및 작업별 limit을 검증합니다.
3. frontend가 보낸 role, path, feature flag 또는 `isAdmin` field가 아니라 신뢰할 수 있는 native state 또는 인증된 remote service에서 관련 local/session/user identity를 설정합니다.
4. 해당 identity에 대해 작업과 resource를 authorize합니다.
5. least-privileged service를 통해 실행하고 안전한 구조화 result/error를 반환합니다.
6. 승인된 metadata만 audit 또는 log하며 secret이나 제한 없는 user content를 절대 log하지 않습니다.

**안전 정책:** frontend validation은 UX 개선용일 뿐입니다. command-side validation, authorization, resource ownership check, rate/size limit 또는 안전한 error mapping을 대체할 수 없습니다. 숨긴 menu item, disabled button 또는 route guard는 authorization control이 아닙니다.

**규약:** 더 좁은 domain input이 가능한데 filesystem path, shell fragment, arbitrary URL, raw SQL, serialized closure 또는 plugin option bag를 command가 받지 않게 합니다. Native 측에서 ID를 trusted record/service로 해석합니다. DTO와 error 요구사항은 [tauri-ipc.ko.md](tauri-ipc.ko.md)를 참조합니다.

---

## Custom command manifest와 최소 권한

**공식 사실.** `invoke_handler`로만 등록한 command는 기본적으로 모든 application window/webview에서 사용할 수 있으므로 등록 자체가 암묵적 allow입니다. Capability로 custom command를 제한하려면 Tauri `AppManifest`에 application command를 선언하고, `AppManifest::commands`가 application manifest용 `allow-$command`와 `deny-$command` permission을 자동 생성하게 한 뒤 대상 window/webview label에 부여합니다. [Capability](https://v2.tauri.app/security/capabilities/), [App Permissions](https://v2.tauri.app/security/permissions/), [Runtime Authority](https://v2.tauri.app/security/runtime-authority/)를 참조합니다. 기존 `#application-manifest` anchor는 사라졌고 `AppManifest::commands` 안내는 capabilities page의 "Target Platform" 앞부분에 있습니다. 정확한 `build.rs`, generated schema, permission 문법은 version-sensitive하므로 설치된 Tauri version의 schema와 공식 예시를 사용합니다.

**공식 사실.** Permission 식별자는 `<name>:default` 또는 `<name>:<command-name>` 형식이며 prefix가 그 permission을 소유한 manifest를 선택합니다. Application permission은 application manifest에서 해석되므로 prefix 없이(`allow-settings-read`) 씁니다. Application permission을 `settings:allow-read`로 쓰면 ACL이 `settings`라는 plugin manifest를 찾게 되어 build가 "permission not found"로 실패합니다.

**프로젝트 규약:** 모든 custom command는 `build.rs`의 `AppManifest` 선언 -> `src-tauri/permissions/`의 named permission -> 대상 label의 least-privilege capability -> Rust validation/authorization이라는 하나의 검토 가능한 chain을 따릅니다. Plugin permission과 app-command permission은 분리하고, app-command 식별자는 prefix 없이 유지합니다.

```toml
# src-tauri/permissions/settings.toml
[[permission]]
identifier = "allow-settings-read"
description = "Allows reading non-secret settings."
commands.allow = ["settings_read"]

[[permission]]
identifier = "allow-settings-update"
description = "Allows updating non-secret settings."
commands.allow = ["settings_update"]
```

```json
// src-tauri/capabilities/main.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "main-settings",
  "windows": ["main"],
  "permissions": ["allow-settings-read", "allow-settings-update"]
}
```

이 snippet은 의도한 검토 형태를 보이는 것이며, generated schema를 대체하는 복사-붙여넣기 예시나 해당 작업을 부여하는 승인이 아닙니다. `AppManifest::commands`를 이미 쓰던 프로젝트에는 자동 생성된 `allow-<command>` permission이 있으므로 plugin식 prefix를 직접 쓰지 말고 그 이름을 참조합니다.

- **안전 정책:** capability마다 하나의 label/window role이 필요한 최소 command/plugin permission만 부여합니다. settings window, main window, authentication window, untrusted/remote-content window가 편의상 하나의 넓은 capability를 상속하면 안 됩니다.
- **안전 정책:** 명시적 allow permission과 좁게 근거를 둔 deny를 사용합니다. 하나의 작업이면 충분한 곳에 plugin의 `default` 또는 모든 command를 부여하지 않습니다. command를 제거하면 오래된 grant도 제거합니다.
- **규약:** 자명하지 않은 모든 permission, scope entry, remote origin, label match 옆에 사람이 읽을 수 있는 reason을 둡니다. capability diff는 security-sensitive change로 검토합니다.
- **규약:** 의도한 label의 allowed call과 다른 관련 label 각각의 denied call을 모두 테스트합니다. denied test가 없으면 security-sensitive change를 막습니다.

---

## Plugin permission과 scope

**공식 사실.** Tauri plugin permission과 scope는 v2 access-control model의 일부입니다. scope는 permission이 도달할 수 있는 data 또는 resource를 제한하며, 문법과 지원 여부는 plugin별로 다릅니다. [Permissions](https://v2.tauri.app/security/permissions/)와 [Scopes](https://v2.tauri.app/security/scope/)를 참조하세요(2026-11-04 접근; 위 근거 주의사항 적용).

- **안전 정책:** 정확한 command, resource, origin, label이 필요한지 확인한 뒤에만 filesystem, shell, HTTP, opener, clipboard, notification, process, deep-link, asset permission을 부여합니다.
- **안전 정책:** filesystem access는 필요한 최소 directory/file과 allowed operation으로 scope를 제한합니다. resolution 뒤 path를 canonicalize하고 validate하며 traversal, 관련되는 경우 symlink escape, user-controlled unrestricted root를 거부합니다.
- **안전 정책:** plugin이 지원하면 HTTP/remote access를 명시적 scheme, host, path, method, request shape로 scope 제한합니다. user-provided URL을 일반 network authority로 바꾸지 않습니다.
- **안전 정책:** 범용 shell/process launcher를 노출하지 않습니다. 승인된 작업을 고정 executable/argument와 검증된 domain input을 가진 고정 native command로 모델링합니다.
- **규약:** plugin의 현재 generated schema와 공식 문서로 scope를 표현합니다. configuration key를 지어내거나 scope 동작이 plugin 간에 같다고 가정하지 않습니다.

---

## CSP, asset, remote content

**공식 사실.** Tauri는 CSP configuration과 asset protocol을 보안 관련 기능으로 문서화합니다. [Content Security Policy](https://v2.tauri.app/security/csp/)와 [Asset Protocol](https://v2.tauri.app/security/asset-protocol/)을 참조합니다(2026-11-04 확인, 위 근거 주의사항 적용).

**안전 정책:** packaged SPA에 맞는 제한적 CSP를 배포합니다. `default-src`는 제한적으로 유지하고 필요한 script/style/connect/image/font/media/frame source만 명시합니다. 명시적이고 문서화된 호환성 필요가 security review를 받지 않았다면 넓은 wildcard, `unsafe-eval`, `unsafe-inline`로 CSP를 약화하지 않습니다. build를 통과시키려고 CSP modification을 끄거나 remote script URL을 주입하지 않습니다.

**안전 정책:** Tauri WebView에 로드되어도 remote content는 신뢰할 수 없습니다. 신뢰할 수 없는 external content는 system browser로 여는 것을 우선합니다. in-app remote-content window가 불가피하면 privileged command/plugin이 없는 별도 label과 capability로 격리하고, navigation/origin을 제한하며 credential, token, sensitive IPC/event data를 붙이지 않습니다.

**안전 정책:** 필요한 경우에만 asset protocol로 local file을 노출합니다. resolve된 file/resource마다 authorize하고 가장 좁은 scope를 사용하며 URL을 올바르게 encode하고 user path를 unrestricted asset URL로 바꾸지 않습니다. `asset:` URL은 요청자가 대상 파일을 읽을 권한이 있다는 증거가 아닙니다.

**공식 사실.** `app.security.assetProtocol.scope`는 `FsScope`이며 허용 glob 배열 또는 `allow`, 선택적 `deny`, 선택적 `requireLiteralLeadingDot`을 가진 object입니다. 배열 형식은 deny를 쓸 수 없고 leading-dot 매칭도 바꿀 수 없습니다. Resolve된 path는 대개 절대 경로이므로 `*/**`가 매칭되지 않으며, resolve된 path를 반영하는 `$APPCACHE/**/*` 같은 pattern을 쓰고 "이 directory 아래 전부"에는 `**`보다 `**/*`를 씁니다. Unix에서 `requireLiteralLeadingDot` 기본값은 `true`이므로 wildcard가 `.cache` 같은 dot-prefixed segment와 매칭되지 않습니다. [Asset protocol scope](https://v2.tauri.app/security/asset-protocol/)를 참조합니다.

**안전 정책:** asset scope는 절대 경로 또는 base-directory pattern으로 쓰고, 민감한 하위 tree에는 명시적 `deny`를 추가합니다. Path가 load되게 만들려고 넓은 allow list에 `requireLiteralLeadingDot: false`를 두지 않습니다. 사용자가 runtime에 directory를 고르면 static 설정을 넓히지 말고 허용된 scope를 의도적으로 persist합니다.

**규약:** 모든 CSP exception, remote origin, asset-protocol 사용을 owner, purpose, label, capability, removal condition과 함께 기록합니다. 새 `connect-src`, remote origin 또는 asset scope는 blocking security review change로 취급합니다.

---

## WebView permission과 navigation 제한

**공식 사실.** Tauri 2.12부터 `WebviewWindowBuilder::on_permission_request`가 `PermissionKind`를 받아 `PermissionResponse::{Allow, Deny, Default}`를 반환합니다. 이는 geolocation, notification, camera/microphone, MIDI, sensor, media key system access, local font, window management, pointer lock, 자동 다운로드, file system access, autoplay 같은 webview 수준 요청을 다룹니다. 이 결정은 capability가 아니라 webview가 강제하므로 ACL이 이를 대신할 수 없습니다. [Announcing Tauri 2.12](https://tauri.app/blog/tauri-2.12/)를 참조합니다.

- **안전 정책:** permission handler가 있으면 제품이 실제로 필요한 kind만 allow하고 나머지는 `Default` 또는 `Deny`로 둡니다. 모든 요청에 `Allow`를 반환하지 않습니다. 전면 allow는 주입된 script에 앱과 같은 device capability를 넘깁니다.
- **안전 정책:** handler는 두 번째 gate이지 대체물이 아닙니다. 그 결과 data를 쓰는 command는 여전히 Rust에서 validate/authorize하며, 어떤 window가 해당 command를 호출할 수 있는지는 capability 집합이 계속 결정합니다.
- **공식 사실:** `app > windows > limitNavigationsToAppBoundDomains`는 WKWebView navigation을 `src-tauri/Info.ios.plist`의 `WKAppBoundDomains` 배열에 등록한 domain으로 제한합니다. WKWebView에서 Service Worker를 쓰려면 필요하고 기본값은 `false`입니다. [Configuration reference](https://v2.tauri.app/reference/config/)를 참조합니다.
- **안전 정책:** remote content를 load하는 앱은 navigation 제한을 켜고 의도한 domain만 등록합니다. Navigation allow list를 platform 다듬기가 아니라 보안 설정으로 취급하고, 등록되지 않은 navigation이 실제로 차단되는지 테스트합니다.
- **규약:** `app > appDirectoriesOverride`를 켜면 Tauri와 해당 API를 쓰는 plugin의 `app_config_dir`, `app_data_dir`, `app_local_data_dir`, `app_cache_dir`, `app_log_dir` 및 `$APPCONFIG` 계열 path variable이 함께 옮겨집니다. 켠 뒤에는 OS 기본값을 가정하지 말고 asset scope, log path, cache 가정을 다시 확인합니다.

---

## Secret, remote service, updater 경계

**안전 정책:** frontend bundle, Tauri configuration, capability, permission, log, source map, updater artifact는 secret store가 아닙니다. API secret, private updater signing key, service-account credential 또는 production token을 여기에 embed하지 않습니다. environment variable 문법은 전달 방법을 바꿀 뿐 client-side secrecy를 만들지 않습니다.

**안전 정책:** native 또는 remote operation에 쓰는 credential에는 명시적 권한, 승인된 platform storage 전략, rotation/revocation 동작, 최소 scope 및 redacted logging이 필요합니다. native store에서 가져온 secret은 authorized native service만 사용할 수 있으며 `invoke`, event, query cache, route data 또는 React state를 통해 왕복시키지 않습니다.

**공식 사실.** Tauri updater는 plugin/configured update mechanism이며 signed update artifact는 security-sensitive합니다. [Updater Plugin](https://v2.tauri.app/plugin/updater/)과 [Tauri Security](https://v2.tauri.app/security/)를 참조하세요(2026-11-04 접근; 위 근거 주의사항 적용).

**공식 사실.** CLI 2.12.0부터 `tauri build`가 updater 서명의 trusted comment에 앱 버전을 기록하고, updater plugin의 `requireSignedVersion` option이 알려진 `version`과 서명된 아티팩트가 다른 응답을 거부합니다. Update endpoint 응답은 서명되지 않으므로 이 option이 없으면 버전 번호가 다른 릴리스와 짝지어질 수 있습니다. `tauri plugin add updater`는 대상 프로젝트에서 이 option을 켭니다. [`@tauri-apps/cli` v2.12.0 release note](https://github.com/tauri-apps/tauri/releases/tag/@tauri-apps/cli-v2.12.0)를 참조하며, plugin 문서 page에는 아직 이 option이 없으므로 설치된 plugin version에서 확인합니다.

**안전 정책:** 명시적인 권한 없이 production updater endpoint를 configure, sign, publish하거나 대상으로 테스트하지 않습니다. private signing material은 repository와 build artifact 밖에 둡니다. Update endpoint trust를 의도적으로 고정/관리하고 auto-update 전에 non-production 환경에서 release process를 validate하며, 활성화 전에 rollback/revocation owner를 정의합니다.

**안전 정책:** endpoint가 둘 이상의 릴리스를 제공할 수 있는 앱은 `requireSignedVersion`을 켜 둡니다. 오래된 endpoint를 맞추려고 끄면 버전 번호를 아티팩트에 결속하는 유일한 검사를 없애는 것입니다.

---

## Tauri v1 access-control pattern 재도입 금지

**공식 사실.** Tauri v2는 v1에서 configuration과 access control을 변경했습니다. v1 예시를 복사하지 말고 최신 migration guide를 따릅니다. [Tauri 1.0에서 마이그레이션](https://v2.tauri.app/start/migrate/from-tauri-1/)을 참조하세요(2026-11-04 접근; 위 근거 주의사항 적용).

다음 v1 유래 pattern은 차단하고 교체합니다.

- `tauri.conf.json`의 `tauri.allowlist` 또는 하나의 넓은 allowlist: 대신 v2 capability, permission, plugin scope를 사용합니다.
- 애플리케이션 전반 invoke shortcut인 `@tauri-apps/api/tauri` 또는 `window.__TAURI__` global: 타입된 native adapter 안에서만 명시적 v2 API import를 사용합니다.
- frontend route/UI check를 command authorization으로 신뢰: Rust에서 validation과 authorization을 강제합니다.
- 기능을 동작시키려고 broad filesystem/shell/http access를 추가: 좁은 capability, permission, scope 및 고정 domain command를 사용합니다.
- 모든 window/webview label에 하나의 capability를 match: label/role별 최소 권한 capability를 사용합니다.
- bundled web asset, frontend environment variable 또는 updater configuration을 secret 보관 장소로 취급.

**Upgrade 점검.** 두 version 경계가 기존 access-control 설정의 동작을 바꿉니다.

- **`2.12.0` 미만:** remote origin에 대해 command를 deny한 capability가 local app에서도 함께 deny했습니다. Origin match 결과를 버렸기 때문입니다. Upgrade하면 각 deny가 자기 실행 컨텍스트로 한정되므로 이전에 막혔던 local 호출이 성공할 수 있습니다. Upgrade를 승인하기 전에 `deny`를 가진 capability마다 allow/deny 근거를 다시 실행합니다.
- **`2.11.6` 미만:** channel queue entry와 대용량 invoke 응답이 이를 만든 webview에 결속되지 않았습니다([GHSA-w28w-mhc8-qvjv](https://github.com/tauri-apps/tauri/security/advisories/GHSA-w28w-mhc8-qvjv)). Workaround가 없으므로 channel을 쓰는 프로젝트는 설정을 조정하는 대신 upgrade합니다.

---

## 차단 보안 gate

적용되는 모든 gate가 통과할 때까지 해당 변경의 구현, review approval 및 release를 차단합니다.

1. **신뢰 gate:** threat boundary, untrusted input, authorized identity, command-side validation/authorization이 명시되어 있으며 UI-only control을 enforcement로 인정하지 않습니다.
2. **Manifest gate:** 각 custom command는 설치된 version의 application manifest에 선언되고 검토된 app-command permission을 가지며 의도한 capability label만 이를 부여합니다. 각 plugin operation에는 좁은 permission과 scope가 있습니다.
3. **최소 권한 gate:** capability, default grant, scope, remote origin, filesystem root, shell executable, label match 어느 것도 문서화된 필요보다 넓지 않습니다.
4. **WebView gate:** CSP, remote-content isolation, navigation 제한, webview permission handler, asset-protocol exposure, event/IPC data flow가 untrusted content에 privileged access를 주지 않습니다.
5. **secret/update gate:** secret이 client-distributed material 또는 IPC에 도달하지 않으며 credential/updater configuration, signing, publication, production endpoint에 명시적 권한과 검토된 lifecycle이 있습니다.
6. **호환성 gate:** v1 allowlist/global/direct-invoke pattern이 남아 있지 않고, 실제 설치 버전에 대해 generated v2 schema와 최신 official guidance를 확인했으며, app-command permission이 prefix 없는 식별자를 씁니다.
7. **version gate:** channel 또는 대용량 IPC 응답을 쓰는 프로젝트는 Tauri `2.11.6` 이상을 실행하고, capability deny를 가진 프로젝트는 `2.12.0`을 넘긴 뒤 allow/deny 쌍을 다시 테스트했습니다.
8. **근거 gate:** 변경에 allowed/denied label/resource case, malformed input, authorization failure, 해당하는 listener cleanup, safe-error behavior가 포함됩니다. focused negative evidence 없는 security-sensitive change는 차단됩니다.

blocker는 design을 좁히거나 명시적 권한과 문서화된 review evidence를 얻어 해결합니다. check를 끄거나 catch-all permission을 추가하거나 WebView를 trusted라고 선언해서 해결하지 않습니다.

## Sources

> 링크 확인 2026-11-04.

| 주장 | 출처 |
|---|---|
| Capability, permission, scope, runtime authority, application manifest의 기본 allow 동작, CSP, asset protocol, updater 보안 동작 | [tauri-v2-2026-11-04.ko.md](../../references/official/tauri/tauri-v2-2026-11-04.ko.md); <https://v2.tauri.app/security/capabilities/>; <https://v2.tauri.app/security/permissions/>; <https://v2.tauri.app/security/scope/>; <https://v2.tauri.app/security/runtime-authority/>; <https://v2.tauri.app/security/csp/>; <https://v2.tauri.app/security/asset-protocol/>; <https://v2.tauri.app/plugin/updater/> |
| Prefix 없는 application permission 식별자와 `allow-$command` 자동 생성 | <https://v2.tauri.app/security/permissions/>; <https://raw.githubusercontent.com/tauri-apps/tauri/dev/crates/tauri-build/src/acl.rs> |
| Webview permission request handler와 `limitNavigationsToAppBoundDomains` | <https://tauri.app/blog/tauri-2.12/>; <https://github.com/tauri-apps/tauri/releases/tag/tauri-v2.12.0>; <https://v2.tauri.app/reference/config/> |
| Updater 서명 버전 결속과 `requireSignedVersion` | <https://github.com/tauri-apps/tauri/releases/tag/@tauri-apps/cli-v2.12.0> |
| `2.11.6` channel IPC floor와 `2.12.0` capability deny scope 수정 | <https://github.com/tauri-apps/tauri/security/advisories/GHSA-w28w-mhc8-qvjv>; <https://github.com/tauri-apps/tauri/releases/tag/tauri-v2.12.0> |
| "v1 pattern을 다시 도입하지 않는다" 목록의 근거인 v1 -> v2 access-control 변화 | [tauri-v2-2026-11-04.ko.md](../../references/official/tauri/tauri-v2-2026-11-04.ko.md); <https://v2.tauri.app/start/migrate/from-tauri-1/> |
| Command 측 validation, authorization, 최소 권한, secret 처리, 허용/거부 근거 | 이 파일의 안전 정책과 이 저장소의 규약; 외부 출처 없음 |
