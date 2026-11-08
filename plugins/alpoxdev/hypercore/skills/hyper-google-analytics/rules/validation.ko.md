# 검증

실행을 완료로 선언하기 전에 이 점검표를 씁니다. 모드별 완료 근거, 표준 보고서는 수집 증명이 아니라는 규칙, 보고서 점검, 수리 한도를 소유합니다.

## 1. The Collection-Proof Rule

측정이 수집됐다고 증명되는 것은 이번 실행에서 다음 중 하나가 성립할 때뿐입니다.

1. 네트워크 캡처가 `tid`가 속성 측정 ID이고 `en`이 기대한 이벤트인 `/g/collect` 요청을 `200`이나 `204` 응답과 함께 보여 줌
2. 디버그 모드가 있는 상태에서 이번 실행이 시작한 세션에 대해 DebugView가 이벤트와 매개변수를 보여 줌
3. 실시간 보고서가 수 분 창 안에 이벤트를 보여 줌
4. Admin API read-back이 쓴 설정 값을 보여 줌

표준 보고서, 속성 대시보드, "내일이면 갱신될" 리포트, 업로드 시도, `/mp/collect`의 `2xx`, CLI 종료 코드 `0`은 수집 증명이 아닙니다. 표준 보고서는 24시간에서 48시간 지연되므로 이번 실행이 바꾼 것을 확인할 수도 반박할 수도 없습니다.

## 2. Completion Evidence By Mode

| Mode | Claim | Required evidence |
|---|---|---|
| `audit` | "Findings reported" | 심각도, 그것을 보여 주는 파일과 줄 또는 요청과 응답, 수정 담당이 붙은 모든 발견 사항. 속성이나 사이트 파일을 바꾸지 않음. 측정 ID와 속성 ID, 각각의 출처가 붙은 대상 줄 |
| `install` | "Installed and collecting" | 바뀐 파일, 모든 측정 명령보다 앞선 동의 기본값, 페이지뷰 출처 하나, CSP 항목, 그리고 기대한 `tid`가 붙은 `page_view`에 대한 1항의 증거 |
| `configure` | "Changed" | 필드 경로가 붙은 이전 값, 정확한 메서드와 본문, 쓰기 전에 밝힌 계정·속성·스트림, `get`에서 읽은 이후 값, 설정이 적용되는 데 걸리는 시간 |
| `analyze` | "Reported" | 요청, 날짜 범위, 250,000행 상한 대비 행 수, 응답이 돌려준 모든 데이터 품질 표시(임계값 적용, 샘플링, `(other)` 통합, HLL++ 추정) |
| `diagnose` | "Fixed" | 실패한 신호의 이전 상태, 고정 순서에서 고른 원인, 변경, 1항을 만족하는 같은 신호의 이후 상태, 전후 짝 |
| `diagnose` | "Exhausted" | 같은 원인에 대한 세 번의 시도와 각각의 변경과 결과, 고정 순서에서 그 원인의 위치, 다음에 모을 근거 |
| any | "Stopped for approval" | 정확한 호출, 바뀌는 것, 적용까지 걸리는 시간, 복구할 수 없는 것, 그 뒤의 근거(`rules/safety-gates.md` §5) |
| any | "Does not apply" | 사이트 루트, 읽은 파일, 요청이 속한 결과물 형태 |

## 3. Report Check

- [ ] `.hyper/google-analytics/<slug>/report.md`가 있고 `references/report-template.md`를 따릅니다.
- [ ] 보고서의 모든 호출이 이번 세션에서 실행됐거나 `not run`으로 사유와 함께 표시됐습니다.
- [ ] 캡처한 모든 요청이 제한됐고(URL 하나, 상태 하나) 모든 비밀이 가려졌으며 가린 사실이 적혔습니다.
- [ ] 모든 분석 숫자가 요청, 날짜 범위, 데이터 품질 표시를 함께 인용합니다.
- [ ] 없는 자격 증명, 꺼진 API, 없는 범위, 건너뛴 점검이 통과한 점검과 분리해 적혔습니다.
- [ ] 마지막 상태 줄이 모드의 종료 결과를 이름으로 적습니다. `audited`, `installed`, `changed`, `reported`, `fixed`, `exhausted`, `stopped-for-approval`, `delayed`, `blocked`, `handoff`입니다.
- [ ] 이번 실행에서 열지 않은 출처의 발견 사항, 숫자, 증명을 복사하지 않았습니다.

## 4. Repair Bound

실패한 점검은 모드 한도 안에서 실패한 단계로 실행을 돌려보냅니다(`SKILL.md` 루프 정책). 실행됐다가 실패한 점검은 나중 시도가 통과해도 보고서에 보이는 채로 남습니다. 세 번째 시도까지 실패한 원인은 다음에 모을 근거와 함께 `exhausted`로 보고하고, 이름만 바꿔 네 번째로 재시도하지 않습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 표준 보고서는 24시간에서 48시간 걸리고 실시간은 수 분 안에 나타나며, `/g/collect`는 전송 성공 시 `200`이나 `204`로 답합니다 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| DebugView는 디버그 모드를 요구하고, 매개변수를 빼는 것만이 끄는 방법입니다 | <https://support.google.com/analytics/answer/7201382> |
| Measurement Protocol은 잘못된 이벤트에도 HTTP 오류 코드를 돌려주지 않으므로 `2xx`는 수용이 아닙니다 | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events> |
| `runReport`는 요청당 최대 250,000행을 돌려줍니다 | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport> |
| 임계값 적용, 샘플링, `(other)` 통합, HLL++ 추정을 리포트로 옮겨야 합니다 | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| 데이터 필터는 적용까지 24시간에서 36시간이 걸리므로 read-back만으로는 그 효과를 증명할 수 없습니다 | <https://support.google.com/analytics/answer/10104470> |

### Evidence grade

`LOCAL` - 상태 목록, 근거 표, 수리 한도는 인용한 페이지 위에서 이 패키지가 고른 설계입니다. 지연, 상한, 표시 사실은 2026-11-08에 읽은 공식 페이지에서 `MEASURED`입니다.
