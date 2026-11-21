# VPS(직접 관리하는 리눅스 서버)

직접 접속하는 리눅스 서버 대상 가이드입니다. Docker가 있는 경우와 없는 경우를 모두 다루며 Kamal, Coolify, Dokploy, 프록시와 `docker rollout` 조합, Caddy 뒤의 systemd를 설명합니다. `rules/target-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. 저장소에 compose 파일이 함께 있으면 [compose.md](compose.md)를 두 번째 가이드로 읽습니다.

이 대상의 실패는 대부분 빌드 실패가 아닙니다. 루프백 주소에만 바인드한 컨테이너, 이미지 안에서 실행할 수 없는 헬스체크, 잘못된 CPU 아키텍처로 만든 이미지, 빠진 시크릿, 방화벽을 우회하는 게시 포트가 원인입니다.

## Contents

- Choose The Path
- Kamal
- Coolify And Dokploy
- Proxy And TLS
- Server Baseline
- Diagnosis Order
- Failure Table
- Approval Required
- Checked
- Sources

## Choose The Path

선호가 아니라 서버에 이미 무엇이 있는지로 정합니다. 결정한 근거를 대상 줄에 기록합니다.

| 순서 | 서버와 저장소의 조건 | 경로 | 이유 |
|---|---|---|---|
| 1 | Docker가 있고 저장소에 `Dockerfile`이나 compose가 있으며 앱이 하나이거나 소수 | Kamal(`config/deploy.yml`) | 프록시, 헬스체크, 롤백, 시크릿이 설정 파일 하나에 모입니다. 무중단 교체와 롤백이 내장되어 있습니다 |
| 2 | 한 서버에서 여러 앱과 도메인을 굴리고 GUI 운영이 필요 | Coolify(`Authorization: Bearer`) 또는 Dokploy(`x-api-key`) | 패널이 프록시와 앱별 설정을 소유하고 배포는 API로 트리거합니다 |
| 3 | compose가 이미 자산이고 제어판을 원하지 않으며 앞에 프록시를 둘 수 있음 | Caddy나 Traefik에 `docker rollout <service>` | 두 인스턴스로 늘리고 healthy를 기다린 뒤 구 컨테이너를 제거합니다. 운영할 패널이 없습니다 |
| 4 | 앱이 컨테이너가 아님 | systemd 유닛과 Caddy 리버스 프록시 | 프로세스를 유닛으로 관리하고 TLS는 프록시가 종료합니다 |

모든 경로에 적용되는 규칙입니다.

- `docker rollout`은 프록시가 필요하고 대상 서비스에 `container_name`이나 `ports`가 있으면 동작하지 않습니다. 두 컨테이너가 이름 하나나 호스트 포트 하나를 공유할 수 없습니다.
- Kamal 2는 v1의 Traefik 구성을 `kamal-proxy`로 바꿨습니다. v1 글이나 예전 블로그의 `traefik` 키, `.env` 시크릿, `app_port: 3000`을 그대로 옮기면 Kamal 2에서 깨집니다.
- Coolify와 Dokploy는 "Docker Swarm"을 다르게 다룹니다. Dokploy는 Swarm이 토대이고 Coolify는 스케일링 문서에서 Swarm을 폐기 예정으로 표시합니다. 한 도구의 조언을 다른 도구에 그대로 적용하지 않습니다.
- 어떤 경로든 시작 전에 확인합니다. 이미지 아키텍처가 호스트와 맞는지, 앱이 `0.0.0.0`에 바인드하는지, 헬스 엔드포인트가 있는지, 시크릿이 있는지, 80과 443이 열려 있는지, DNS A/AAAA가 호스트를 가리키는지, 백업이 있는지입니다.

## Kamal

정본은 `config/deploy.yml`이고 `config/deploy.<destination>.yml`이 그 위에 병합되며 `-d <destination>`으로 선택합니다. Kamal은 모르는 키를 거부하므로 오타가 조용히 무시되지 않고 바로 실패합니다.

| 키 | 용도 |
|---|---|
| `service`, `image` | 컨테이너 이름 접두사와 이미지 저장소 |
| `servers` | 호스트 목록, 또는 역할별 호스트 |
| `registry` | 사용자 이름과 시크릿 이름으로 읽는 비밀번호 |
| `env.secret` | `.kamal/secrets`에서 읽는 이름. 값을 직접 적지 않습니다 |
| `proxy.host` / `proxy.hosts` | 프록시가 라우팅할 호스트 이름. 없으면 모든 요청을 전달합니다 |
| `proxy.app_port` | 컨테이너가 노출하는 포트. 기본값 `80` |
| `proxy.ssl` | Let's Encrypt 자동 HTTPS. 서버 하나와 `host` 설정이 필요합니다 |
| `proxy.healthcheck.path`, `interval`, `timeout` | 기본 경로 `/up`을 배포 타임아웃까지 1초에 한 번 요청합니다 |
| `builder.arch` | `amd64` 또는 `arm64`. 호스트가 빌드 기계와 다르면 지정합니다 |
| `builder.remote` | 로컬 아키텍처와 맞지 않는 빌드에 쓰는 `ssh://docker@builder` |
| `readiness_delay` | 컨테이너가 뜬 뒤 준비 판정까지 기다리는 초. 기본 `7`이며 프록시나 헬스체크가 없을 때만 적용됩니다 |
| `deploy_timeout` | 준비를 기다리는 초. 기본 `30` |
| `drain_timeout`, `stop_timeout` | 드레인과 `SIGTERM` 이후 정지까지 기다리는 초 |
| `retain_containers` | 남겨 두는 구 컨테이너와 이미지 수. 기본 `5` |
| `accessories.<name>` | 앱과 별도로 관리하는 데이터베이스와 캐시 |

