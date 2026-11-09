# 검증

**Purpose**: 실행이 성공을 보고하기 전에 모드마다 가져야 할 근거를 정해, 상태 코드나 대시보드 한눈, 에이전트의 코드 해석만으로 작동하는 태그를 주장하지 않게 합니다.

## 1. Completion Evidence Per Mode

| Mode | Evidence required |
|---|---|
| `audit` | 실행한 스크립트마다의 JSON, 발견 사항마다의 파일과 줄·페이지 오프셋·컨테이너 항목, 사용한 방법(서버가 보낸 HTML 또는 렌더링된 브라우저)과 함께 나열한 모든 페이지 |
| `install` | 바뀐 파일의 diff, 컨테이너 ID 하나·로더 하나·같은 ID의 직접 Google 태그 없음을 보여 주는 두 번째 `gtm-detect.sh` 실행, `verify` 표 |
| `configure` | 바뀐 작업공간 항목이나 가져오기 JSON, 변경 뒤 새 `error` 발견 사항이 없는 `gtm-container-audit.sh` 실행, `verify` 표, 게시 결과(버전 ID) 또는 제안한 게시 동작 |
| `verify` | 계획한 태그마다 한 행. §2와 같습니다 |
| `diagnose` | 증상, 증상을 설명한 계층, 변경, 같은 검사의 전후 결과 |
| `analyze` | 컨테이너 개수와 발견 사항, 계획 대 컨테이너 비교, 데이터 확인이면 보고서·날짜 범위·데이터 품질 표시 |

## 2. Verification Row

| Column | Content |
|---|---|
| Tag | 태그 이름과 유형 |
| Trigger event | 발화시킨 dataLayer 이벤트나 내장 이벤트 |
| Fired | Preview, Tag Assistant, 렌더링된 페이지에서 본 `yes`, `no`, `blocked by consent` |
| Request | 목적지 요청(예: `en` 값이 있는 `/g/collect` 요청) 또는 `none` |
| Key parameters | 요청이나 디버그 뷰에서 본, 계획이 요구하는 매개변수 |
| Consent state | 그 시점의 동의 유형과 상태 |
| Result | 이유와 함께 `verified`, `failed`, `not verified` |

태그는 이번 실행에서 요청이나 디버그 이벤트를 관찰했을 때만 `verified`입니다. 브라우저나 디버그 기능이 없으면 행을 `not verified`로 표시하고 사용자가 실행할 수 있는 정확한 검사를 적습니다.

## 3. Disallowed Proof

- HTTP 200을 응답하는 `gtm.js`. 알 수 없는 컨테이너 ID도 빈 컨테이너(리소스 버전 `1`, 태그 없음)로 200을 응답합니다.
- 최근 24~48시간의 GA4 표준 보고서, 또는 그곳에 데이터가 없다는 사실.
- 코드를 읽어 맞다고 판단한 것, 또는 스크립트 발견 사항 목록이 비어 있다는 것.
- 광고 차단기, CSP, iframe, 늦게 로드되는 태그가 설명할 수 있는 상황에서 "no tags found"가 나온 Tag Assistant 실행.

## 4. Report Gate

- `.hyper/gtm/<slug>/report.md`가 있고 `references/report-template.md`를 따릅니다.
- 보고서의 모든 수치에 출처(스크립트 출력, 요청, 보고서)와 날짜가 있습니다.
- 승인 등급 동작은 승인 인용과 결과를 함께 적었거나 제안 동작 목록에 있습니다.
- 남은 위험 절에 모든 `not verified` 행과 열린 발견 사항이 있습니다.
- `결과:` 줄이 §5의 다섯 값 중 하나만 이름으로 적고 실제로 한 일과 일치합니다.

## 5. Terminal Result

보고서의 `결과:` 줄은 다음 단계가 읽는 값이므로 요약이 아니라 결과 하나를 적습니다. 다음 순서로 고릅니다.

| 값 | 해당 상황 |
|---|---|
| `blocked` | 사용자만 줄 수 있는 것이 없어서 진행할 수 없고, 승인으로도 풀리지 않을 때. 컨테이너 ID 누락, 사이트나 저장소 접근 없음, 제공되지 않은 컨테이너 내보내기, API 단계에 필요한 자격 증명 없음입니다 |
| `exhausted` | `diagnose`의 근본 원인이 통과 증명 없이 시도 세 번을 다 썼거나, 계속하려면 같은 고친 일을 새 이름으로 바꿔 분류해야 할 때 |
| `proposed` | 승인 게이트에서 멈췄고 승인 등급 동작이 하나 이상 제안 목록에 있을 때. 게시, 다시 게시, 덮어쓰기 가져오기, 삭제, 권한 변경, 실서비스 동의 변경입니다 |
| `partial` | 모드가 요구하는 근거가 승인도 진단 예산도 아닌 이유로 불완전할 때. 브라우저나 디버그 기능이 없어 남은 `not verified` 행, 닿지 못한 페이지, 실행하지 못한 점검입니다 |
| `verified` | 모드가 요구하는 점검이 모두 돌았고 주장하는 태그마다 요청이나 디버그 이벤트가 있을 때. 증명된 `install`, 증명된 `verify`, 발견 사항 모두에 근거가 있고 편집이 없었던 `audit`이나 `analyze`입니다 |

- `verified`는 기본값이 아닙니다. 승인 뒤 게시하고 실서비스 페이지에서 다시 검증했으면 `verified`이고, 게시했지만 다시 검증하지 못했으면 `partial`입니다.
- 요청한 범위를 모두 돌고 발견 사항 모두에 근거가 있는 `audit`이나 `analyze`는 `verified`입니다. 돌지 못한 점검이 있으면 `partial`이고, 보고서의 남은 위험 절이 그 점검을 이름으로 적습니다.
- 이 값은 컨테이너 상태가 아니라 이번 실행의 증거를 말합니다. `error` 발견 사항이 많은 컨테이너도 감사를 돌고 모든 발견 사항에 근거가 있으면 `verified`로 끝납니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 표준 보고서는 24~48시간 걸리고 네트워크 요청과 DebugView가 즉시 확인 수단이라는 점 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| 광고 차단기, CSP, iframe, 늦은 로드, AMP로 인한 Tag Assistant 연결 실패 | <https://support.google.com/tagassistant/answer/10039345> |
| 알 수 없는 컨테이너 ID가 빈 컨테이너로 200을 응답한다는 점 | execution check, 2026-11-08, `references/verification.md` §4 |

### Evidence grade

`LOCAL` - 근거 표는 위 출처 위에 이 패키지가 설계한 것입니다.
