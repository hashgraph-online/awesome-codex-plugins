# 성능

> 패키징한 빌드를 재고, main 프로세스를 비워 두며, 첫 창이 필요로 하는 것만 로드하고, renderer 번들은 별도 예산으로 다룹니다.

규칙은 날짜가 붙은 스냅숏에서 연 페이지가 그대로 진술하면 `official`, 이 패키지가 기본값으로 고르면 `hypercore-default`로 표시합니다. 순서는 흔한 영향 순이며 측정으로 매긴 순위가 아닙니다.

## Measure first

| 목표 | 명령 또는 도구 |
|---|---|
| 첫 창이 보일 때까지의 cold start | 패키징한 빌드에서 main이 `app` `ready`와 창 `ready-to-show` 시각을 한 번씩 기록 |
| main 프로세스 blocking | `contentTracing` 기록(Electron 45부터 Perfetto 형식), 또는 패키징하지 않은 빌드에 `--inspect` |
| renderer 번들 구성 | 번들 분석기(예: `rollup-plugin-visualizer`)를 붙인 renderer Vite 빌드 |
| renderer 런타임 | 창의 Chromium DevTools Performance 패널 |
| 패키지 크기 | `app.asar` 크기와 packager가 만든 설치 파일 크기 |
| 메모리 | 고정 시나리오를 돈 뒤 프로세스별 `app.getAppMetrics()` |

모든 수치는 프로덕션 빌드에서 나옵니다. 개발 서버는 번들하지 않은 모듈을 내려 주므로 그 시작 시간으로 출하 앱을 판단할 수 없습니다.

## Rules

1. `official` — 모듈은 require하기 전에 살핍니다. transitive 의존성 하나가 큰 파일을 시작 경로로 끌어올 수 있습니다.
2. `official` — 코드를 너무 일찍 로드하고 실행하지 않습니다. 첫 창이 필요로 하지 않는 일(업데이트 확인, 색인, 분석)은 `ready-to-show` 뒤로 미룹니다. `require`는 비싸고, 특히 Windows에서 그렇습니다.
3. `official` — main 프로세스를 절대 막지 않습니다. UI 스레드가 있고 OS 이벤트와 창을 중개하는 곳입니다. 오래 걸리는 CPU나 I/O 작업은 `utilityProcess`나 worker thread로 옮깁니다.
4. `official` — renderer를 절대 막지 않습니다. 작고 미뤄도 되는 일에는 `requestIdleCallback`을, 긴 작업에는 Web Worker를 씁니다.
5. `official` — 불필요한 polyfill을 덜어 냅니다. Chromium 버전은 Electron major마다 고정돼 있습니다. Vite 빌드 target을 넓은 브라우저 목록이 아니라 그 Chromium으로 맞춥니다.
6. `official` — 첫 화면이 필요로 하지 않는 네트워크 요청은 미루거나 병렬로 돌립니다.
7. `official` — 모듈 로딩 비용을 한 번만 치르도록 코드를 번들합니다. electron-vite는 세 프로세스를 모두 번들합니다. trace에서 시작 `require` 비용이 보이면 main과 preload도 번들 상태로 둡니다.
8. `official` — 앱이 기본 메뉴를 출하하지 않으면 `ready` 전에 `Menu.setApplicationMenu(null)`을 부릅니다. 그러면 Electron이 메뉴를 만드는 일을 건너뜁니다.
9. `hypercore-default` — `BrowserWindow`를 `show: false`로 만들고 `ready-to-show`에 보여 줍니다. 사용자가 빈 프레임을 보는 일이 없습니다.
10. `hypercore-default` — router 플러그인의 `autoCodeSplitting`으로 renderer route를 나누고, 무거운 기능 라이브러리(에디터, 차트)는 lazy route 뒤에 둡니다.
11. `hypercore-default` — IPC payload는 작게, 묶어서 보냅니다. 크거나 잦은 데이터는 `invoke`를 여러 번 부르지 말고 `MessagePort`로 흘려보내고, 바뀔 때마다 데이터 전체를 보내지 않습니다.
12. `hypercore-default` — renderer 전용 패키지는 `devDependencies`에 두어 한 번만 번들되고 `app.asar`에 또 복사되지 않게 합니다(`rules/electron/packaging.md` §5).

## Do not

- 개발 서버 실행에서 시작 시간 개선을 주장하지 않습니다.
- 시작 시간을 아끼려고 sandbox나 context isolation을 끄지 않습니다.
- 측정 없이 V8 snapshot을 넣지 않습니다. `LoadBrowserProcessSpecificV8Snapshot` fuse가 snapshot이 아끼는 시간의 일부를 다시 치르게 하고, Performance 자습서에도 snapshot 레시피가 없습니다.
- renderer를 빨라 보이게 하려고 작업을 preload로 옮기지 않습니다. preload도 페이지 로드를 막습니다.
- packager와 bundler를 한 번에 다시 조정하지 않습니다. 측정마다 레버 하나입니다.

## Checklist

- [ ] 변경 전에 패키징한 빌드의 시작 시간, renderer 번들 크기, `app.asar` 크기를 기록했습니다.
- [ ] `ready-to-show` 전의 동기 작업을 main 프로세스 trace에서 확인했습니다.
- [ ] 미뤄 둔 작업이 첫 창이 보인 뒤에 시작합니다.
- [ ] 긴 CPU나 I/O 작업이 utility process나 worker에 있습니다.
- [ ] 빌드 target이 출하 Chromium과 맞습니다.
- [ ] 측정마다 레버 하나만 바꾸고, 같은 명령으로 잰 전후 수치를 남겼습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 애플리케이션 메뉴 항목을 포함한 여덟 가지 성능 권고 | https://www.electronjs.org/docs/latest/tutorial/performance |
| 45에서 Perfetto protobuf가 된 `contentTracing` 기록 | https://www.electronjs.org/docs/latest/breaking-changes |
| V8 snapshot fuse와 그 시작 비용 | https://www.electronjs.org/docs/latest/tutorial/fuses |
| `utilityProcess`와 `MessagePort` 스트림 | https://www.electronjs.org/docs/latest/api/utility-process, https://www.electronjs.org/docs/latest/tutorial/message-ports |
| 빈 프레임 없이 창을 보이는 `ready-to-show` | https://www.electronjs.org/docs/latest/api/browser-window |
| router `autoCodeSplitting` | https://tanstack.com/router/latest/docs/framework/react/guide/automatic-code-splitting |
| electron-vite 의존성 처리 | https://electron-vite.org/guide/dependency-handling |
| 기본값으로서의 show-on-ready, lazy 기능 route, 묶은 IPC, `devDependencies` 배치 | 이 패키지의 관례, 공식 요구 사항 아님 |
