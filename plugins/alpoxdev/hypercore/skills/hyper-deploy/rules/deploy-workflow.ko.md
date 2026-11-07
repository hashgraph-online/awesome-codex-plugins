# 배포 워크플로

대상이 정해진 뒤 이 규칙을 사용합니다. 모드 선택, 모드별 단계, 진단 순서, 보고서 경로를 소유합니다. 승인 등급은 `rules/safety-gates.md`에, 준비 스크립트는 `rules/preflight.md`에, 완료 근거는 `rules/validation.md`에 있습니다.

## 1. Pick The Mode

요청한 결과물에서 고르고, 저장소 파일로 확인합니다.

| 요청한 결과물 | 모드 | 허용하는 수정 |
|---|---|---|
| 준비 판정, 또는 그것을 막는 방해 요소의 수리 | `preflight` | 재현된 lint, 타입 검사, 빌드 실패에 묶인 파일 |
| 같은 판정에 "validate only", "고치지 말고", "do not edit"가 붙음 | `preflight` 검증 전용 | 보고서만 |
| 배포 설정이 없고 첫 배포를 원함 | `setup` | 새 설정 파일: `Dockerfile`, `.dockerignore`, compose 파일, 플랫폼 설정, 상태 엔드포인트 배선 |
| 이미 있는 설정을 이름이 지정된 환경에 배포 | `deploy` | 없음. 준비 단계가 방해 요소를 고칠 때만 예외 |
| 이미 있는 배포의 설정 변경 | `change` | 요청이 지목한 설정 파일이나 플랫폼 설정 |
| 실패했거나 죽거나 비정상이거나 잘못 동작하는 배포 | `diagnose` | 근본 원인이 가리키는 파일이나 설정 |

요청이 결과물을 섞으면("설정하고 staging에 배포해줘") 이 순서로 모드를 돌리고 멈추는 첫 모드에서 멈춥니다. `preflight`, `setup` 또는 `change`, `deploy`입니다. 이번 실행의 배포가 실패하면 `diagnose`가 이어받습니다.

## 2. Identify Before Writing

플랫폼, 서버, 레지스트리에 쓰는 첫 명령 전에:

1. 대상 정체를 밝힙니다. 프로젝트, 환경, 서비스 ID나 이름, Worker 이름과 환경, 이미지 저장소와 태그, 또는 호스트와 Compose 프로젝트입니다.
2. 환경과 그것이 운영인지 밝힙니다. 환경을 밝히지 않은 요청은 대상에 비운영 환경이 있으면 그쪽에 배포합니다. 유일한 환경이 운영이면 먼저 질문 하나를 합니다.
3. 가이드가 지목한 자격 증명 변수가 설정됐는지 값을 출력하지 않고 확인합니다. 없으면 멈추고 변수 이름을 밝힙니다.
4. 실행이 쓸 정확한 하위 명령과 플래그를 CLI의 `--help`에서 읽고 CLI 버전을 기록합니다.

연결된 디렉터리, 기본 환경, CLI 프롬프트에 대한 답은 정체가 아닙니다. 밝힌 뒤 행동합니다.

## 3. Mode Phases

### `preflight`

`rules/preflight.md`를 따릅니다. 스택 감지, 전체 기준선 실행, 트리아지, 좁은 수리, 새 전체 증명 실행입니다. 통과한 실행은 준비 판정이고 배포 승인이 아닙니다.

### `setup`

1. 가이드의 정본 설정 절을 읽고, 가이드가 현재로 표시한 형식을 씁니다. 폐기된 형식은 쓰지 않습니다.
2. 앱이 빌드되고 시작되는 가장 작은 설정을 씁니다. 빌드와 시작 명령, 대상이 포트로 라우팅할 때 듣는 주소 `0.0.0.0`과 플랫폼의 포트 변수, 대상이 상태를 점검할 때 상태 엔드포인트입니다.
3. 가이드가 검증기를 지목하면 로컬에서 검증합니다(`docker compose config -q`, `wrangler deploy --dry-run`, `railway config plan`).
4. 비운영 환경에 한 번 배포하고 아래 `deploy` 2-4단계를 돌립니다.

### `deploy`

1. 저장소가 지원 스택을 가지면 준비 단계를 돌립니다(`rules/preflight.md`). 실패한 증명은 배포를 멈춥니다.
2. 2절의 정체를 명시적으로 넘겨 가이드의 배포 명령을 돌립니다.
3. 명령이 돌려준 배포 ID나 버전을 기록합니다.
4. 그 ID로 가이드의 상태 명령을 가이드의 제한 시간 안에서 종료 상태에 닿을 때까지 폴링합니다. 그다음 상태 점검을 돌립니다.

### `change`

