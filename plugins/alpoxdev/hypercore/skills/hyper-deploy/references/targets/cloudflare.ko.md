# Cloudflare Workers

Cloudflare 대상 가이드입니다. Workers와 Static Assets, Workers Builds, Workers Containers를 다룹니다. `rules/target-detection.md`가 이곳으로 라우팅한 뒤 읽습니다. Pages는 이전 대상으로만 나옵니다. Cloudflare가 신규 프로젝트에 Workers를 쓰라고 하므로 이 가이드는 새 Pages 프로젝트를 만들지 않습니다.

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

신규 프로젝트는 Pages가 아니라 Workers와 Static Assets로 시작합니다. Pages 제품 페이지는 Workers가 "most Pages use cases"를 지원하고 기능이 더 넓다며 신규 프로젝트를 Workers로 시작하라고 안내합니다. Pages가 폐기된 것은 아니므로 기존 Pages 프로젝트는 이전하기 전까지 계속 동작합니다.

| 발견한 파일 | 경로 | 명령 |
|---|---|---|
| `wrangler.jsonc` | Wrangler, 신규 프로젝트 권장 | 프로젝트 로컬 `wrangler` |
| `wrangler.json` / `wrangler.toml` | Wrangler, 지원됨 | 프로젝트 로컬 `wrangler` |
| `cloudflare.config.ts` | `cf` CLI, 오픈 베타 | `cf`, Wrangler 금지 |

`cloudflare.config.ts`는 오픈 베타인 `cf` CLI의 설정입니다. 이 경로는 Node.js 22.18 이상이 필요하고 `"type": "module"`을 요구하며 Bun에서는 동작하지 않습니다. 그 프로젝트에 Wrangler를 추가하지 않습니다. Wrangler와 `cf`는 서로 다른 규칙으로 설정을 읽으므로 Wrangler를 더하면 충돌하는 두 번째 도구 체인이 생깁니다.

Wrangler 프로젝트의 최소 설정은 `name`, `main`, `compatibility_date`입니다. 자산만 제공하는 Worker는 `main`을 생략할 수 있고, 그때는 `assets.binding`도 넣지 않습니다. 이름은 영문자, 숫자, 하이픈만 되고 밑줄은 안 되며 255자 이하입니다. `workers.dev` 호스트명을 받으면 63자 이하입니다.

| 목적 | 키 |
|---|---|
| 진입점 | `main` |
| 런타임 | `compatibility_date` (`yyyy-mm-dd`), `compatibility_flags` (`["nodejs_compat"]`) |
| 정적 자산 | `assets.directory`, `assets.binding`, `assets.not_found_handling` (`single-page-application`, `404-page`, `none`), `assets.run_worker_first`(bool 또는 패턴 100개까지) |
| 라우팅 | `routes[]`(`pattern`, `zone_name`, `custom_domain`), `workers_dev`, `preview_urls` |
| 환경 | `env.<name>` |
| 평문 값 | `vars`, `define`(빌드 시점 치환) |
| 시크릿 검사 | `secrets.required` |
| 관측 | `observability.enabled`, `observability.head_sampling_rate`, `observability.logs.invocation_logs` |
| 저장소 바인딩 | `kv_namespaces`, `r2_buckets`, `d1_databases`, `queues`, `services`, `hyperdrive` |
| 실행 | `limits.cpu_ms`(기본 30000, 최대 300000), `upload_source_maps` |
| 컨테이너 | `containers[]`, `durable_objects.bindings`, `exports.<Class>` |

`assets.not_found_handling`의 기본값은 `none`입니다. Pages의 자동 매칭에 기대던 단일 페이지 앱은 이 키를 명시하기 전까지 딥 링크에서 404를 냅니다.

환경은 바인딩과 `vars`를 상속하지 않습니다. `env.staging`은 자기 `kv_namespaces`, `d1_databases`, `vars`를 직접 선언해야 하고, 상속되는 것은 일부 스칼라 설정뿐입니다. 스테이징 배포가 "성공"한 뒤 런타임에서 `env.DB`가 `undefined`로 읽히는 사고는 런타임 결함이 아니라 이 누락입니다.

바인딩에 ID가 없거나 R2 버킷에 `bucket_name`이 없으면 Wrangler가 리소스를 새로 만들고 새 ID를 설정 파일에 적어 넣습니다. 배포 전에 설정을 읽고 기존 리소스를 나열합니다. 무심코 실행한 배포가 계정에 과금 대상 리소스를 만들 수 있습니다.