배포 순서가 곧 진단 순서입니다. 레지스트리 로그인, 빌드와 푸시, 풀, `kamal-proxy` 확인, 새 컨테이너 기동, `GET /up`이 `200 OK`일 때 트래픽 전환, 구 컨테이너 정지, 정리입니다. 전환 전 실패는 이전 버전이 계속 서비스하므로 안전하고, 전환 후 실패는 배포 문제가 아니라 런타임 문제입니다.

Kamal 2에서 시크릿은 `.env`와 `.env.rb`에서 `.kamal/secrets`로 옮겼고 `.kamal/secrets-common`과 `.kamal/secrets.<destination>`도 씁니다. 값은 `$ENV_VAR`이거나 `$(op read ...)` 같은 명령 치환입니다. `.env`는 더 이상 자동으로 읽히지 않고, `.kamal/secrets`의 값도 설정 파일로 내보내지지 않습니다.

```sh
kamal deploy -d staging            # 빌드, 푸시, 릴리스, 전환
kamal deploy --lock-wait           # 즉시 실패 대신 배포 잠금을 기다림
kamal app version                  # 지금 실행 중인 버전
kamal app details                  # 호스트별 컨테이너 상태
kamal details                      # 앱, 프록시, 액세서리
kamal app logs -n 200              # 줄 수를 제한한 런타임 로그
kamal app containers -q            # 롤백에 쓸 수 있는 이미지 태그
kamal audit                        # 서버의 감사 로그
```

- 배포가 자동으로 잡는 잠금을 다른 배포가 쥐고 있으면 즉시 실패합니다. `--lock-wait`은 대신 폴링하며 `--lock-wait-timeout`(기본 900)과 `--lock-wait-interval`(기본 15)로 조정합니다. `kamal lock acquire`로 직접 잡은 잠금은 기다리지 않습니다.
- `kamal rollback <sha>`는 이전 이미지만 되돌립니다. 이번 실행에서 명시 승인을 받아야 하는 프로덕션 동작으로 제시하고, 데이터베이스와 볼륨, 마이그레이션은 되돌아가지 않는다고 함께 밝힙니다. 구 컨테이너는 기본 3일 뒤 정리되므로 그 이후에는 롤백 대상이 없을 수 있습니다.
- 액세서리는 `kamal deploy`가 갱신하지 않고 무중단 배포가 없습니다. 데이터베이스 액세서리를 재시작하는 마이그레이션은 계획된 중단이지 롤링 교체가 아닙니다.
- 진단 목적으로 `kamal config`를 실행하지 않습니다. 시크릿을 포함한 병합 설정 전체를 출력합니다.

## Coolify And Dokploy

두 패널 모두 API로 배포합니다. 트리거는 작업을 대기열에 넣을 뿐입니다.

