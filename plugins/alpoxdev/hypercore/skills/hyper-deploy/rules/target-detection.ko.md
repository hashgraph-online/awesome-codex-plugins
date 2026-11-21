# 대상 감지

`preflight`를 뺀 모든 실행 시작 때, 대상을 말하기 전에 이 규칙을 사용합니다. 신호 순서, 충돌, 신호가 결정하지 못할 때 허용되는 질문 하나를 소유합니다.

## 1. Signals

대상 루트를 읽고 이 순서로 맞춥니다. 요청이 대상을 지목하지 않으면 맞는 첫 행이 결정합니다.

| Order | Signal file or request fact | Target | Guide |
|---|---|---|---|
| 1 | `.railway/railway.ts`, `.railway/railway.py`, `.railway/railway.go`, `railway.toml`, `railway.json`, 연결된 `.railway/` 디렉터리 | `railway` | `references/targets/railway.md` |
| 2 | `cloudflare.config.ts`(`cf` CLI 경로) 또는 `wrangler.jsonc`, `wrangler.json`, `wrangler.toml`(Wrangler 경로) | `cloudflare` | `references/targets/cloudflare.md` |
| 3 | `config/deploy.yml`(Kamal), 또는 요청에 나온 서버 주소, SSH 호스트, Coolify, Dokploy | `vps` | `references/targets/vps.md` |
| 4 | `compose.yaml`, `compose.*.yaml`, `docker-compose.yml`, `docker-compose.*.yml` | `compose` | `references/targets/compose.md` |
| 5 | 위에 해당하지 않고 `Dockerfile`만 있음 | `docker-image` | `references/targets/docker-image.md` |

판단한 파일과 그것을 결정한 줄이나 키를 대상 줄에 기록합니다.

## 2. Conflicts

- 요청이 대상을 지목하면("Railway에", "to Cloudflare", "VPS로") 파일보다 그 대상이 이깁니다. 지목한 대상에 아직 설정이 없으면 모드는 `setup`입니다.
- 플랫폼 파일 옆의 `Dockerfile`이나 compose 파일은 그 플랫폼의 빌드 입력이지 두 번째 대상이 아닙니다. Railway는 찾은 `Dockerfile`로 빌드하고, Kamal이나 Coolify 서버는 compose나 이미지를 돌립니다.
- compose 파일과 요청의 서버 주소가 함께 있으면 `vps`로 라우팅하고, `references/targets/compose.md`를 두 번째 가이드로 읽습니다.
- 요청에 대상이 없고 플랫폼 파일이 둘이면(예: `railway.toml`과 `wrangler.jsonc`) 둘을 밝히는 질문 하나를 하고, 요청한 앱 경로와 서비스가 맞는 쪽을 권하며, 답이 없으면 그 권고로 계속한다고 밝힙니다.
- 신호도 요청의 대상도 없으면, `setup`에서는 다섯 대상을 나열하고 스택에서 권고를 붙인 질문 하나를 합니다(`Dockerfile`을 쓸 수 있는 서버 앱 → `railway`, 정적이나 엣지 앱 → `cloudflare`). 다른 모드에서는 배포 대상을 찾지 못했다고 보고하고 멈춥니다.

## 3. CLI Check

대상이 정해지면 네트워크나 자격 증명 없이 그 CLI를 확인합니다.

| Target | Check |
|---|---|
| `railway` | `command -v railway && railway --version` |
| `cloudflare` | 프로젝트 로컬 바이너리 먼저: `npx --no-install wrangler --version`, `cf` 경로에서는 `npx --no-install cf --version` |
| `docker-image`, `compose` | `docker --version && docker compose version && docker buildx version` |
| `vps` | Kamal 경로에서는 `command -v kamal && kamal version`, 아니면 `ssh -V` |

없는 CLI는 그 영향과 함께 기록합니다. 실행은 절대 전역 설치를 하지 않고, 설치 명령을 보고하고 그 CLI가 필요한 단계에서 멈춥니다.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Railway는 2026-12-01까지 `railway.toml`이나 `railway.json`을 읽고, 그것을 `.railway/railway.ts` 작성 파일로 교체합니다 | <https://docs.railway.com/config-as-code/reference>, `railway config --help` (railway 5.71.0, 2026-11-07) |
| Railway는 `Dockerfile`을 찾으면 항상 그것으로 빌드합니다 | <https://docs.railway.com/config-as-code/reference> |
| `cloudflare.config.ts`는 공개 베타인 `cf` CLI 설정입니다 | <https://developers.cloudflare.com/cf/projects/cloudflare-config/> |
| 새 Wrangler 프로젝트는 `wrangler.jsonc`를 씁니다 | <https://developers.cloudflare.com/workers/wrangler/configuration/> |
| Kamal은 `config/deploy.yml`을 읽습니다 | <https://kamal-deploy.org/docs/configuration/overview/> |

### Evidence grade

`LOCAL` - 신호 순서와 동점 처리 규칙은 이 패키지의 설계입니다.