설정의 `vars`는 다음 배포에서 대시보드에서 고친 값을 덮어씁니다. 대시보드 값을 유지하려면 `keep_vars: true`(또는 `--keep-vars`)를 쓰고, 그렇지 않으면 파일을 정본으로 삼습니다. 배포가 시크릿을 지우는 일은 없습니다.

Next.js는 프레임워크 가이드가 신규 앱에 `vinext`(Vite 플러그인, 아직 베타)를 권장합니다. `npx vinext check`, `npx vinext init`, `npx @vinext/cloudflare deploy` 순서입니다. OpenNext 어댑터(`@opennextjs/cloudflare`)는 기존 앱을 유지하는 경로가 됐습니다. 설정 파일 없이 `wrangler deploy`를 실행하면 프레임워크를 자동 감지하고 Next.js 프로젝트를 `vinext`로 바꾸는 대화형 확인이 뜨므로, 비대화형 실행에서는 이 경로를 쓰지 않습니다.

| Pages 개념 | Workers 대응 |
|---|---|
| `pages_build_output_dir` | `assets.directory` |
| SPA와 404 자동 판별 | `assets.not_found_handling` 명시 |
| Functions가 정적 자산보다 먼저 실행 | 자산 우선, `assets.run_worker_first`로 조정 |
| `_worker.js` 고급 모드 | `main`으로 옮기고 `.assetsignore`에 `_worker.js` 추가 |
| `functions/` 파일 라우팅 | `wrangler pages functions build --outdir=./dist/worker/` |
| `_routes.json`, 미들웨어 | `assets.run_worker_first` 패턴 |
| 자동 제외되던 `node_modules`, `.git`, `.DS_Store` | `.assetsignore`에 직접 작성 |

정적 자산 한도는 파일 수가 Free 20,000개, Paid 100,000개이고 파일당 25 MiB입니다.

## Authentication

두 변수를 모두 설정합니다. 토큰만 있으면 Wrangler가 계정을 추측합니다.

```sh
[ -n "${CLOUDFLARE_API_TOKEN:-}" ] && echo token-set
[ -n "${CLOUDFLARE_ACCOUNT_ID:-}" ] && echo account-set
npx --no-install wrangler whoami --json
```

`CLOUDFLARE_API_TOKEN`은 `CLOUDFLARE_API_KEY`와 `CLOUDFLARE_EMAIL` 조합보다, 그리고 OAuth 로그인보다 우선합니다. `wrangler whoami`는 미인증이면 비0으로 종료하므로 쓰기 명령 전에 확인할 항목은 이것 하나입니다. 토큰은 "Edit Cloudflare Workers" 템플릿으로 만들고 배포에 필요한 계정과 존으로 범위를 좁힙니다. `wrangler login` OAuth는 그렇게 좁힐 수 없습니다.

실제 배포에 `--temporary`를 쓰지 않습니다. 임시 계정에 배포하고 60분짜리 claim URL을 발급하며, 그 시간이 지나면 배포가 사라집니다. 계정 없이 첫 시연을 할 때만 쓰는 기능입니다.

토큰을 명령행에 넘기거나 출력하거나 보고서에 복사하지 않습니다. 존재 확인은 아무것도 출력하지 않는 검사로 합니다.

## Identify And Deploy

프로젝트 로컬 바이너리(`npx --no-install wrangler` 또는 `node_modules/.bin`의 `wrangler`)를 실행하고 `--help`를 읽습니다. 전역 설치로 대체하지 않습니다. 배포 전에 Worker 이름, 환경, 설정 파일을 먼저 밝힙니다.

```sh
npx --no-install wrangler deploy --env staging --strict --dry-run
npx --no-install wrangler deploy --env staging --strict
```

- `--dry-run`은 업로드 없이 컴파일과 검증만 합니다. `--outdir`을 붙이면 번들 크기를 읽습니다.
- `--strict`는 비대화형 환경에서 원격 설정을 덮어쓸 수 있는 배포를 막습니다. 에이전트가 실행하는 배포에는 항상 켭니다.
- `--env <name>`은 `env.<name>`을 선택합니다. Vite 플러그인 프로젝트는 빌드 시점에 `CLOUDFLARE_ENV`로 환경을 정합니다. 배포 시점의 `--env`는 이미 평탄화된 설정을 바꾸지 못합니다.
- `WRANGLER_OUTPUT_FILE_PATH=<file>`은 줄 단위 JSON 이벤트(`wrangler-session`, `deploy`, `version-upload`, `command-failed`)를 `version_id`와 대상 URL과 함께 기록합니다. 성공 문자열을 맞추지 말고 이 파일을 해석합니다.

