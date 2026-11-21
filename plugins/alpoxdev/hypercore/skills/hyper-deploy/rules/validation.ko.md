# 검증

실행을 완료로 선언하기 전에 이 체크리스트를 사용합니다. 모드마다 필요한 완료 근거, 종료 상태 규칙, 보고서 점검을 소유합니다.

## 1. The Terminal-State Rule

이번 실행이 만든 배포가 아래를 모두 만족할 때만 성공입니다.

1. 플랫폼이 그 배포 ID나 버전에 종료 성공 상태를 보고합니다(Railway의 `SUCCESS`, Containers를 쓸 때 모든 컨테이너 인스턴스가 새 버전인 Cloudflare의 활성 버전, Compose의 `healthy`, 완료된 Kamal 배포).
2. 대상 가이드가 지목한 상태 점검이 성공을 돌려줍니다. 대상에 그런 점검이 있을 때입니다.
3. 그 배포의 런타임 로그가 활성화된 뒤 제한된 구간에서 치명적 오류를 보이지 않습니다.

업로드, 대기하거나 시작된 빌드, 시작된 롤아웃, CLI 종료 코드 `0`, 상태 점검이 없는 서비스에서 돌아온 `--wait`는 성공이 아닙니다. `SKIPPED`, `NEEDS_APPROVAL`, `SLEEPING`, `REMOVED`, 알 수 없는 상태는 그 상태로 보고합니다.

## 2. Completion Evidence By Mode

| Mode | Claim | Required evidence |
|---|---|---|
| `preflight` | "준비됨" | 마지막 수정 뒤 새로 돌린 전체 `deploy-check.sh`가 종료 코드 `0`, `executed`가 0보다 크고, 건너뛴 게이트를 모두 밝힘 |
| `preflight` 검증 전용 | "방해 요소 보고함" | 전체 실행 결과와 방해 요소 목록. 보고서 밖에 고친 파일 없음 |
| `setup` | "배포 설정됨" | 새 설정 파일, 가이드가 지목할 때의 로컬 검증기 출력, 1절을 만족하는 비운영 배포 |
| `deploy` | "배포됨" | 명령 전에 밝힌 대상 정체, 배포 ID, 그리고 1절 |
| `change` | "변경됨" | 변경 전 값, 계획한 diff나 plan 출력, 변경 후 값, 재배포에 대한 1절 |
| `diagnose` | "고침" | 변경 전 증상 줄, 원인, 변경, 변경 후 같은 신호, 재배포에 대한 1절 |
| `diagnose` | "한도 소진" | 같은 근본 원인에 세 번 시도, 각각의 변경과 결과, 다음에 모을 근거 |
| 모든 모드 | "승인을 기다려 멈춤" | 정확한 명령, 바뀌는 것, 되돌릴 수 없는 것, 그 뒤의 근거(`rules/safety-gates.md` §4) |
| 모든 모드 | "해당 없음" | 대상 루트, 읽은 파일, 요청이 속한 결과물 형태 |

## 3. Report Check

- [ ] `.hyper/deploy/<slug>/report.md`가 있고 `references/report-template.md`를 따릅니다.
- [ ] 보고서의 모든 명령이 이번 세션에서 실행됐거나, 사유와 함께 `not run`으로 표시됐습니다.
- [ ] 모든 로그 발췌가 범위가 제한되고 가려졌으며, 가림을 밝혔습니다.
- [ ] 모든 롤백 제안이 데이터베이스, 볼륨, 연결된 리소스는 복구되지 않는다고 밝힙니다.
- [ ] 건너뛴 게이트, 없는 CLI, 없는 자격 증명이 통과한 점검과 따로 적혔습니다.
- [ ] 마지막 상태 줄이 모드의 종료 결과를 밝힙니다. `ready`, `unproven`, `deployed`, `changed`, `fixed`, `exhausted`, `stopped-for-approval`, `blocked`, `handoff`입니다.

## 4. Repair Bound

게이트가 실패하면 실행을 실패한 단계로 되돌리되 모드의 한도 안에서만 합니다(`SKILL.md`, loop policy). 실행됐다가 실패한 점검은 나중 실행이 통과해도 보고서에 보이게 남깁니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 그 배포의 `SUCCESS`를 관측하지 않고 배포를 성공으로 보고하지 않습니다 | <https://github.com/railwayapp/railway-skills> |
| 배포 성공은 롤아웃이 시작됐다는 뜻이고, 모든 컨테이너 인스턴스가 교체됐다는 뜻이 아닙니다 | <https://developers.cloudflare.com/containers/configuration/rollouts/> |
| `--wait`는 서비스가 실행 중이거나 정상이 될 때까지 기다리고, 상태 점검이 없으면 실행 중만 관측합니다 | <https://docs.docker.com/reference/cli/docker/compose/up/> |
| 완료 사슬과 검증 깊이 | `instructions/validation/index.md` |

### Evidence grade

`LOCAL` - 상태 목록과 근거 표는 인용한 플랫폼 문서 위에서 이 패키지가 고른 설계입니다.
