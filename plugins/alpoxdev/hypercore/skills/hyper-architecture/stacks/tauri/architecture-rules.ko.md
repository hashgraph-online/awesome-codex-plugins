# Tauri 아키텍처 규칙

> Tauri v2 + Vite + React + TanStack Router file-based routing + TanStack Query의 핵심 taxonomy와 gate입니다.

먼저 이 문서를 읽습니다. 구현 세부에는 topic rule을 읽고 vendor/API 사실이 중요하면 날짜가 있는 official reference를 읽습니다.

## 규칙 라벨과 권위

| Label | Meaning | Enforcement |
|---|---|---|
| **Official** | Tauri, TanStack, Vite, React의 요구사항 또는 문서화된 동작입니다. | 상위 우선순위 project/user instructions가 지원되는 대안을 선택하지 않는 한 따릅니다. |
| **Safety** | Hypercore의 security 또는 runtime-correctness 경계입니다. | Touched work에서는 차단됩니다. 명시적으로 수용한 risk와 필요한 authority 없이는 완화하지 않습니다. |
| **Hypercore convention** | Vendor requirement를 넘어선 local maintainability convention입니다. | Touched surface에 적용합니다. Brownfield exception은 무관한 migration을 강제하지 않고 기록할 수 있습니다. |

Official fact는 날짜가 있는 evidence이며 실행 instruction이 아닙니다. 사용자와 repository instructions가 이 스킬보다 우선하지만 credentials, native side effects, publication, release, deployment, destructive operation을 승인하지는 않습니다.

## 지원 runtime shape

### Complete packaged Vite SPA

**Official:** Tauri는 Vite frontend build를 WebView의 static asset으로 package합니다. TanStack Router는 `@tanstack/router-plugin/vite`를 통해 생성된 file-based routing을 소유합니다. TanStack Query는 asynchronous data cache와 freshness를 소유하며 file-routing system을 제공하지 않습니다.

**Safety:** Browser module, route, loader state, Query state를 Tauri command, IPC, native authority로 매핑하지 않습니다. Renderer/browser code와 Tauri IPC/Rust code를 서로 다른 trust boundary로 유지합니다.

**Hypercore convention:** Architecture decision에 선택한 mode를 명명하고, 문서화되지 않은 script에 의존하지 말고 configuration에서 Vite, Router plugin, `src-tauri` wiring을 명시적으로 유지합니다.

### Incomplete adoption

**Official:** Tauri v2는 Vite, React, Router, Query를 요구하지 않고 static frontend를 host할 수 있습니다.

**Safety:** 이 스킬이 trigger되었다는 이유만으로 framework layer를 install, migrate, remove, rewrite하지 않습니다. 사용자가 adoption step을 요청할 때까지 기존 build/security behavior를 보존합니다.

**Hypercore convention:** Incrementally adopt합니다. 먼저 Vite/React entrypoint와 static package wiring을 만들고, 식별된 benefit이 있는 곳에 Router file-based routing과 Query를 추가합니다. Missing layer와 compatibility constraint는 violation이 아니라 adoption plan으로 기록합니다.

### Route away

**Official:** Framework-specific rule은 해당 runtime과 dependency evidence가 있을 때만 적용합니다.

**Safety:** Web-only app에 Tauri IPC/capability rule을 적용하거나 이 stack 밖의 project를 이 static SPA architecture로 취급하지 않습니다.

**Hypercore convention:** Rust-only, web-only, documentation-only task는 짧은 boundary note 후 적용할 workflow로 라우팅합니다. Full-stack TanStack runtime은 산출물 형태가 다릅니다. Packaged static SPA 경계가 아니라 server-owned route, loader, SSR data-flow를 내놓으므로 full-stack architecture workflow로 라우팅합니다.

## 아키텍처 레이어

```text
Renderer / WebView
  React UI -> TanStack Router (generated file routes) -> TanStack Query -> browser-safe remote API
       |
       | Tauri IPC (narrow, validated)
       v
Tauri Rust commands/plugins/state
  local OS/native boundary
```

### Ownership rule

- **Official:** Tauri command는 Tauri API를 통해 invoke하며 capability, permission, plugin scope가 Tauri configuration에 따라 access를 관리합니다.
- **Safety:** Privileged native operation은 반드시 좁은 IPC/plugin boundary를 통과해야 합니다. 그 boundary에서 untrusted input을 validate하고 caller/action을 authorize하며 필요한 최소 capability/scope만 노출합니다.
- **Safety:** Browser-visible code에는 server-only 또는 native-only credentials가 있으면 안 됩니다. `VITE_`-prefixed value는 public build-time value이지 secret이 아닙니다.
- **Official:** TanStack Router는 route state/navigation과 생성된 file-based routing을 소유합니다. TanStack Query는 asynchronous remote-data cache/server-state behavior를 소유하며 file-based routing을 소유하지 않습니다.
- **Hypercore convention:** Route adapter를 thin하게 유지합니다. Page는 routed screen을 조합하고 module은 응집된 domain UI/query/model behavior를 소유하며 shared component는 독립적인 재사용이 생긴 뒤에만 승격합니다.
- **Hypercore convention:** Local native operation은 explicit IPC adapter 뒤에 둡니다. Generic `utils`, `services`, component, IPC catch-all을 피하고 shared code를 하나의 이름 있는 responsibility로 묶습니다.

