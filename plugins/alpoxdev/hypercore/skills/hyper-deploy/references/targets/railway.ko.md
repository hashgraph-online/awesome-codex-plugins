# Railway

Railway 대상 가이드입니다. `rules/target-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. 신규 작업의 현행 작성 파일, 기존 저장소에 남아 있는 폐기 예정 설정 파일, 비대화형 배포와 검증 명령, 진단, 롤백이 되돌리지 않는 범위를 다룹니다.

## Contents

- Canonical Configuration
- Authentication
- Identify And Deploy
- Success Test
- Status And Logs
- Change Settings
- Rollback
- Failure Table
- Approval Required
- Checked
- Sources

## Canonical Configuration

신규 작업은 Infrastructure as Code를 씁니다. `.railway/railway.ts`(정식 출시) 하나가 정본이고 `.railway/railway.py`, `.railway/railway.go`는 베타입니다. 세 파일 중 하나만 두고 그 옆에 맞는 패키지를 설치합니다(TypeScript는 `npm install railway`, Python은 `pip install railway-sdk`, Go는 `go get github.com/railwayapp/railway-go-sdk@v0.3.0`). CLI는 현재 디렉터리에서 위로 올라가며 가장 가까운 작성 파일을 찾으므로 `--file`은 두 번째 파일이 있을 때만 필요합니다.

```ts
import { defineRailway, project, service } from "railway/iac";

export default defineRailway(() => {
  const web = service("web", {
    build: "pnpm build",
    start: "pnpm start",
    healthcheck: "/health",
    healthcheckTimeout: 60,
    env: { NODE_ENV: "production", STRIPE_SECRET_KEY: preserve() },
  });

  return project("my-app", { resources: [web] });
});
```

| 목적 | 작성 형식 |
|---|---|
| 빌드와 시작 | `build`, `start` |
| 헬스 게이트 | `healthcheck`(경로), `healthcheckTimeout`(초, 플랫폼 기본 300) |
| 빌드와 배포 사이 | `preDeploy`(명령 문자열 하나) |
| 확장 | `replicas: 3`, 또는 `{ "us-west2": 2 }` 같은 리전 맵 |
| 소스 | `source: github("owner/repo", { branch: "main" })`, 또는 `image("ghcr.io/acme/api:1.2.3", { autoUpdates: { type: "patch" } })` |
| 변수 | `env: { KEY: "value" }`, 서비스 간 `db.env.DATABASE_URL`, 공유 `ctx.shared.NAME` → `${{shared.NAME}}`, 기존 값 유지 `preserve()` |
| 스토리지 | `volume("data", { region, sizeMB })`와 `volumeMounts: { "/data": data }` |
| 환경별 상태 | `defineRailway((ctx) => …)`와 `ctx.environment`, `ctx.isEnvironment(name)` |

Config as Code(`railway.toml` / `railway.json`)는 폐기 예정입니다. 이미 쓰는 서비스는 **2026-12-01**까지 동작하고 그날 이후로는 읽지 않습니다(강제 종료). 신규 서비스는 선택할 수 없습니다. 한 서비스를 두 체계가 함께 관리할 수 없으므로 `railway config plan`은 먼저 마이그레이션해야 할 서비스를 지목하고 중단합니다. 이전은 `railway config migrate`(기본은 미리보기)로 계획하고 `--apply`로 파일을 씁니다. 기존 파일 삭제는 컷오버 뒤에 `--apply --delete-files`로 합니다. `railway config migrate cutover`가 서비스를 Config as Code에서 떼어 내고 `railway config migrate status`가 남은 서비스를 보여 줍니다. 새 `railway.toml`을 손으로 만들지 않습니다.

빌더: Railpack이 기본이고 Node, Python, Go, PHP, Java, Ruby, Deno, Rust, Elixir, 셸 스크립트, 정적 HTML을 설정 없이 빌드합니다. `Dockerfile`이 있으면 Dockerfile 빌드로 바뀌며 파일 이름은 대문자 D로 시작하는 `Dockerfile`이어야 합니다. 다른 이름이나 위치는 `RAILWAY_DOCKERFILE_PATH`로 지정합니다. Nixpacks는 상류에서 유지보수 모드이므로 이 가이드는 선택지로 제시하지 않습니다. Railpack 설정은 `RAILPACK_*` 서비스 변수나 자체 설정 파일로 합니다.

## Authentication

토큰은 두 종류이고 한 번에 하나만 설정합니다.

| 변수 | 범위 | 용도 |
|---|---|---|
| `RAILWAY_TOKEN` | 프로젝트 하나와 환경 하나 | 해당 환경의 배포, 재배포, 로그, 변수, `config apply` |
| `RAILWAY_API_TOKEN` | 계정과 워크스페이스 | 환경 생성·삭제, 여러 프로젝트 작업, MCP 서버 |

둘 다 설정하면 CLI가 오류로 끝납니다. MCP 서버는 과금과 감사에 사용자 신원이 필요해 프로젝트 토큰을 거부하므로 MCP로 진행하는 실행에는 `RAILWAY_API_TOKEN`이 필요합니다. 토큰을 명령줄 인자로 넘기지 않습니다. 셸 기록과 프로세스 목록에 남습니다.

```sh
[ -n "${RAILWAY_TOKEN:-}" ] && echo project-token-set
[ -n "${RAILWAY_API_TOKEN:-}" ] && echo account-token-set
railway whoami
```

존재 확인은 값을 출력하지 않습니다. `railway whoami`는 CLI가 어떤 신원으로 해석했는지 확인합니다. 인증되지 않은 호출은 어느 변수가 빠졌는지 알려 주지 않고 실패하므로 토큰 확인보다 먼저 실행하지 않습니다.

## Identify And Deploy

배포가 아니라 컨텍스트부터 확인합니다.

```sh
railway status --json
```

그다음 쓰기 명령마다 프로젝트, 환경, 서비스를 명시하고 링크된 디렉터리에 기대지 않습니다. `--project`에는 `--environment`가 필요하고, 서비스가 둘 이상이면 `--service`도 넘깁니다.

```sh
railway up --project <PROJECT_ID> --environment <ENV> --service <SERVICE> \
  --detach --json -m "<release summary>"
