# 위험 비례 테스트와 검증

> Tauri v2 + Vite + React + TanStack Router + TanStack Query 아키텍처 변경의 근거를 선택할 때 이 규칙을 적용한다. 프로젝트에 이미 있는 명령을 실행한다. 이 규칙을 만족하기 위해 테스트 프레임워크를 추가하거나, 네이티브 런타임을 위조하거나, 배포/서명하거나, 실제 사용자 데이터를 변경하지 않는다.

## 변경한 경계에 따라 근거를 선택한다

| 변경한 경계 | 최소 근거 | 위험이 커지면 추가할 근거 |
|---|---|---|
| 순수 React UI, route 상태, query 표시 | pending, success, error, not-found 동작의 focused frontend test | suspense, retry, accessibility, reload 동작의 browser-level navigation test |
| Vite Router plugin, route file, provider wiring | route tree를 생성하고 Router plugin이 React plugin보다 앞서는지 확인하는 production Vite build | validated search input을 포함해 생성된 route를 이동하는 browser-level navigation |
| Query factory, loader, `loaderDeps`, mutation | 새 `QueryClient`를 쓰는 focused test; key input, loader cache reuse, targeted invalidation 검증 | stale/failed fetch와 route preload 테스트로 Router가 아닌 Query가 freshness를 소유함 입증 |
| Desktop API adapter 또는 IPC schema | type이 지정된 mock으로 adapter 단위 테스트; command 이름, 인자, 결과 정규화, rejection mapping 검증 | privileged operation의 Rust command test와 capability/permission 검토 |
| Rust command, state, filesystem, plugin, authorization | validation, authorization, state transition, error form을 다루는 Rust unit/integration test | OS 통합, window, dialog, filesystem, updater, plugin 동작을 위한 disposable profile의 `@wdio/tauri-service` native E2E |
| 패키징된 Tauri navigation 또는 deep link | 패키징된 test build의 native E2E: launch, 생성된 route 간 이동, 지원하는 deep link 열기, active route reload | platform별 protocol registration과 거부되거나 malformed인 deep-link payload 테스트 |
| capability, permission, scope, CSP, asset policy, secret | manifest와 최소 권한 계약에 대한 static security review | 허용 경로는 동작하고 거부 경로는 안전하게 실패함을 보이는 native E2E |
| 이 skill package | skill-focused validation: frontmatter/link, bilingual rule parity, source-ledger date/version field, 관련 eval case | 상위 workflow가 요구하는 전체 repository skill validation |

변경한 경계를 우회하는 테스트는 근거가 아니다. 예를 들어 component mock은 Rust authorization을 입증하지 못하며, 성공한 Vite build는 패키징된 navigation이나 deep-link handling을 입증하지 못하고, 허용된 IPC 호출의 성공은 거부가 강제됨을 입증하지 못한다.

## Frontend, Router, Query 사례

UI test는 결정적으로 유지하고, type이 지정된 router context로 의존성을 주입한다. 변경한 생성 route 또는 query 기반 route마다 해당되는 다음 사례를 다룬다.

1. Vite production build가 file route에서 route tree를 생성하고, `@tanstack/router-plugin/vite`가 React plugin보다 먼저 배치된다.
2. module이 소유하는 `QueryClient` 하나와 router 하나가 생성되고, `QueryClientProvider`와 `RouterProvider`가 같은 instance를 받는다.
3. Root route가 type이 지정된 router context를 선언하고, route code는 raw Tauri bridge가 아닌 좁은 `DesktopApi`를 받는다.
4. loader가 shared context client와 component가 `useSuspenseQuery`로 읽는 동일한 `queryOptions` factory를 사용해 `ensureQueryData`를 호출한다.
5. 결과를 바꾸는 route parameter와 검증된 `loaderDeps` search 값이 query key/factory input에 나타난다. 잘못된 search input은 route가 정의한 validation 동작을 따른다.
6. Query가 freshness 소유자일 때 `defaultPreloadStaleTime: 0`이 있고, freshness/refetch assertion은 Query policy에 속한다.
7. navigation 중 pending UI가 나타난다. 예상된 fetch/IPC rejection은 error UI와 retry path에 도달하고, 없는 resource는 not-found UI에 도달한다.
8. 성공한 mutation은 영향받은 key만 invalidate하거나 갱신하고, view는 새 authoritative result를 표시한다.

