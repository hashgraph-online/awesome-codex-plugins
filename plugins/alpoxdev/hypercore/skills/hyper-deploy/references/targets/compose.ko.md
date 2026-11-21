# Docker Compose 대상 가이드

로컬이나 SSH로 접속한 Docker 호스트 한 대에서 `compose.yaml`로 배포하는 저장소를 위한 대상 가이드입니다. `rules/target-detection.md`가 이 파일로 보낸 뒤 읽습니다. 배포 중에 `Dockerfile`도 빌드하면 이미지 규칙은 Docker 이미지 가이드가 맡고, 이 가이드는 프로젝트 모델, 배포 순서, 롤백이 되돌리지 못하는 것을 맡습니다.

## Contents

- Canonical Configuration
- Remote Host
- Validate And Deploy
- Success Test
- Status And Logs
- Change And Redeploy
- Rollback
- Failure Table
- Approval Required
- Checked
- Sources

## Canonical Configuration

파일 두 개를 순서대로 합칩니다. `compose.yaml`은 개발 형태이고, `compose.production.yaml`은 프로덕션에 필요한 차이만 담습니다. 조건문을 넣은 단일 파일은 쓰지 않고, 최상위 `version` 키도 쓰지 않습니다.

```yaml
# compose.yaml
name: shop
x-db-url: &db_url postgres://shop:${DB_PASSWORD:?DB_PASSWORD is required}@db:5432/shop

services:
  web:
    image: ghcr.io/example/shop-web:${TAG:?TAG is required}
    build: { context: ., secrets: [npm_token] }
    ports: ["127.0.0.1:8080:8080"]
    environment:
      NODE_ENV: production
      DATABASE_URL: *db_url
    secrets: [db_password]
    depends_on:
      db: { condition: service_healthy, restart: true }
      migrate: { condition: service_completed_successfully }
    healthcheck:
      test: ["CMD", "node", "dist/healthcheck.js"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    restart: unless-stopped

  migrate:
    image: ghcr.io/example/shop-web:${TAG:?TAG is required}
    build: { context: . }
    command: ["node", "dist/migrate.js"]
    environment: { DATABASE_URL: *db_url }
    depends_on:
      db: { condition: service_healthy }
    restart: "no"

  db:
    image: postgres:18
    environment:
      POSTGRES_DB: shop
      POSTGRES_USER: shop
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets: [db_password]
    volumes: ["db_data:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shop -d shop"]
      interval: 10s
      retries: 5
      start_period: 30s
    restart: unless-stopped

secrets:
  db_password: { environment: DB_PASSWORD }
  npm_token: { environment: NPM_TOKEN }

volumes:
  db_data:
```

```yaml
# compose.production.yaml
services:
  web:
    ports: !override ["127.0.0.1:8080:8080"]
    logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
  db:
    ports: !reset []
```

| 규칙 | 이유 |
|---|---|
| 분기를 넣은 한 파일 대신 `compose.production.yaml` | 프로덕션 파일은 차이만 담고, 개발 파일은 그대로 실행할 수 있게 남습니다 |
| 최상위 `version` 없음 | 폐기된 키입니다. Compose는 경고를 출력하고 스키마 선택에 쓰지 않습니다 |
| `condition`이 있는 긴 형식의 `depends_on` | 짧은 목록 형식은 의존 서비스가 *시작*될 때까지만 기다리고, 쓸 수 있는 상태가 될 때까지는 기다리지 않습니다 |
| 마이그레이션 서비스에 `condition: service_completed_successfully` | 앱이 시작되기 전에 마이그레이션이 끝나야 합니다. 작업 서비스에 `service_healthy`를 걸면 영원히 막힙니다 |
| 오래 도는 모든 서비스에 `healthcheck`, 서버는 `restart: unless-stopped`, 작업은 `"no"` | 헬스 체크가 없으면 "healthy"를 정의하는 것이 없어서 어떤 대기도 `running`만 보고 통과합니다. `unless-stopped`는 수동 정지는 존중하면서 장애 뒤에는 다시 시작하고, 다시 시작되는 작업은 끝없이 반복됩니다 |
| 필수 값에 `${VAR:?message}` | 값이 없으면 빈 문자열을 조용히 넣지 않고 그 메시지로 보간이 실패합니다 |
| `127.0.0.1:8080:8080` | 모든 인터페이스에 게시하면 호스트 방화벽과 상관없이 포트가 인터넷에 열립니다 |