| 패널 | 트리거 | 인증 헤더 | 응답의 의미 |
|---|---|---|---|
| Coolify | `GET /api/v1/deploy?uuid=<uuid>&force=false`, 또는 `{"uuid":"...","force":false}`를 담은 `POST` | `Authorization: Bearer $COOLIFY_TOKEN` | 대기열에 들어간 배포 UUID. 배포 페이지에서 완료까지 확인해야 합니다 |
| Dokploy | `{"applicationId":"..."}`를 담은 `POST /api/application.deploy` | `x-api-key: $DOKPLOY_API_KEY` | 호출 수락. `application.one`의 `applicationStatus`/`composeStatus`가 `idle`, `running`, `done`, `error` 중 하나입니다 |

```sh
curl --fail-with-body --header "Authorization: Bearer $COOLIFY_TOKEN" \
  "$COOLIFY_URL/api/v1/deploy?uuid=$COOLIFY_UUID&force=false"
curl --fail-with-body --request POST "$DOKPLOY_URL/api/application.deploy" \
  --header "x-api-key: $DOKPLOY_API_KEY" --header 'Content-Type: application/json' \
  --data '{"applicationId":"'"$DOKPLOY_APP_ID"'"}'
```

- 요청 수락은 성공이 아닙니다. Coolify는 API 요청이 수락됐다고 모든 리소스가 healthy가 됐다고 보지 말라고 분명히 말합니다. 배포 기록, 헬스체크, URL 순서로 확인합니다.
- Coolify는 실행 중인 컨테이너를 건드리기 전에 소스에서 이미지를 빌드하므로 빌드 실패는 현재 버전을 그대로 둡니다. 롤링 교체에는 헬스체크가 필요하고, 호스트 포트 매핑이나 고정 컨테이너 이름, 프리뷰에서는 stop-then-start로 떨어져 짧게 트래픽이 끊깁니다.
- 대시보드에서 설정한 HTTP 헬스체크는 애플리케이션 컨테이너 안에서 실행됩니다. 최종 이미지에 `curl`이나 `wget`이 있어야 하고, 서버에만 설치해서는 부족합니다. 둘 다 없으면 컨테이너는 항상 unhealthy입니다. Compose가 아닌 Dockerfile 앱에서는 Dockerfile의 `HEALTHCHECK`가 우선합니다.
- Dokploy는 기본값이 현재 컨테이너를 멈추고 새 컨테이너를 시작하는 방식이라 배포할 때마다 Bad Gateway가 납니다. 무중단에는 Swarm 헬스체크와 업데이트 설정의 `"FailureAction": "rollback"`, `"Order": "start-first"`가 필요합니다. 헬스체크는 컨테이너 안에서 `curl -f http://localhost:<port>/health`로 실행되므로 이미지에 `curl`이 있어야 합니다.
- Dokploy의 Volume Backups는 Docker named volume에만 동작합니다. `../files` 바인드 마운트나 배포 시 정리되는 절대 호스트 경로는 그 방식으로 백업할 수 없습니다.
- `composeStatus`를 읽으려면 `applicationId`가 필요하고, 그 값이 상태를 보여 줄 뿐 헬스체크 통과를 증명하지는 않습니다. 두 패널 모두 최종 배포 결과를 헬스 판정과 함께 돌려주는 일반 상태 엔드포인트를 문서화하지 않았고 이 가이드에서도 확인하지 못했습니다. 없는 폴링을 지어내지 말고 그 한계를 밝힙니다.
- 두 패널의 롤백은 이미지를 바꿉니다. 마이그레이션을 되돌리거나 볼륨을 복원하거나 외부 서비스를 바꾸지 않습니다. Kamal도 같습니다.

## Proxy And TLS

Caddy는 다음 조건이 모두 성립하면 HTTPS를 자동으로 구성합니다. 도메인의 A/AAAA 레코드가 서버를 가리키고, 80과 443이 외부에 열려 있고, Caddy가 그 포트를 바인드하거나 전달받을 수 있고, 데이터 디렉터리가 쓰기 가능하며 영속적이고, 호스트 이름이 설정에 나옵니다. HTTP에서 HTTPS로의 리다이렉트도 기본입니다. 와일드카드 인증서에는 DNS-01 챌린지가 필요하고 기본 HTTP-01과 TLS-ALPN으로는 발급되지 않습니다.

```caddyfile
app.example.com {
  reverse_proxy 127.0.0.1:3000 {
    health_uri /health
    health_interval 5s
    lb_try_duration 15s
  }
}
```

