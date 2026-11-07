# AI Design Slop 정리 결과

## 처리 요약

- 대상: `<path 또는 surface>`
- 모드: `design | restyle | mockup | audit | clean | verify`
- 디자인 브리프: `.hyper/design/<slug>/brief.md | 해당 없음`
- Detector: `v2 | unavailable (사유)`
- 실행한 engine: `text | css | markup | context | dom | visual`
- Baseline delta: `미사용 | only-new | unavailable (사유)`
- Generic-output risk: `low | medium | high | unassessed`
- 렌더링 검증: `complete | static_only | unavailable`
- 수정 pass: `0 | 1 | 2 | 3`
- 정석 수치 점검: `pass | fail (항목) | static_only`
- 독립 검토: `subagent | self (degraded) | user | 미실행 (사유)`
- 납품 게이트: `pass | fail (항목) | 미실행 (사유)`
- 최종 상태: `pass | review_required | blocked`

## Brief inference

- 화면 유형:
- Visitor mode:
- 사용자:
- 주요 task:
- 보존해야 할 정체성:
- 필수 data/state/cardinality:
- 이번 작업 범위:
- 미확인 사항:

## 발견 사항

| # | ID | 분류 | 심각도 | 탐지 / 수정 신뢰도 | Engine / 증거 | Exception | 처리 | 상태 |
|---|---|---|---|---|---|---|---|---|
| 1 | `rule.id` | `default-risk` | `P2` | `high / low` | `text / static-source` at `file:line` | `not-checked` | `review` | `open` |

## 적용한 변경

- 파일:
- 변경 내용:
- 보존한 계약:
- Candidate 또는 persisted waiver: `없음 | rule, narrow scope, reason, source`

## 검증

- Detector/baseline:
- Build/typecheck/lint/test:
- Rendered evidence: viewport/state/locator 사실 또는 `static_only` / `unavailable` 사유
- Desktop/mobile render:
- Accessibility:
- Reduced motion:
- 기능 regression:
- Report validator:

| 게이트 항목 | 결과 | 증거 |
|---|---|---|
| H1~H11, 정석 수치, P1~P13, L1~L7 | `PASS / FAIL / n/a / not run` | file:line, 명령 출력, 캡처, 클릭 확인 기록 |

## 남은 위험

- 렌더링 미검증 항목:
- Review-only/context-dependent finding:
- 사용자 결정 필요 항목:
- 증거 경계: screenshot은 keyboard, semantic, accessibility, end-to-end behavior를 증명하지 않는다.
- 기타 caveat:
