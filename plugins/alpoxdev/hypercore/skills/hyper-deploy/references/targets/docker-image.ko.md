# Docker Image

배포 신호가 `Dockerfile` 하나뿐인 저장소를 위한 대상 가이드입니다. 이미지를 빌드해 레지스트리에 푸시하고, 푸시된 매니페스트와 실행 중인 컨테이너를 증거로 확인합니다. `rules/target-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. `compose.yaml`도 함께 있으면 Compose 가이드가 실행을 맡고 이 가이드는 빌드만 제공합니다.

## Contents

- Canonical Configuration
- Authentication
- Build And Push
- Success Test
- Status And Logs
- Failure Table
- Approval Required
- Checked
- Sources

## Canonical Configuration

멀티스테이지 `Dockerfile` 하나가 빌더 스테이지에서 산출물을 만들고 그 산출물만 최소 런타임 스테이지로 복사합니다. 여기서는 이미지가 납품물이므로 런타임 스테이지가 계약 전체를 집니다. 베이스 고정, 비root 사용자, exec form 명령, 헬스 프로브, `.dockerignore`로 좁힌 빌드 컨텍스트입니다.

```dockerfile
# syntax=docker/dockerfile:1

FROM node:22.20.0-bookworm-slim@sha256:0000000000000000000000000000000000000000000000000000000000000000 AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY . .
RUN npm run build