활성 헬스체크에는 `health_uri`나 `health_port`가 필요합니다. `lb_try_duration`은 그 시간 동안 요청을 다른 백엔드로 재시도하므로 컨테이너 교체 구간을 덮습니다. Caddy에는 Docker 라벨 자동 발견이 내장되어 있지 않으므로 서비스 이름과 포트, 또는 루프백에 게시한 포트로 지정합니다.

Traefik은 Docker 라벨(`traefik.http.routers.<name>.rule`, `traefik.docker.network`, `traefik.http.services.<name>.loadbalancer.server.port`)로 컨테이너를 발견합니다. `providers.docker.exposedByDefault` 기본값이 `true`라 라벨이 없는 컨테이너도 라우팅 대상이 될 수 있으므로 `false`로 두고 라벨을 직접 붙입니다. `docker.sock`을 마운트하면 프록시가 그 호스트의 root에 준하는 Docker 데몬 권한을 갖습니다. 읽기 전용 마운트도 API를 노출하므로 socket proxy를 선호하고 소켓을 TCP로 게시하지 않습니다.

ACME는 Let's Encrypt가 호스트에 닿아야 성립합니다. HTTP-01은 80, TLS-ALPN-01은 443입니다. TLS를 종료하는 프록시는 그 포트를 혼자 써야 합니다.

## Server Baseline

- Docker는 컨테이너 포트를 기본으로 모든 인터페이스에 게시하고 그 트래픽을 `nat` 테이블에서 ufw의 `INPUT` 체인보다 먼저 라우팅합니다. 그래서 포트를 막는 ufw 규칙이 그 포트를 막지 못합니다. 게시 포트를 루프백에 묶고(`-p 127.0.0.1:3000:3000`) 프록시만 밖으로 내보내거나, Docker의 자체 accept 규칙보다 먼저 처리되는 `DOCKER-USER` 체인에 규칙을 넣습니다. Docker가 만든 체인은 직접 고치지 않습니다.
- Ubuntu에서 ufw는 기본으로 비활성입니다. 호스트가 방화벽으로 보호된다고 말하기 전에 `sudo ufw status verbose`를 읽습니다. 그 줄이 `Status: active`일 때까지 "ufw를 켰다"는 가정일 뿐입니다.
- SSH는 키 전용 로그인과 root 제한을 씁니다. `PasswordAuthentication no`와 `PermitRootLogin prohibit-password`(또는 `without-password`)는 문서 인용이 아니라 관행이므로 [INFERENCE]로 취급하고, `sshd`를 재시작하기 전에 `sudo sshd -t`로 검증합니다. 설정이 깨지면 유일한 접속 경로를 잃습니다. Kamal은 기본으로 키를 써서 root로 SSH 접속하므로 키 전용으로 잠그면 비밀번호를 쓰던 다른 자동화가 끊깁니다.
- 다시 만들 수 없는 것을 백업합니다. named volume 또는 데이터베이스 자체 덤프, `.kamal/secrets`, 패널의 `.env`(Coolify는 `/data/coolify/source/.env`를 요구합니다), 프록시의 인증서 저장소입니다. 한 번도 복원해 보지 않은 백업은 추측입니다.
- 작은 프로덕션 호스트에서는 빌드를 분리합니다. CI에서 빌드해 레지스트리에 푸시하고 호스트는 풀해서 실행만 합니다.

## Diagnosis Order

다음 순서로 읽고 원인이 보이면 멈춥니다.

1. 지금 무엇이 서비스 중인가: `kamal app version`이나 `kamal details`, `docker compose ps`, 또는 패널의 현재 배포 상태입니다. 실패한 배포는 대개 이전 버전을 그대로 둡니다.
2. 실패한 시도의 배포 로그: Coolify나 Dokploy의 배포 로그, `kamal deploy -v` 출력, `docker compose` 출력입니다.
3. 호스트의 컨테이너 상태와 헬스: `docker ps -a`, `docker inspect --format '{{.State.Health.Status}} {{.State.ExitCode}}'`, 그다음 `docker logs <container> --tail 200`입니다.
4. 프록시 경로: `kamal proxy logs`, `docker logs coolify-proxy --tail 50`, `journalctl -u caddy -n 100`, TLS와 리다이렉트 사슬을 보는 `curl -I https://<host>`입니다.
5. 네트워크 내부에서: `docker exec <container> curl -fsS localhost:<port>/health`, 그다음 외부에서 `curl -fsS https://<host>/health`입니다.
6. 위에서 설명되지 않으면 호스트 자원: `df -h`, `free -m`, `dmesg -T | grep -i -E 'oom|killed process'`입니다.

