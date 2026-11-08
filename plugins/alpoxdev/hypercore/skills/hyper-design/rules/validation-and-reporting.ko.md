# 검증과 보고

report를 쓰기 전에 읽는다. 이 파일은 검증 순서, report 구성, 각 주장이 인용해야 할 근거를 소유한다.

## 검증 순서

1. 같은 대상에 `scripts/detect-slop.sh`를 다시 실행하고 rule ID, severity count, engine과 evidence field, 사용한 baseline delta를 비교한다. 실행 전과 후의 JSON을 `.hyper/design/<slug>/` 아래에 저장한다.
2. 변경한 화면마다 정석 수치 체크리스트(`rules/craft-floor.md` §9)를 실행한다.
3. 변경 파일을 포함하는 가장 작은 project build, typecheck, lint, test 명령을 실행한다. 실패를 억제하지 말고 살펴본다.
4. 렌더링이 가능하면 확인 대상 폭과 화면이 드러내는 상태를 살펴본다. 그렇지 않으면 렌더링이 필요한 항목을 `static_only` 또는 `unavailable`로 표시한다.
5. 변경이 영향을 주는 keyboard focus, semantics, 측정 가능한 contrast, reduced motion, responsive overflow를 확인한다.
6. 직접 영향받은 동작을 실행하고 copy, route, form contract, state transition, analytics hook을 보존한다.
7. 독립 검토(`rules/independent-review.md`)를 실행하고 그 발견 사항에 답한다.
8. 저장한 리포트를 `scripts/validate-report.sh --report .hyper/design/<slug>/report.md`로 검증하고 residual risk를 기록한다.

## Claim 규칙

- detector 또는 동등한 정적 검사를 실제로 실행하지 않았다면 “문제 없음”으로 보고하지 않는다.
- 렌더링 검사 없이 visual pass를 보고하지 않는다.
- screenshot 또는 CSS source만으로 accessibility pass를 보고하지 않는다.
- context-dependent·review-only heuristic을 확정 결함으로 바꾸지 않는다.
- `generic-output risk`를 AI 저작 결과라고 부르지 않는다.
- candidate exception 또는 baseline을 suppression이나 remediation pass로 취급하지 않는다.
- product metric, brand claim, testimonial, user, source provenance를 발명하지 않는다.
- 실행하지 않은 검사는 모두 불가능하거나 범위 밖인 이유와 함께 기록한다.

## 필수 리포트 section

`brief-only`를 뺀 모든 모드에서 `assets/report-template.ko.md`를 기본으로 쓴다. 리포트 제목은 validator가 고정하며 모든 모드에서 같게 읽힌다. validator가 결과를 확인할 수 있도록 다음 heading을 유지한다.

- `# AI Design Slop 정리 결과`
- `## 처리 요약`
- `## Brief inference`
- `## 발견 사항`
- `## 적용한 변경`
- `## 검증`
- `## 남은 위험`

요약에는 mode, `brief.md` 경로 또는 `해당 없음`, detector version과 engine, generic-output risk, baseline delta, 이유가 있는 candidate 또는 persisted waiver, `complete | static_only | unavailable` rendered-evidence 상태, 정석 수치 결과, 검토 모드(`subagent | self (degraded) | user | 미실행`)도 기록한다.

`audit`은 변경을 적용하지 않았다고 쓸 수 있다. `verify`는 확인한 변경 또는 finding set을 식별해야 한다. `design`, `restyle`, `mockup`은 만들거나 바꾼 token과 파일을 나열한다. 빈 section은 허용하지 않으며 이유와 함께 `없음` 또는 `미검증`을 쓴다.

## 완료 결정

- `pass`: 모든 해당 critical guard가 통과하고 사용자 결정이 남지 않음.
- `review_required`: 안전한 작업은 끝났지만 context-dependent·review-only 결정이 남음.
- `blocked`: 필수 evidence, authority, capability 또는 critical guard가 없음.

한계가 명시되고 숨은 critical 실패를 pass처럼 제시하지 않을 때만 caveat가 있는 결과가 유효하다.

## Sources

> 확인 2026-11-07.

이 파일에서 외부 출처는 사용하지 않았다.

검증 순서, claim 규칙, report section은 이 패키지 자체 것이다. 필수 한국어 heading은 이 패키지의 report template과 report validator에 맞춘다.