railway up --project <PROJECT_ID> --environment <ENV> --service <SERVICE> \
  --ci -m "<release summary>"
```

- `--detach`(별칭 `--no-wait`)는 업로드가 접수되고 빌드가 **큐에 들어간** 시점에 반환합니다. `--json`이면 `{"deploymentId": …, "logsUrl": …}`를 출력하므로 ID를 보관합니다.
- `--ci`는 빌드 로그만 스트리밍하고 배포 판정을 종료 코드로 냅니다. 인증된 배포에서 `--json`은 CI 동작을 포함합니다.
- CI 모드가 아니면 stdout이 터미널이 아닐 때도 업로드 직후 반환합니다. 에이전트 실행에서 `--detach`를 빼도 기다렸다는 뜻이 아니므로 어느 경우든 ID로 상태를 확인합니다.
- 링크가 없는 비대화형 실행은 프로젝트를 만들지 않고 `NOT_AUTHENTICATED`나 프로젝트 없음 오류로 끝납니다. 스크립트와 CI는 프로젝트를 암묵적으로 만들지 않으므로 프로젝트가 먼저 있어야 하고 이름을 지정해야 합니다.

`railway deploy`와 `railway down`은 코드 배포가 아니며 릴리스에 쓰지 않습니다. `railway deploy`는 템플릿을 프로젝트에 프로비저닝하고(`--template postgres`), `railway down`은 서비스에서 가장 최근 배포를 제거합니다. 코드는 `railway up`(또는 같은 동작인 `railway deployment up`)으로 나갑니다.

## Success Test

성공은 이번 실행의 `deploymentId`가 `SUCCESS`에 닿고, 런타임 로그 창이 조용하고, 서비스 URL이 2xx를 돌려줄 때입니다.

```sh
railway deployment list --project <PROJECT_ID> --environment <ENV> --service <SERVICE> \
  --limit 10 --json
