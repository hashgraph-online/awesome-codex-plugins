# 증거와 심각도

finding에 disposition을 붙이기 전에 읽는다. 이 파일은 finding 기록, evidence 종류, confidence 분리, 심각도 분류를 소유한다.

## Finding 기록

모든 finding은 다음을 포함한다.

| 필드 | 요구 사항 |
|---|---|
| `claim` | 취향 판정이 아닌 관찰 가능한 진술 |
| `risk` | 제품, usability, identity, accessibility, maintenance에서 실패할 수 있는 결과 |
| `severity` | 아래 정의의 P0–P3 |
| `confidence` | `high`, `medium`, `low` |
| `engine` | `text`, `css`, `markup`, `context`, `dom`, `visual` 중 실제 실행한 engine |
| `evidence kind` | `static-source`, explicit local context, rendered handoff, accessibility, behavior, rationale |
| `detection confidence` | engine이 signature를 관찰한 확실성 |
| `remediation confidence` | 변경이 protected contract를 보존할 확실성 |
| `exception status` | `not-checked`, `candidate`, documented waiver; candidate는 계속 review 가능 |
| `cluster` | generic-output 우선순위 group이며 authorship 증거가 아님 |
| `evidence` | file/line, DOM/CSS, screenshot/state, command 결과, brief, source |
| `warrant` | 이 맥락에서 증거가 risk를 뒷받침하는 이유 |
| `recommendation` | 제한된 action과 함께 `remove`, `replace`, `preserve`, `ask`, `block` |
| `verification` | action 후 필요한 관찰 가능 검사 |
| `caveat` | 예외, 부족한 증거, false-positive risk |

## Severity

- `P0` blocking: task completion을 막거나 심각한 accessibility, behavior, security, data-integrity 실패를 일으킴.
- `P1` major: 반복되는 고영향 AI pattern, 확인된 WCAG AA 위반, 심각한 responsive 실패.
- `P2` minor: workaround가 있고 task를 막지 않지만 개선 가치가 있음.
- `P3` polish: 취향에 가까운 refinement이며 광범위 자동 변경 근거로 사용할 수 없음.

## Confidence

- `high`: source, DOM/CSS, deterministic output에서 직접 확인.
- `medium`: 강한 heuristic이지만 맥락 예외 가능.
- `low`: screenshot 해석, 제품 의도, 주관적 review에 의존.

Source match의 high confidence가 제거 판단의 high confidence를 뜻하지 않는다. 둘이 다르면 탐지 신뢰도와 수정 판단을 prose에서 분리한다.

## Evidence family

- `validator`: detector, schema, fixture, test, build, CI output.
- `screenshot`: viewport/state capture 또는 visual diff.
- `accessibility`: contrast, keyboard, semantics, reduced-motion 증거.
- `user`: persona evidence, cognitive walkthrough, user test.
- `source`: brief, design system, standard, documented practice.
- `rationale`: decision record, rejected alternative, owner, debt, review trigger.

정적 detector는 실제 contrast, visual hierarchy, usability, user preference를 확정할 수 없다. Screenshot은 semantic correctness, keyboard behavior, 모든 responsive state를 증명하지 못한다. finding과 최종 리포트에 이 한계를 쓴다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

severity, confidence, evidence family 정의는 이 패키지 자체 것이다. WCAG AA는 `P1` severity 기준 이름으로만 쓰였고 WCAG 문서를 인용하거나 재진술하지 않았다.
