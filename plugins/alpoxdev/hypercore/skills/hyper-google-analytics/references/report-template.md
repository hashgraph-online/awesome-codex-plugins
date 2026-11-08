# Report Template

Use this reference when writing `.hyper/google-analytics/<slug>/report.md`. Keep the `##` headings in English; write the prose in Korean.

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

- Omit a section only when the mode cannot produce it, and write `none` when it can but nothing happened.
- Every call in `## Actions` ran in this session.
- Redact tokens, `api_secret` values, and credentials, and say what was redacted. An `api_secret` shows at most its first 4 characters.
- `## Collection Proof` states the standard report was not used as proof, or the result line says `delayed` when delay is the only finding.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| The report fields and the result values | this package's design, 2026-11-08 |
| A standard report lags 24 to 48 hours and cannot stand in for a collection proof | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| A report carries its data-quality flags: thresholding, sampling, `(other)`, and HLL++ estimates | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| A report that records what was observed, what was omitted, and what is unresolved | `instructions/validation/index.md` |

### Evidence grade

`LOCAL` - the template is this package's own; the two Google facts it enforces are `MEASURED` from the pages cited above.
