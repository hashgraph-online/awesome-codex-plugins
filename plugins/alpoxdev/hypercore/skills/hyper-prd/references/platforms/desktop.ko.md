# Desktop Platform Checklist

PRD에서 판정한 플랫폼에 데스크톱이 포함될 때만 이 파일을 불러온다. macOS, Windows, Linux 데스크톱 빌드의 플랫폼 요구사항 블록과 출시 게이트 표를 채우는 항목을 소유한다. 배포 채널, 서명과 공증, 자동 업데이트, 데스크톱 통합이 여기에 해당한다.

## Contents

- How to use
- Distribution channel
- Signing and notarization
- Auto-update
- Desktop integration
- Release gate rule
- Sources

## How to use

- 항목을 플랫폼 요구사항 블록으로 옮기고 PRD의 문장으로 각각 답한다. 이 표를 PRD에 그대로 붙이지 않는다.
- 등급이 출시 게이트 표에 무엇이 들어가야 하는지를 정한다. `[M]`·`[M-조건]` 항목은 모두 결론을 적는다(해당, 비해당과 이유, `[확인 필요]`). `[G]` 항목은 제품에 관련 있을 때만 적는다.
- `[M-조건]` 항목은 문장 안에 조건을 밝힌다. 조건이 거짓이면 행을 지우지 않고 게이트 표에 "비해당"과 이유를 적는다.
- 쓴 그대로 검증할 수 없는 항목은 요구사항이 아니다. "스토어 가이드라인을 준수한다"는 금지하고, 조항과 관측 가능한 상태를 적는다.
- PRD의 모든 수치 목표에는 임계값, 측정 방법, 분위수를 함께 적는다. "충분히 빠르게"는 목표치가 아니다.
- 확인 날짜는 모든 행이 2026-11-07이다. 스토어 정책 값과 그 날짜는 바뀌므로 분기마다 각 행을 다시 확인하고 날짜를 갱신한다.

## Distribution channel

서명과 업데이트 항목이 이 결정에 기대므로 이 파일의 나머지보다 채널을 먼저 정한다.

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D1 | `[M]` | macOS 채널: Mac App Store 또는 Developer ID 직접 배포. 선택, 계정 소유자, 그 선택이 서명과 업데이트에 강제하는 것을 적는다. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |
| D2 | `[M]` | Windows 채널: Microsoft Store 또는 직접 배포 설치 파일. 선택, 계정 소유자, 배포할 설치 파일 형식을 적는다. | https://v2.tauri.app/distribute/windows-installer/ | 2026-11-07 |
| D3 | `[M]` | Linux 채널: Flathub 또는 다른 패키지 저장소. 선택, 패키지를 배포하는 주체, 패키지 갱신 방법을 적는다. | https://docs.flathub.org/docs/for-app-authors/requirements | 2026-11-07 |
| D4 | `[M-조건]` | 조건: macOS를 Developer ID로 배포한다. 배포 전에 모든 빌드를 공증한다. 공증 자격 증명 보유자와 공증 티켓을 출시 단계에서 스테이플하는지 적는다. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |
| D5 | `[M-조건]` | 조건: macOS를 Mac App Store로 배포한다. D4는 비해당이므로 게이트 표에 그 이유를 적고 대신 스토어 제출 의무를 기록한다. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |
| D6 | `[M-조건]` | 조건: Linux를 Flathub로 배포한다. 정적 권한을 절대 최소로 유지해 제출하고, 요청하는 권한마다 그것이 필요한 기능을 적는다. | https://docs.flathub.org/docs/for-app-authors/requirements | 2026-11-07 |

## Signing and notarization

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D7 | `[M]` | Windows: 인증서 소유자와 서명 ID를 기록하고 다이제스트 알고리즘으로 SHA256을 쓴다. SignTool이 그렇게 권고한다. | https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool | 2026-11-07 |
| D8 | `[M]` | Windows: 서명할 산출물(설치 파일, 실행 파일, 업데이트 패키지)과 출시 전에 서명 실패를 어떻게 검출하는지 적는다. | https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool | 2026-11-07 |
| D9 | `[G]` | macOS: 지원하는 최소 macOS 버전과 배포 아키텍처(Intel, Apple silicon, 둘 다), 아키텍처별 공증과 스테이플 여부를 기록한다. | https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution | 2026-11-07 |