롤백보다 수정과 재배포가 먼저입니다. 실패한 배포는 대개 아무것도 교체하지 않았습니다. 같은 원인에 대한 재배포를 시도 1회로 세고 최대 3회까지 갑니다.

## Failure Table

| # | 증상 | 원인 | 수정 | 확인 |
|---|---|---|---|---|
| 1 | 프록시가 502/503, `Connection refused`, Coolify `No available server` | 앱이 `localhost`나 `127.0.0.1`에만 바인드 | `0.0.0.0`에 바인드하고 내부 포트를 프록시와 헬스체크에 맞춤 | `docker exec <c> curl -fsS localhost:<port>/health`가 0을 돌려주고 공개 URL이 200 |
| 2 | 502, 헬스체크 unhealthy, 앱 오류 없음 | 앱, `proxy.app_port`, Coolify `Ports Exposes`, compose `expose` 사이의 포트 불일치 | 한 곳에서 포트를 고치고 재배포 | `docker port <c>`, 공개 URL 200 |
| 3 | `(unhealthy)`, 헬스체크 종료 코드 `127` | 최종 이미지에 `curl`이나 `wget`이 없음 | 이미지에 하나를 설치하거나 명령 체크로 바꿈 | `docker exec <c> curl -f localhost:<port>/health; echo $?`가 0 |
| 4 | `deploy_timeout`/`StartPeriod`에서 배포 타임아웃 | 느린 기동, 잘못된 경로, 짧은 준비 대기 | 기동 로그 시간을 확인한 뒤 `readiness_delay`, `deploy_timeout`, `start_period`를 올림 | 배포가 끝나고 `GET /up`이 200 |
| 5 | `DATABASE_URL is not set`, 인증 실패, 빈 변수 | `.kamal/secrets`, 패널 환경, compose 환경에 시크릿이 빠졌거나 재배포 없이 값만 설정 | 해당 경로가 읽는 원본에 값을 넣고 재배포 | 앱 로그에 값이 로드되고 스모크 요청 통과 |
| 6 | `no buildpack`, `start command not found` | 빌더 자동 감지가 잘못된 전략을 고름 | `Dockerfile`을 커밋하고 빌드를 그쪽으로 지정 | 배포 로그에 Dockerfile 빌드 단계 |
| 7 | `exec format error`, `no matching manifest` | 잘못된 아키텍처로 빌드한 이미지 | `--platform linux/amd64`로 빌드하거나 `builder.arch` 설정, 로컬 기계가 다르면 `builder.remote` 사용 | `docker inspect --format '{{.Architecture}}' <image>`가 호스트와 일치 |
| 8 | 종료 코드 137, `Killed process`, `Out of memory` | 메모리 한도나 호스트 메모리 고갈. 호스트에서 빌드할 때 흔함 | 메모리를 올리거나 빌드를 CI로 옮김. Dokploy는 빌드 서버 분리를 권장 | 재배포 후 `docker stats`가 안정 |
| 9 | 배포 로그의 마이그레이션 오류, 크래시 루프 | 릴리스 안에서 마이그레이션이 실행되다 중간에 실패 | 하위 호환 스키마로 별도 릴리스 단계로 분리 | 앱이 기동하고 스키마 버전이 기대값 |
| 10 | `no space left on device` | 이미지, 빌드 캐시, 정지한 컨테이너가 누적 | `docker image prune`, `kamal prune`, 패널의 Docker 정리 | `df -h`에 여유 |
| 11 | ACME 챌린지 실패, `NXDOMAIN`, 인증서 미발급 | DNS가 호스트를 가리키지 않거나 80/443이 닫혔거나 전파 대기. 와일드카드에 DNS-01 누락 | A/AAAA를 바로잡고 포트를 열고 기다린 뒤 와일드카드에는 DNS-01 추가 | `dig +short A <host>`, `curl -vI https://<host>`가 유효한 사슬을 보여 줌 |
| 12 | ufw가 막는 포트가 인터넷에서 응답 | Docker가 `0.0.0.0`에 게시하고 ufw `INPUT`보다 먼저 라우팅 | `127.0.0.1`에 바인드하거나 `DOCKER-USER`에서 필터 | 외부에서 `nc -z <host> <port>`가 실패 |
| 13 | 프록시 로그의 `client version 1.24 is too old` | 프록시의 Docker 클라이언트가 데몬 API보다 오래됨 | 데몬 API를 지원하는 프록시 릴리스로 업그레이드 | 프록시 로그에 오류가 없고 URL이 200 |
| 14 | 배포가 잠금 메시지와 함께 즉시 실패 | 다른 배포가 Kamal 잠금을 쥐고 있음 | `--lock-wait-timeout`을 조정해 `kamal deploy --lock-wait` 실행 | 배포가 완료 |