## Platform 및 packaging gate

| Gate | Label | Requirement |
|---|---|---|
| Static frontend | **Official** | Tauri `frontendDist`는 build된 static Vite frontend artifact를 가리키고 development configuration은 의도한 Vite dev URL/command를 사용해야 합니다. |
| Router generation | **Official** | `@tanstack/router-plugin/vite`가 file-based route를 생성하고 Vite configuration에서 React plugin보다 먼저 위치해야 합니다. |
| Query ownership | **Safety** | Query cache와 freshness는 TanStack Query에 유지해야 하며 Query를 file-routing system으로 설명하지 않습니다. |
| Asset paths | **Official** | Vite/Tauri asset base와 output path는 browser dev server뿐 아니라 packaged application asset에서도 동작해야 합니다. |
| Client environment | **Safety** | Renderer code는 public configuration만 사용해야 하며 local secret file 또는 server-only environment value에 의존하면 안 됩니다. |
| Privileged surface | **Safety** | 새 command/plugin access에는 review된 capability, permission, scope, validation, error path가 있어야 합니다. |
| CSP/scopes | **Safety** | CSP, capabilities, permissions, scopes는 least-privilege를 유지해야 하며 workaround로 끄거나 넓히지 않습니다. |
| Generated output | **Official** | Generated route/build artifact를 손으로 편집하지 않습니다. Source/configuration을 변경하고 project workflow로 regenerate합니다. |

## Brownfield adoption policy

Brownfield project에는 legacy layout, router, query, IPC, config pattern이 있을 수 있습니다. 모든 finding을 실행 전에 분류합니다.

1. **Touched code의 Safety 또는 Official correctness issue:** 완료 전에 차단하거나 수정합니다.
2. **Untouched reachable code의 Safety issue:** 명확히 보고합니다. 요청 작업이 이에 의존하거나 사용자가 더 넓은 변경을 승인할 때 수정합니다.
3. **Untouched code의 Hypercore convention:** 범위가 있는 migration recommendation을 기록하고 요청을 repo-wide refactor로 넓히지 않습니다.
4. **Missing stack layer:** incomplete-adoption mode를 선택하고 false compliance failure가 아닌 가장 작은 순서화된 adoption step을 제안합니다.

Untouched라는 이유로 legacy code를 compliant라고 부르지 않습니다. Convention 위반을 vendor requirement라고 부르지 않습니다.

## Blocking gate

아래 적용 가능한 gate 중 하나라도 실패한 touched change는 완료하지 않습니다.

1. **Mode gate:** Project/runtime mode를 알 수 없거나 missing stack layer를 complete adoption으로 취급하거나 full-stack TanStack project를 이 packaged static SPA로 취급해 full-stack architecture workflow로 라우팅하지 않았습니다.
2. **Boundary gate:** Browser module, route, loader state, Query state를 Tauri command 또는 native authority로 매핑합니다.
3. **Secret gate:** Renderer-reachable path가 credentials, private configuration, native filesystem/process access, server-only dependencies를 read/exfiltrate할 수 있습니다.
4. **IPC gate:** 새 privileged command/event/plugin path에 least privilege, validation, authorization, capability/permission/scope coverage, safe error handling이 없거나, 설계가 설치된 Tauri version이 제공하지 않는 channel/대용량 응답 scoping에 의존합니다.
5. **Input gate:** Untrusted renderer, web, deep-link, event, IPC data가 validation/authorization 없이 native-sensitive behavior에 도달합니다.
6. **Platform gate:** Static packaging, route generation, asset paths, CSP, Vite environment exposure, capability configuration이 development 밖에서 실패하거나 unsafe해집니다.
7. **Authority gate:** 명시적 authority 없이 credentials, native side effects, destructive actions, publication, release, deployment이 필요합니다.
8. **Evidence gate:** 동일하게 선언한 check를 최대 두 번 실행한 뒤에도 required validation이 없거나 실패했거나 잘못 표현되었습니다.

Blocking gate는 concrete fix, evidence가 있는 project-supported alternative, authority-gated action에 대한 명시적 user decision으로만 해제할 수 있습니다. Convention-only deviation은 blocking-gate waiver가 아닙니다.

## Validation 결정

완료를 주장하기 전에 mode와 touched layer를 식별하고, 적용할 blocking gate를 평가하고, `rules/tauri/testing.ko.md`의 허용된 focused check를 실행하고, exact output 또는 check가 허용되지 않은 이유를 기록합니다. Failed validation pass 뒤에는 한 번의 correction pass만 허용합니다. 두 번째 결과 뒤에는 다른 optimization loop를 시작하지 말고 remaining blocker를 보고하고 중단합니다.