# 계획 형식

계획 파일을 쓰거나 검증하기 전에 이 참조를 읽습니다. 이 파일은 계획 문법, 즉 제목 순서, todo 행 필드, 체크박스 상태, 완성 예시를 맡습니다.

## 목차

1. 파일 위치와 slug
2. 제목 순서
3. TL;DR
4. Scope
5. 검증 전략
6. 실행 전략
7. Todos
8. 최종 검증 wave
9. 커밋 전략
10. 성공 기준
11. Handoff
12. 체크박스 상태
13. 완성 예시

## 1. 파일 위치와 slug

계획은 `.hyper/plans/<slug>.md`에, 드래프트는 `.hyper/drafts/<slug>.md`에 둡니다. slug는 소문자 ASCII 케밥 표기로 `^[a-z0-9]+(-[a-z0-9]+)*$`에 맞고 48자 이하여야 합니다. `..`, `/`, 절대 경로는 거부합니다. 계획의 첫 줄은 `# <slug> - Work Plan`입니다.

## 2. 제목 순서

아래 제목이 각각 한 번씩, 이 순서와 문구로 나옵니다.

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

제목을 더 넣는 것은 마지막 제목 아래에서만 허용하고 실행자는 그 절을 무시합니다. 제목을 옮기거나 이름을 바꾸면 계약이 깨집니다.

## 3. TL;DR

마지막에 채웁니다. 여섯 줄을 담습니다.

- 사용자가 얻는 것
- 이 접근을 고른 이유
- 하지 않을 것
- `Effort:`는 `Quick`, `Short`, `Medium`, `Large`, `XL` 중 정확히 하나이고 시간이나 일수는 쓰지 않습니다
- `Risk:`는 근거 확보 중 찾은 구체적 위험이고, 작업 트리가 더러우면 그 사실도 포함합니다
- `Decisions made for you:`는 채택한 기본값과 되돌릴 수 있는지를 함께 적습니다

## 4. Scope

`### Affected user and ideal state`는 결과가 닿는 대상과 그 대상이 오늘 어떻게 쓰고 앞으로 어떻게 쓸지 적은 뒤 행을 둡니다.

| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | 걸리거나 퇴행하는 것이 없는 상태의 속성 | 그 이유 |
| GAP-1 | 그 상태와 오늘의 차이 | 그 이유 |

`### Must have`는 필요한 결과를 적습니다. `### Must NOT have`는 계획이 거부하는 추가 항목을 적습니다. 요청하지 않은 기능, 근거 없는 추상화, 말없는 범위 확장이 여기에 해당합니다. 이것은 안전장치이고 요청을 줄이는 수단이 아닙니다.

## 5. 검증 전략

테스트 수준과 실제 점검을 적습니다. 단위·통합 명령, 타입 검사, 린트, 빌드, todo별 실제 표면 점검(HTTP 응답, 터미널 실행, 브라우저 흐름, 데이터베이스 diff)이 여기에 해당합니다. 적용되는 적대적 범주와 적용되지 않는 이유도 적습니다. 최종 검증 wave는 여기서 요약하고 §8에서 구체화합니다.

## 6. 실행 전략

wave마다 `### Wave <N>` 절을 하나 두고 그 wave에서 도는 todo 번호를 적은 뒤, 의존성 행렬을 둡니다.

```markdown
| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | src/auth/login.ts |
```

한 wave의 todo는 쓰기 범위가 겹치지 않거나 순차로 실행합니다. wave마다 todo 5~8개를 목표로 합니다. 마지막이 아닌 wave에서 3개 미만이면 지나치게 덜 나눈 것입니다.

## 7. Todos

모든 실행 항목은 유일한 양의 정수로 번호를 붙인 column-zero 행입니다.

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

- 들여쓰기는 두 칸이고 아홉 필드가 이 순서로 나옵니다.
- `Acceptance`는 사람의 판단 없이 에이전트가 실행할 수 있어야 합니다.
- `QA happy`와 `QA failure`는 각각 변경이 동작함과 안전하게 실패함을 증명하고, 둘 다 근거 경로를 가집니다.
- `Tier: low`는 기계적이거나 파일 하나짜리 작업의 기본값, `medium`은 일반적인 다중 파일 작업, `high`는 억지로 쪼개지 않는 하나의 어려운 문제입니다.
- 구현과 그 테스트는 todo 하나입니다.
- column-zero `- [ ] <N>.` 행만 todo로 셉니다. 제목, 문단, 일반 불릿은 과제가 아닙니다.

## 8. 최종 검증 wave

모든 todo 뒤에 실행합니다. 행은 고정입니다.

```markdown
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)
```

여기서 나온 부족분은 메모가 아니라 새 `- [ ] <N>.` todo가 됩니다.

## 9. 커밋 전략

todo마다 커밋 하나를 저장소 메시지 관례로 만들고, 그 todo의 쓰기 범위만 담습니다. 근거 파일을 커밋하는지 무시하는지, wave를 병합 하나로 올리는지도 적습니다. 각 todo의 커밋 줄과 이 전략이 일치해야 합니다.

## 10. 성공 기준

| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1, 3 | `curl -i`가 여섯 번째 요청에 429를 돌려준다 | `.hyper/qa/<slug>/3-happy.txt` |

모든 `IS-` 행이 정확히 한 번 나옵니다. 증명 QA가 없는 행이 있으면 계획은 미완성입니다.

## 11. Handoff

```markdown
## Handoff
- Auto-execute: yes | no (<reason>)
- Delivery: local | make-pr | ship
- Plan-only requested: yes | no
```

`Auto-execute: yes`는 계획 파일, 통과한 구조 자기 점검, 승인됐거나 수렴한 리뷰, 거부 없음, 열린 소유자 결정 없음이 모두 성립할 때만 씁니다.

