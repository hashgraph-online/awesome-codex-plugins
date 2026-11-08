# Issue Body Template

본문을 쓸 때 이 참고 파일을 사용한다. 골격을 복사해 모든 자리표시자를 바꾼다. `##` 이름과 `hyper:` 키는 적힌 그대로 유지한다. 제목과 자리표시자를 바꾼 내용은 모두 영어로 쓴다(`rules/issue-contract.md` 2a절). 제목은 커밋 제목 형태 `type(scope): imperative summary`를 따른다.

## Contents

- 골격
- 작성 예
- 규칙

## 골격

```markdown
## What

<한 단락. 무엇이 잘못됐는지 또는 무엇을 원하는지. 누가 영향을 받고 무엇이 달라지는지.>

## Evidence

- `<path>:<line>` - 이것이 보여 주는 것
- `<command>` -> 관측한 출력 중 중요한 줄만

<위 내용 중 추론한 것이 있으면 Assumption 줄:>
- Assumption: <the inferred statement> - Confirm by: <what would confirm it>

## Cause

<bug: 위 경로에 연결한 확인된 원인. 증상, 유발 조건, 원인을 구분해 적는다.>

## Intended behavior

<feature 또는 task: 결정된 동작. 오류 경로와 바뀌지 않는 동작 포함.>

## Scope

<변경 경계를 한두 문장으로. 무엇을 고치고, 더하고, 지우는지.>

```yaml
hyper:
  touches:
    - <경로 또는 글롭>
  depends_on: []
  conflicts_with: []
  lane_hint: <kebab-case>
  verify: "<그대로의 명령>"
  size: <s | m | l>
```

## Out of scope

- <독자가 포함됐다고 오해할 만한 것>

## Acceptance

- [ ] <명령과 기대 결과가 붙은 이분법 검사>
- [ ] <오류 경로 검사>

## Verify

```sh
<hyper.verify의 그대로의 명령>
```

Pass: <작업이 끝났을 때 출력이 어떤 모습인지>.
```

## 작성 예

실제 이슈는 영어로 쓰므로 작성 예도 영어 그대로 둔다.

Title: `fix(orders): return 409 on idempotency key replay`

```markdown
## What

`POST /api/orders` returns 500 instead of 409 when the same idempotency key is replayed within the retry window. Callers retrying after a timeout create duplicate orders.

## Evidence

- `src/api/orders.ts:88` - the idempotency key is read after the insert attempt
- `bun test src/api/orders.test.ts` -> `1 fail: replays a duplicate key` with `duplicate key value violates unique constraint`
- `docs/contracts/orders.md:14` - the contract requires 409 on replay

## Cause

The insert runs before the key lookup at `src/api/orders.ts:88`, so a replay reaches the database unique constraint and the unhandled error becomes a 500. The contract lookup was added later at `:95` and never moved ahead of the insert.

## Scope

Move the key lookup before the insert and return 409 with the stored order id when a replay is found. The insert path and the response shape for new orders stay unchanged.

```yaml
hyper:
  touches:
    - src/api/orders.ts
    - src/api/orders.test.ts
  depends_on: []
  conflicts_with: []
  lane_hint: orders-idempotency
  verify: "bun test src/api/orders.test.ts"
  size: s
```

## Out of scope

- Changing the retry window length
- Backfilling duplicate orders already created

## Acceptance

- [ ] `bun test src/api/orders.test.ts` passes, including the replay case asserting 409 and the original order id
- [ ] A first request still returns 201 with a new order id

## Verify

```sh
bun test src/api/orders.test.ts
```

Pass: every case green, and the replay case logs `409` rather than `500`.
```

## 규칙

- 본문은 홀로 선다. "앞서 논의한 대로"도, 이해에 필요한 링크도 없고, 인용한 출력 말고는 모두 영어다.
- 인용은 짧게, 출처를 붙이고, 비밀은 가린다.
- 본문 하나에 `hyper:` 블록 하나이며 `## Scope`의 유일한 펜스 `yaml` 블록이다.
- `verify`는 이슈가 다르게 말하지 않는 한 브라우저, 자격증명, 네트워크 호출 없이 실행 가능해야 한다.

## Sources

> 확인 2026-11-07.

| Claim | Source |
|---|---|
| 본문 절, `hyper:` 키, 작성 예의 형태 | 이 패키지가 이슈 작성 선행 사례 위에 세운 설계, 2026-11-07 |
| 로그와 세션이 사라진 뒤에도 쓸 수 있는 본문 | [kdy1-scripts add-issue](https://github.com/kdy1/kdy1-scripts) |

### 근거 등급

`LOCAL` - 템플릿과 예시는 이 저장소의 이슈 흐름을 위해 이 패키지가 직접 작성한 것이다.