환경 변수는 서로 다른 세 가지 경로로 들어오고, 이들을 섞는 것이 "변수가 비어 있다"의 가장 흔한 원인입니다.

| 출처 | 들어가는 곳 | 우선순위 |
|---|---|---|
| 셸 환경 | Compose 파일 안 `${VAR}`의 보간 | 보간 출처 가운데 가장 높음 |
| `--env-file <file>` | 보간과 `COMPOSE_*` 자체 설정 | 프로젝트 `.env`보다 우선 |
| 프로젝트 디렉터리의 `.env` | 보간에만 쓰임 | 가장 낮음, `--env-file`이 없을 때만 |
| 서비스의 `env_file:` | 컨테이너 환경 | `environment:`보다 낮고 이미지 `ENV`보다 높음 |
| 서비스의 `environment:` | 컨테이너 환경 | `env_file:`보다 높음 |

- `.env`의 값은 그 자체로 컨테이너에 넘어가지 않습니다. `environment:`나 `env_file:`을 거쳐야 컨테이너 변수가 됩니다.
- `docker compose config --environment`는 보간에 실제로 쓰인 변수를 출력합니다. 어떤 파일이 값을 넣었는지 가장 빨리 확인하는 방법입니다.

비밀 값은 환경 변수가 아니라 secret으로 넘깁니다.

- 서비스는 자기 `secrets:` 항목으로만 secret을 받습니다. 최상위에 선언만 해서는 아무 권한도 생기지 않습니다.
- `/run/secrets/<name>`에 읽기 전용으로 마운트되며 Linux 컨테이너에서만 지원됩니다.
- secret 출처로 쓰는 `environment:`는 Compose에서는 되지만 `docker stack deploy`에서는 되지 않습니다. 파일을 프로젝트와 함께 배포한다면 `file:`이 낫습니다.
- `_FILE` 관례를 따르는 이미지(`postgres`, `mysql`)는 `POSTGRES_PASSWORD_FILE=/run/secrets/db_password`를 읽습니다. 그러면 값이 `docker inspect`에 아예 나타나지 않습니다.

profile은 백업 작업이나 관리 화면 같은 선택적 서비스를 기본 시작에서 뺍니다. 핵심 서비스에는 profile을 붙이지 않습니다. 붙이면 평범한 `up`이 불완전한 스택을 띄웁니다.

원격 `include`와 `extends` 참조는 실행되는 내용입니다. Compose는 `privileged`, 호스트 바인드 마운트, `network_mode: host`, 호스트 `provider` 훅까지 파일을 적힌 그대로 적용하므로, 읽어 보지 않은 중첩 include가 이 권한을 모두 줍니다. include, extends, override, 보간을 하나의 모델로 풀어 주는 `docker compose config` 출력을 검토하고, 원격 include는 다이제스트로 고정합니다.

프로덕션에서 실제로 무엇이 실행될지 정하는 병합 규칙은 다음과 같습니다.

| 필드 종류 | 병합 동작 |
|---|---|
| 단일 값(`image`, `command`, `mem_limit`) | 뒤 파일의 값으로 바뀝니다 |
| `ports`, `expose`, `dns`, `tmpfs`, `env_file` | 이어 붙습니다. 그래서 `!override`/`!reset`을 쓰지 않으면 지운 포트가 남습니다 |
| `environment`, `labels` | 키 기준으로 합치고 뒤 값이 이깁니다 |
| `volumes`, `devices` | 컨테이너 마운트 경로 기준으로 합칩니다 |
| 모든 상대 경로 | 그 경로가 적힌 파일이 아니라 첫 번째 `-f` 파일을 기준으로 풀립니다 |

