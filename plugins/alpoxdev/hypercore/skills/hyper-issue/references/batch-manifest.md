# Batch Manifest

Use this reference before writing `.hyper/issues/<slug>/batch.md`. It owns the manifest format, the lane table, and the handoff line.

## Contents

- Format
- Rules
- Worked example lane split

## Format

```markdown
# Batch: <slug>

- 생성 일시: YYYY-MM-DD HH:MM
- 저장소: <owner/repo>
- 질의: `<the exact query>` | 번호: `<the numbers as written>` -> <expanded list>
- 수집: <rows returned> / 총계 <total> | 페이지 <n>개 | 잘림 없음 (번호 모드: 남김 <k> / 지목 <n>)
- 대상 브랜치: <base branch>
- 레인 상한: <n>
- 차단: <none | the blockers, one per line>

## Issue 목록

| # | 이슈 | 제목 | 분류 | 크기 | 레인 | 순서 | verify |
|---|---|---|---|---|---|---|---|
| 1 | #12 | <title> | bug | s | orders-idempotency | 1 | `bun test src/api/orders.test.ts` |
| 2 | #14 | <title> | task | m | docs-parity | 1 | `bash scripts/check.sh` |

## Lane 표

| Lane | 이슈 순서 | 쓰는 경로 | 근거 |
|---|---|---|---|
| orders-idempotency | #12 | src/api/orders.ts, src/api/orders.test.ts | 1 |
| docs-parity | #14 | skills/**/*.md | 1 |

## 그래프

- 간선: #12 -> #14 (직접 선언 아님, `touches` 겹침 아님, 순서만 선언 순서)
- 순환: <none | the cycle>

## 공백과 차단

- <issue> - `hyper:` 블록 없음, `## Scope`에서 재도출함
- <issue> - `size: l`, 배정 전 분할 필요
- #<n> - 제외: <pull request | closed | not found | read failed>

## 핸드오프

- 배치 명세: `.hyper/issues/<slug>/batch.md`
- 이슈 <n>건, 레인 <m>개, 차단 <k>건
- 다음 단계는 이 파일을 고정 입력으로 읽는다. 목록을 바꾸지 않는다.
- 다음 단계: hyper (넘김, YYYY-MM-DD HH:MM) | 없음 (<--no-run | --from-hyper | 실행 가능한 레인 없음>)
```

## Rules

- The `## Issue 목록` order is the canonical order from selection; never re-sort it after the fact.
- `## Lane 표` lists the union of written paths per lane, so a reader can confirm the lanes are disjoint at a glance.
- A lane with one issue still appears; a lane is not "parallelism", it is a write set.
- `## 그래프` records edges with their origin: declared, overlap-derived, or ordering-only.
- `## 공백과 차단` is never empty unless every issue had a parseable block, no split was needed, and no named number was excluded; write `none` explicitly.
- The handoff line's counts are read off the tables, never estimated.
- `대상 브랜치` records only the branch the user named for delivery. With no named branch it reads `미정 (사용자 지정 없음)`; the batch never invents a base branch, because the plan stage picks its own integration base and the user's delivery words decide the push.

## Worked Example Lane Split

Three issues arrive:

- `#21` writes `src/api/a.ts` and `src/api/a.test.ts`, `size: s`
- `#22` writes `src/api/a.ts`, `depends_on: [21]`
- `#23` writes `docs/api.md`

Result: `#21` and `#22` share a path, so they form one lane in dependency order (`21`, then `22`); `#23` is its own lane. Two lanes, both runnable at once, with no path written by two lanes.

A fourth issue `#24` that writes both `src/api/a.ts` and `docs/api.md` joins the `21`/`22` lane and forces `#23` to wait behind it in a merged lane, because merging the lanes is the only way to keep the write sets disjoint.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| A fixed canonical list, per-lane order, and a manifest the next stage reads unchanged | [kdy1-scripts slop-fix-batch](https://github.com/kdy1/kdy1-scripts) |
| Disjoint write sets as the lane rule, and shared files forcing one lane | [automazeio/ccpm](https://github.com/automazeio/ccpm) |
| Conflict rates between concurrent agent changes as the reason for disjointness | [AI Agent PRs on GitHub](https://arxiv.org/abs/2607.04697) |

### Evidence grade

`LOCAL` - the manifest format and the lane table are this package's design; the freeze rule is adapted from the named prior art.