## 12. 체크박스 상태

| State | Meaning |
|---|---|
| `- [ ]` | 열림 |
| `- [x]` | 완료하고 검증됨 |
| `- [~]` | 막힘으로 닫힘. `Unmet: <gap>` 중첩 줄을 함께 쓴다 |

중첩 체크박스는 과제가 아닙니다.

## 13. 완성 예시

```markdown
# login-rate-limit - Work Plan
## TL;DR
- What you get: `/login`에 IP당 분당 5회 제한을 모든 노드에 걸쳐 적용한다.
- Why this approach: 기존 Redis 클라이언트가 이미 공유 카운터를 제공한다.
- What it will not do: 계정 잠금, CAPTCHA, 관리자 우회 화면은 없다.
- Effort: Short
- Risk: 로그인 경로에 Redis 의존성이 하나 늘어난다.
- Decisions made for you: Redis 저장(되돌릴 수 있음), `Retry-After`가 붙은 429(되돌릴 수 있음).
## Scope
### Affected user and ideal state
Affected user: 로드 밸런서를 거쳐 로그인하는 사람.
| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | 노드를 넘나들어도 IP당 카운트가 하나다 | 밸런서 뒤 사용자가 다섯 번 세어지지 않는다 |
| IS-2 | 제한 응답이 언제 다시 시도할지 알려 준다 | 사용자가 추측하지 않고 기다릴 수 있다 |
| GAP-1 | 오늘은 제한이 없다 | 무차별 대입이 무제한이다 |
### Must have
- `POST /login`에 IP당 분당 5회 제한을 둔다.
### Must NOT have
- 계정 잠금, CAPTCHA, 관리자 우회 엔드포인트.
## Verification strategy
- 단위·통합은 `bun test src/auth`, 타입 검사는 `bun run typecheck`, 실제 표면 점검은 `curl -i`로 한다.
## Execution strategy
### Wave 1
- Todo 1~3.
| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | src/util/rate-limit.ts |
| 2 | 1 | 1 | src/auth/login.ts |
| 3 | 2 | 1 | src/auth/login.test.ts |
## Todos
- [ ] 1. 공유 IP 카운터 추가
  Wave: 1
  Depends on: none
  Write scope: src/util/rate-limit.ts
  References: src/redis.ts:12
  Acceptance: `bun test src/util`가 3개 통과로 종료 코드 0
  QA happy: `bun -e "..."`가 `ok 1..5`를 출력; evidence: .hyper/qa/login-rate-limit/1-happy.txt
  QA failure: Redis를 멈춘 상태에서 같은 스크립트가 비정상 종료; evidence: .hyper/qa/login-rate-limit/1-failure.txt
  Commit: feat(auth): add shared per-IP counter
  Tier: low - 유틸 모듈 하나
- [ ] 2. 로그인 핸들러에서 제한 적용
  Wave: 1
  Depends on: 1
  Write scope: src/auth/login.ts
  References: src/auth/login.ts:40
  Acceptance: `bun test src/auth/login.test.ts`가 4개 통과로 종료 코드 0
  QA happy: `curl -i`를 다섯 번 호출하면 200 다섯 번 뒤 429; evidence: .hyper/qa/login-rate-limit/2-happy.txt
  QA failure: 잘못된 IP 헤더는 500이 아니라 400; evidence: .hyper/qa/login-rate-limit/2-failure.txt
  Commit: feat(auth): enforce per-IP login limit
  Tier: medium - 핸들러 하나와 공유 제한기
- [ ] 3. 재시도 대기 시간 반환
  Wave: 1
  Depends on: 2
  Write scope: src/auth/login.ts
  References: src/auth/login.ts:40
  Acceptance: `bun test src/auth/login.test.ts`가 5개 통과로 종료 코드 0
  QA happy: 429 응답에 `Retry-After: 60`이 붙는다; evidence: .hyper/qa/login-rate-limit/3-happy.txt
  QA failure: 제한 직전 요청에는 `Retry-After`가 없다; evidence: .hyper/qa/login-rate-limit/3-failure.txt
  Commit: feat(auth): return retry window on limit
  Tier: low - 응답 헤더 하나
## Final verification wave
- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)
## Commit strategy
todo마다 커밋 하나, 컨벤셔널 커밋, 근거 파일은 커밋하지 않음, wave 1은 병합 하나로 올린다.
## Success criteria
| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1, 2 | 한 IP의 다섯 요청이 카운트 하나를 공유한다 | .hyper/qa/login-rate-limit/2-happy.txt |
| IS-2 | 3 | 429 응답에 `Retry-After`가 있다 | .hyper/qa/login-rate-limit/3-happy.txt |
## Handoff
- Auto-execute: yes
- Delivery: local
- Plan-only requested: no
```

## Sources

> 확인 2026-11-03.

| Claim | Source |
|---|---|
| 제목 순서, `IS-`와 `GAP-` 행의 의미, todo 필드 목록, tier 어휘, 고정된 `F1`부터 `F4` 행, 성공 기준 열, 인계 필드, 체크박스 상태 | 이 패키지 자체 설계, 사용자 지시, 2026-11-03 |
| slug 규칙과 드래프트 경로 | 저장소의 `.hyper/` 작업 디렉터리 관례를 따른 이 패키지 자체 설계 |
| 계획 골격과 산출 규칙은 OmO 공유 스킬 패키지의 `ulw-plan` 템플릿 스크립트를 각색한 것 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| column-zero 과제 행만 과제로 센다 | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |

### 근거 등급

`LOCAL` - 이 파일은 패밀리 계약의 문법을 예시와 함께 다시 적은 것입니다. 예시의 경로와 명령은 형태를 보여 주려고 만든 가상 값입니다.