1. 가이드의 읽기 명령으로 현재 설정을 읽고 기록합니다.
2. 계획한 변경을 diff, plan 출력, 전후 값으로 보여 줍니다. 플랫폼이 즉시 적용하는 변경(예: 배포를 만드는 Cloudflare secret)은 배포로 다룹니다.
3. 적용하고, 플랫폼이 필요로 하면 재배포하고, `deploy` 3-4단계를 돌립니다.

### `diagnose`

1. 이 순서로 읽고 원인이 보이면 좁히기를 멈춥니다.
   1. 지금 무엇이 서비스 중인가: 활성 배포나 버전과 그 상태
   2. 실패한 배포의 빌드 로그
   3. 실패한 배포의 배포 로그와 런타임 로그
   4. 런타임 상태와 상태 점검: 종료 코드, 재시작 횟수, 상태 프로브 출력, 메모리
   5. 프록시, 네트워크, DNS, TLS 경로
   6. 네트워크나 컨테이너 안에서 보내는 내부 요청
2. 근거를 가이드의 실패 표와 맞춥니다. 증상, 로그나 상태 줄, 원인, 수리를 기록합니다.
3. 원인을 그것이 가리키는 파일이나 설정에서 고칩니다. 롤백보다 수리와 재배포를 먼저 봅니다. 실패한 배포는 보통 이전 버전을 서비스 중으로 남깁니다.
4. 재배포하고 같은 신호를 전후로 비교합니다. 실패를 보여 준 신호가 이제 성공을 보여 주고 배포가 종료 상태에 닿아야 수리가 증명됩니다.
5. 같은 근본 원인에 재배포 한 번을 시도 하나로 셉니다. 세 번이 되면 `exhausted`로 멈추고 시도한 것과 다음에 모을 근거를 보고합니다.

롤백은 사용자가 이번 실행에서 승인하지 않으면 실행하지 않고 제안합니다(`rules/safety-gates.md`).

## 4. Common Failure Signatures

대상 가이드마다 자체 표를 갖습니다. 아래 신호는 대상 전반에 반복되므로 먼저 확인합니다.

| Signature | Usual cause | Check |
|---|---|---|
| Connection refused, 502, "failed to respond", 상태 점검 불가 | 앱이 `127.0.0.1`이나 다른 포트에서 듣고 있음 | 시작 명령과 플랫폼이 설정하는 포트 변수 |
| 상태 점검 시간 초과 | 느린 시작, 잘못된 경로, 이미지에 프로브 도구 없음 | 시작 로그 시각, 상태 경로, 이미지의 `curl`이나 `wget` |
| 종료 코드 137 또는 "Killed process" | 메모리 부족, 또는 시간 초과 뒤 강제 종료 | 메모리 지표와 정지 제한 시간 |
| `exec format error`, "no matching manifest" | CPU 아키텍처가 다른 이미지 | 이미지의 플랫폼과 호스트 아키텍처 |
| 런타임에 변수가 빈 값으로 읽힘 | 빌드 시점에만 설정, 다른 환경에 설정, 단계적 변경 뒤 재배포 안 함 | 이 환경의 플랫폼 변수 목록 |
| 배포가 "성공"했는데 아무것도 바뀌지 않음 | 명령이 다른 프로젝트·환경·서비스에 닿음, 또는 빌드가 건너뛰어짐 | 배포 ID의 정체와 상태 |

## 5. Report Path

`references/report-template.md`로 `.hyper/deploy/<slug>/report.md`를 씁니다. `<slug>`는 실행을 나타내는 짧은 케밥 케이스 이름이고, 그 폴더가 다른 실행의 것이면 `-2`, `-3`을 붙입니다. `preflight`는 `rules/preflight.md`가 요구할 때 `.hyper/deploy/<slug>/flow.json`에 추적 상태도 둡니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 분리된 Railway 업로드는 배포가 대기 상태라는 것만 확인하며, 성공은 배포의 `SUCCESS` 상태입니다 | <https://github.com/railwayapp/railway-skills> |
| 소스 빌드가 실패하면 현재 애플리케이션 버전이 계속 실행됩니다 | <https://coolify.io/docs/core/build-deployment-model> |
| `wrangler secret put`이 새 버전을 만들고 배포합니다 | <https://developers.cloudflare.com/workers/configuration/secrets/> |
| 앱은 `0.0.0.0`과 주입된 `PORT`에 바인드해야 합니다 | <https://docs.railway.com/networking/troubleshooting/application-failed-to-respond> |
| 종료 코드 137은 SIGKILL을 뜻합니다 | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| arm64 호스트는 에뮬레이션 없이 amd64 이미지를 돌릴 수 없습니다 | <https://docs.docker.com/build/building/multi-platform/> |

### Evidence grade

`LOCAL` - 모드 순서, 진단 순서, 세 번 시도 한도는 이 패키지의 설계입니다. 신호 표는 2026-11-07에 읽은 인용 플랫폼 문서에서 각색했습니다.
