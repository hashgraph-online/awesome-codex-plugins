# Project Discovery

**Purpose**: 프로젝트를 꼼꼼히 읽고, 어떤 형태의 README가 필요한지 작성 전에 감지한다.

## 1. 형태 감지 신호

섹션을 고르기 전에 프로젝트 형태를 감지한다:

| 프로젝트 형태 | 강한 신호 |
|---|---|
| **CLI** | `package.json`의 `bin` 필드, `src/cli/*`, 단일 실행 스크립트, `Cargo.toml` `[[bin]]`, Python `entry_points`/`console_scripts` |
| **Library** | `package.json`의 `main`/`module`/`exports`, `lib/`, `src/index.*`, `Cargo.toml` `[lib]`, CLI 진입점이 없는 Python 패키지 |
| **Web app** | `next.config.*`, `vite.config.*`, `nuxt.config.*`, `app/` 또는 `pages/`, 매니페스트의 프레임워크 의존성 |
| **Monorepo** | `packages/`, `apps/`, `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, 루트 `workspaces` 필드 |
| **Plugin** | `.claude-plugin/`, `agents/`, `skills/`, 에디터/플랫폼용 플러그인·마켓플레이스 매니페스트 |
| **Framework** | 템플릿/제너레이터/`create-*` 명령을 노출 |
| **Docs site** | `docusaurus.config.*`, `astro.config.*`, `mkdocs.yml`, `vitepress`, 큰 `docs/` 트리 |
| **Service / API** | `Dockerfile`, `serve` 스크립트, 서버 진입점, 라우트 폴더, 배포된 라이브러리 export 없음 |

신호가 겹칠 때는 주된 산출물을 우선한다: 앱 진입점이 없이 배포된 패키지는 라이브러리, 배포된 SDK가 있는 서버는 둘 다일 수 있다 — 주된 사용을 먼저 문서화하고 보조 표면은 링크한다.

## 2. 먼저 살필 파일

작성 전에 다음 순서로 읽는다:

1. 기존 `README.md` (모노레포면 루트와 패키지 단위 모두).
2. 언어와 관습 힌트를 위한 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`.
3. `LICENSE` 또는 `LICENSE.*`.
4. 매니페스트: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `deno.json`, `pubspec.yaml`.
5. 패키지 매니저를 확정할 락파일: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lockb`, `Cargo.lock`, `poetry.lock`, `uv.lock`.
6. 워크스페이스 매니페스트: `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`.
7. 진입점: `bin`, `main`, `module`, `exports`, `src/index.*`, `src/cli/*`, 프레임워크 설정 파일.
8. 스크립트: `package.json`의 `scripts` 필드, `Makefile`, `justfile`, `Taskfile.yml`.
9. 플러그인 매니페스트: `.claude-plugin/*.json`, `agents/`, `skills/`, 마켓플레이스 메타데이터.
10. 구조 파악용 최상위 폴더: `src/`, `packages/`, `apps/`, `cli/`, `instructions/`, `scripts/`, `docs/`.

형태와 주요 명령이 분명해지면 읽기를 멈춘다. 소스 파일을 모두 읽지 않는다.

## 3. Install 명령 도출

설치 스니펫은 관습이 아니라 실제 매니페스트에서 고른다:

- Node: 락파일에서 패키지 매니저를 고른다 (`pnpm install`, `npm install`, `yarn install`, `bun install`).
- 배포된 라이브러리: 매니페스트의 `name`을 기반으로 소비자 설치를 보여준다 (`npm install <name>`, `pnpm add <name>`).
- CLI 바이너리: 실행 경로를 보여준다 (`npx <name>`, `pnpm dlx <name>`, `cargo install <name>`, `pipx install <name>`).
- 플러그인/마켓플레이스: 프로젝트의 기존 README나 플러그인 매니페스트에서 도출한다. 마켓플레이스 URL을 지어내지 않는다.
- 로컬 전용 프로젝트(비공개 또는 이름 없음): 소스에서 시작하는 설치를 적는다 (`git clone` 후 dev/build).

매니페스트에 `name`이 없거나 비공개면 이름을 지어내지 않는다. 대신 로컬 설치 경로를 사용한다.

## 4. Usage / 예시 도출

가장 작은 진짜 예시를 찾는다:

- **Library**: 공개 export를 읽고 가장 잘 문서화된 함수를 사용하는 3-10줄 스니펫을 고른다.
- **CLI**: 실제 명령 핸들러 파일이나 캡처된 `--help` 출력에서 최상위 명령을 나열하고, 현실적인 명령 하나를 인용한다.
- **Web app / service**: dev 명령, 서비스 URL, 프로덕션 빌드 명령을 보여준다.
- **Plugin**: 호스트 환경에서 플러그인이 설치되고 호출되는 방식을 기존 프로젝트 문서에서 도출한다.

지어낸 또는 가설 예시는 진짜처럼 내보내지 말고 `<!-- TODO -->`로 표시한다.

## 5. 프로젝트 맵은 필요할 때만

"Project structure" 섹션은 다음 경우에만 추가한다:

- 새 기여자가 탐색해야 할 최상위 폴더가 4개 이상이거나,
- 나열할 만한 패키지가 여러 개인 모노레포일 때.

그 외엔 생략한다. README는 안내하는 곳이지 파일 트리를 거울처럼 비추는 곳이 아니다.

## 6. 언어와 관습 힌트

README가 한국어 기본값을 쓸 수 있는지, 아니면 다른 대상 언어를 보존해야 하는지 다음 신호로 결정한다:

- 새 README 산문은 기본적으로 한국어로 쓴다.
- 기존 대상 `README.md`가 주로 비한국어이고 작업이 외과적 리팩터/업데이트라면, 사용자가 번역을 요청하지 않은 한 일관성을 위해 그 언어를 보존한다.
- 사용자가 언어를 명시했으면 그 언어를 사용한다. 보존 신호가 충돌하고 산출물 언어가 크게 달라질 수 있으면 한 번만 묻고, 영어를 조용히 선택하지 않는다.

## 7. Discovery 산출물

작성 전에 짧은 프로필을 작업 노트에 기록한다:

```text
Type: [cli | library | web-app | monorepo | plugin | framework | docs-site | service]
Package manager: [npm | pnpm | yarn | bun | cargo | uv | poetry | go | deno | other]
Entry: [경로 또는 명령]
Primary scripts: [dev/build/test/lint/release]
README language: [ko default | user-requested | preserve-existing]
Existing README state: [missing | present-accurate | present-stale]
License: [SPDX 또는 "missing"]
```

이 프로필이 `rules/readme/section-design.md`의 섹션 선택과 `rules/readme/validation.md`의 검증 요약을 이끈다.

## Sources

> 외부 출처 없음. 내용 확인 2026-09-21.

이 규칙은 README 작성을 위한 저장소 로컬 탐색 절차를 서술한다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
