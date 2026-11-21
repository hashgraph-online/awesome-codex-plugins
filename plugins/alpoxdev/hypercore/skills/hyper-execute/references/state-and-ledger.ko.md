# State And Ledger

이 참조 파일은 `state.json`이나 `ledger.jsonl`을 쓰기 전, 그리고 컨텍스트 압축이나 중단 직후에 읽습니다. 디스크 스키마, 이벤트 어휘, 완료 블록 템플릿, 재개 점검 목록을 소유합니다.

## 목차

- 디렉터리 배치
- `state.json`
- `ledger.jsonl`
- 이벤트 어휘
- 예시 줄
- 완료 블록 템플릿
- 재개 점검 목록

## 디렉터리 배치

```text
.hyper/execute/<slug>/
├── state.json          # 현재 위치, 객체 하나, 제자리에서 덮어씀
├── ledger.jsonl        # 추가 전용, 줄마다 JSON 객체 하나
└── evidence/           # 각 웨이브 워크트리에서 복사해 온 아티팩트
```

`<slug>`는 계획 slug입니다. 소문자 ASCII kebab-case, `^[a-z0-9]+(-[a-z0-9]+)*$`, 최대 48자입니다. 계획은 `.hyper/plans/<slug>.md`에 있고 여기로 복사하지 않습니다.

이 디렉터리의 모든 경로는 `state.json`에 기록한 메인 체크아웃 절대 경로인 `main_root` 기준으로 풉니다. `.hyper/`는 gitignore되어 웨이브 워크트리 안에 없을 수 있으므로, 워크트리 상대 경로로 읽거나 쓰지 않습니다. 체크박스 전환은 `<main_root>/.hyper/plans/<slug>.md`의 계획을 고칩니다.

## `state.json`

객체 하나를 모든 단계 경계에서 덮어씁니다. 이것은 실행의 이력이 아니라 현재 위치입니다.

| 필드 | 타입 | 의미 |
|---|---|---|
| `schema_version` | integer | `1` |
| `slug` | string | 계획 slug |
| `plan_path` | string | `main_root` 기준으로 푼 계획 경로 |
| `main_root` | string | 메인 체크아웃의 절대 경로. 계획, 상태, 원장, 근거 경로를 모두 여기 기준으로 풉니다 |
| `integration_base` | string | 0단계에 기록한 브랜치 이름, 분리된 HEAD면 sha |
| `delivery` | string | `local`, `make-pr`, `ship` 중 하나 |
| `status` | string | `active`, `paused`, `blocked`, `complete` 중 하나 |
| `current_wave` | integer 또는 null | 실행 중인 웨이브, 첫 웨이브 전에는 null |
| `worktree_path` | string 또는 null | 현재 웨이브 워크트리의 절대 경로 |
| `lane_worktrees` | 문자열 배열, 선택 | 웨이브가 병렬 레인으로 돌 때 레인별 워크트리 절대 경로, 레인 합치기 순서대로 |
| `wave_bases` | object | 웨이브 번호에서 그 웨이브가 시작한 브랜치로 가는 맵: `"1": "main"`, `"2": "hyper/billing-retry/w1"` |
| `started_at` | string | ISO 8601 시각 |

런타임이나 실행이 필요로 할 때 쓰는 선택 필드: `updated_at`, `goal_id`, `subagent_capability`(`available` 또는 `none`), `isolation`(`worktree`, `in-place`, `in-place (no vcs)`), `stop_reason`, `rows`(행 번호에서 `{ "state": "open|in_progress|done|blocked", "attempts": 0, "checkpoint_opened_at": null }`로 가는 맵).

```json
{
  "schema_version": 1,
  "slug": "billing-retry",
  "plan_path": ".hyper/plans/billing-retry.md",
  "main_root": "/Users/me/dev/shop",
  "integration_base": "main",
  "delivery": "local",
  "status": "active",
  "current_wave": 2,
  "worktree_path": "/Users/me/dev/shop/.hyper/worktree/billing-retry-w2",
  "wave_bases": { "1": "main", "2": "main" },
  "started_at": "2026-11-03T09:10:00+09:00"
}
```

