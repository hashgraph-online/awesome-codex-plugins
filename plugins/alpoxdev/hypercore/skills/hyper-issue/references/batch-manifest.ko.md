# Batch Manifest

`.hyper/issues/<slug>/batch.md`를 쓰기 전에 이 참고 파일을 사용한다. 명세 형식, 레인 표, 핸드오프 줄을 소유한다.

## Contents

- 형식
- 규칙
- 레인 분할 예

## 형식

```markdown
# Batch: <slug>

- 생성 일시: YYYY-MM-DD HH:MM
- 저장소: <owner/repo>
- 질의: `<그대로의 질의>` | 번호: `<적힌 그대로의 번호>` -> <전개한 목록>
- 수집: <반환 행 수> / 총계 <total> | 페이지 <n>개 | 잘림 없음 (번호 모드: 남김 <k> / 지목 <n>)
- 대상 브랜치: <base branch>
- 레인 상한: <n>
- 차단: <none | 차단 요인, 줄마다 하나>

## Issue 목록

| # | 이슈 | 제목 | 분류 | 크기 | 레인 | 순서 | verify |
|---|---|---|---|---|---|---|---|
| 1 | #12 | <제목> | bug | s | orders-idempotency | 1 | `bun test src/api/orders.test.ts` |
| 2 | #14 | <제목> | task | m | docs-parity | 1 | `bash scripts/check.sh` |

## Lane 표

| Lane | 이슈 순서 | 쓰는 경로 | 근거 |
|---|---|---|---|
| orders-idempotency | #12 | src/api/orders.ts, src/api/orders.test.ts | 1 |
| docs-parity | #14 | skills/**/*.md | 1 |

## 그래프

- 간선: #12 -> #14 (직접 선언 아님, `touches` 겹침 아님, 선언 순서만)
- 순환: <none | 순환 경로>

## 공백과 차단

- <이슈> - `hyper:` 블록 없음, `## Scope`에서 재도출함
- <이슈> - `size: l`, 배정 전 분할 필요
- #<n> - 제외: <pull request | closed | not found | read failed>

## 핸드오프

- 배치 명세: `.hyper/issues/<slug>/batch.md`
- 이슈 <n>건, 레인 <m>개, 차단 <k>건
- 다음 단계는 이 파일을 고정 입력으로 읽는다. 목록을 바꾸지 않는다.
- 다음 단계: hyper (넘김, YYYY-MM-DD HH:MM) | 없음 (<--no-run | --from-hyper | 실행 가능한 레인 없음>)
```

## 규칙

- `## Issue 목록`의 순서는 선택 시점의 정규 순서다. 나중에 다시 정렬하지 않는다.
- `## Lane 표`는 레인별 쓰는 경로의 합집합을 적어, 레인이 서로 겹치지 않음을 한눈에 확인하게 한다.
- 이슈가 하나뿐인 레인도 적는다. 레인은 병렬성이 아니라 쓰기 집합이다.
- `## 그래프`는 간선과 그 출처를 적는다. 직접 선언, 겹침 도출, 순서만.
- `## 공백과 차단`은 모든 이슈에 파싱 가능한 블록이 있고, 분할이 필요 없었고, 뺀 번호가 없었던 경우가 아니면 비어 있지 않다. 그런 경우에도 `none`을 명시한다.
- 핸드오프 줄의 개수는 표에서 읽어 센다. 추정하지 않는다.
- `대상 브랜치`에는 사용자가 납품 대상으로 지목한 브랜치만 적는다. 지목이 없으면 `미정 (사용자 지정 없음)`으로 적는다. 배치는 기준 브랜치를 지어내지 않는다. 통합 기준은 계획 단계가 정하고, 푸시 여부는 사용자의 납품 단어가 정한다.

## 레인 분할 예

이슈 세 개가 들어온다.

- `#21`은 `src/api/a.ts`와 `src/api/a.test.ts`를 쓴다. `size: s`
- `#22`는 `src/api/a.ts`를 쓴다. `depends_on: [21]`
- `#23`은 `docs/api.md`를 쓴다.

결과: `#21`과 `#22`가 경로를 공유하므로 의존 순서의 한 레인이 된다(`21` 다음 `22`). `#23`은 자기 레인이다. 레인 두 개가 동시에 돌 수 있고, 두 레인이 같은 경로를 쓰지 않는다.

`src/api/a.ts`와 `docs/api.md`를 모두 쓰는 `#24`가 추가되면 `21`/`22` 레인에 합류하고, `#23`은 그 뒤로 밀린 합쳐진 레인에 들어간다. 쓰기 집합을 겹치지 않게 유지하려면 레인을 합치는 것 외에 방법이 없기 때문이다.

## Sources

> 확인 2026-11-07.

| Claim | Source |
|---|---|
| 정규 목록 고정, 레인별 순서, 다음 단계가 그대로 읽는 명세 | [kdy1-scripts slop-fix-batch](https://github.com/kdy1/kdy1-scripts) |
| 서로 겹치지 않는 쓰기 집합이라는 레인 규칙과, 공유 파일이 레인을 하나로 강제하는 점 | [automazeio/ccpm](https://github.com/automazeio/ccpm) |
| 동시 에이전트 변경 사이의 충돌률이 분리 이유라는 근거 | [AI Agent PRs on GitHub](https://arxiv.org/abs/2607.04697) |

### 근거 등급

`LOCAL` - 명세 형식과 레인 표는 이 패키지의 설계이고, 고정 규칙은 위 선행 사례를 각색했다.