railway logs <DEPLOYMENT_ID> --lines 100 --json
curl -sS -o /dev/null -w '%{http_code}\n' https://<domain>/health
```

- `railway up`이 돌려준 ID로 맞춥니다. "가장 최근 배포"로 판정하지 않습니다. 다른 소스가 동시에 낸 더 새로운 배포는 이번 결과가 아닙니다.
- `--ci`의 종료 코드 `0`만으로는 부족합니다. 변경 파일이 워치 패턴에 걸리지 않은 빌드는 `SKIPPED`로 끝나면서 `0`을 낼 수 있고, 분리 실행이나 비TTY 실행은 업로드만 하고 `0`을 낼 수 있습니다.
- 상태는 `QUEUED` → `INITIALIZING` → `BUILDING` → `DEPLOYING`(GitHub 검사 대기 시 `WAITING` 추가) → `SUCCESS`로 흐릅니다. `FAILED`, `CRASHED`, `SKIPPED`, `SLEEPING`, `NEEDS_APPROVAL`, `REMOVING`, `REMOVED`는 성공이 아닙니다. 상태를 그대로 보고하고 다음 동작을 밝힙니다. `NEEDS_APPROVAL`은 사람 승인을 기다리는 상태이므로 빌드 중인 것처럼 계속 조회하지 않습니다.
- 헬스 체크는 배포 시점의 일회성 게이트이고 지속 모니터링이 아닙니다. 볼륨을 붙인 서비스는 배포 하나만 볼륨을 잡을 수 있어 헬스 체크가 있어도 무중단이 되지 않습니다.

## Status And Logs

모든 로그 명령에는 상한이 필요합니다. `--lines`, `--since`, `--until`이 없으면 CLI가 중단될 때까지 스트리밍합니다.

| 질문 | 명령 |
|---|---|
| 현재 컨텍스트와 리소스 | `railway status --json`, `railway environment config --json` |
| 배포 이력과 상태 | `railway deployment list --limit 10 --json` |
| 빌드 로그 | `railway logs --build --lines 400 --json` |
| 특정 배포의 런타임 로그 | `railway logs <DEPLOYMENT_ID> --lines 200 --json` |
| 실패했더라도 최신 배포의 런타임 로그 | `railway logs --latest --lines 200 --json` |
| 오류만 | `railway logs <DEPLOYMENT_ID> --lines 200 --filter "@level:error" --json` |
| HTTP 실패 | `railway logs --http --status ">=400" --lines 100 --json` |
| 버려진 네트워크 흐름 | `railway logs --network --status dropped --lines 100 --json` |
| 실패한 DNS 조회 | `railway logs --dns --status failed --since 1h --lines 100 --json` |
| CPU, 메모리, 볼륨, HTTP 지표 | `railway metrics --since 1h --json`, `--memory`, `--http`, `--raw` |
| 도메인과 인증서 상태 | `railway domain list --json`, `railway domain status <domain> --json` |
| 변수 | `railway variable list --json`(값을 출력하므로 결과를 붙여 넣지 않습니다) |
| 크론 실행 | `railway cron list` |

`railway logs`는 HTTP, 네트워크, DNS 필터(`@httpStatus:>=500`, `@path:/api`, `@peer_kind:internet`, `@rcode:NXDOMAIN`)를 받고 한 번에 로그 종류 하나만 봅니다. 배포 로그는 기본이 가장 최근 성공 배포이므로 실패를 진단할 때는 ID를 넘깁니다.

## Change Settings

변수는 스테이징됩니다. 값을 설정하면 대기 변경이 쌓이고 다음 배포에서 서비스에 반영됩니다. `railway variable set`은 `--skip-deploys`가 없으면 그 배포를 일으킵니다.

```sh
railway variable set DATABASE_URL --service <SERVICE> --environment <ENV> --stdin
railway variable set LOG_LEVEL=debug --service <SERVICE> --environment <ENV> --skip-deploys
railway variable delete OLD_KEY --service <SERVICE> --environment <ENV>
```

- `--stdin`은 표준 입력에서 값을 읽으므로 비밀값이 인자 목록에 남지 않습니다. 명령줄의 `KEY=VALUE`는 비밀이 아닌 값에만 씁니다.
- `--skip-deploys`는 배포 없이 변경만 기록합니다. 배포가 돌기 전에는 값이 살아 있지 않습니다.
- `variable list --json`과 `-k/--kv`는 원시 값을 출력합니다. 필요할 때만 읽고 보고서에 옮기지 않습니다.
- 봉인 변수(sealed variable)는 쓸 수 있지만 값을 읽을 수 없습니다. 해제가 불가능하고, `railway variables`와 `railway run`이 값을 주지 않으며, PR 환경이나 환경·서비스 복제 시 복사되지 않고, 환경 비교에 나타나지 않고, 외부 통합과 동기화되지 않습니다. 그래서 복제한 환경에는 이 변수가 없고, 있다고 가정한 실행은 기동에서 실패합니다.

인프라 변경은 운영 설정을 직접 고치지 않고 계획과 적용을 거칩니다.

```sh
railway config plan --environment <ENV> --detailed-exit-code
railway config plan --out railway-plan.json
railway config apply --plan railway-plan.json --yes --confirm-destructive
```

- `plan`은 읽기만 합니다. 변수 값은 `--show-values`를 주지 않으면 `«hidden»`로 나옵니다.
- `--detailed-exit-code`는 변경이 대기 중이면 `2`, 없으면 `0`으로 끝나는 CI 드리프트 게이트입니다.
- 비대화형 파괴적 적용에는 `--yes`와 `--confirm-destructive`가 모두 필요합니다. `apply`는 항상 새 계획을 먼저 돌리고 환경 etag나 `.railway/` 트리가 계획과 달라졌으면 거부하므로 동시 변경 뒤에는 다시 계획합니다.
- `railway config pull --include-variables`는 봉인하지 않은 값과 봉인하지 않은 비밀을 `.railway/railway.ts`에 복호화해 넣습니다. 에이전트 흐름에서 실행하지 않고 가져온 값은 `preserve()`로 둡니다.

## Rollback

임의의 이전 배포로 되돌리는 동작은 대시보드에서만 합니다. CLI에는 롤백 하위 명령이 없습니다.

- 롤백은 그 배포의 Docker 이미지와 커스텀 변수를 함께 복원합니다. 그사이 바꾼 변수도 되돌아갑니다.
- 플랜의 이미지 보존 기간 안에서만 됩니다. Free와 Trial 24시간, Hobby 72시간, Pro 120시간, Enterprise 360시간입니다. 지나면 롤백 항목이 사라지고 재배포만 남습니다.
- 코드와 서비스 변수만 되돌립니다. 데이터베이스, 볼륨과 그 안의 데이터, 버킷, 서비스에 연결된 리소스는 복원되지 않고, 이미 실행한 스키마 마이그레이션도 그대로 남습니다.
- 제안하기 전에 보존 기간, 변수가 되돌아간다는 점, 데이터는 돌아오지 않는다는 점을 밝힙니다.

원인이 이미지가 아닐 때의 대안은 다음 순서로 고릅니다.

| 명령 | 재빌드 | 쓰는 때 |
|---|---|---|
| `railway redeploy --service <SERVICE> --yes` | 아니요, 같은 이미지 | 빌드는 정상이고 알려진 이미지로 컨테이너를 다시 띄울 때 |
| `railway redeploy --from-source --yes` | 예, 최신 커밋이나 이미지 | 오래된 코드가 원인일 때 |
| `railway redeploy --commit <SHA> --yes` | 예, 그 커밋 한 번 | 특정 커밋을 고정하지 않고 한 번 시험할 때 |
| `railway restart --service <SERVICE> --yes` | 아니요, 같은 컨테이너 | 런타임에서 프로세스가 멈췄을 때 |

`railway down`은 가장 최근 배포를 제거합니다. 롤백이 아니고 서비스를 이전 이미지로 되돌리지 않습니다.

## Failure Table

| # | 시그니처 | 원인 | 수정 | 확인 | 위험 | 출처 |
|---|---|---|---|---|---|---|
| 1 | `Application failed to respond`(502), 헬스 체크가 `service unavailable`이나 `status 400` 보고 | 앱이 `localhost`나 고정 포트에 바인드했거나 대상 포트와 수신 포트가 다름 | `0.0.0.0`에 바인드하고 `PORT`를 읽습니다. 도메인 대상 포트를 맞추거나 `PORT` 변수를 설정합니다 | `railway logs --http --status ">=400"`, 이어서 `curl -I https://<domain>/health`가 2xx | proceed | <https://docs.railway.com/networking/troubleshooting/application-failed-to-respond> |
| 2 | `No start command could be found` | Railpack이 시작 명령을 찾지 못함 | 작성 파일의 `start`나 서비스 설정의 시작 명령을 지정합니다(예: `uvicorn main:app --host 0.0.0.0 --port $PORT`) | 재배포가 `SUCCESS`이고 앱 로그에 수신 대기가 보임 | proceed | <https://docs.railway.com/deployments/troubleshooting/no-start-command-could-be-found> |
| 3 | 배포가 300초 근처에서 `FAILED` | 헬스 체크 타임아웃, 또는 앱의 호스트 필터가 `healthcheck.railway.app`을 막음 | `healthcheckTimeout`이나 `RAILWAY_HEALTHCHECK_TIMEOUT_SEC`를 올리고 기동 지연을 없애고 헬스 호스트를 허용합니다 | `SUCCESS`와 헬스 경로 2xx | proceed | <https://docs.railway.com/deployments/healthchecks> |
| 4 | `KeyError`, `undefined`, 빈 호스트로 접속 | 환경에 변수가 없거나, 설정했지만 배포하지 않음 | `--stdin`으로 설정한 뒤 스테이징 변경이 반영되도록 배포합니다 | 런타임 로그가 정상 기동하고 HTTP 로그가 200 | proceed | <https://docs.railway.com/variables> |
| 5 | 의존성 설치 실패, 엉뚱한 패키지 매니저, `Cannot find module` | 빌더가 프로젝트를 잘못 감지했거나 빌드가 다른 디렉터리에서 실행됨 | `build`를 명시하고 런타임 버전은 `RAILPACK_*` 변수로 맞춥니다. 저장소 전체가 아니라 서비스 루트를 옮깁니다 | 빌드 로그에 의도한 명령이 보이고 `SUCCESS` | proceed | <https://docs.railway.com/builds/railpack> |
| 6 | 컨테이너 즉시 종료, `exec format error`, 앱 로그 없이 재시작 반복 | 이미지가 다른 CPU 아키텍처로 빌드됨(로컬 arm64를 amd64에 배포) | `docker build --platform linux/amd64`로 다시 빌드해 푸시하고 `railway redeploy --from-source` | `SUCCESS`와 앱 로그 한 줄 | proceed | <https://docs.railway.com/guides/private-container-registry> |
| 7 | 종료 코드 137, 재시작 반복 | 메모리 부족 | 메모리 사용을 줄이거나 플랜 한도 안에서 복제본을 늘립니다 | `railway metrics --since 1h --memory`가 안정되고 30분 동안 재시작 없음 | explicit approval(비용) | <https://docs.railway.com/deployments/troubleshooting/slow-deployments> |
| 8 | `Pre-deploy command timed out after N seconds`, 배포 중단 | 마이그레이션이 실패했거나 멈춤. pre-deploy에는 볼륨이 없고 의존성을 직접 갖춰야 함 | 명령을 고치고 1–3600초 상한 안에 두며 pre-deploy에서 볼륨을 건드리지 않습니다 | 재배포 `SUCCESS`, 마이그레이션 로그 종료 코드 0 | explicit approval(스키마 변경) | <https://docs.railway.com/deployments/pre-deploy-command> |
| 9 | `ENOTFOUND redis.railway.internal` | IPv6 전용 레거시 환경에서 클라이언트가 A 레코드만 조회하거나, 서비스가 다른 프로젝트·환경에 있음 | ioredis와 bullmq에는 `family=0`을 설정하고 같은 프로젝트·환경인지 확인합니다. 외부에서는 공개 URL을 씁니다 | `railway logs --dns --status failed`가 비고 앱이 연결됨 | proceed | <https://docs.railway.com/databases/troubleshooting/enotfound-redis-railway-internal> |
| 10 | 배포가 `SKIPPED`, "no changed files match watch patterns" | 워치 경로가 바뀐 파일을 제외했거나 실패한 GitHub 검사 묶음이 배포를 건너뜀 | 워치 경로를 고치거나 `railway redeploy --from-source`를 씁니다 | 새 배포가 `SUCCESS` | proceed | <https://docs.railway.com/deployments/github-autodeploys> |
| 11 | 커스텀 도메인이 404, 인증서 오류 | CNAME만 넣고 TXT 검증 레코드가 없거나 인증서 재시도가 필요함 | 안내된 두 레코드를 그대로 넣고 `railway domain certificate retry`를 실행합니다 | `curl -I https://<domain>`가 200, `railway domain status`가 유효한 인증서 표시 | proceed | <https://docs.railway.com/networking/domains/working-with-domains> |
| 12 | 쓰기에서 `EACCES`, 또는 배포 후 데이터 소실 | 볼륨 마운트 경로가 틀렸거나 비루트 사용자가 썼거나 빌드·pre-deploy에서 씀 | `/app/...` 아래에 마운트하고 비루트 이미지면 `RAILWAY_RUN_UID=0`을 설정하며 런타임에만 씁니다 | 재시작 후 파일이 남음 | explicit approval(볼륨 변경) | <https://docs.railway.com/volumes> |
| 13 | 크론이 실행되지 않고 이전 실행이 계속 활성 | 프로세스가 종료되지 않거나 주기가 5분보다 짧거나 UTC가 아님 | 작업이 끝나면 종료하고 연결을 닫으며 UTC 기준 5분 이상 간격으로 잡습니다 | `railway cron list`에 다음 주기의 완료 실행이 보임 | proceed | <https://docs.railway.com/cron-jobs> |
| 14 | 종료 코드 `0`인데 실제로 배포되지 않음 | 업로드만 되었거나 분리·비TTY 반환, 또는 건너뛴 빌드 | 위 성공 판정을 이번 실행의 배포 ID로 적용합니다 | `deployment list --json`에서 그 ID가 `SUCCESS` | proceed | <https://docs.railway.com/cli/up> |