`wrangler deploy`는 버전을 만들고 트래픽 100%를 한 번에 옮깁니다. 업로드와 릴리스를 나누려면 다음 순서를 씁니다.

```sh
npx --no-install wrangler versions upload --tag "$GIT_SHA" --message "$MSG"
npx --no-install wrangler versions deploy <NEW_ID>@10% <OLD_ID>@90% -y
npx --no-install wrangler versions deploy <NEW_ID>@100% -y
```

Worker의 첫 배포는 반드시 `wrangler deploy`여야 합니다. 버전이 하나도 없으면 `versions upload`가 실패합니다. Durable Object 클래스 생명주기 변경이나 Service Worker 문법도 `versions upload`로는 실을 수 없습니다. 점진 배포 중에는 같은 사용자의 연속 요청이 서로 다른 버전으로 갈 수 있으므로, 10% 단계가 통과했다고 새 버전이 옳다고 단정하지 않습니다.

Containers를 쓰면 `wrangler deploy`가 새 Worker를 먼저 활성화하고 그다음 이미지를 빌드하고 밀어 넣고 롤아웃합니다. 이 단계는 트랜잭션이 아니어서 이미지나 롤아웃 실패가 Worker가 이미 운영 중인 뒤에 날 수 있습니다.

## Success Test

성공은 이번 실행이 만든 버전이 활성 버전인 것과 HTTP 응답, 조용한 오류 로그를 모두 만족할 때입니다.

```sh
npx --no-install wrangler deployments status --json
npx --no-install wrangler versions list --json
curl -sS -o /dev/null -w '%{http_code}\n' https://<route>/
npx --no-install wrangler tail --format json --status error --version-id <ID>
```

- `deployments status --json`은 활성 버전과 그 버전이 가진 트래픽 비율을 알려 줍니다. 그 버전 ID가 이번 실행의 결과와 같아야 합니다. `deploy`의 종료 코드 0만으로는 아무것도 증명하지 못합니다.
- `wrangler tail`은 중단할 때까지 계속 실행됩니다. 반드시 범위를 둡니다. 타임아웃이나 줄 수 제한과 함께 30~60초 창을 캡처하고, `outcome`이 `ok`이고 `exceptions`가 빈 배열인지 확인합니다. Worker 하나에 붙을 수 있는 클라이언트는 최대 10개이고, 부하가 큰 Worker는 샘플링합니다.
- HTTP는 라우트에서 200과 기대한 본문 또는 캐시 헤더를 확인합니다. 정적 자산 앱이면 딥 링크도 요청합니다. `not_found_handling` 문제가 드러나는 지점입니다.

Containers는 종료 상태가 하나 더 있습니다. 배포 성공은 롤아웃이 시작됐다는 뜻일 뿐입니다.

```sh
npx --no-install wrangler containers instances <APP_ID> --json
```

이번 실행 버전의 모든 인스턴스가 `running`이고 이전 버전 인스턴스가 사라져야 합니다. 첫 배포는 이미지 프로비저닝에 수 분이 걸리고, 그동안 Worker URL은 응답하지만 컨테이너 라우트는 실패합니다.

## Status And Logs

| 확인할 것 | 명령 |
|---|---|
| 어느 버전이 몇 %로 운영 중인가 | `wrangler deployments status --json` |
| 어떤 버전이 있는가 | `wrangler versions list --json`, `wrangler versions view <ID> --json` |
| 기계 판독 배포 결과 | `WRANGLER_OUTPUT_FILE_PATH` ND-JSON |
| 실시간 런타임 로그 | `wrangler tail --format json --status error --search "<text>" --version-id <ID>` |
| 저장된 런타임 로그 | 대시보드의 Workers Logs 또는 Cloudflare API. `observability.enabled` 필요 |
| 컨테이너 인스턴스 | `wrangler containers instances <APP_ID> --json`, `wrangler containers info <ID>` |
| 빌드 상태와 로그 | `GET /accounts/{account_id}/builds/workers/{worker_tag}/builds`, 그다음 `GET /accounts/{account_id}/builds/builds/{build_uuid}/logs` |