테스트마다 새 `QueryClient`를 사용한다. Assertion을 가리는 retry와 timer는 test client에서 끄거나 제어할 수 있으나 production default는 production policy로 남긴다. `window.__TAURI__`나 Router internal이 아니라 좁은 `DesktopApi`를 mock한다. Mock은 adapter 계약에 관련된 success, rejection, malformed/unexpected-result path를 재현해야 한다.

## Rust, IPC, Native E2E 사례

Rust는 happy-path JavaScript만이 아니라 policy boundary에서 테스트한다.

- 변경한 command마다 deserialization, input validation, authorization, path/scope validation, state isolation, typed response serialization, 안전한 error를 unit/integration test한다.
- filesystem 또는 persistence 사례에는 temporary directory, test state, 명시적 cleanup을 쓴다. test code가 user profile, production endpoint, signing credential, 실제 secret store를 가리키게 하지 않는다.
- privileged command에는 authorized request와 unauthorized, malformed, out-of-scope request를 모두 입증한다. 후자는 side effect 또는 민감한 error 공개 없이 실패해야 한다.
- 패키징된 navigation에는 unsigned development/test package를 disposable profile로 실행한다. 최초 생성-route rendering, in-app navigation, 지원하는 deep link, active route의 reload를 검증하고, test가 만든 artifact만 정리한다.
- client route guard test를 authorization 주장으로 바꾸지 않는다. native command authorization에는 Rust-side 근거가 필요하다.

**권장 native harness.** Tauri는 WebdriverIO와 `@wdio/tauri-service`를 권장 end-to-end 경로로 문서화하며 Windows, Linux, macOS를 지원합니다.

- 기본 `embedded` provider는 `tauri-plugin-wdio-webdriver`로 앱 내부 WebDriver server를 실행하므로 외부 driver를 설치하지 않습니다. macOS 지원도 이 경로입니다. 외부 driver를 선호하면 Windows/Linux는 `tauri-driver`를 쓰고, CrabNebula fork는 모든 platform을 지원하지만 macOS에는 유료 key가 필요합니다.
- `tauri-plugin-wdio`는 backend 접근을 추가합니다. Rust 측 호출을 위한 `browser.tauri.execute()`, command(IPC) mocking, frontend/backend log 수집입니다. Native authorization과 거부는 UI 상태에서 추론하지 말고 `execute()`로 확인합니다.
- Service의 **browser mode**는 Vite dev server에 붙은 일반 Chrome에서 frontend를 실행하고 `invoke()`를 가로챕니다. 이는 renderer 근거일 뿐이며 packaged app을 실행하지 않으므로 packaging, plugin, OS dialog, native permission 근거를 대신하지 못합니다.
- Test project에서 service와 plugin version을 고정하고 실행에 쓴 provider를 기록하며, release-critical flow는 한 provider의 결과가 다른 OS로 전이된다고 가정하지 말고 출시 대상 OS마다 다시 실행합니다.

## Build와 Security 게이트

패키징된 Vite SPA에서 build와 package 근거는 반드시 다음을 모두 확립해야 한다.

- Vite production build가 완료되고 정적 frontend asset을 내보내며, Router plugin이 React plugin보다 먼저 배치된 상태로 file route에서 route tree를 생성한다.
- Tauri build가 의도한 frontend distribution을 소비하고, navigation 또는 native behavior가 변경됐을 때 생성된 package가 대상 test environment에서 실행된다.
- 패키징된 app test가 development server에 의존하지 않고 생성-route navigation, 지원하는 deep link, active route reload를 다룬다.
- 최종 capability/permission/scope/CSP/asset 설정이 테스트한 동작에 필요한 command, window, origin, path, asset에만 권한을 준다.
- test log, snapshot, fixture data, error report, 패키징된 frontend asset에 credential, private path, raw native error가 없다.

실패한 Vite production build, 생성 route tree 누락, 잘못된 plugin order, 패키징된 navigation/deep-link/reload 실패, 확장된 capability, 테스트하지 않은 denial path는 모두 release blocker로 취급한다.

## 범위가 제한된 수정 루프

검증은 범위가 제한된 수정 루프이며, 끝없는 최적화가 아니다.

