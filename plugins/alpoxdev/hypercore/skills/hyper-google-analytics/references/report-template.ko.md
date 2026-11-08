# 보고서 템플릿

`.hyper/google-analytics/<slug>/report.md`를 쓸 때 이 참조를 사용합니다. `##` 제목은 영어로 두고 본문은 한국어로 씁니다.

## Template

```markdown
# <실행 제목>

- Mode: audit | install | configure | analyze | diagnose
- Target: <사이트 이름이나 저장소 경로> (<판단 파일>)
- Property: <계정 이름> / `properties/<숫자>` / `G-XXXXXXXXXX`
- Stream: <스트림 이름과 ID, 또는 해당 없음>
- Environment: <production | preview | local>
- Credentials: <사용한 자격 증명 종류와 범위; 값은 적지 않음>
- Result: audited | installed | changed | reported | fixed | exhausted | stopped-for-approval | delayed | blocked | handoff

## Evidence

- `<경로>:<줄>` - <그것이 보여 주는 것>
- `<요청>` -> <상태 코드와 발췌, 비밀 가림>
- `<Admin API 메서드>` -> <응답 필드와 값>

## Findings

| # | Severity | Finding | Evidence | Fix owner |
|---|---|---|---|---|
| 1 | blocks-data / corrupts-metric / misleads-report / cosmetic | <발견 사항> | <파일과 줄 또는 요청> | code / property / tag manager / consent |

## Collection Proof

- Signal: <`/g/collect` with `tid` and `en`, DebugView, or Realtime>
- Captured at: <시각>
- Standard report used as proof: no

## Report Quality

| Request | Date range | Rows | Thresholded | Sampled | `(other)` | Notes |
|---|---|---|---|---|---|---|
| <runReport 요청 요약> | <시작~끝> | <n> / 250,000 | yes / no | yes / no | yes / no | <HLL++ 추정 등> |

## Actions

| # | Call | Tier | Result |
|---|---|---|---|
| 1 | `<method and body>` | proceed / named in the request / approved | <read-back 또는 응답 줄> |

## Diagnosis

| Symptom | Request or response line | Cause (order position) | Fix | Before | After |
|---|---|---|---|---|---|

## Proposed, Not Run

- `<정확한 호출>` - <바뀌는 것>, <적용까지 걸리는 시간>, <복구할 수 없는 것>, <제안하는 이유>

## Gaps And Risks

- <없는 자격 증명, 꺼진 API, `not run` 점검, 미해결 원인, 다시 확인했거나 하지 않은 자주 바뀌는 사실>
```

## Rules

- 모드가 만들 수 없는 절만 생략하고, 만들 수 있는데 아무 일도 없었으면 `none`이라고 씁니다.
- `## Actions`의 모든 호출은 이번 세션에서 실행했습니다.
- 토큰, `api_secret` 값, 자격 증명을 가리고 무엇을 가렸는지 밝힙니다. `api_secret`은 앞 4글자까지만 보여 줍니다.
- `## Collection Proof`에 표준 보고서를 증명으로 쓰지 않았다고 적거나, 지연이 유일한 발견 사항이면 결과 줄을 `delayed`로 적습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 보고서 필드와 결과 값 | 이 패키지의 설계, 2026-11-08 |
| 표준 보고서는 24시간에서 48시간 지연되고 수집 증명을 대신할 수 없습니다 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| 리포트는 데이터 품질 표시(임계값 적용, 샘플링, `(other)`, HLL++ 추정)를 함께 담습니다 | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| 무엇을 관측했고 무엇을 생략했고 무엇이 미해결인지 기록하는 보고서 | `instructions/validation/index.md` |

### Evidence grade

`LOCAL` - 이 템플릿은 이 패키지 자체의 것입니다. 템플릿이 강제하는 Google 사실 둘은 위에 인용한 페이지에서 `MEASURED`입니다.