빌드는 이름이 아니라 `script_tag`로 식별하고, Builds API는 사용자 범위 토큰만 받습니다. 빌드 로그는 90일 보존합니다. Workers Logs는 Free 3일, Paid 7일 보존하고 로그 한 줄은 256 KB가 상한입니다.

## Change Settings

`wrangler secret put KEY`는 새 버전을 만들고 즉시 배포합니다. 설정 편집이 아니라 배포 행위입니다. 운영 트래픽을 옮기므로 배포와 같은 승인 등급에 속하고, 나중 릴리스를 위해 시크릿을 미리 준비하는 수단이 아닙니다.

| 목적 | 명령 |
|---|---|
| 지금 바로 적용되는 시크릿 | `wrangler secret put KEY`, 또는 `wrangler secret bulk secrets.json`(최대 100개, `null`은 삭제) |
| 버전에만 실어 두는 시크릿 | `wrangler versions secret put KEY` |
| 코드와 함께 올리는 시크릿 | `wrangler deploy --secrets-file .env.production` |
| 시크릿이 없으면 배포 실패 | 설정의 `secrets.required: ["KEY"]` |
| 로컬 개발 | `.dev.vars` 또는 `.dev.vars.<env>`, 같은 자리에 `.env`를 두지 않음 |

`--secrets-file`은 dotenv 문법을 해석하고 `$VAR`을 프로세스 환경변수로 확장하므로 내용을 통제하는 파일에만 지정합니다. `--secrets-file` 배포에서 빠진 시크릿은 이전 버전에서 유지되고, 어떤 배포도 시크릿을 지우지 않습니다.

미리보기는 운영 전 검증에 권장되는 방식입니다(`wrangler preview`, 프로젝트 로컬 Wrangler 4.135.0 이상). Version URL(`<version-prefix>-<worker>.workers.dev`)은 이전 방식이고 `preview_urls` 키를 그대로 쓰며, Durable Object가 있는 Worker에는 생성되지 않고 Workers Logs나 `wrangler tail`로 읽을 수도 없습니다. 둘 다 운영 리소스를 그대로 사용하고, 미리보기 URL은 Cloudflare Access를 설정하지 않으면 공개입니다. URL을 넘겨주기 전에 이 점을 알립니다. 예전 `--preview-alias` 브랜치 미리보기는 Previews가 대신합니다.

## Rollback

```sh
npx --no-install wrangler rollback [<VERSION_ID>] --message "rollback: <reason>"
```

롤백은 지정한 버전으로 새 배포를 즉시 만들고 트래픽을 그리로 옮깁니다. 되감기가 아니라 앞으로 가는 동작입니다. 버전 ID를 생략하면 직전 버전으로 갑니다. `--message`를 주면 확인 프롬프트를 건너뜁니다.

- 롤백 대상은 최근 100개 버전까지이고, 점진 배포가 쓰는 창과 같습니다.
- 롤백이 되돌리는 것은 Worker 코드뿐입니다. Worker에 바인딩된 리소스와 그 데이터, D1 내용, KV 항목, R2 객체, Queues는 바뀌지 않습니다.
- Durable Object 클래스 생명주기 변경이 있었거나 대상 버전이 기대하는 바인딩 리소스가 사라졌으면 롤백이 거부됩니다. 어떤 버전이 쓰던 이미지를 지우면 그 버전으로의 롤백도 깨집니다.
- 데이터베이스를 되돌리는 일은 위험이 다른 별개 작업입니다. `wrangler d1 time-travel restore <DB> --bookmark <BM>`은 데이터베이스를 제자리에서 덮어쓰고 진행 중 쿼리를 취소하는 파괴적 명령입니다. `wrangler d1 migrations apply --remote`는 스키마와 데이터를 바꿉니다. 둘 다 명시적 승인과 되돌릴 북마크 또는 백업을 먼저 밝혀야 합니다.

## Failure Table