1. 가장 작은 위험 적합 gate를 실행하고, 실패한 command/scenario, 영향받은 boundary, 관찰한 failure를 기록한다.
2. 확립된 architecture contract를 유지하며 입증된 원인만 수정한다.
3. 동일한 gate와 직접 영향을 받은 gate를 다시 실행한다.
4. **같은 gate에 대해 validate/fix pass는 최대 두 번만** 수행한다. 성공하면 즉시 멈춘다.

두 번째 pass도 실패하면 코드 변경을 멈춘다. 관찰한 두 failure, 바뀐 hypothesis, command/scenario, environment constraint, 가장 작은 unresolved blocker를 보고한다. 통과를 만들기 위해 test, permission, CSP, type check, error handling을 약화하지 않는다. 필요한 production deployment, signing, credential, destructive migration, 외부 action은 수행하지 말고 명시적 권한을 요청해 중단한다.

## 스킬 패키지 검사

이 skill package를 변경하면 저장소 root에서 다음 검사를 순서대로 실행한다.

```bash
node -e "const fs=require('node:fs'); const p='skills/hyper-architecture/assets/evals/tauri-cases.jsonl'; fs.readFileSync(p,'utf8').trim().split(/\\n/).forEach((line,index)=>{try{JSON.parse(line)}catch(error){throw new Error(`${p}:${index+1}: ${error.message}`)}});"
bash scripts/check-sources.sh --offline
bash scripts/verify.sh
```

저장소의 skill-corpus validator가 구조 gate다. 저장소 유지보수 명령이므로 형제 skill의 경로를 넣지 않고 이름으로만 적는다: `validate-skills-corpus.sh --root skills --only hyper-architecture --json`. JSONL parse는 fixture-integrity gate이며 behavior 실행이 아니다. 이 package에는 package-specific behavior runner가 없다. Fixture의 stable positive, negative, boundary, missing-context, unsafe-action, source-guard, regression case를 직접 검사하고 실행했다고 주장하지 않는다. Validator를 지어내거나 fixture 존재를 behavior 증거로 취급하지 않는다.

## Readback checklist

Handoff 전 어떤 gate를 실행했고 결과가 무엇인지, 또는 gate를 실행할 수 없는 정확한 이유를 쓴다. 다음을 확인한다.

- [ ] 범위 안의 변경한 frontend, Router, Query, Rust, IPC, native, build, security, skill surface마다 맞는 테스트가 있다.
- [ ] Router test가 file-route generation과 Router plugin order를 확인하고, Query test는 하나의 injected client와 좁은 desktop API mock을 쓴다.
- [ ] Authorization과 denial 근거는 route guard만이 아니라 Rust-side에 있다.
- [ ] 패키징된 SPA 근거가 Vite production build와 development server 없는 생성-route navigation, deep-link handling, reload를 다룬다.
- [ ] Native E2E는 disposable state만 사용했으며, publication, signing, credential, destructive production change를 하지 않았다.
- [ ] 동일 gate가 두 번 이하의 correction pass 안에 통과했다.

## Sources

> 링크 확인 2026-11-04.

| 주장 | 출처 |
|---|---|
| Native 근거 행의 근거인 Tauri testing layer, IPC mock, mock runtime, WebdriverIO 기반 native harness | [tauri-v2-2026-11-04.ko.md](../../references/official/tauri/tauri-v2-2026-11-04.ko.md); <https://v2.tauri.app/develop/tests/>; <https://v2.tauri.app/develop/tests/mocking/>; <https://v2.tauri.app/develop/tests/webdriver/>; <https://webdriver.io/docs/desktop-testing/tauri> |
| Router plugin 순서, 생성된 route tree, `defaultPreloadStaleTime`, loader/Query assertion | [tanstack-vite-react-2026-11-04.ko.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.ko.md) |
| Disposable profile에서의 패키징된 navigation, deep-link, reload 근거 | [tauri-v2-2026-11-04.ko.md](../../references/official/tauri/tauri-v2-2026-11-04.ko.md); <https://v2.tauri.app/develop/tests/webdriver/> |
| 범위가 제한된 수정 루프, 스킬 패키지 검사, readback checklist | 이 파일의 규약; 여기서 이름을 밝히는 저장소 명령은 외부 출처가 아닌 저장소 정책이다 |