`!reset`은 기본 파일이 정한 값을 지웁니다(`ports: !reset []`, `environment: {FOO: !reset null}`). `!override`는 목록을 이어 붙이지 않고 바꿉니다. 오버레이에서 게시 포트를 확실히 빼는 방법은 이 둘뿐입니다.

## Remote Host

단일 호스트 배포는 Docker 소켓으로 서버에 닿고, 이 소켓은 그 서버의 root 권한과 같습니다. 지원되는 방법은 두 가지입니다.

```sh
docker context create prod --docker host=ssh://deploy@vps.example.com --description "production"
docker context use prod && docker info --format '{{.Name}} {{.ServerVersion}}'
# or per command, without a context:
DOCKER_HOST=ssh://deploy@vps.example.com docker info --format '{{.Name}} {{.ServerVersion}}'
```

- SSH 사용자는 원격 호스트의 Docker 소켓에 접근할 수 있어야 합니다. `docker` 그룹 구성원은 root와 같습니다.
- `DOCKER_HOST`와 `DOCKER_CONTEXT`는 선택한 context보다 우선하고, `--context`와 `--host` 플래그는 둘 다보다 우선합니다. 명령이 어느 엔진으로 가는지 항상 `docker info`로 확인합니다.
- `~/.ssh/config`에 `ControlMaster auto`, `ControlPath`, `ControlPersist yes`를 두면 호출마다 SSH 핸드셰이크를 새로 하지 않습니다. 명령을 수십 번 내는 배포에서 차이가 납니다.
- SSH 대신 TLS(`DOCKER_HOST=tcp://host:2376`, `DOCKER_TLS_VERIFY=1`, `DOCKER_CERT_PATH`)를 써도 권한 모델은 같습니다. 클라이언트 키를 가진 사람은 데몬을 조종할 수 있으므로 키를 root 비밀번호처럼 다룹니다.
- 로컬 `default` context가 실수로 선택된 상태에서 쓰기 명령을 실행하지 않습니다. context를 확인한 뒤, 이번 실행의 대상 호스트와 프로젝트 이름을 밝힙니다.

## Validate And Deploy

아무것도 바꾸지 않고 검증한 다음, 대기와 제한 시간을 걸어 배포합니다.

```sh
docker compose -f compose.yaml -f compose.production.yaml config -q
docker compose -f compose.yaml -f compose.production.yaml config --images --services --profiles
docker compose -f compose.yaml -f compose.production.yaml --dry-run up -d
docker compose -f compose.yaml -f compose.production.yaml pull
docker compose -f compose.yaml -f compose.production.yaml up -d --wait --wait-timeout 180 --remove-orphans
```

| 명령 | 증명하는 것 |
|---|---|
| `config -q` | 파일이 파싱·병합·보간되고 모든 `${VAR:?}`에 값이 있습니다. `--images --services --profiles`는 이번 실행이 건드릴 대상을 밝힙니다 |
| `--dry-run up -d` | 계획: 무엇을 만들고 받고 시작할지, 상태 변경 없이 |
| `pull` 뒤 `up -d --wait --wait-timeout` | 무엇이든 멈추기 전에 지금 자격 증명으로 이미지를 받을 수 있는지, 그다음 모든 컨테이너가 실행 중이고 healthy인지, 아니면 제한 시간에 명령이 실패하는지 |