FROM gcr.io/distroless/nodejs22-debian12:nonroot@sha256:0000000000000000000000000000000000000000000000000000000000000000 AS runtime
WORKDIR /app
COPY --from=build --chown=nonroot:nonroot /src/dist ./dist
COPY --from=build --chown=nonroot:nonroot /src/node_modules ./node_modules
USER nonroot:nonroot
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD ["/nodejs/bin/node", "-e", "fetch('http://127.0.0.1:3000/healthz').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
ENTRYPOINT ["/nodejs/bin/node", "dist/server.js"]
```

| Rule | Why it is in the template |
|---|---|
| `# syntax=docker/dockerfile:1` on line 1 | BuildKit 프런트엔드를 고정합니다. 캐시·시크릿 마운트가 번들 프런트엔드로 되돌아가지 않고 모든 기기에서 같게 동작합니다 |
| Base pinned by tag **and** digest | 태그는 가변값이고 digest가 검토된 바이트입니다. 갱신 경로를 위해 사람이 읽는 태그를 옆에 둡니다 |
| Named builder stage plus a minimal runtime stage | 툴체인, 소스, 개발 의존성이 남습니다. 최종 이미지에는 빌드 산출물만 들어갑니다 |
| `COPY --from=build --chown=…` | `USER`가 권한을 내리기 전에 런타임 파일 소유자를 비root 사용자로 맞춥니다 |
| `USER` with an explicit uid or name | 프로세스가 권한 없이 시작합니다. 그룹을 지정하면 다른 그룹 멤버십이 모두 무시되고, 주 그룹이 없는 이미지는 `root` 그룹으로 실행됩니다 |
| `ENTRYPOINT`/`CMD` in exec form | shell form은 `/bin/sh -c`의 자식이 되어 앱이 PID 1이 아니고 `SIGTERM`을 받지 못합니다. `JSONArgsRecommended`가 이걸 잡습니다 |
| `HEALTHCHECK` with `--start-period` | `start-period` 중 실패는 `--retries`에 누적되지 않습니다. 느린 기동이 `unhealthy`로 잘못 찍히는 것을 막습니다 |
| `.dockerignore` next to the `Dockerfile` | 비밀, `.git`, `node_modules`, 빌드 산출물을 컨텍스트 밖으로 둡니다. `COPY . .`가 그것들을 실어 보낼 수 없습니다 |

digest 고정의 갱신 경로는 선택이 아니라 한 쌍입니다. 봇이 주기적으로 digest를 다시 쓰고(Dependabot의 `package-ecosystem: docker`, 또는 제안 베이스를 보는 `docker scout recommendations`), 사람이 diff를 검토합니다. 베이스만 새로 받는 것은 `docker build --pull`이고 전 단계를 다시 도는 것은 `--no-cache`이며, 둘은 다른 문제를 풉니다.

`.dockerignore`에는 최소 `**/.git`, `**/node_modules`, `**/.env`, `**/.env.*`, `dist`, `build`, 테스트 픽스처 디렉터리를 넣습니다. `COPY` 제외를 추가하기 전에 컨텍스트를 먼저 좁히십시오. 무시된 파일을 뒤의 `COPY`가 지목하면 이미지가 작아지는 게 아니라 빌드 체크 위반이 됩니다.

푸시한 뒤가 아니라 빌드 전에 파일을 검사합니다.

```sh
docker build --check .
```

`--check`는 빌드 체크 묶음의 위반을 보고하고 위반이 하나라도 보고되면 0이 아닌 코드로 끝나므로 게이트입니다. `SecretsUsedInArgOrEnv`와 `JSONArgsRecommended`가 이 묶음에서 나옵니다. 둘 다 레지스트리 푸시 뒤보다 여기서 고치는 편이 쌉니다.

## Authentication

토큰을 표준 입력으로 넘겨 비대화형으로 로그인합니다. `-p`로 넘긴 토큰은 셸 히스토리와 프로세스 목록에 남으므로 쓰지 않습니다.

```sh
printf '%s' "$TOKEN" | docker login <registry> -u <user> --password-stdin
```

자격 증명이 있는지는 출력 없이 확인하고, 그 값을 로그인에 넘깁니다.

```sh
[ -n "${GHCR_TOKEN:-}" ] && echo ghcr-token-set
printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u <github-user> --password-stdin
```

| Registry | Credential | Note |
|---|---|---|
| GHCR | 워크플로 안에서는 `GITHUB_TOKEN`, 그 밖에는 `read:packages` / `write:packages` 권한의 PAT | 첫 푸시가 **비공개** 패키지를 만듭니다. `LABEL org.opencontainers.image.source=https://github.com/<owner>/<repo>`를 넣어 패키지가 저장소로 연결되게 합니다 |
| Docker Hub | 계정 비밀번호가 아니라 PAT 또는 OAT | 2FA·SSO 계정은 CLI에서 비밀번호를 거부합니다. OAT는 저장소 범위로 제한하고 계정 사용량과 분리할 수 있습니다 |

자격 증명은 `~/.docker/config.json`에 기본 base64로 남거나 `osxkeychain`, `secretservice`, `wincred`, `pass` 같은 `credsStore` / `credHelpers`에 들어갑니다. 헬퍼를 쓰십시오. 대신 로그인하지 않습니다. 자격 증명이 없으면 이 단계에서 멈추고 정확한 명령을 보고합니다.

## Build And Push

이미지를 실행할 호스트의 아키텍처로 빌드하고 같은 명령에서 푸시합니다. arm64 기기에서 `docker build`만 하면 arm64 이미지가 만들어지고 그 이미지는 amd64 서버에서 실패합니다.

```sh
SHA=$(git rev-parse --short HEAD)
IMG=<registry>/<owner>/<image>:$SHA

docker buildx build \
  --platform linux/amd64 \
  --secret id=npmrc,src="$HOME/.npmrc" \
  --tag "$IMG" \
  --tag <registry>/<owner>/<image>:latest \
  --push .
```

| Choice | Rule |
|---|---|
| Platform | 런타임이 amd64 서버 하나뿐이면 `--platform linux/amd64`, 양쪽에서 돌아야 하면 `--platform linux/amd64,linux/arm64`입니다. 기본 짝이 아니라 실제 런타임 요구마다 하나씩 정합니다 |
| Tag | 배포 태그는 git SHA입니다. `latest`는 사람용으로 함께 붙일 수 있지만 배포가 고정하는 태그가 아닙니다. 롤백이 가리키는 것은 불변 digest입니다 |
| Secrets | `--secret id=…,src=…`가 값을 필요한 `RUN` 하나에만 `/run/secrets/<id>`로 마운트합니다. `ARG`와 `ENV`는 `docker history`와 provenance attestation에 남으므로 토큰을 그 길로 보내지 않습니다 |
| Output | 출력은 `--push`입니다. `docker-container` 드라이버는 결과를 로컬 이미지 저장소에 적재하지 않으므로 `--push`나 `-o`가 없는 빌드는 로컬에 검사할 것을 남기지 않습니다 |
| Cache | 패키지 관리자·컴파일러 캐시에는 `--mount=type=cache`를 씁니다. `target=`으로 경로를 지정해 두 스테이지가 실수로 같은 경로를 공유하지 않게 합니다 |
| Verification of the build | `docker build --check .`를 먼저 돌리고 그다음 이 푸시를 합니다. 체크 실패를 푸시로 넘기지 않습니다 |

빌더를 직접 만들어야 할 때(구버전 엔진, 기본 빌더가 없는 CI) 푸시 요구가 함정입니다.

```sh
docker buildx create --name container-builder --driver docker-container --bootstrap --use
docker buildx build --platform linux/amd64 --tag "$IMG" --push .
```

사설 Git 컨텍스트는 별도 시크릿 형식을 씁니다. 사용자명 `x-access-token`의 Basic 인증은 `--secret id=GIT_AUTH_TOKEN`, GitLab `CI_JOB_TOKEN`처럼 임의 헤더는 `--secret id=GIT_AUTH_HEADER`입니다. 호스트별로는 호스트 이름을 id에 붙입니다. 예를 들어 `id=GIT_AUTH_TOKEN.github.com,env=GITHUB_TOKEN`입니다.

## Success Test

성공은 푸시된 매니페스트가 런타임 플랫폼을 나열하고, 그 아키텍처의 호스트에서 이미지가 시작해 자체 헬스 프로브를 통과하는 것입니다.

```sh
docker buildx imagetools inspect <registry>/<owner>/<image>:$SHA
docker run --rm --platform linux/amd64 <registry>/<owner>/<image>:$SHA
docker image inspect -f '{{.Os}}/{{.Architecture}}' <registry>/<owner>/<image>:$SHA
```

- `imagetools inspect`는 매니페스트 항목마다 `Platform:` 줄을 하나씩 냅니다. 그 목록에 `linux/amd64`가 있어야 하고, 태그에 붙은 추가 플랫폼은 모두 런타임이 실제로 가진 것이어야 합니다.
- 푸시가 `0`으로 끝난 것은 바이트가 접수됐다는 뜻이지 매니페스트 플랫폼이 맞다는 뜻이 아닙니다. 매니페스트를 읽으십시오.
- 대상 호스트에서는 `uname -m`이 실행 가능 여부를 정합니다. `x86_64`는 `linux/amd64`, `aarch64`는 `linux/arm64`가 필요합니다.
- 빌드 기기에서의 로컬 `docker run`은 에뮬레이션을 타고 통과해 잘못된 플랫폼을 숨길 수 있습니다. 런타임 아키텍처에서 확인하거나 받아온 이미지의 `.Architecture`를 읽으십시오.
- 헬스는 `docker inspect`에서 컨테이너가 `healthy`에 도달하고 프로브 명령이 `0`을 반환해야 합니다. 헬스체크 없이 `running`인 컨테이너는 프로세스가 시작했다는 것만 증명합니다.

## Status And Logs

| Question | Command |
|---|---|
| Manifest platforms and sizes | `docker buildx imagetools inspect <image>:<tag>` |
| What was built and when | `docker image inspect -f '{{.Created}} {{.Os}}/{{.Architecture}}' <image>` |
| Container state, exit code, health | `docker inspect -f '{{.State.Status}} {{.State.ExitCode}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' <container>` |
| Last health probe output | `docker inspect -f '{{json .State.Health}}' <container>` |
| Bounded runtime log | `docker logs --tail 200 --timestamps <container>` |
| Build log of one stage | `docker buildx build --progress=plain --target <stage> .` |
| Registry tags and digests | `docker buildx imagetools inspect <image>` |
| Exit 137 containers | `docker ps -a --filter 'exited=137' --format '{{.Names}} {{.Status}}'` |

모든 로그 명령에 `--tail`이나 시간 범위가 붙고, 흐르는 채로 두는 명령은 없습니다. `State.Health.Log`는 마지막 프로브 출력(최대 4096바이트)을 남기므로 `curl: not found`나 `connection refused`를 아무것도 다시 돌리지 않고 볼 수 있습니다.

종료 코드가 해석을 정합니다. 장기 실행 서비스의 `0`은 명령이 포그라운드가 아니었다는 뜻이고, `137`은 OOM 강제 종료나 정지 시간 초과로 인한 SIGKILL이며, `143`은 정상 SIGTERM 정지입니다. `running`인데 `unhealthy`이면 프로세스가 아니라 프로브가 틀린 것입니다.

## Failure Table

| # | Signature | Cause | Fix | Check | Tier | Source |
|---|---|---|---|---|---|---|
| 1 | 컨테이너 시작 시 `exec format error`, 줄에 `standard_init_linux.go` | 빌드 기기 아키텍처로 이미지를 만들어 다른 아키텍처 호스트로 푸시함 | `--platform linux/amd64`(또는 호스트 플랫폼)로 다시 빌드해 같은 태그를 푸시하고 호스트에서 받음 | `imagetools inspect`가 런타임 플랫폼을 나열하고 컨테이너가 시작함 | proceed | <https://docs.docker.com/build/building/multi-platform/> |
| 2 | `no matching manifest for linux/amd64 in the manifest list entries` | 아키텍처 하나만 푸시해 받는 호스트와 맞는 매니페스트 항목이 없음 | 빠진 플랫폼을 빌드·푸시하거나 멀티플랫폼 태그를 만듦 | 호스트에서 같은 `docker pull`이 성공함 | proceed | <https://docs.docker.com/build/building/multi-platform/> |
| 3 | `docker history`, `ARG`/`ENV` 줄, provenance attestation에 토큰이나 비밀번호가 보임 | 시크릿 마운트 대신 `ARG`나 `ENV`로 비밀을 넘김 | `RUN --mount=type=secret`으로 옮기고 빌드 시 `--secret`을 넘김. 그 자격 증명은 유출로 보고 교체함 | `docker history --no-trunc <image>`에 비밀이 없고 `--check`가 `SecretsUsedInArgOrEnv`를 보고하지 않음 | explicit approval (rotating the credential) | <https://docs.docker.com/build/building/secrets/>, <https://docs.docker.com/reference/build-checks/> |
| 4 | `failed to compute cache key: "/app/x" not found`, 또는 `COPY`가 파일을 조용히 빠뜨림 | `.dockerignore`가 제외한 파일을 `COPY`가 지목했거나 경로가 다른 스테이지 기준임 | `.dockerignore` 패턴이나 `COPY` 경로를 고침. 컨텍스트는 좁게, 복사는 명시적으로 유지함 | `docker build --check .`가 `CopyIgnoredFile`을 보고하지 않고 빌드가 경로를 해석함 | proceed | <https://docs.docker.com/reference/build-checks/> |
| 5 | 런타임에 `Cannot find module`, `no such file`, 또는 빈 디렉터리 | 산출물이 빌더 스테이지에 남았거나 `COPY --from`이 다른 스테이지나 경로를 지목함 | 이름 붙인 빌더 스테이지에서 산출물을 런타임 스테이지로 복사하고 빌더 안 경로를 확인함 | 최종 이미지에 파일이 있음: `docker run --rm <image> ls <path>` | proceed | <https://docs.docker.com/build/building/multi-stage/> |
| 6 | 쓰기, 1024 미만 포트 바인드, 캐시 디렉터리에서 `permission denied` | `USER`가 없거나 파일을 root로 복사해 런타임 사용자가 쓸 수 없음 | `COPY --chown=<user>:<group>`을 쓰고 `USER` 전에 쓰기 가능한 디렉터리를 만들며 비특권 포트에 바인드함 | 컨테이너가 비root 사용자로 실행되며 상태 경로에 씀 | proceed | <https://docs.docker.com/reference/dockerfile/> |
| 7 | 푸시가 10분 근처에서 멈췄다가 실패하거나 레지스트리가 레이어를 거부함 | 레이어 하나가 레지스트리의 레이어 크기 한도를 넘었거나 느린 회선에서 업로드 창이 닫힘 | 레이어를 나누고 산출물을 줄이며 좁은 회선에서는 `--max-concurrent-uploads`를 낮춤 | 푸시가 끝나고 `imagetools inspect`에 새 digest가 보임 | proceed | <https://docs.docker.com/reference/cli/docker/image/push/>, <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry> |

## Approval Required

| Action | Tier |
|---|---|
| 매니페스트, 이미지 설정, 컨테이너 상태, 헬스 로그, 빌드 체크 출력 읽기. 로컬 태그로 `docker build`, 저장소의 `Dockerfile`이나 `.dockerignore` 수정 | proceed |
| 레지스트리에 새 태그 푸시 | proceed |
| 실행 중인 배포가 고정한 기존 태그에 푸시, 이미 배포된 digest의 태그를 다시 푸시(태그를 덮어씀) | explicit approval |
| 레지스트리에서 이미지나 태그 삭제(`docker buildx imagetools` 제거, 레지스트리 삭제 호출), 레지스트리 정리, 배포가 아직 쓰는 로컬 이미지 삭제 | explicit approval |
| 대신 로그인, 레지스트리 계정이나 패키지 생성, 토큰 출력, 채팅에서 토큰 값 요구 | never |

승인은 그 승인이 지목한 동작 하나만 덮습니다. 태그 하나를 덮어쓰는 승인은 두 번째 환경의 태그를 덮지 않고, 이미지 하나를 지우는 승인은 배포가 고정한 태그를 덮지 않습니다.

## Checked

> Volatile. Checked 2026-11-07; re-read the live page when a flag, a limit, or a digest decides the run.

| Fact | Value |
|---|---|
| Docker Engine | 27.3.1, 2026-11-07에 로컬 실행 |
| Compose | v2.30.3 (`up --wait --wait-timeout --no-deps --force-recreate --remove-orphans`) |
| buildx | v0.18.0, `docker-container` 드라이버 사용 가능 |
| Build checks | `docker build --check`는 보고된 위반이 있으면 0이 아닌 코드로 종료 |
| Digest form | `image:tag@sha256:…`, 갱신 경로를 위해 태그는 유지 |
| GHCR limits | 레이어당 10GB, 업로드 10분 |
| Push concurrency | 기본 5레이어 동시 업로드, `--max-concurrent-uploads`로 낮춤 |
| Health check defaults | `interval` 30s, `timeout` 30s, `start-period` 0s, `start-interval` 5s, `retries` 3 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Pin the base image version to a specific digest for supply-chain traceability | <https://docs.docker.com/build/building/best-practices/> |
| Build arguments are not recommended for passing secrets | <https://docs.docker.com/reference/dockerfile/> |
| Secrets passed as `ARG`/`ENV` persist in the final image; use secret mounts | <https://docs.docker.com/build/building/secrets/> |
| Multi-stage builds leave the toolchain and unwanted files behind, and `--target` selects a stage | <https://docs.docker.com/build/building/multi-stage/> |
| A `linux/amd64` container cannot run on an arm64 host without emulation | <https://docs.docker.com/build/building/multi-platform/> |
| `--check` exits non-zero when violations are reported | <https://docs.docker.com/build/checks/> |
| `SecretsUsedInArgOrEnv` and `CopyIgnoredFile` are build-check rules | <https://docs.docker.com/reference/build-checks/> |
| `docker login` with `--password-stdin` keeps the password out of shell history | <https://docs.docker.com/reference/cli/docker/login/> |
| GHCR login form, private default visibility, `org.opencontainers.image.source` label, 10 GB per layer, 10-minute timeout | <https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry> |
| `docker image push` uploads five layers at a time by default | <https://docs.docker.com/reference/cli/docker/image/push/> |
| `--push` is shorthand for `--output=type=registry,unpack=false` | <https://docs.docker.com/reference/cli/docker/buildx/build/> |
| `imagetools inspect` lists each platform in the manifest | <https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/> |
| Exit 137 means the container was killed with SIGKILL | <https://docs.docker.com/reference/cli/docker/container/ls/> |
| `HEALTHCHECK` defaults and the meaning of `start-period` for retries | <https://docs.docker.com/reference/dockerfile/> |
| `docker init` writes `.dockerignore`, `Dockerfile`, `compose.yaml`, and overwrites existing files | <https://docs.docker.com/reference/cli/docker/init/> |
| A multi-platform image cannot be loaded into the local image store | <https://docs.docker.com/build/ci/github-actions/multi-platform/> |
| Scout reports vulnerable packages and recommends a base upgrade | <https://docs.docker.com/scout/> |

### Evidence grade

로컬 도구 표면은 `DIRECT`입니다. Docker Engine 27.3.1, Compose v2.30.3, buildx v0.18.0을 2026-11-07에 실행했고 이 가이드의 플래그는 그 바이너리에서 나왔습니다. GHCR의 레이어 크기, 업로드 창, 첫 푸시 가시성처럼 실제 레지스트리에서만 보이는 동작은 `SECONDARY`입니다. Docker와 GitHub의 자체 문서에서 인용했고 이 환경에서 레지스트리에 대해 실행해 검증하지는 않았습니다. 템플릿의 digest는 공개된 이미지가 아니라 0으로 채운 예시입니다. 파일을 쓰기 전에 `docker buildx imagetools inspect`로 실제 digest를 확인하십시오.