| # | 시그니처 | 원인 | 수정 |
|---|---|---|---|
| 1 | `Missing entry-point: The entry-point should be specified via the command line … or the main config field` | 빌드 루트에 설정이 없거나 `main` 누락 | `main`을 추가하거나 Builds 루트 디렉터리를 고칩니다 |
| 2 | `The name in your Wrangler configuration file … must match the name of your Worker` | 설정 `name`과 대시보드 Worker 이름 불일치 | `env.<name>` 접미사 규칙이 아니면 `name`을 맞춥니다 |
| 3 | `Could not route to /client/v4/accounts/<ID>/workers/services/… [code: 7003]` | 설정에 다른 `account_id`가 박혀 있음 | 그 키를 지우고 `CLOUDFLARE_ACCOUNT_ID`를 씁니다 |
| 4 | `The build token selected for this build has been deleted or rolled` | 빌드 토큰이 오래됨 | 새 토큰을 발급하고 Builds 설정을 갱신합니다 |
| 5 | `Build was timed out` | 빌드 20분 상한 | 빌드를 나누고 의존성을 캐시하고 `path_includes`로 범위를 좁힙니다 |
| 6 | 배포는 성공하는데 사이트가 404나 빈 페이지 | `assets.directory`가 빌드 산출물과 불일치, 또는 `not_found_handling` 없는 SPA | 디렉터리를 고치고 `not_found_handling: "single-page-application"`을 설정합니다 |
| 7 | 로컬은 되는데 빌드에서 `npm ci` 실패 | 빌드 이미지의 npm이 lockfile보다 낮음 | `"packageManager": "npm@x.y.z"`를 고정합니다 |
| 8 | 업로드에서 `10027` | Worker 번들이 64 MiB 한도 초과 | 의존성을 제거하거나 나누고 `--dry-run --outdir`로 확인합니다 |
| 9 | `10021`과 `Script startup exceeded CPU time limit` | top-level 스코프 작업 과다 | 초기화를 지연하고 시작 시간을 1초, 메모리를 128 MB 근처로 줄입니다 |
| 10 | 런타임 `1102`와 `Worker exceeded resource limits` | CPU 한도 초과(Free 10 ms, Paid 기본 30 s) | `limits.cpu_ms`를 300000까지 올리거나 작업을 나눕니다 |
| 11 | `1102`와 `Exceeded Memory` | isolate 128 MB 한도 | `TransformStream`으로 스트리밍하고 큰 값은 R2, KV, D1로 옮깁니다 |
| 12 | `1101`과 `The script will never generate a response` | 미해결 Promise 또는 닫히지 않은 WebSocket | no-floating-promises 린트를 넣고 서버를 닫고 WebSocket을 수락합니다 |
| 13 | `1042`, 또는 같은 존 fetch 실패 | 같은 존의 다른 Worker를 라우트로 fetch | 서비스 바인딩이나 Custom Domain을 씁니다 |
| 14 | `1019` | Worker 호출 체인이 16회 초과 | 호출 체인을 평탄화합니다 |
| 15 | 배포 후 환경변수가 사라짐 | `deploy`가 대시보드 `vars`를 덮어씀 | `keep_vars: true` 또는 `--keep-vars`를 쓰고 파일을 정본으로 삼습니다 |
| 16 | 런타임에서 바인딩이 `undefined` | `env.<name>`에 그 바인딩과 `vars`를 선언하지 않음. 상속되지 않음 | 환경마다 바인딩을 선언합니다 |
| 17 | 시크릿 누락으로 배포 실패 | `secrets.required`를 선언했는데 시크릿이 없음 | `wrangler secret put` 또는 `--secrets-file`을 씁니다 |
| 18 | Custom Domain 추가 실패 | 그 호스트명에 기존 CNAME이 있거나 소유하지 않은 존 | 기존 CNAME을 먼저 지우고 도메인을 추가합니다 |
| 19 | 새 Worker에서 `versions upload` 실패 | `versions upload`는 첫 버전을 만들지 못함 | `wrangler deploy`를 한 번 실행합니다 |
| 20 | `versions upload`가 `10211` 반환 | Durable Object 마이그레이션 대기, Wrangler 4.131.0 미만 | `wrangler deploy`를 실행하거나 Wrangler를 올립니다 |
| 21 | D1 마이그레이션 실패 | SQL 오류 또는 제약 위반 | 그 마이그레이션만 롤백됩니다. 고쳐서 다시 적용하고 외래 키는 `PRAGMA defer_foreign_keys = true`를 씁니다 |

### Containers

