# 계획 형식

`.hyper/plans/<slug>.md`를 쓰기 직전에 이 파일을 읽는다. 이 패키지가 쓰는 계획 문법을 다시 적어 계획 파일이 다른 참조를 필요로 하지 않게 한다.

계획은 이 스킬이 인사이트 묶음으로부터 쓴다. 별도 기획 단계가 만드는 것이 아니며, 완성된 파일이 실행 단계가 소비하는 산출물이다.

## Contents

1. Location and slug
2. Header sequence
3. TL;DR
4. Scope
5. Verification strategy
6. Execution strategy
7. Todos
8. Final verification wave
9. Commit strategy
10. Success criteria
11. Handoff
12. Checkbox states
13. Worked fragment

## 1. 위치와 slug

계획은 `.hyper/plans/<slug>.md`에 있고 `<slug>`는 토론 디렉터리와 같은 slug다. 소문자 ASCII 케밥 표기이며 `^[a-z0-9]+(-[a-z0-9]+)*$`에 맞고 48자 이하이다. `..`, `/`, 절대 경로는 거절한다.

첫 줄은 `# <slug> - Work Plan`이다.

## 2. 제목 순서

다음 제목이 순서대로 정확히 한 번씩 나온다.

```text
# <slug> - Work Plan
## TL;DR
## Scope
### Affected user and ideal state
### Must have
### Must NOT have
## Verification strategy
## Execution strategy
## Todos
## Final verification wave
## Commit strategy
## Success criteria
## Handoff
```

제목은 마지막 아래에만 더할 수 있고 실행자는 무시한다. 순서를 바꾸거나 이름을 바꾸면 계약이 깨진다.

## 3. TL;DR

마지막에 채운다. 여섯 줄이다.

- 사용자가 얻는 것
- 이 접근을 고른 이유
- 하지 않을 것
- `Effort:`는 `Quick`, `Short`, `Medium`, `Large`, `XL` 중 하나. 시간이나 일수는 쓰지 않는다.
- `Risk:` 토론이 드러낸 구체적 위험. 작업 트리가 지저분하면 그것도 포함한다.
- `Decisions made for you:` 묶음에서 살아남은 결정과 가역성

토론 출처는 `Risk:` 줄에 한 구절로 들어간다. 할 일이 되지 않는다.

## 4. 범위

`### Affected user and ideal state`는 결과가 닿는 사람과 오늘 및 이후의 사용 방식을 적고, 그다음 행을 둔다.

| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | 아무것도 걸리거나 퇴행하지 않는 상태의 속성 | 이유 |
| GAP-1 | 그 상태와 오늘의 차이 | 이유 |

묶음의 모든 하드 제약이 `IS-` 행이 된다. 거절한 추가는 모두 `### Must NOT have` 줄이 된다.

`### Must have`는 필수 결과를 적는다. `### Must NOT have`는 계획이 거절하는 추가를 적는다. 요청하지 않은 기능, 추측성 추상화, 조용한 범위 확장, 토론이 이긴 구체적 대안이 대상이다.

## 5. 검증 전략

테스트 수준과 실제 점검을 적는다. 단위·통합 명령, 타입체크, 린트, 빌드, 그리고 할 일마다의 실제 표면 점검(HTTP 응답, 터미널 실행, 브라우저 흐름, 데이터베이스 차이)이다. 적용되는 적대적 부류와 적용되지 않는 이유를 적는다. 최종 검증 웨이브를 여기서 요약하고 §8에서 명세한다.

## 6. 실행 전략

웨이브마다 `### Wave <N>` 블록 하나에 그 웨이브에서 도는 할 일 번호를 적고, 이어서 의존성 행렬을 둔다.

```markdown
| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | src/auth/login.ts |
```

한 웨이브의 할 일은 쓰기 범위가 겹치지 않거나 순차로 돈다. 웨이브당 다섯에서 여덟 개를 목표로 하고, 마지막이 아닌 웨이브에 세 개 미만이면 분할이 부족하다.

## 7. 할 일

모든 실행 항목은 열 너비 0에서 시작하는 행이고 고유한 양의 정수로 번호를 매긴다.

```markdown
- [ ] <N>. <title>
  Wave: <wave number>
  Depends on: <todo numbers or none>
  Write scope: <exact paths or globs>
  References: <paths with line anchors, documentation URLs>
  Acceptance: <literal command and expected result>
  QA happy: <tool, exact invocation, binary observable>; evidence: <path>
  QA failure: <tool, exact invocation, binary observable>; evidence: <path>
  Commit: <message in the repository's convention>
  Tier: low | medium | high - <one-line reason>
```

필드 규칙:

- 들여쓰기는 두 칸이고 아홉 필드가 이 순서로 나온다.
- `Acceptance`는 사람 판단 없이 에이전트가 실행할 수 있어야 한다.
- `QA happy`와 `QA failure`는 각각 동작과 안전한 실패를 증명하고 둘 다 증거 경로를 갖는다.
- `Tier: low`는 기계적이거나 단일 파일인 기본값, `medium`은 표준 다중 파일 작업, `high`는 강제로 쪼개지 않는 하나의 어려운 문제다.
- 구현과 그 테스트는 한 할 일이다.
- 열 너비 0의 `- [ ] <N>.` 행만 할 일이다. 제목, 문단, 일반 불릿은 작업이 아니다.
- 열린 질문에 막힌 할 일은 `Acceptance`에 게이트를 적거나 `- [~]`와 중첩 `Unmet: <gap>`으로 닫는다.