## Approval Required

| 동작 | 등급 |
|---|---|
| 상태, 배포 로그, 컨테이너 상태와 헬스, 프록시 로그 읽기, `kamal app version`, `kamal details`, `kamal app logs`, `docker compose ps`, `curl` 확인, 저장소의 `config/deploy.yml`이나 compose 파일 편집 | proceed |
| 비프로덕션 환경의 `kamal setup`, `kamal deploy`, `kamal redeploy`, Coolify나 Dokploy 배포 트리거, `docker rollout`, systemd 재시작 | proceed |
| 같은 명령을 프로덕션에서 실행 | named environment |
| `kamal rollback`, 패널 롤백, `kamal remove`, `kamal accessory remove`, `docker compose down -v`, `docker volume rm`, `docker system prune --volumes`, 실제 데이터에 대한 스키마 다운 마이그레이션이나 복원, 볼륨이나 데이터베이스 삭제, DNS 레코드 변경, 방화벽 규칙 변경, 3000 포트의 패널 접근 차단(`docker service update --publish-rm`), 레지스트리 태그 덮어쓰기 | explicit approval |
| 로그인, 계정이나 프로젝트 생성, 전역 CLI 설치, 토큰이나 `kamal config` 출력을 채팅이나 보고서에 남기기 | never |

모든 롤백 제안은 무엇을 되돌리는지(이미지)와 데이터베이스, 볼륨, 마이그레이션, 연결된 리소스는 되돌아가지 않는다는 점을 함께 밝힙니다. 승인은 그것이 지목한 동작 하나만 덮습니다.

## Checked

> 자주 바뀝니다. 2026-11-07에 아래 출처로 확인했습니다. 결정이 플래그나 기본값, 플러그인에 달려 있으면 실제 페이지를 다시 읽습니다.