- `config -q`에는 배포에 쓰는 `-f` 플래그를 같은 순서로 모두 넘깁니다. 기본 파일만 검증하면 실제로 실행되지 않을 모델을 검증한 것입니다.
- `--dry-run`은 Compose 전역 플래그이므로 하위 명령 앞에 둡니다. `pull`을 먼저 하면 "image not found"나 만료된 자격 증명이 반쯤 교체된 스택이 아니라 배포 전 오류로 드러납니다.
- `--wait`는 분리(detached) 모드를 함께 켜고 `--wait-timeout`이 대기를 제한합니다. 제한 시간이 없으면 healthy가 되지 않는 서비스 때문에 클라이언트가 포기할 때까지 멈춰 있습니다.
- `--remove-orphans`는 파일에서 지운 서비스의 컨테이너를 지웁니다. 프로젝트 이름이 맞으면 안전하고, 틀리면 관계없는 컨테이너를 지웁니다.
- 프로젝트 이름을 명시해(`-p <project>` 또는 최상위 `name`) 다른 디렉터리 프로젝트의 컨테이너를 넘겨받지 않게 합니다.
- 재시작할 때 잠깐 끊긴다고 예상합니다. 앞에 프록시나 순차 배포 도구가 없으면 Compose는 이전 컨테이너를 멈춘 뒤 새 컨테이너를 시작하며, 무중단은 보장되지 않습니다.

## Success Test

Compose는 모든 서비스가 실행 중이고, 헬스 체크가 있는 서비스는 healthy일 때만 성공을 알립니다.

```sh
docker compose -f compose.yaml -f compose.production.yaml ps --format json
```

- 출력의 모든 서비스가 `"State": "running"`이어야 하고, 헬스 체크를 정의한 서비스는 `"Health": "healthy"`여야 합니다. `"Health": ""`는 그 서비스에 헬스 체크가 없다는 뜻입니다.
- `up --wait`의 종료 코드도 같은 조건을 보지만 프로세스 목록과 함께 읽어야 합니다. 대기 시간이 끝난 뒤 `0`으로 종료된 서비스는 종료 코드에 더 이상 드러나지 않는 실패입니다. 그다음 컨테이너가 확인하는 것과 같은 헬스 엔드포인트로, 게시된 주소를 통해 앱에 요청합니다.

Without a healthcheck, `--wait` only confirms the service is running. (헬스 체크가 없으면 `--wait`는 서비스가 실행 중인지만 확인합니다.)

함정은 이 한 문장에 있습니다. `healthcheck`가 없는 서비스에는 healthy 상태가 생기지 않으므로, `up --wait`는 컨테이너가 뜨자마자 반환합니다. 그래서 1초 뒤에 죽거나 500을 돌려주는 앱도 "배포 성공"이 됩니다. 헬스 체크가 없는 서비스로 이루어진 스택에서는 `up --wait`를 시작 확인으로만 보고, 배포를 성공이라 말하기 전에 직접 요청을 보냅니다.

## Status And Logs

| 질문 | 명령 |
|---|---|
| 모든 컨테이너 또는 실행 중인 컨테이너의 현재 상태 | `docker compose ps --all --format json`, `docker compose ps --status=running` |
| 컨테이너가 멈춘 이유 | `docker inspect --format '{{.State.Status}} {{.State.ExitCode}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' <container>` |
| 마지막 헬스 확인 출력 | `docker inspect --format '{{json .State.Health}}' <container>` |
| 서비스 하나의 제한된 로그, 재시작과 OOM을 포함한 최근 이벤트 | `docker compose logs --no-color --tail=200 --since=15m <service>`, `docker compose events --json --since=30m` |
| 서비스가 실제로 게시하는 호스트 포트와 그 안에서 도는 프로세스 | `docker compose port <service> 8080`, `docker compose top` |

진단을 가르는 종료 코드는 다음과 같습니다. 오래 도는 서비스의 `0`은 명령이 끝났다는 뜻이므로, 프로세스가 fork했거나 entrypoint가 반환한 것입니다. `137`은 OOM killer의 `SIGKILL`이거나 유예 시간을 넘긴 정지입니다. `143`은 정상 정지인 `SIGTERM`입니다.