`state.json`은 어떤 사실의 유일한 기록이 아닙니다. 원장과 어긋나면 이력은 원장을 따르고, 열린 행은 계획을 따릅니다.

## `ledger.jsonl`

추가 전용입니다. 줄마다 JSON 객체 하나입니다. 모든 줄은 아래 키 집합을 전부 담고, 해당하지 않는 필드는 생략하지 않고 `null` 또는 `[]`로 씁니다. 그래야 이벤트 종류와 무관하게 하나의 필터로 파일을 읽을 수 있습니다.

| 필드 | 타입 | 의미 |
|---|---|---|
| `event` | string | 이벤트 어휘 중 하나 |
| `ts` | string | ISO 8601 시각 |
| `task` | string 또는 null | 행 번호와 제목, 또는 웨이브 라벨 |
| `attempt` | integer 또는 null | 그 행의 시도 번호, 1부터 |
| `checkpoint_opened_at` | string 또는 null | 그 행의 첫 배정 시각, ISO 8601 |
| `commands` | 문자열 배열 | 실행한 명령과 결과 줄을 그대로 |
| `artifact` | 문자열 배열 | 근거 경로 |
| `adversarial_classes` | 객체 배열 | `{ "class": "...", "result": "...", "reason": "..." }` |
| `cleanup` | 문자열 배열 | 철거 영수증, 또는 자원을 남긴 사유 |
| `verdict` | 객체 또는 null | `{ "verdict": "...", "failure_class": "...", "signature": "..." }` |

`wave`, `tier`, `worker`, `write_scope`, `commit`, `pr`, `state`, `reason` 같은 추가 키를 허용합니다. 재개할 때 유용한 정보가 바로 이 키들입니다.

## 이벤트 어휘

| 이벤트 | 기록 시점 |
|---|---|
| `run.started` | 계획, 기준, 전달 방식을 기록했을 때 |
| `goal.registered` | 세션 목표를 세웠거나 목표 id를 기록했을 때 |
| `resume` | 일시 정지, 압축, 중단 뒤 디스크에서 이어갈 때 |
| `wave.started` | 웨이브를 열 때. 행, 인수 줄, 워크트리를 함께 적습니다 |
| `dispatch` | 워커 작업을 배정했거나 행의 작업을 다시 시작했을 때 |
| `verdict` | 검증자가 판정을 반환했을 때. `needs-fix`도 포함합니다 |
| `row.closed` | 행을 게이트 아티팩트와 함께 `[x]`로 뒤집었을 때 |
| `row.blocked` | 행을 `Unmet:` 줄과 서명을 붙여 `[~]`로 뒤집었을 때 |
| `landed` | 웨이브가 자기 기준에 반영되었을 때. 로컬 병합이나 PR 생성이며, 반영 sha나 PR URL을 함께 적습니다 |
| `delivery` | 푸시, PR, 병합을 수행했거나 사유와 함께 건너뛰었을 때 |
| `cleanup` | 워크트리, 브랜치, 디렉터리를 제거했거나 남겼을 때 |
| `stop` | 실행을 조기 종료할 때. 사유와 열린 행을 적습니다 |

## 예시 줄

```json
{"event":"dispatch","ts":"2026-11-03T09:20:00+09:00","task":"2. Add retry budget","attempt":1,"checkpoint_opened_at":"2026-11-03T09:20:00+09:00","commands":[],"artifact":[],"adversarial_classes":[{"class":"stale_state","result":"pending","reason":"row regenerates a cache"}],"cleanup":[],"verdict":null,"wave":2,"tier":"medium","write_scope":"src/billing/retry.ts"}
{"event":"verdict","ts":"2026-11-03T10:02:00+09:00","task":"2. Add retry budget","attempt":1,"checkpoint_opened_at":"2026-11-03T09:20:00+09:00","commands":["bun test src/billing -> 41 pass"],"artifact":[".hyper/execute/billing-retry/evidence/2-gates-curl.txt"],"adversarial_classes":[{"class":"stale_state","result":"pass","reason":"second run reused state without a stale read"}],"cleanup":["port 4310 closed"],"verdict":{"verdict":"confirmed","failure_class":"none","signature":null}}
{"event":"row.blocked","ts":"2026-11-03T11:40:00+09:00","task":"5. Migrate ledger backfill","attempt":3,"checkpoint_opened_at":"2026-11-03T10:10:00+09:00","commands":["bun run migrate -> duplicate key on ledger_id"],"artifact":[],"adversarial_classes":[],"cleanup":["temp database dropped"],"verdict":{"verdict":"needs-fix","failure_class":"product","signature":"duplicate key on ledger_id"}}
```