| Fact | Value |
|---|---|
| Kamal 최신 릴리스 | v2.12.0(2026-06-18) |
| Kamal 프록시 | Kamal 2에서 `kamal-proxy`가 Traefik을 대체했고 `app_port` 기본값은 80 |
| Kamal 준비 판정 | `/up`을 1초에 한 번 요청. `readiness_delay` 7초, `deploy_timeout` 30초, `retain_containers` 5 |
| Kamal 롤백 창 | 구 컨테이너는 기본 3일 뒤 정리 |
| Kamal 잠금 대기 | `--lock-wait-timeout` 900초, `--lock-wait-interval` 15초 |
| Coolify 헬스체크 | HTTP 체크가 컨테이너 안에서 실행되며 이미지에 `curl`이나 `wget`이 필요 |
| Coolify 배포 API | `GET` 또는 `POST /api/v1/deploy`, `deploy` 권한의 `Bearer` 토큰. 수락은 healthy가 아님 |
| Dokploy 기본 교체 | stop-then-start. Swarm 헬스체크와 `start-first`가 없으면 Bad Gateway |
| Dokploy API | `x-api-key`, `applicationStatus`/`composeStatus`가 `idle`, `running`, `done`, `error` |
| Dokploy 백업 | named volume만 가능하고 `../files` 바인드 마운트는 불가 |
| Docker와 ufw | 게시 포트는 `nat` 테이블을 거쳐 ufw `INPUT` 체인을 우회 |
| Traefik 기본값 | `exposedByDefault: true` |
| Caddy 자동 HTTPS | A/AAAA와 열린 80/443, 쓰기 가능한 데이터 디렉터리 |
| `docker rollout` | 프록시가 필요하고 대상 서비스의 `container_name`과 `ports`를 거부 |

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| Kamal은 SSH로 root에 키 인증으로 접속하고 Docker를 설치하며 레지스트리가 필요 | <https://kamal-deploy.org/docs/installation/> |
| `GET /up`이 `200 OK`일 때 트래픽을 전환하며 그 순서가 배포 순서 | <https://kamal-deploy.org/docs/commands/deploy/> |
| `/up`을 배포 타임아웃까지 1초마다 요청, `healthcheck` 경로와 간격, `app_port` 기본 80, SSL은 서버 하나와 `host` 필요 | <https://kamal-deploy.org/docs/configuration/proxy/> |
| 모르는 키 거부, `config/deploy.<destination>.yml` 병합, `readiness_delay`·`deploy_timeout`·`drain_timeout`·`stop_timeout`·`retain_containers` 기본값 | <https://kamal-deploy.org/docs/configuration/overview/> |
| 액세서리는 배포로 갱신되지 않고 무중단 배포가 없음 | <https://kamal-deploy.org/docs/configuration/accessories/> |
| 로컬 아키텍처와 맞지 않는 빌드에 `builder.arch`와 `builder.remote` 사용 | <https://kamal-deploy.org/docs/configuration/builders/> |
| 시크릿이 `.kamal/secrets`로 이동했고 `.env`는 더 이상 읽히지 않음 | <https://kamal-deploy.org/docs/upgrading/secrets-changes/> |
| Kamal 2에서 Traefik이 `kamal-proxy`로 대체됨 | <https://kamal-deploy.org/docs/upgrading/overview/> |
| `kamal rollback <sha>`, 구 컨테이너는 기본 3일 뒤 정리 | <https://kamal-deploy.org/docs/commands/rollback/> |
| `kamal app logs`, `app details`, `app version`, `app containers` | <https://kamal-deploy.org/docs/commands/app/> |
| `--lock-wait`, `--lock-wait-timeout` 900, `--lock-wait-interval` 15. 직접 잡은 잠금은 기다리지 않음 | <https://kamal-deploy.org/docs/commands/lock/> |
| `kamal config`는 시크릿을 포함한 병합 설정을 출력 | <https://kamal-deploy.org/docs/commands/view-all-commands/> |
| Kamal 최신 릴리스 v2.12.0(2026-06-18 게시) | <https://api.github.com/repos/basecamp/kamal/releases/latest> |
| Coolify는 SSH로 접속해 서버를 Docker 워크로드용으로 준비 | <https://coolify.io/docs/core/what-is-coolify> |
| Bearer 토큰 형식, `deploy` 권한, API 접근 스위치, 401과 403의 의미 | <https://coolify.io/docs/api/authorization> |
| 배포 웹훅 URL 형식, `uuid`/`tag`/`force`, 수락된 요청은 헬스의 증거가 아님 | <https://coolify.io/docs/core/automation/deploy-webhooks> |
| 소스 빌드 실패는 현재 버전을 그대로 두고, 롤링과 stop-then-start의 조건이 다름 | <https://coolify.io/docs/core/build-deployment-model> |
| HTTP 체크는 컨테이너 안에서 실행되고 이미지에 `curl`이나 `wget`이 필요 | <https://coolify.io/docs/applications/configuration/health-checks> |
| `No available server`의 원인: 포트 불일치, unhealthy 컨테이너 등 | <https://coolify.io/docs/troubleshoot/applications/no-available-server> |
| 롤백은 이전 이미지를 배포하며 마이그레이션 반전과 영속 스토리지 복원은 하지 않음 | <https://coolify.io/docs/applications/deployments/rollbacks> |
| `/data/coolify/source/.env` 백업 | <https://coolify.io/docs/start-with-self-hosted> |
| Dokploy 포트 80, 443, 3000과 설치 요구 사항, Docker Swarm 토대 | <https://docs.dokploy.com/docs/core/installation> |
| `/settings/profile`에서 API 토큰 생성, `x-api-key` 헤더 | <https://docs.dokploy.com/docs/api> |
| `application.deploy`는 `applicationId`를 받고 `application.one`과 `applicationStatus` 값이 있음 | <https://docs.dokploy.com/docs/api/application> |
| 기본 배포가 실행 중인 컨테이너를 먼저 멈춰 Bad Gateway가 나며 무중단에는 Swarm 헬스체크가 필요 | <https://docs.dokploy.com/docs/core/applications/zero-downtime> |
| 프로덕션에서 헬스체크와 `FailureAction: rollback`, `Order: start-first` 사용 | <https://docs.dokploy.com/docs/core/applications/going-production> |
| named volume은 Volume Backups로 백업되고 `../files` 바인드 마운트는 안 되며 절대 호스트 경로는 배포 시 정리됨 | <https://docs.dokploy.com/docs/core/docker-compose> |
| Swarm 자동 롤백과 레지스트리 기반 수동 롤백 | <https://docs.dokploy.com/docs/core/applications/rollbacks> |
| `composeStatus` 값 `idle`, `running`, `done`, `error` | <https://docs.dokploy.com/docs/api/compose> |
| 자동 HTTPS의 전제 조건과 HTTP에서 HTTPS로의 리다이렉트 | <https://caddyserver.com/docs/automatic-https> |
| 활성 헬스체크와 재시도에 쓰는 `health_uri`, `health_interval`, `lb_try_duration` | <https://caddyserver.com/docs/caddyfile/directives/reverse_proxy> |
| Docker 프로바이더 라벨과 `exposedByDefault` 기본값 `true` | <https://doc.traefik.io/traefik/reference/install-configuration/providers/docker/> |
| HTTP-01은 80, TLS-ALPN-01은 443으로 Let's Encrypt가 호스트에 닿아야 함 | <https://doc.traefik.io/traefik/reference/install-configuration/tls/certificate-resolvers/acme/> |
| 게시 포트는 `nat` 테이블에서 ufw `INPUT` 체인보다 먼저 라우팅됨 | <https://docs.docker.com/engine/network/packet-filtering-firewalls/> |
| `DOCKER-USER`가 Docker 자체 accept 규칙보다 먼저 처리되고 Docker 체인은 고치지 않아야 함 | <https://docs.docker.com/engine/network/firewall-iptables/> |
| 주소 없이 게시하면 모든 인터페이스에 바인드되며 ufw가 포트를 막아도 열림 | <https://docs.docker.com/reference/cli/docker/container/run/> |
| Docker 데몬을 조종할 수 있는 사람은 호스트 root 권한을 가짐 | <https://docs.docker.com/engine/security/protect-access/> |
| ufw는 처음에 비활성이고 `ufw status verbose`로 확인 | <https://documentation.ubuntu.com/server/how-to/security/firewalls/> |
| 기본이 키 기반 SSH 인증이고 재시작 전 `sshd -t`로 검증 | <https://documentation.ubuntu.com/server/how-to/security/openssh-server/> |
| 종료 상태 137은 `SIGKILL` | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| `docker rollout`은 확장, 대기, 구 컨테이너 제거 순서이며 `container_name`, `ports`, 프록시 제약과 드레인 훅이 있음 | <https://raw.githubusercontent.com/wowu/docker-rollout/master/README.md> |
| 장기 실행 서비스에는 `Type=exec` 권장 | <https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html> |

