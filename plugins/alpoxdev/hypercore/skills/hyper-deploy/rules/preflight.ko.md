# 배포 전 점검

`preflight` 모드와 `deploy`의 준비 단계에서 이 규칙을 사용합니다. 번들 준비 스크립트, 그 결과를 읽는 방식, 트리아지, 복잡한 수리의 추적 상태, 위임 레인을 소유합니다. 통과한 준비 실행은 판정이고 배포 승인이 아닙니다.

## 1. Scripts

대상 루트에서 실행합니다. 대상이 하위 디렉터리면 경로를 맞추거나 절대 경로를 씁니다.

| Script | Purpose |
|---|---|
| `bash skills/hyper-deploy/scripts/stack-detect.sh` | 감지한 스택(`node`, `rust`, `python`)을 출력하고, 지원 스택이 없으면 `1`로 끝납니다 |
| `bash skills/hyper-deploy/scripts/deploy-check.sh [--parallel\|--sequential]` | 전체 증명: 품질 점검에 빌드를 더하고, 기본은 동시 실행입니다 |
| `bash skills/hyper-deploy/scripts/lint-check.sh` | 스택별 품질 점검 |
| `bash skills/hyper-deploy/scripts/build-run.sh` | 스택별 빌드 단계 |
| `bash skills/hyper-deploy/scripts/pm-detect.sh` | Node 패키지 매니저 감지(`npm`/`yarn`/`pnpm`/`bun`) |

결과 읽기:

- `deploy-check.sh`는 실행한 점검이 모두 통과하면 `0`, 하나라도 실패하면 `1`, 아무것도 실행하지 않았으면 `2`, 사용법 오류면 `64`로 끝납니다.
- 종료 코드 `2`는 통과가 아니라 실패한 판정입니다. 아무것도 설정되거나 설치되지 않았으므로 준비됐음이 증명되지 않습니다.
- 모든 실행은 `PRE_DEPLOY_SUMMARY executed=<n> skipped=<m>`을 출력합니다. 보고서에 그 줄을 인용합니다. 그것이 적용 범위 주장입니다.
- 건너뛴 게이트는 "설정되지 않음"이나 "도구 설치 안 됨"을 뜻합니다. 통과로 세지 않습니다.
- Node 점검은 프로젝트 자체 스크립트를 쓰고, 그다음 프로젝트 로컬 `node_modules/.bin` 바이너리를 씁니다. 없는 도구는 건너뛰기이고 암묵적 `npx` 설치가 아닙니다.
- `cargo fmt`에는 `rustfmt`가 필요하고, 없으면 형식 게이트를 건너뜁니다. Clippy는 Cargo 1.97 이상에서 `CARGO_BUILD_WARNINGS=deny`로, 이전 도구 체인에서는 `-- -D warnings`로 경고를 거부합니다.
- Python 게이트는 선택 사항입니다. `ruff`나 `flake8`, 그다음 `mypy`나 `compileall` 대체입니다.
- `lint-check.sh`가 이미 Node 타입 검사와 린트를 동시에 돌리므로 그 둘에 레인을 나누지 않습니다.
- 동시 도구 체인이 메모리나 CPU나 공유 빌드 캐시를 다툴 때는 `--sequential`이나 `PRE_DEPLOY_MODE=sequential`을 씁니다.

## 2. Phases

| Phase | Action | Required evidence |
|---|---|---|
| Scope | 대상 루트를 확인하고, 요청을 검증 전용인지 수리 가능인지 읽고, `stack-detect.sh`를 돌립니다 | 감지한 스택, 또는 지원하지 않는 스택 정지 |
| Baseline | 수정 전에 전체 `deploy-check.sh`를 한 번 돌립니다 | 종료 코드, 요약 줄, 정확한 실패 출력 |
| Triage | 실패를 스택, 명령, 우선순위로 묶고 형태를 고릅니다(3절) | 담당과 근거가 붙은 실패 그룹 |
| Fix | 재현된 실패가 요구하는 것만 바꾸고 가장 좁은 명령을 다시 돌립니다 | 변경 범위와 재실행 출력 |
| Prove | 마지막 수정 뒤 리더 문맥에서 전체 `deploy-check.sh`를 다시 돌립니다 | `executed`가 0보다 크고 종료 코드 `0` |

실패가 뻔해 보인다고 기준선을 건너뛰지 않고, 좁은 재실행의 통과를 판정으로 다루지 않습니다. 검증 전용 모드에서는 기준선 뒤에 멈추고 보고합니다.

## 3. Triage Shapes

확신이 없으면 위쪽으로 분류합니다.