## 8. 최종 검증 웨이브

모든 할 일 뒤에 돈다. 행은 고정이다.

```markdown
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)
```

여기서 발견한 부족은 메모가 아니라 새 `- [ ] <N>.` 할 일이 된다.

## 9. 커밋 전략

할 일마다 커밋 하나를 저장소 메시지 관례대로 만들고 그 할 일의 쓰기 범위만 담는다. 증거 파일을 커밋하는지 무시하는지, 웨이브를 한 번의 병합으로 착륙시키는지 적는다. 각 할 일의 커밋 줄과 이 전략이 일치해야 한다.

## 10. 성공 기준

| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1, 3 | `curl -i`가 여섯 번째 요청에 429를 반환한다 | `.hyper/qa/<slug>/3-happy.txt` |

모든 `IS-` 행이 정확히 한 번 나온다. 증명 QA가 없는 행은 계획이 미완이라는 뜻이다.

## 11. 인계

```markdown
## Handoff
- Auto-execute: yes | no (<reason>)
- Delivery: local | make-pr | ship
- Plan-only requested: yes | no
```

`Auto-execute: yes`는 계획 파일, 통과한 구조 자체 점검, 승인됐거나 수렴한 리뷰, 선택 철회 없음, 열린 소유자 결정 없음이 모두 필요하다. 묶음에 사용자 판단이 필요한 열린 질문이 남아 있으면 인계는 `Auto-execute: no (<열린 질문>)`다.

## 12. 체크박스 상태

| State | Meaning |
|---|---|
| `- [ ]` | 열림 |
| `- [x]` | 완료하고 검증함 |
| `- [~]` | 막힘으로 닫음, 중첩 `Unmet: <gap>` 줄 |

중첩 체크박스는 작업이 아니다.

## 13. 예시 조각

```markdown
# login-rate-limit - Work Plan
## TL;DR
- What you get: a per-IP limit of 5 requests per minute on `/login`, applied across all nodes.
- Why this approach: the existing Redis client already holds shared counters, and the debate kept it over an in-process counter.
- What it will not do: no account lockout, no CAPTCHA, no admin bypass screen.
- Effort: Short
- Risk: the shared counter adds a Redis dependency to the login path; a five-perspective debate ran before this plan and settled the storage question.
- Decisions made for you: Redis storage (reversible), 429 with `Retry-After` (reversible).
## Scope
### Affected user and ideal state
Affected user: a person signing in through a load balancer.
| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | One count per IP across nodes | A user behind a balancer is not counted five times |
| IS-2 | The over-limit reply says when to retry | The user can wait instead of guessing |
| GAP-1 | No limit exists today | Brute force is unbounded |
### Must have
- A 5-per-minute per-IP limit on `POST /login`.
### Must NOT have
- Account lockout, CAPTCHA, or an admin bypass endpoint.
## Verification strategy
- `bun test src/auth` for unit and integration, `bun run typecheck`, `curl -i` for the real-surface check.
## Execution strategy
### Wave 1
- Todos 1 to 3.
| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | src/util/rate-limit.ts |
| 2 | 1 | 1 | src/auth/login.ts |
| 3 | 2 | 1 | src/auth/login.test.ts |
## Todos
- [ ] 1. Add a shared per-IP counter
  Wave: 1
  Depends on: none
  Write scope: src/util/rate-limit.ts
  References: src/redis.ts:12
  Acceptance: `bun test src/util` exits 0 with 3 passing
  QA happy: `bun -e "..."` prints `ok 1..5`; evidence: .hyper/qa/login-rate-limit/1-happy.txt
  QA failure: the same script with a stopped Redis exits non-zero; evidence: .hyper/qa/login-rate-limit/1-failure.txt
  Commit: feat(auth): add shared per-IP counter
  Tier: low - one utility module
## Final verification wave
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)
## Commit strategy
One commit per todo, conventional commits, no evidence files committed, wave 1 lands as one merge.
## Success criteria
| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1, 2 | five requests from one IP share one count | .hyper/qa/login-rate-limit/2-happy.txt |
| IS-2 | 3 | the 429 response carries `Retry-After` | .hyper/qa/login-rate-limit/3-happy.txt |
## Handoff
- Auto-execute: yes
- Delivery: local
- Plan-only requested: no
```

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| 제목 순서, `IS-`/`GAP-` 행 의미, 아홉 할 일 필드, tier 어휘, 고정 `F1`~`F4` 행, 성공 기준 열, 인계 필드, 체크박스 상태 | 이 패키지의 계획 문법. `instructions/skill/SKILL_AUTHORING.md`와 패키지 계획 계약에서 재수록 |
| slug 규칙 | `.hyper/` 작업 디렉터리 관례를 따르는 이 패키지의 설계 |
| 열린 질문에 막힌 할 일의 게이트 규칙 | 이 패키지의 설계, 2026-11-10 (issue #26) |

### Evidence grade

`LOCAL` - 예시 조각의 경로와 명령은 형식만 보여주는 허구다.
