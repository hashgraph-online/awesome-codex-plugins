# 상태 스키마

네 상태 파일과 검증기 출력의 정확한 JSON 모양이다. 상태 파일을 쓰는 동안 읽는다.

## 목차

1. `goals.json`
2. `ledger.jsonl` 행
3. `final-gate.json`
4. 검증기 명령, 출력, 종료 코드

## 1. `goals.json`

```json
{
  "schema_version": 1,
  "run_id": "orders-refactor-2026-11-09",
  "objective": "주문 모듈을 의존하는 네 목표로 나눠 모두 끝낸다",
  "status": "active",
  "current_goal_id": "G1",
  "goals": [
    {
      "id": "G1",
      "title": "주문 가격 계산을 한 모듈로 옮긴다",
      "objective": "모든 가격 호출 지점이 새 모듈을 쓰고 옛 경로가 없다",
      "status": "in_progress",
      "depends_on": [],
      "surfaces": ["cli", "http"],
      "attempt": 0,
      "cycles": 1,
      "criteria": [
        {
          "id": "C1",
          "scenario": "깨끗한 작업 트리에서 `npm test -- orders`를 실행한다",
          "pass_condition": "명령이 종료 코드 0으로 끝난다",
          "expected_evidence": ".hyper/loop/orders-refactor-2026-11-09/evidence/g1-c1.log",
          "essential": true,
          "cleanup": "만든 자원 없음",
          "adversarial_classes": [
            {"name": "빈 장바구니", "status": "pass", "evidence": "evidence/g1-c1.log:12"}
          ],
          "status": "pass"
        }
      ]
    }
  ]
}
```

| 수준 | 필드 | 타입 | 비고 |
|---|---|---|---|
| 루트 | `schema_version` | 숫자 | `1` |
| 루트 | `run_id` | 문자열 | 재개해도 유지한다. `brief.md`에도 적는다 |
| 루트 | `objective` | 문자열 | 묶어 둔 결과 |
| 루트 | `status` | 문자열 | `active`, `paused`, `blocked`, `failed`, `complete`, `cancelled` |
| 루트 | `current_goal_id` | 문자열 또는 null | 재개 규칙이 고른 목표 |
| 목표 | `id`, `title`, `objective` | 문자열 | `id`는 실행 전체에서 고유하다 |
| 목표 | `status` | 문자열 | `pending`, `in_progress`, `complete`, `failed`, `blocked`, `cancelled` |
| 목표 | `depends_on` | 문자열 배열 | 존재하는 id, 순환 없음 |
| 목표 | `criteria` | 배열 | 최소 하나 |
| 목표 | `surfaces` | 문자열 배열 | 선택. 게이트의 표면 검사를 이끈다 |
| 목표 | `attempt`, `cycles` | 숫자 | 실패 한도용 계수 |
| 기준 | `id` | 문자열 | 목표 안에서 고유하다 |
| 기준 | `scenario` | 문자열 | 무엇을 어떤 입력과 환경에서 실행하는지 |
| 기준 | `pass_condition` | 문자열 | 이분형 문장 하나 |
| 기준 | `expected_evidence` | 문자열 | 경로. 비어 있지 않은 파일로 해석돼야 통과한다 |
| 기준 | `essential` | 불리언 | 필수. 없으면 `true`로 읽는다 |
| 기준 | `cleanup` | 문자열 | 이 기준이 책임지는 정리 |
| 기준 | `adversarial_classes` | 배열 | 선택. `pass`에는 증거, `not_applicable`에는 이유가 필요하다 |
| 기준 | `status` | 문자열 | `pending`, `in_progress`, `pass`, `fail`, `blocked`, `cancelled` |

## 2. `ledger.jsonl` 행

한 줄에 JSON 객체 하나. 덧붙이기만 하고 편집하지 않는다. `event` 필드가 행 종류를 고른다.

증거 행:

```json
{"event":"evidence","goal_id":"G1","criterion_id":"C1","verdict":"pass",
 "tree":"4f0c…","diff_sha256":"9ab1…","command":"npm test -- orders",
 "evidence":"종료 코드 0, 테스트 42개 통과","artifacts":["evidence/g1-c1.log"],
 "rationale":"기준의 시나리오가 정확히 이 명령이다"}
```

체크포인트 행:

```json
{"event":"checkpoint","goal_id":"G1","tree":"4f0c…","diff_sha256":"9ab1…",
 "criteria":["C1","C2"],"rationale":"핵심 기준 모두 신선하고 의존이 완료됐다"}
```

조향 행:

```json
{"event":"steering","verb":"revise_criterion","decision":"accepted",
 "goal_id":"G2","criterion_id":"C3","evidence":"…","rationale":"…"}
```

실패 행:

```json
{"event":"failure","goal_id":"G2","signature":"npm test -- billing :: AssertionError: total",
 "attempts":3,"cycles":2,"rationale":"같은 서명으로 세 번 실패"}
```

`verdict`는 `pass`, `fail`, `blocked` 중 하나다. `event`가 없는 행은 증거 행으로 읽는다.

## 3. `final-gate.json`