## Approval Required

| 동작 | 등급 |
|---|---|
| `railway status`, `deployment list`, 상한을 건 `logs`, `metrics`, `variable list`, `domain status`, `cron list`, `railway config plan`, 저장소의 작성 파일 편집 | proceed |
| 비프로덕션 환경의 `railway up`, `redeploy`, `restart`, 변수 변경, `railway config apply` | proceed |
| 같은 동작을 프로덕션에서 | named environment |
| 프로덕션 롤백(대시보드), `railway down`, 서비스·환경·도메인·볼륨·버킷 삭제, 프로덕션 환경의 `railway config apply --confirm-destructive`, `railway config partials release`나 `transfer`, 실제 데이터를 건드리는 pre-deploy나 수동 데이터베이스 마이그레이션, 비용이 늘어나는 변경(복제본, 플랜, 리전), 새 공개 도메인이나 TCP 프록시 생성, `config pull --include-variables` | explicit approval |
| 로그인, 계정이나 프로젝트 생성, CLI 전역 설치, 토큰이나 `variable list --json` 값 출력, 봉인 변수 해제 시도 | never |

승인은 이름을 댄 동작 하나에만 적용됩니다. 롤백 승인은 뒤따르는 배포를 덮지 않고, 변수 변경 승인은 재배포를 덮지 않습니다.

