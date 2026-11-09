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

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 표준 보고서는 24~48시간 걸리고 네트워크 요청과 DebugView가 즉시 확인 수단이라는 점 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| 광고 차단기, CSP, iframe, 늦은 로드, AMP로 인한 Tag Assistant 연결 실패 | <https://support.google.com/tagassistant/answer/10039345> |
| 알 수 없는 컨테이너 ID가 빈 컨테이너로 200을 응답한다는 점 | execution check, 2026-11-08, `references/verification.md` §4 |

### Evidence grade

`LOCAL` - 근거 표는 위 출처 위에 이 패키지가 설계한 것입니다.