## Auto-update

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D10 | `[G]` | 앱이 스스로 업데이트하는지, 한다면 어느 채널로 하는지 정하고 업데이트 피드 소유자와 출시 주기를 적는다. | https://www.electronjs.org/docs/latest/api/auto-updater | 2026-11-07 |
| D11 | `[G]` | OS별 업데이트 방식을 적는다. Electron 기본 autoUpdater는 Linux를 지원하지 않으므로 Linux 빌드는 패키지 저장소로 업데이트를 내보내거나 다른 방식을 써야 한다. | https://www.electronjs.org/docs/latest/api/auto-updater | 2026-11-07 |
| D12 | `[M-조건]` | 조건: Tauri 업데이터 플러그인을 쓴다. 업데이트 서명 검증은 끌 수 없다. 업데이트 서명 키 보유자, 보관 위치, 교체 방법을 적는다. | https://v2.tauri.app/plugin/updater/ | 2026-11-07 |
| D13 | `[G]` | 배포 규칙. 스토어나 벤더 규정이 아니라 이 PRD를 위한 설계 권고다. PRD가 자체적으로 업데이트 확인 주기, 단계별 비율, 단계를 멈추는 지표를 정하고, 그 수치는 인용한 한도가 아니라 PRD의 선택이다. 여기 연결한 배포 문서는 채널과 설치 파일만 다루며 배포 규칙을 두지 않는다. | https://v2.tauri.app/distribute/ | 2026-11-07 |
| D14 | `[G]` | 업데이트를 내려받거나 설치하지 못했을 때 사용자가 보는 것과 배포를 중단할 수 있는 사람을 적는다. | https://www.electronjs.org/docs/latest/api/auto-updater | 2026-11-07 |

## Desktop integration

| Id | Grade | What the PRD must settle | Source | Checked |
|---|---|---|---|---|
| D15 | `[G]` | 트레이: 트레이 아이콘 유무, 메뉴 구성, 주 창을 닫을 때의 동작(종료 또는 상주)을 정한다. | https://www.electronjs.org/docs/latest/tutorial/tray | 2026-11-07 |
| D16 | `[G]` | 프로토콜 핸들러: URL 스킴, 앱이 꺼져 있을 때 각 링크의 동작, 알 수 없거나 형식이 틀린 링크에 보여 줄 화면을 정한다. | https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app | 2026-11-07 |
| D17 | `[G]` | 단일 인스턴스: 두 번째 실행이 기존 창을 앞으로 가져올지, 새 창을 열지, 거부할지와 프로토콜 링크가 실행 중인 인스턴스에 도달하는지를 정한다. | https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app | 2026-11-07 |

## Release gate rule

위의 `[M]`·`[M-조건]` 행은 모두 PRD 출시 게이트 표에 결론 하나와 함께 들어간다.

| Conclusion | When to write it |
|---|---|
| 해당 | 의무가 성립하고, PRD가 그것을 만족하는 관측 가능한 상태를 적는다. |
| 비해당 + 이유 | 조건이 거짓이다(다른 채널, 다른 OS). 이유는 그 결정을 밝힌다. |
| `[확인 필요]` | 답이 저장소나 대화에 없다. 누가 답하는지 적는다. |

## Sources

> 확인 2026-11-07.

| Claim | Source |
|---|---|
| Developer ID 배포에는 공증이 필요하다 | [Notarizing macOS software before distribution](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution) - "all software built after June 1, 2019, and distributed with Developer ID must be notarized" |
| Windows 서명 다이제스트 권고 | [SignTool](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool) - "We recommend SHA256." |
| Electron은 Linux 자동 업데이트를 지원하지 않는다 | [Electron autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater) - "There is no built-in support for auto-updater on Linux" |
| Tauri 업데이트 서명은 플러그인 사용 시 필수다 | [Tauri updater plugin](https://v2.tauri.app/plugin/updater/) - "This cannot be disabled." |
| 데스크톱 배포 채널과 설치 파일 | [Tauri distribute](https://v2.tauri.app/distribute/)와 [Windows installer](https://v2.tauri.app/distribute/windows-installer/) |
| Flathub 권한 예산 | [Flathub app requirements](https://docs.flathub.org/docs/for-app-authors/requirements) - "Static permissions must be kept to an absolute minimum." |
| 트레이 메뉴 동작 | [Electron tray](https://www.electronjs.org/docs/latest/tutorial/tray) |
| 프로토콜 처리와 단일 인스턴스 | [Launch app from URL in another app](https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app) |

### Evidence grade

`LOCAL` - ID 체계, 등급, 출시 게이트 규칙은 위 출처를 조합한 이 패키지의 설계다. 스토어와 벤더 문장은 나열한 문서에서 그대로 인용했다. 스토어 정책 값과 날짜는 바뀌므로 출시 게이트를 승인하기 전에 분기마다 인용문과 2026-11-07 확인 날짜를 다시 검증해야 한다.