## 완료 블록 템플릿

마지막 검증 웨이브 뒤에 한 번 출력합니다.

```text
HYPER EXECUTE COMPLETE - <slug>
Plan: <plan_path>
Main root: <main_root>
Delivery: <local | make-pr | ship>   Base: <integration_base>   Status: <complete | blocked>
CI: <green | failing | unverified | not-applicable>
Rows: <n> done, <m> blocked
Blocked:
  - <행 번호와 제목>: <공백>  (signature: <서명>, attempts: <시도 수>)
Verification:
  - <명령> -> <결과>
  - <명령> -> <결과>
Artifacts: <evidence 디렉터리>, <중요 아티팩트 경로>
Landed commits: <sha> <subject> (웨이브별)
Pull requests: <url> (<상태>) | none
Removed: <워크트리 경로>, <병합된 브랜치>, <제거했으면 repo-wt 디렉터리>
Kept: <경로>: <사유>
Residual risk: <한두 줄, 또는 "none identified">
```

채우는 규칙: 모든 숫자는 기억이 아니라 원장에서 읽습니다. `- [~]` 행마다 공백을 붙여 이름을 밝힙니다. 빈 줄로 두지 말고 `none`이라고 씁니다. CI 수리 상한 때문에 PR이 멈췄으면 `CI: failing`을 반드시 적고, PR URL을 `Pull requests:` 줄에 남깁니다. maker-checker를 쓸 수 없었으면 결정적 검사에 기대는 행을 밝히는 줄을 추가합니다.

## 재개 점검 목록

1. 계획, `state.json`, `ledger.jsonl` 순서로 읽습니다. 상태를 대화에서 읽지 않습니다.
2. 모든 경로를 `main_root` 기준으로 풀고, `slug`, `plan_path`, `integration_base`, `wave_bases`가 디스크의 계획과 브랜치에 맞는지 확인합니다.
3. 열린 행마다 시도 횟수와 `checkpoint_opened_at`을 원장에서 다시 계산합니다.
4. `git worktree list --porcelain`을 실행해 `worktree_path`와 비교합니다.
5. `checkpoint_opened_at`이 있는 모든 행의 4시간 경계를 확인하고, 지난 행은 `[~]`로 닫습니다.
6. `evidence/` 아래 어떤 근거 파일이 있는지 확인하고, 열 수 없는 아티팩트를 다시 주장하지 않습니다.
7. 무엇을 읽었고 어디서 이어가는지 `resume` 이벤트로 덧붙입니다.
8. 계속할지 묻지 않고 상태가 가리키는 단계에서 진행합니다.

## Sources

> 확인 2026-11-03.

| Claim | Source |
|---|---|
| 원장과 상태의 분리, 행별 시도와 체크포인트 필드, 완료 블록 내용은 `ulw-execute` 스킬을 각색한 것 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| 권위 있는 계획과 진행 상황을 컨텍스트 밖에 두고 압축 뒤에 다시 읽는다 | `instructions/context-engineering/CONTEXT_ENGINEERING.md` |
| 근거 파일이 없으면 일어나지 않은 일이다 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| 모든 종료 조건에 숫자 상한을 둔다 | `instructions/loop-engineering/LOOP_ENGINEERING.md` |

### 근거 등급

`LOCAL` - 이 파일은 이 패키지의 파일 형식을 정의합니다. 모든 원장 줄이 같은 필드 집합을 갖는 것은 이 패키지의 선택이며, 이벤트 종류별로 필드를 달리 두지 않고 하나의 필터로 읽히게 하려는 것입니다. 원본 원장은 이벤트별 부분 필드를 썼습니다.