트래픽이 없는 `running` 컨테이너는 헬스 체크가 없거나, 컨테이너 안에서 `127.0.0.1`에 바인드했거나, 다른 포트를 게시한 경우입니다. 마지막 경우는 `docker compose port`가 답해 줍니다.

## Change And Redeploy

| 변경 | 명령 | 주의 |
|---|---|---|
| 서비스 하나의 새 이미지 | `docker compose build web && docker compose up --no-deps -d web` | `--no-deps`는 의존 서비스를 그대로 두며, 서비스가 캐시한 연결과 DNS 항목도 남습니다. 의존 서비스 주소가 바뀌지 않았을 때만 씁니다 |
| 새 환경 값이나 설정 | `docker compose up -d <service>` | `restart`는 Compose 변경을 전혀 반영하지 않습니다. 파일에서 바꾼 변수는 재생성해야 들어갑니다 |
| 전부 재생성 | `docker compose up -d --force-recreate` | 이미지와 설정이 바뀌지 않은 컨테이너까지 재생성하므로 모든 서비스가 잠깐 끊깁니다 |
| 의존 서비스 이미지도 바뀜 | `docker compose up -d --always-recreate-deps <service>` | 서비스와 함께 의존 서비스도 재생성합니다. `--no-deps`가 피하는 동작입니다 |
| 파일만 다시 읽기 | `docker compose config -q` | 검증만 하고 상태는 바꾸지 않습니다 |

- `docker compose restart`는 기존 컨테이너를 기존 설정 그대로 다시 시작하므로 파일 변경이 반영되지 않습니다. 파일을 바꿨으면 `up -d`를 씁니다.
- `--force-recreate`의 범위는 *선택한 서비스*입니다. 서비스 인자가 없으면 프로젝트 전체이고 스택 전체가 끊깁니다. 서비스 이름을 넘깁니다.
- `--no-deps` 없이 `up -d <service>`를 하면 설정이 바뀐 의존 서비스도 재생성합니다. 공통 기본 설정을 고친 뒤라면 보통 이쪽이 원하는 동작입니다.
- 다시 빌드한 뒤에도 이미지 태그가 같으면 `--pull always`나 다이제스트 변경이 있어야 하고, 아니면 호스트가 이전 이미지를 계속 씁니다. Git SHA로 태그를 붙이면 이 문제가 사라집니다.

## Rollback

Compose에는 원자적인 롤백이 없습니다. 실제 수단은 이전 이미지 태그로 `up -d`를 다시 하는 것입니다.

```sh
TAG=<previous-sha> docker compose -f compose.yaml -f compose.production.yaml up -d --wait
```

- 실행하기 전에 밝힙니다. 이 배포는 *이전 이미지와 설정*을 되돌리지만, 데이터베이스 내용, 이름 있는 볼륨, 업로드한 파일, 마이그레이션이 바꾼 것은 되돌리지 않습니다. 이전 버전이 마이그레이션된 스키마를 읽지 못하면 롤백에는 앞으로 가는 수정이나 데이터베이스 복원이 필요하고, 복원은 따로 승인을 받습니다.
- `deploy:`의 `rollback_config`는 Swarm과 다른 오케스트레이터의 기능이며 일반 Compose는 무시하므로 롤백 계획으로 제시하지 않습니다. 이전 태그가 남아 있어야 하며, 태그를 Git SHA로 붙이는 이유입니다. 실패한 배포가 이전 컨테이너를 계속 서비스하게 두었다면 앞으로 가는 수정을 우선합니다. 빌드나 `pull`이 실패했다면 실행 중인 스택은 건드려지지 않았습니다.

## Failure Table