| Shape | Signals | Path |
|---|---|---|
| 단순 | 스택 하나, 실패 명령 하나, 담당이 분명함 | 바로 수리하고 상태 파일을 두지 않습니다 |
| 중간 | 한 스택의 실패 여러 개, 하나씩 고칠 수 있음 | 추적 상태를 두고 바로 수리합니다(4절) |
| 복잡 | 여러 스택, 공유 설정, 빌드 그래프, 또는 알 수 없는 수리 전략 | 추적 상태 |
| 레인 | 스택이나 파일로 실패가 서로 겹치지 않고 각자 성공 조건이 있음 | 추적 상태와 레인(5절), 최대 셋 |

앞선 단계가 실패해서 생긴 오류를 쫓기 전에 첫 근본 실패를 먼저 고칩니다.

## 4. Tracked State

중간, 복잡, 레인 형태에서는 `.hyper/deploy/<slug>/flow.json`을 두고 단계가 바뀔 때마다 갱신합니다.

```json
{
  "version": 1,
  "target_root": ".",
  "current_phase": "baseline",
  "stacks": ["node"],
  "max_fix_attempts": 3,
  "phase_history": [{ "phase": "detect", "status": "complete", "evidence": "stack-detect.sh output", "updated_at": "ISO-8601" }],
  "baseline": { "command": "bash skills/hyper-deploy/scripts/deploy-check.sh", "exit_code": 1, "summary": "PRE_DEPLOY_SUMMARY executed=2 skipped=1" },
  "failure_groups": [{ "id": "node-typecheck", "stack": "node", "command": "npm run typecheck", "priority": 1, "owner": "leader", "status": "open", "attempts": 0, "evidence": "exact failure excerpt" }],
  "fixes": [],
  "validation_history": [],
  "verdict": null
}
```

- 대상 점검을 돌리기 전에 `attempts`를 올립니다. 중단된 실행이 시도를 숨기지 못하게 합니다. 재개해도 초기화하지 않습니다.
- 같은 근본 원인으로 `max_fix_attempts`에 닿으면 그 그룹을 `exhausted`로 두고 `done`이 아니라 `exhausted`로 보고합니다. 새 근본 원인은 새 그룹입니다.
- 검사자는 대상 명령이나 `deploy-check.sh`이고, 에이전트가 자기 diff를 읽는 것은 아닙니다.
- 재개할 때 파일을 먼저 읽고 가장 이른 미완 단계에서 이어 갑니다. 대상 루트, 스택 집합, 패키지 매니저, 검증 명령이 바뀌었을 때만 기준선으로 되돌립니다.
- `verdict`는 `ready`, `unproven`, `exhausted`, `handoff` 중 하나로 끝납니다.

## 5. Lanes

실패가 스택이나 파일로 독립적이고 위임 기능이 있을 때만 위임합니다. 아니면 같은 일을 순차로 합니다.

두 레인이 같은 파일, 잠금 파일, manifest, 빌드 설정, CI나 배포 설정을 만질 때, 또는 리더의 다음 단계가 그 결과에 막혀 있을 때는 나누지 않습니다.

모든 레인 프롬프트는 목표, 범위(스택, 명령, 파일, 대상 루트), 소유(읽기 전용 또는 정확한 쓰기 가능 파일), 금지 행동(파괴적 명령, 외부 부수 효과, 무관한 정리, 소유 밖 수정), 출력(파일, 명령 출력, 결과, 방해 요소), 정지 조건을 담습니다. 레인마다 자기 그룹의 시도 한도를 물려받습니다.

레인이 돌아오면 리더가 바뀐 파일을 모두 살피고 마지막 전체 `deploy-check.sh`를 직접 돌립니다. 준비됐음은 절대 위임하지 않습니다.

## 6. Forbidden

- 점검을 약화시켜 통과시키는 일. `|| true`, `continue-on-error`, 린트 수준 낮추기, 단언 삭제, 번들 스크립트 수정입니다.
- 명시적 승인 없이 의존성을 설치하거나 올리거나 잠금 파일이나 manifest를 바꾸는 일. 프로젝트 자체 빌드가 의존성을 받는 것은 예상된 일이고, 없는 도구를 설치로 바꾸는 것은 아닙니다.
- 코드 리뷰, 좁은 재실행, 레인의 서술, 마지막 수정보다 오래된 실행으로 준비됐음을 주장하는 일.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 스크립트, 종료 코드, 요약 줄, 트리아지 형태, 추적 상태, 레인 계약은 이 저장소의 이전 독립 준비 점검 패키지(마지막 존재 커밋 `3b8576d`)에서 가져왔습니다 | user instruction, 2026-11-07; repository history |
| 실패 그룹은 선언한 시도 한도에서 멈추고 `exhausted`로 보고합니다 | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| 검사자는 행위자와 분리되며, 건너뛴 점검은 통과가 아닙니다 | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| Cargo 1.97 이상의 Clippy 경고 거부 설정 | <https://doc.rust-lang.org/clippy/usage.html> |

### Evidence grade

`LOCAL` - 이 규칙은 이 패키지 자체의 준비 워크플로를 다시 적은 것입니다. 시도 한도와 레인 상한은 이 패키지가 고른 값입니다.
