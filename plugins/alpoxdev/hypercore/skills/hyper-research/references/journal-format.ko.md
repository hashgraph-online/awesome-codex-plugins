# 저널 형식

기본, deep, parallel 실행에서 저널 디렉터리를 열기 전에 이 참고 파일을 사용합니다. `--quick`은 source ledger와 질의 로그를 저널 대신 리포트 안에 둡니다.

## 목차

- 디렉터리 구조
- `brief.md`
- `sources.md`
- `queries.md`
- `expansion.md`
- `claims.md`
- `verify-<slug>.md`
- 작성 규칙

## 디렉터리 구조

```text
.hyper/research/
├── [NN].slug.md          # 저장된 리포트
└── [NN].slug/            # 저널, 같은 이름
    ├── brief.md
    ├── sources.md
    ├── queries.md
    ├── expansion.md
    ├── claims.md
    └── verify-<slug>.md  # 실행 검사마다 하나, 있을 때만
```

모든 파일은 리더가 씁니다. lane은 텍스트를 돌려주기만 하고 여기에 쓰지 않습니다.

## `brief.md`

```markdown
# Brief: <주제>

Run started: YYYY-MM-DD HH:MM | Depth: default | Parallel: no

## Analysis
Core question:
Axes:
- A1 <축> - <무엇을, 어디서, 왜>
Expected truths:
- E1 <진술> - status: true | violated | unknown
Entity: <정규 이름, 1차 출처 URL, 신뢰도>
Codebase relevant: | External: | Execution checks likely: | Precision demand:

## Fidelity
as of: 실행 시작 시점의 최신, YYYY-MM-DD (answered_by: default)
source floor: standard (answered_by: default)
derived numbers: allowed (answered_by: default)
asked: <물어본 필드, 없으면 none>

## Steering
- <사용자 표현 그대로> - <적용된 웨이브>
```

## `sources.md`

소스를 여는 순간 한 행을 씁니다. `S<n>` id는 실행 내내 고정이며 리포트가 인용하는 값입니다.

```markdown
| # | Source | URL/path | Publisher | Published/updated | Accessed | Version/freshness | Channel | Grade | Role | Relevant claim | Used? | Caveat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | | | | | | | | S/A/B/C | lead/primary-evidence/supporting/conflict/rejected | | yes/no | |
```

- 등급: 1차, 공식, 표준, 자사 자료는 S입니다. 독립 방법론이나 주요 기관은 A입니다. 실무자나 벤더 자료는 B입니다. 홍보성, 출처 불명, 오래된 자료, lead만 있는 경우는 C입니다.
- 스니펫이나 lane의 요약으로 쓴 행은 원본을 열 때까지 `Caveat`에 `unverified`로 표시합니다.
- 위험도가 높은 행 아래에는 주장이 기대는 구절이나 줄을 그대로 남깁니다.
- 막힌 페이지 경로로 연 소스는 `Channel`에 경로와 출처 표시를, `Version/freshness`에 스냅숏 시각을, `Caveat`에 접근 보고서 경로를 적습니다(`references/channel-selection.ko.md`, 막힌 출처). 끝내 열지 못한 소스도 행을 남기고 `Used?`를 `no`로, 막은 신호를 `Caveat`에 적습니다.

## `queries.md`

```markdown
| # | Query / command | Channel | Axis or lead | Why this query | Result | Follow-up |
|---|---|---|---|---|---|---|
```

같은 질의나 의미가 같은 질의를 두 번 쓰지 않습니다. claim gate용 반대 검색은 `Why` 열에 `counter:`를 붙여 여기에 기록합니다.

## `expansion.md`

```markdown
## Wave 1
Searches or lanes: <목록>
Returns:
- <lane 또는 축>: <요약>
  ## EXPAND (verbatim)
Leads opened: L1 <lead>, L2 <lead>
Leads closed: L0 duplicate of ... | dead end because ...

## Excursions
| id | parent claim or axis | trigger | budget | depth | exit rule | changed in the answer |
|---|---|---|---|---|---|---|

## Run state
converged | exhausted (상한, 열린 lead, 마지막 결과, 확장 계획) | blocked (접근 불가)
```

## `claims.md`

```markdown
## verified-claims
- C1: <진술>

## Claim table
| claim_id | statement | risk | sources | domains | primary | counter-search | dates (published / accessed / valid as of) | lineage | status |
|---|---|---|---|---|---|---|---|---|---|
| C1 | | high | S1, S4 | 2 | S1 | Q7: 더 강한 근거 없음 | | MEASURED | supported |

## Unresolved
- C5: <진술> - <빠진 근거>

## Refuted
- C6: <진술> - <반대 근거와 S id>
```

상태는 `supported`, `partial`, `refuted`, `unresolved` 중 하나입니다. 리포트에서 위험도가 높은 주장으로 단정할 수 있는 것은 `## verified-claims`의 행뿐입니다.

## `verify-<slug>.md`

```markdown
# Verify: <주장>
Claim id: C3 | Source: S2 | Contradiction: S5
Environment: <운영체제, 런타임, 의존성 버전>
## Code
## Output
## Verdict
CONFIRMED | REFUTED | PARTIAL - <위 출력에 근거>
Cleanup: <임시 디렉터리 제거, 경로>
```

## 작성 규칙

- 사건이 생길 때 덧붙이고, 실행 끝에 몰아서 쓰지 않습니다.
- 관찰한 내용을 바꾸려고 지난 행을 고쳐 쓰지 않습니다. 새 행을 추가하고 옛 행은 이유와 함께 `rejected`나 `conflict`로 표시합니다.
- 날짜는 어디서나 절대 날짜로 씁니다. 상대 날짜를 쓰지 않습니다.
- 추출한 주장은 원문 페이지 텍스트가 아니라 출처와 날짜를 함께 저장합니다.

## Sources

> 확인 2026-11-03.

| Claim | Source |
|---|---|
| 출처, 확장, 주장, 검증 파일을 따로 두고 리더가 실시간으로 쓰는 세션 저널은 `ulw-research` 스킬을 각색한 것 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| ledger 열, 등급, 역할, 질의 로그, 원본을 열기 전까지 `unverified`로 두는 에이전트 행 | `instructions/sourcing/references/source-ledger.md` |
| 검색한 원문 텍스트를 영구 상태에 저장하지 않음 | `instructions/sourcing/references/retrieval-safety.md` |

### 근거 등급

`LOCAL` - 이 파일은 이 패키지 자체의 저널 배치를 규정합니다. 파일 이름과 열은 이 패키지의 선택이며, 상류 스킬은 다른 파일 집합을 씁니다.