Workers는 포트를 열지 않고 헬스체크도 없습니다. 포트나 헬스체크 실패는 이 경로에만 있습니다. Containers가 없는 Worker에 Docker식 진단을 적용하면 오진입니다.

| # | 시그니처 | 원인 | 수정 |
|---|---|---|---|
| 22 | Worker는 정상인데 컨테이너 라우트가 5xx | 첫 배포 프로비저닝, 또는 이미지나 롤아웃 실패(비트랜잭션) | 수 분 기다린 뒤 `containers instances`와 이미지 빌드 로그를 읽습니다 |
| 23 | `Container is not listening to port 8080` | 컨테이너 프로세스가 아직 포트를 열지 않음 | 재시도 루프로 폴링하고 기대 포트에 `0.0.0.0`으로 바인드합니다 |
| 24 | 컨테이너가 `internal error` | Docker 소켓을 찾지 못함 | `DOCKER_HOST`를 지정합니다 |
| 25 | Python 컨테이너가 배포 후에만 `UnicodeEncodeError: 'idna' codec can't encode …` | 배포 환경 hostname이 DNS 레이블 한도를 넘는 64자 | hostname을 조회하지 않는 서버를 씁니다(예: `socketserver`) |

## Approval Required

| 동작 | 등급 |
|---|---|
| `--dry-run`, `wrangler versions upload`, `deployments status`, `versions list`, `tail`, `containers instances`, Builds API 조회, 저장소의 설정 편집 | proceed |
| 운영 배포와 재배포, 운영에서의 `wrangler secret put`(즉시 배포됨) | named environment |
| 운영에서의 `wrangler rollback`, `versions deploy` 100% 승격, `wrangler delete`, `d1 migrations apply --remote`, `d1 execute --remote`, `d1 time-travel restore`, `containers images delete`, `wrangler secret delete`, 라우트와 Custom Domain 변경, `workers_dev`와 `preview_urls` 비활성화, Preview 삭제, `--containers-rollout=immediate` | explicit approval |
| 로그인, 계정이나 프로젝트 생성, 전역 CLI 설치, 토큰 출력 | never |

롤백 전에는 코드만 되돌리고 바인딩된 리소스와 데이터는 현재 상태로 남는다는 점을 밝힙니다.

## Checked

> 자주 바뀝니다. 2026-11-07에 아래 출처로 확인했습니다. 플래그, 한도, 권장 사항에 따라 결정이 갈리면 실제 페이지를 다시 확인합니다.