```json
{
  "status": "complete",
  "tree": "4f0c…",
  "diff_sha256": "9ab1…",
  "surfaceEvidence": [
    {"criterionRef": "G1:C1", "surface": "cli", "invocation": "npm test -- orders",
     "verdict": "passed", "artifactRefs": ["evidence/g1-c1.log"]},
    {"criterionRef": "G2:C1", "surface": "http", "invocation": "curl -s localhost:3000/orders",
     "verdict": "passed", "artifactRefs": ["evidence/g2-c1.txt"]}
  ],
  "criteriaCoverage": {
    "totalCriteria": 2,
    "passCount": 2,
    "originalIntent": "주문 모듈을 나누고 모든 목표를 끝낸다",
    "desiredOutcome": "가격 모듈 하나, 옛 경로 없음, 테스트 통과",
    "userOutcomeReview": "기준마다 신선한 캡처가 있고 표면을 실제로 건드렸다"
  },
  "review": {"by": "deterministic", "recommendation": "approve",
             "evidence": "bash <skill-dir>/scripts/verify-loop-state.sh --final … 이 종료 코드 0"},
  "blockers": []
}
```

| 필드 | 계약 |
|---|---|
| `status` | `complete`, `blocked`, `paused`. `complete`만 통과한다 |
| `tree`, `diff_sha256` | 마지막 변경 뒤에 뜬 스냅샷과 같아야 한다 |
| `surfaceEvidence[].criterionRef` | `<goal-id>:<criterion-id>`. 기준 id만 쓰는 것은 다른 목표가 같은 id를 쓰지 않을 때만 인정된다. 아니면 행 하나가 여러 기준을 덮어 버린다 |
| `surfaceEvidence[].verdict` | 통과 행은 `passed` |
| `surfaceEvidence[].surface` | 선언한 표면과 일치한다. 예: `cli`, `http`, `browser`, `data` |
| `criteriaCoverage` | 개수에는 `essential: false` 기준도 포함한다 |
| 덮임 규칙 | 기준마다 통과 `surfaceEvidence` 행이 하나 필요하고, `goals.json`에 선언한 표면마다 그 표면의 통과 행이 최소 하나 더 필요하다 |
| `review` | 독립 리뷰어가 없었을 때만 `deterministic` |
| `blockers` | `complete`에서만 빈 배열 |

## 4. 검증기 명령, 출력, 종료 코드

```bash
bash <skill-dir>/scripts/verify-loop-state.sh snapshot [--dir <loop-dir>] [--repo <path>] [--limit <n>]
bash <skill-dir>/scripts/verify-loop-state.sh --goal <goal-id> --dir <loop-dir> [--repo <path>]
bash <skill-dir>/scripts/verify-loop-state.sh --final <final-gate.json> [--dir <loop-dir>] [--repo <path>]
bash <skill-dir>/scripts/verify-loop-state.sh --self-test
bash <skill-dir>/scripts/verify-loop-state.sh --help
```

`--dir`는 `goals.json`과 `ledger.jsonl`이 있는 루프 디렉터리이며 지문에서 제외된다. `--repo`의 기본값은 `--dir`을 담은 작업 트리다. `--final`에서 `--dir`의 기본값은 게이트 파일의 디렉터리다. `--limit`은 `snapshot` 출력에 나열할 미추적 항목 수를 제한하며 기본값은 200이다.

| 모드 | 출력 | 종료 0 | 종료 1 | 종료 2 |
|---|---|---|---|---|
| `snapshot` | `status`, `tree`, `diff_sha256`, `untracked[]`, `excluded` | 지문 계산됨 | — | 저장소 아님, git 실패 |
| `--goal` | 기준별 `state`(`pass`, `stale`, `failing`, `missing`, `missing-evidence-file`), `essential_fresh`, `summary` | 핵심 기준이 모두 신선함 | 핵심 기준 하나가 신선하지 않음 | 목표 없음, `goals.json` 없음·잘못됨, `--dir` 없음 |
| `--final` | 기준별 `evidence`와 `surface`, `surfaces[]`, `snapshot_bound`, `gate_status` | 완전한 게이트, 모든 기준 신선, 모든 표면 덮임, 스냅샷에 묶임 | 그중 하나가 실패 | 게이트 파일 없음·잘못됨, 알 수 없는 `status` |
| `--self-test` | `{"ok":true,…}`와 실행한 검사 | 자기 시험 사례가 모두 기대대로 동작 | 자기 시험 사례 하나가 어긋남 | git 없음, 임시 디렉터리 불가 |

오류는 `{"status":"error","code":"<CODE>","message":"<text>"}` 객체 하나를 출력하고 종료 코드 2로 끝난다.

## Sources

> 확인 2026-11-09.

아래 출처 경로는 원본 저장소의 스킬 루트(`skills` 디렉터리)를 기준으로 적었다.

| Claim | Source |
|---|---|
| 네 상태 파일과 기준 필드 이름 | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/omp-ledger.md` (메커니즘 참조, 재작성) |
| 게이트 필드 `surfaceEvidence`와 `criteriaCoverage` | `dbc-hbin/omp-ulw@74df40f ulw-loop/references/full-workflow.md` (메커니즘 참조, 재작성) |
| 명령 구성, JSON 출력, 종료 코드 | `skills/hyper-loop/scripts/verify-loop-state.sh`. `--self-test`로 확인했다 |
| 게이트 상태 어휘 `complete`, `blocked`, `paused` | 이 패키지의 실행 계약, 2026-11-09 |

### Evidence grade

`LOCAL` - 스키마는 실행 가능한 정의인 번들 스크립트와 일치한다. 자기 시험은 `pass`와 `stale` 상태, 그리고 덮이지 않은 기준을 게이트가 거부하는 것을 증명한다. 스크립트가 읽지 않는 필드는 사람 검토자를 위한 문서이며 스크립트가 강제하는 제약이 아니다.