## Checked

> 자주 바뀝니다. 2026-11-07에 확인했습니다. 플래그, 한도, 폐기 날짜가 판단을 좌우하면 실제 페이지를 다시 확인합니다.

| 사실 | 값 |
|---|---|
| CLI | railway 5.71.0을 로컬에 설치해 2026-11-07에 실행 |
| 플래그 | 이 문서의 모든 플래그는 같은 바이너리의 `railway <command> --help`에서 다시 읽었고 기억에 의존하지 않음 |
| 작성 파일 | `.railway/railway.ts`(정식), `.py`와 `.go`는 베타, 파일은 하나만 |
| Config as Code 종료 | 2026-12-01, 강제. 신규 서비스는 선택 불가 |
| 빌더 | Railpack 기본, 파일 이름이 정확히 `Dockerfile`이면 Dockerfile, Nixpacks는 제시하지 않음 |
| 헬스 체크 | 배포 시점 2xx 폴링만, 기본 타임아웃 300초, 호스트 `healthcheck.railway.app` |
| 이미지 보존 | Free 24시간, Hobby 72시간, Pro 120시간, Enterprise 360시간 |
| pre-deploy | 볼륨 없음, 사설망 사용 가능, 타임아웃 1–3600초, 재시도 없음 |
| 크론 | UTC, 최소 5분 간격, 프로세스가 종료되어야 함 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Config as Code는 폐기 예정이고 기존 서비스는 2026-12-01까지 동작하며 신규 서비스는 선택할 수 없음 | <https://docs.railway.com/config-as-code> |
| IaC가 Config as Code를 대체하고 작성 파일은 하나이며 한 서비스를 두 체계가 관리할 수 없고 레거시 서비스에서는 `config plan`이 중단됨 | <https://docs.railway.com/infrastructure-as-code> |
| TypeScript DSL: services, build, start, healthcheck, preDeploy, replicas, env, preserve, volumes | <https://docs.railway.com/infrastructure-as-code/reference> |
| `config migrate` 플래그와 cutover, undo, status, `plan --out` 뒤 `apply --plan`, `--detailed-exit-code`, 값 마스킹, 오래된 계획 거부 | <https://docs.railway.com/cli/config> |
| Railpack은 설정 없이 빌드하고 나열한 언어를 지원함 | <https://docs.railway.com/builds/railpack> |
| Dockerfile 이름은 대문자 D의 `Dockerfile`이어야 하고 다른 이름은 `RAILWAY_DOCKERFILE_PATH`로 지정함 | <https://docs.railway.com/builds/dockerfiles> |
| 빌드·시작 명령 재정의와 exec 형식에서 `$PORT`를 쓰려면 셸이 필요함 | <https://docs.railway.com/builds/build-and-start-commands> |
| `RAILWAY_TOKEN`은 프로젝트 범위, `RAILWAY_API_TOKEN`은 계정 범위이고 하나만 설정할 수 있음 | <https://docs.railway.com/cli/login> |
| 프로젝트 토큰은 환경 하나에 한정되고 배포 관련 동작만 수행함 | <https://docs.railway.com/cli/deploying> |
| MCP 서버는 프로젝트 토큰을 거부함 | <https://docs.railway.com/ai/mcp-server> |
| `up` 플래그, `--detach`는 큐 진입 시 반환, 비대화형 실행은 프로젝트를 만들지 않음, 종료 코드 의미 | <https://docs.railway.com/cli/up> |
| stdout이 터미널이 아니고 CI 모드가 아니면 조기 반환함 | <https://raw.githubusercontent.com/railwayapp/cli/master/src/commands/up.rs> |
| `deployment list`의 `--limit`과 `--json`, `deployment up`, `deployment redeploy` | <https://docs.railway.com/cli/deployment> |
| 로그 종류, `--lines`가 스트리밍을 끄는 동작, 필터 문법, `--latest` | <https://docs.railway.com/cli/logs> |
| 배포 상태와 헬스 체크 유무에 따른 Active 판정 | <https://docs.railway.com/deployments/reference> |
| 헬스 체크는 2xx를 폴링하고 기본 타임아웃 300초이며 배포 후 모니터링은 없고 볼륨 서비스는 다운타임이 생기며 검사 호스트가 정해져 있음 | <https://docs.railway.com/deployments/healthchecks> |
| pre-deploy는 빌드와 배포 사이에 실행되고 볼륨이 없으며 사설망을 쓰고 재시도가 없고 1–3600초 상한이 있음 | <https://docs.railway.com/deployments/pre-deploy-command> |
| 변수는 스테이징되고 배포로 반영되며 봉인 변수에는 제약이 있음 | <https://docs.railway.com/variables> |
| 스테이징 변경은 검토하고 배포해야 반영됨 | <https://docs.railway.com/deployments/staged-changes> |
| 롤백은 이미지와 커스텀 변수를 복원하고 플랜 보존 기간에 제한되며 대시보드에서만 됨 | <https://docs.railway.com/deployments/deployment-actions> |
| 플랜별 보존 기간 | <https://docs.railway.com/pricing/plans> |
| 볼륨은 런타임에만 마운트되고 빌드와 pre-deploy에는 없으며 비루트 이미지는 `RAILWAY_RUN_UID=0`이 필요함 | <https://docs.railway.com/volumes> |
| 커스텀 도메인에는 CNAME과 TXT가 모두 필요하고 TXT가 없으면 404이며 전파에 최대 72시간이 걸림 | <https://docs.railway.com/networking/domains/working-with-domains> |
| 크론 일정은 UTC이고 최소 5분 간격이며 프로세스가 종료되어야 함 | <https://docs.railway.com/cron-jobs> |
| 워치 경로 때문에 배포가 건너뛰어질 수 있고 실패한 검사 묶음은 즉시 배포를 건너뜀 | <https://docs.railway.com/deployments/github-autodeploys> |
| 종료 코드 137은 OOM 킬 | <https://docs.railway.com/deployments/troubleshooting/slow-deployments> |
| Apple Silicon에서 빌드한 arm64 이미지는 `--platform linux/amd64` 없이 Railway에서 즉시 크래시함 | <https://docs.railway.com/guides/private-container-registry> |
| ioredis는 IPv6 전용 레거시 사설망에서 `family=0`이 필요함 | <https://docs.railway.com/databases/troubleshooting/enotfound-redis-railway-internal> |
| `Application failed to respond`는 앱이 `0.0.0.0:$PORT`에 듣지 않거나 대상 포트가 틀렸다는 뜻 | <https://docs.railway.com/networking/troubleshooting/application-failed-to-respond> |
| `No start command could be found`는 Railpack이 시작 명령을 찾지 못했다는 뜻 | <https://docs.railway.com/deployments/troubleshooting/no-start-command-could-be-found> |
| 그 배포의 `SUCCESS`를 보기 전에는 성공을 보고하지 않으며 `--detach`는 큐잉이고 종료 코드 0은 건너뜀일 수 있음 | <https://github.com/railwayapp/railway-skills> |

### Evidence grade

CLI 표면은 `DIRECT`입니다. railway 5.71.0을 설치해 위의 모든 명령과 플래그를 2026-11-07에 `--help`로 읽었고, 비TTY 조기 반환은 공개된 CLI 소스에서 확인했습니다. 보존 기간과 플랜별 한도처럼 실제 프로젝트가 있어야 보이는 플랫폼 동작은 `SECONDARY`입니다. Railway 자체 문서에서 인용했고 이 환경의 프로젝트에 대해 실행해 확인하지는 않았습니다. 2026-12-01 종료일은 문서 배너이지 서명된 계약이 아니므로 이전이 그 날짜에 걸려 있으면 페이지를 다시 읽습니다.
