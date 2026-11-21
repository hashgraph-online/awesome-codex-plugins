# <slug> - Work Plan

## TL;DR

- What you get: <결과를 한 줄로>
- Why this approach: <근거에 기반한 이유>
- What it will not do: <거부하는 추가 항목>
- Effort: <Quick | Short | Medium | Large | XL>
- Risk: <구체적 위험. 작업 트리가 더러우면 그 사실 포함>
- Decisions made for you: <채택한 기본값과 되돌릴 수 있는지>

## Scope

### Affected user and ideal state

Affected user: <누구>, 오늘은 <어떻게 쓰는지>, 실행 뒤에는 <어떻게 쓰는지>.

| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | <걸리거나 퇴행하는 것이 없는 상태의 속성> | <이유> |
| GAP-1 | <그 상태와 오늘의 차이> | <이유> |

### Must have

- <필요한 결과>

### Must NOT have

- <계획이 거부하는 추가 항목>

## Verification strategy

<테스트 수준, 정확한 명령, 실제 표면 점검, 적용되는 적대적 범주>

## Execution strategy

### Wave 1

- Todo <번호>

| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | <경로> |

## Todos

- [ ] 1. <제목>
  Wave: 1
  Depends on: none
  Write scope: <정확한 경로나 글롭>
  References: <줄 앵커가 붙은 경로, 문서 URL>
  Acceptance: <실제 명령과 기대 결과>
  QA happy: <도구, 정확한 실행, 이분법 관찰값>; evidence: <경로>
  QA failure: <도구, 정확한 실행, 이분법 관찰값>; evidence: <경로>
  Commit: <저장소 관례의 메시지>
  Tier: <low | medium | high> - <한 줄 이유>

## Final verification wave

- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)

## Commit strategy

<todo마다 커밋 하나, 메시지 관례, 근거 파일 처리, wave 착지 방식>

## Success criteria

| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1 | <점검> | <경로> |

## Handoff

- Auto-execute: <yes | no (reason)>
- Delivery: <local | make-pr | ship>
- Plan-only requested: <yes | no>

<!-- .hyper/plans/<slug>.md로 복사하고 모든 <placeholder>를 바꿉니다. 제목은 적힌 그대로 유지합니다. -->