| # | 신호 | 원인 | 수정 | 확인 | 등급 | 출처 |
|---|---|---|---|---|---|---|
| 1 | `dependency failed to start: container … is unhealthy` | `service_healthy` 의존 서비스가 끝내 healthy가 되지 않음 | `State.Health.Log`를 읽고 확인 명령을 고치거나 `start_period`를 늘림 | `compose ps --format json`에 `"Health": "healthy"` | proceed | <https://docs.docker.com/compose/how-tos/startup-order/> |
| 2 | `up --wait`는 반환했는데 앱이 500을 주거나 죽어 있음 | 헬스 체크가 없어 대기가 `running`만 봄 | `healthcheck`를 추가하고 `--wait`로 다시 실행 | `ps --format json`에 헬스 상태가 있고, unhealthy 서비스에서 대기가 실패 | proceed | <https://docs.docker.com/reference/cli/docker/compose/up/> |
| 3 | 컨테이너 안에서 변수가 비어 있음 | `.env`에만 있고 `environment:`나 `env_file:`로 넘기지 않음, 또는 다른 파일에 설정 | `environment:`로 넘기고 `docker compose config --environment`로 확인 | `docker inspect --format '{{json .Config.Env}}' <container>`에 값이 보임 | proceed | <https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/> |
| 4 | `restart` 뒤에도 바꾼 변수가 반영되지 않음 | `restart`는 기존 컨테이너 설정을 유지 | `docker compose up -d <service>`로 재생성 | `docker inspect`에 새 값 | proceed | <https://docs.docker.com/reference/cli/docker/compose/restart/> |
| 5 | 게시한 포트가 밖에서 안 되고 호스트에서는 됨 | Docker 게시 포트가 ufw `INPUT` 체인을 우회하거나, 바인드가 `127.0.0.1` | `127.0.0.1`에 게시하고 앞에 프록시를 두거나, 클라우드 방화벽·보안 그룹을 염 | 호스트 밖에서 보낸 요청이 성공 | explicit approval(방화벽 변경) | <https://docs.docker.com/engine/network/packet-filtering-firewalls/> |
| 6 | 컨테이너는 `running`, 응답이 없음 | 앱이 컨테이너 안에서 `127.0.0.1`에 바인드하거나, 게시한 포트와 다른 포트를 들음 | `0.0.0.0`에 바인드하고 `ports`를 실제 포트에 맞춤 | `docker compose port <svc> <port>`와 호스트에서 `curl` | proceed | <https://docs.docker.com/reference/compose-file/services/> |
| 7 | `docker inspect` 출력에서 비밀 값이 보임 | secret이 아니라 환경 변수로 넘김 | `secrets:`로 옮기고, 이미지가 지원하면 `_FILE` 관례를 씀 | `docker inspect`에 값이 아니라 경로가 보임 | 값을 교체해야 하면 explicit approval | <https://docs.docker.com/compose/how-tos/use-secrets/> |
| 8 | 오버레이로 지우려던 게시 포트가 다시 나타남 | 목록 필드는 바뀌지 않고 이어 붙음 | 오버레이에 `ports: !reset []`나 `ports: !override [...]` | `docker compose config`에 의도한 포트만 | proceed | <https://docs.docker.com/reference/compose-file/merge/> |
| 9 | 컨테이너가 `137`로 반복 종료 | 메모리 부족 | 컨테이너 한도를 올리거나 메모리를 줄이고 `docker compose events --json`으로 확인 | 30분 동안 OOM 이벤트 없음 | 비용이 드는 자원 한도를 올리면 explicit approval | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| 10 | 아무도 쓰지 않은 설정이 적용되거나 원격 출처 경고 | 원격 `include`나 `extends`가 모델로 풀림 | `docker compose config` 출력을 전부 읽고 원격 참조를 다이제스트로 고정 | 풀린 모델이 검토한 설정과 같음 | 원격 내용을 바꿔야 하면 explicit approval | <https://docs.docker.com/compose/trust-model/> |

## Approval Required