### Evidence grade

모든 벤더 주장은 `SECONDARY`입니다. 2026-11-07에 각 게시자의 문서에서 인용했고, 이 가이드의 어떤 명령도 이 환경의 실제 서버에서 실행하지 않았습니다. 같은 페이지가 표 값으로 명시한 Caddy, Docker, Traefik 기본값(`app_port` 80, `exposedByDefault` true, ufw 비활성)만 `DIRECT`입니다. sshd 지시문(`PasswordAuthentication no`, `PermitRootLogin prohibit-password`)은 `[INFERENCE]`입니다. Ubuntu 문서는 키 기반 인증과 `sshd -t`를 다루지만 그 두 줄은 인용하지 않으므로 관행으로 다루고, 접속을 잠그기 전에 호스트에서 확인합니다. `applicationStatus`를 넘어서는 패널 배포 상태 폴링은 `UNVERIFIED`입니다. Coolify와 Dokploy 모두 최종 배포 결과를 헬스 판정과 함께 돌려주는 엔드포인트를 문서화하지 않으므로, 실행은 그 한계를 밝히고 패널의 배포 기록을 읽습니다. Docker와 ufw 관련 사실은 Docker 문서가 ufw `INPUT` 우회를 명시하고 `DOCKER-USER` 체인을 제시한다는 점에 근거하며, 실제 호스트에서 규칙을 시험하지는 않았습니다.