| Fact | Value |
|---|---|
| 신규 프로젝트 | Workers와 Static Assets. Pages는 폐기되지 않았지만 시작점이 아님 |
| 신규 Wrangler 프로젝트 설정 | `wrangler.jsonc`. TOML도 계속 동작 |
| `cf` CLI 경로 | `cloudflare.config.ts`, 오픈 베타, Node.js 22.18 이상, Bun 미지원 |
| Next.js | `vinext` 베타 권장, 기존 앱은 OpenNext |
| Worker 크기 | 비압축 64 MiB |
| 정적 자산 | Free 20,000개, Paid 100,000개, 파일당 25 MiB |
| 빌드 | 최대 20분, 동시 6개, 메모리 8 GB |
| 롤백 창 | 최근 100개 버전 |
| D1 time travel 보존 | Free 7일, Paid 30일 |
| Containers | Workers Paid 플랜, 계정당 이미지 저장 50 GB, `SIGTERM` 유예 15분 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| 신규 프로젝트는 `wrangler.jsonc` 권장, 일부 기능은 JSON 설정 전용 | <https://developers.cloudflare.com/workers/wrangler/configuration/> |
| 신규 프로젝트는 Workers로 시작, Workers가 대부분의 Pages 사용 사례를 지원 | <https://developers.cloudflare.com/pages/> |
| Pages 이전 대응표, 명시적 SPA 처리, `.assetsignore` | <https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/> |
| `cloudflare.config.ts`는 `cf` CLI의 오픈 베타 설정 | <https://developers.cloudflare.com/cf/projects/cloudflare-config/> |
| `deploy`가 버전을 만들고 트래픽 100%를 옮김 | <https://developers.cloudflare.com/workers/versions-and-deployments/> |
| 첫 업로드에서 `versions upload` 실패 | <https://developers.cloudflare.com/workers/versions-and-deployments/deployment-management/> |
| 점진 배포와 롤백은 최근 100개 버전까지만 지원 | <https://developers.cloudflare.com/workers/versions-and-deployments/gradual-deployments/>, <https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/> |
| 롤백은 바인딩된 리소스를 바꾸지 않음 | <https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/> |
| `--strict`, `versions`, `rollback`, `tail` 플래그 | <https://developers.cloudflare.com/workers/wrangler/commands/workers/> |
| `wrangler secret put`은 즉시 배포, `secrets.required`, `--secrets-file` | <https://developers.cloudflare.com/workers/configuration/secrets/> |
| `WRANGLER_OUTPUT_FILE_PATH` ND-JSON 이벤트 | <https://developers.cloudflare.com/workers/wrangler/system-environment-variables/> |
| CI용 `CLOUDFLARE_API_TOKEN`과 `CLOUDFLARE_ACCOUNT_ID` | <https://developers.cloudflare.com/workers/ci-cd/external-cicd/github-actions/> |
| 빌드 한도와 빌드 명령 | <https://developers.cloudflare.com/workers/ci-cd/builds/configuration/>, <https://developers.cloudflare.com/workers/ci-cd/builds/limits-and-pricing/> |
| 빌드 로그 API와 90일 보존 | <https://developers.cloudflare.com/workers/ci-cd/builds/api-reference/> |
| Workers Logs 보존과 기본 관측 설정 | <https://developers.cloudflare.com/workers/observability/logs/workers-logs/> |
| 오류 코드 10021, 10027, 1019, 1042, 1101, 1102 | <https://developers.cloudflare.com/workers/observability/errors/>, <https://developers.cloudflare.com/workers/platform/limits/> |
| Next.js는 `vinext` 권장, 기존 앱은 OpenNext | <https://developers.cloudflare.com/workers/framework-guides/web-apps/nextjs/>, <https://developers.cloudflare.com/workers/framework-guides/web-apps/opennext/> |
| 임시 배포는 60분 안에 claim 가능 | <https://developers.cloudflare.com/workers/platform/claim-deployments/> |
| Durable Object가 있는 Worker에는 Version URL이 생성되지 않음 | <https://developers.cloudflare.com/workers/versions-and-deployments/version-urls/> |
| Previews가 운영 전 검증의 권장 방식 | <https://developers.cloudflare.com/workers/previews/compare-workflows/> |
| 기존 CNAME이 있는 호스트에는 Custom Domain을 추가할 수 없음 | <https://developers.cloudflare.com/workers/configuration/routing/custom-domains/> |
| 설정 없는 `wrangler deploy`는 프레임워크를 자동 감지 | <https://developers.cloudflare.com/workers/get-started/prompting/> |
| Containers 배포는 트랜잭션이 아님 | <https://developers.cloudflare.com/containers/guides/deploy/> |
| 배포 성공은 롤아웃 시작을 뜻함 | <https://developers.cloudflare.com/containers/configuration/rollouts/> |
| 컨테이너 포트 8080 준비 상태와 문제 해결 | <https://developers.cloudflare.com/containers/guides/local-dev/> |
| 컨테이너 한도와 이미지 저장 | <https://developers.cloudflare.com/containers/platform/limits/> |
| D1 마이그레이션은 백업을 캡처하고 실패한 마이그레이션만 롤백 | <https://developers.cloudflare.com/d1/reference/migrations/>, <https://developers.cloudflare.com/workers/wrangler/commands/d1/> |
| D1 time travel restore는 제자리에서 덮어쓰는 파괴적 연산 | <https://developers.cloudflare.com/d1/reference/time-travel/> |
| 프로젝트의 Wrangler 버전을 쓰고, `cloudflare.config.ts` 프로젝트에는 `cf`를 쓰고, `secret put`을 배포로 취급 | <https://github.com/cloudflare/skills> |

### Evidence grade

`LOCAL` - 절 순서, 승인 등급, 실패 분류는 위 Cloudflare 1차 문서를 바탕으로 이 패키지가 정한 설계입니다. 이 환경에서는 CLI를 실행하지 못했으므로 모든 플래그와 종료 동작은 관찰이 아니라 문서 인용입니다. Previews, `vinext`, `cloudflare.config.ts`는 베타 또는 오픈 베타라 폐기 공지 없이 바뀔 수 있으므로 의존하기 전에 실제 페이지를 다시 읽습니다.