| 동작 | 등급 |
|---|---|
| `config -q`, `config --environment`, `config --images`, `--dry-run up`, `pull`, `ps`, 제한을 건 `logs`, `docker inspect`, `compose port`, `compose top`, 저장소 안 Compose 파일 수정 | proceed |
| 비프로덕션 프로젝트에서 `up -d`, `build`, `--force-recreate`, `restart`, `-v` 없는 `down` | proceed |
| 같은 동작을 프로덕션에서 | named environment |
| `docker compose down -v`, `docker volume rm`, `docker system prune --volumes`, `down --rmi`, 파일에서 이름 있는 볼륨 제거, 볼륨의 `!reset`, 실제 데이터에 대한 마이그레이션 서비스, 새 공개 포트 게시, 방화벽·DNS 변경, 데이터베이스 복원이 필요한 롤백 | explicit approval |
| 로그인, 호스트나 계정 생성, Compose 전역 설치, `.env`·`env_file`·`docker inspect`의 비밀 값 출력 | never |

`docker compose down -v`는 파일에 선언된 이름 있는 볼륨과 컨테이너에 붙은 익명 볼륨을 지웁니다. 데이터베이스, 업로드 파일, 큐 상태가 함께 사라지고, 스택 안의 어떤 것도 이를 다시 만들지 못합니다. 승인을 묻기 전에 볼륨 이름과 그 안의 내용을 밝히고, 실패한 배포 뒤의 정리 명령으로 절대 실행하지 않습니다.

## Checked

> 변동 가능. 2026-11-07에 아래 출처와 로컬 CLI로 확인했습니다. 플래그나 기본값이 실행을 좌우하면 페이지를 다시 읽습니다.

| 사실 | 값 |
|---|---|
| 로컬 CLI | Docker 27.3.1, Compose v2.30.3-desktop.1, buildx v0.18.0-desktop.2 |
| `--wait` / `--dry-run` | `--wait`는 분리 모드를 함께 켜고 running이나 healthy를 기다리며 `--wait-timeout`으로 제한됩니다. `--dry-run`은 전역 플래그이고 상태 변경 없이 계획을 출력합니다 |
| 환경 변수 순서 | 보간: 셸 > `--env-file` > 프로젝트 `.env`. 컨테이너: `run -e` > 보간된 `environment`/`env_file` > `environment` > `env_file` > 이미지 `ENV` |
| Secrets | `/run/secrets/<name>`에 읽기 전용, Linux 컨테이너만. `environment` 출처는 `docker stack deploy`에서 미지원 |
| 병합 / `version` | 단일 값은 교체, `ports`/`expose`/`dns`/`tmpfs`는 이어 붙임, `environment`/`labels`는 키 기준 병합, `volumes`는 마운트 경로 기준 병합, 그 밖에는 `!reset`/`!override`. 최상위 `version` 키는 폐기됐고 경고를 냅니다 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 프로덕션 차이는 추가 `compose.production.yaml`에 두고, 서비스 하나는 `build web` 뒤 `up --no-deps -d web`으로 다시 배포 | <https://docs.docker.com/compose/how-tos/production/> |
| `--wait`는 running이나 healthy를 기다리고 분리 모드를 켬, `--wait-timeout`이 제한, `--force-recreate`, `--no-deps`, `--remove-orphans`, `--always-recreate-deps` | <https://docs.docker.com/reference/cli/docker/compose/up/> |
| `config`는 `-q`, `--images`, `--services`, `--profiles`, `--environment`로 병합·해석·검증하고, Dry Run 모드는 스택을 바꾸지 않고 명령을 시험 | <https://docs.docker.com/reference/cli/docker/compose/config/>, <https://docs.docker.com/reference/cli/docker/compose/> |
| Compose는 시작 시 준비 상태를 기다리지 않음, `condition: service_healthy`와 `service_completed_successfully`, 의존 서비스의 `restart: true` | <https://docs.docker.com/compose/how-tos/startup-order/> |
| 짧은 형식 `depends_on`은 healthy를 기다리지 않음 | <https://docs.docker.com/reference/compose-file/services/> |
| 보간 우선순위: 셸, `--env-file`, 프로젝트 `.env`, `${VAR:?error}`, `config --environment` | <https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/> |
| 컨테이너 우선순위: `run -e`, 보간된 `environment`/`env_file`, `environment`, `env_file`, 이미지 `ENV` | <https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/> |
| Secret은 `/run/secrets/<name>`에 마운트되고 서비스별로 부여되며 Linux 전용이고 `_FILE` 관례를 씀. 출처는 `file`이나 `environment`이고 `environment`는 `docker stack deploy`에서 미지원 | <https://docs.docker.com/compose/how-tos/use-secrets/>, <https://docs.docker.com/reference/compose-file/secrets/> |
| 병합 규칙, 기본 파일 기준 상대 경로, `!reset`, `!override` | <https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/>, <https://docs.docker.com/reference/compose-file/merge/> |
| 핵심 서비스에는 profile을 붙이지 않음 | <https://docs.docker.com/compose/how-tos/profiles/> |
| Compose는 모든 파일을 신뢰하고, include와 extends가 특권 설정을 가져올 수 있으며, 이름 충돌은 병합하지 않고 경고하고, 원격 참조는 다이제스트로 고정 | <https://docs.docker.com/compose/trust-model/>, <https://docs.docker.com/reference/compose-file/include/> |
| `restart`는 Compose 파일 변경을 반영하지 않음, `ps --format json`은 컨테이너마다 `State`·`Health`·`ExitCode`를 냄, `logs`는 `--tail`·`--since`·`--no-color`를 받음, `down -v`는 이름 있는 볼륨과 익명 볼륨을 지움, `pull`은 컨테이너를 시작하지 않고 이미지를 받음 | <https://docs.docker.com/reference/cli/docker/compose/restart/>, <https://docs.docker.com/reference/cli/docker/compose/ps/>, <https://docs.docker.com/reference/cli/docker/compose/logs/>, <https://docs.docker.com/reference/cli/docker/compose/down/>, <https://docs.docker.com/reference/cli/docker/compose/pull/> |
| Context와 `DOCKER_HOST`/`DOCKER_CONTEXT` 우선순위, SSH context, 원격 사용자의 소켓 접근, root와 같은 TLS 키 | <https://docs.docker.com/engine/manage-resources/contexts/>, <https://docs.docker.com/engine/security/protect-access/> |
| Docker 게시 포트는 ufw의 `INPUT`/`OUTPUT` 체인을 우회 | <https://docs.docker.com/engine/network/packet-filtering-firewalls/> |
| `exited=137`은 `SIGKILL` | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| `deploy.rollback_config`는 오케스트레이터 동작이고 Compose 롤백이 아님 | <https://github.com/compose-spec/compose-spec/blob/main/deploy.md> |
| 최상위 `version` 요소는 폐기됐고 경고를 출력 | <https://github.com/compose-spec/compose-spec/blob/main/04-version-and-name.md> |
| 파괴적인 Docker 명령은 무엇이 지워지는지 정확히 밝히고 명시적 확인을 받음 | <https://github.com/docker/skills> |

### Evidence grade

CLI 표면은 `DIRECT`입니다. 2026-11-07에 Compose v2.30.3과 Docker 27.3.1이 설치되어 있었고, 위 플래그는 모두 `--help`에서 읽었습니다. 병합·우선순위 표, 신뢰 모델, secret 동작은 `SECONDARY`입니다. Docker와 compose-spec 문서에서 옮겼고, 여기서 실제 다중 파일 프로젝트로 실행해 보지는 않았습니다. 원자적 롤백이 없다는 것은 버전에 따른 사실이 아니라 단일 호스트 Compose의 설계 특성이며, `deploy:` 롤백 설정이 오케스트레이터 전용으로 남아 있는 동안 유효합니다.
