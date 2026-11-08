# Work Tracks

> 라우팅한 뒤 대상마다 세 트랙 중 무엇을 실행할지 고르고, 정해진 순서 하나로 실행하며, 트랙마다 자기 근거로 검증합니다.

## 1. 세 트랙

| Track | 맡는 일 | 읽는 파일 |
|---|---|---|
| architecture | 폴더 배치, 라우트, 모듈·서버 경계, 데이터 접근, 검증, 플랫폼 경계 | `stacks/<stack>/core.md`와 그 가이드가 안내하는 파일 |
| setup | 린트, 포맷, 타입 검사, 툴체인 고정, 에디터·훅 연결, CI 검사 순서 | 대상이 쓰는 언어마다 `rules/setup/<language>.md`, `rules/setup/repo.md`, `assets/templates/setup/`의 템플릿 |
| performance | 빌드 결과물, 번들·에셋 무게, 렌더링·데이터 로딩 비용, 런타임·릴리스 프로필 설정 | `rules/<stack>/performance.md` |

setup 트랙에서 스택별로 읽는 언어 파일입니다.

| Stack | Setup files |
|---|---|
| nextjs, tanstack-start, vite, expo, lynx, astro, hono | `rules/setup/typescript.md` |
| tauri | `rules/setup/typescript.md`와 `rules/setup/rust.md`(`src-tauri` crate) |
| axum, rust | `rules/setup/rust.md` |

`rules/setup/repo.md`는 패키지마다가 아니라 저장소마다 한 번 적용합니다.

## 2. 트랙 고르기

저장소에서 무엇이 빠져 보이는지가 아니라 요청 문구로 고릅니다.

| Request | Tracks |
|---|---|
| 더 좁은 범위가 없는 프로젝트 전체 요청: "아키텍처 잡아줘", "셋업해줘", "알아서 다 해줘", "전체 수정", "set up this project", 새 프로젝트, 인자 없는 `hyper-architecture` 호출 | architecture, setup, performance |
| 폴더, 라우트, 계층, 경계, 데이터 접근, 플랫폼 경계 | architecture |
| 린트, 포맷, oxlint, Prettier, ESLint·Biome 이전, rustfmt, clippy, analyzer, tsconfig, git hook, CI 검사 | setup |
| 느린 페이지, 번들 크기, 빌드 크기, Lighthouse, Core Web Vitals, 시작 시간, 끊김, 릴리스 프로필, "최적화", "성능" | performance |
| 위 행 중 둘 이상이 한 요청에 있음 | 합집합을 §3 순서로 |

"점검만", "리뷰만", "audit only", "report only"가 있으면 고른 트랙을 모두 보고 모드로 실행합니다. 파일 경로가 붙은 발견 사항만 내고 수정하지 않습니다.

## 3. 순서

대상마다 고른 트랙을 이 순서로 실행합니다.

1. **setup**: 먼저 실행해 이후 수정을 검증할 포매터, 린터, 타입 검사기를 갖춥니다.
2. **architecture**: 스택 가이드의 자체 워크플로를 따릅니다.
3. **performance**: 마지막에 architecture 트랙이 남긴 구조 위에서 측정합니다.

각 트랙은 다음 트랙을 시작하기 전에 자기 검증을 마칩니다. 한 트랙의 게이트가 실패하면 그 대상은 멈추고, 보고에 실패한 게이트와 실행하지 않은 트랙을 적습니다.

## 4. Track rules

### Setup

- 먼저 감지합니다. 기존 린트·포맷·타입 설정(`.eslintrc*`, `eslint.config.*`, `biome.json*`, `.prettierrc*`, `.oxlintrc.json`, `tsconfig*.json`, `rustfmt.toml`, `clippy.toml`, `Cargo.toml`의 `[lints]`, `lefthook.yml`, `.husky/`)과 그것을 실행하는 스크립트를 읽습니다.
- 목표 표준은 TypeScript는 oxlint와 Prettier, Rust는 rustfmt와 clippy입니다. 프로젝트가 다른 도구를 쓰는데 그 도구를 유지한다는 결정이 기록돼 있지 않으면(`AGENTS.md`, `CONTRIBUTING.md`, 설정 주석) 언어 파일의 이전 단계로 표준에 옮깁니다. 기록된 결정이 있으면 그 결정이 우선하며 이전하지 않고 보고합니다.
- 템플릿보다 엄격한 기존 규칙을 약하게 만들지 않습니다. 템플릿을 기존 설정에 합칩니다.
- 저장소 전체 포맷은 모든 파일을 바꿉니다. 새 프로젝트이거나 `전체 수정`일 때만, 다른 변경을 섞지 않은 독립 단계로 실행합니다. 그 밖에는 이번 실행이 건드린 파일만 포맷합니다.
- 검사를 실행하는 패키지 스크립트나 태스크 러너 항목을 추가하거나 고쳐서 `rules/setup/repo.md`의 CI 검사 순서가 그것을 부를 수 있게 합니다.

### Architecture

- 라우팅한 스택 가이드를 그대로 따릅니다. 이 파일은 그 규칙에 아무것도 더하지 않습니다.

### Performance

- 바꾸기 전에 측정합니다. 빌드, 번들, 프로파일, 감사 명령을 밝히고 그 수치를 기록합니다.
- 스택 파일의 규칙 목록에서 한 번에 한 가지만 바꾸고, 프로덕션 빌드에서 같은 측정을 다시 실행합니다. 한 실행에서 대상마다 최대 세 건까지만 바꾸고 나머지는 다음 단계로 적습니다.
- 측정 수치가 나아지고 setup·architecture 트랙의 검사가 모두 통과할 때만 변경을 남기고, 그렇지 않으면 되돌립니다. 전후 수치를 보고합니다.
- 여기서 측정할 수 없는 규칙(기기 없음, 프로덕션 빌드 불가, 네트워크 없음)은 측정하지 않음으로 보고하며 개선으로 주장하지 않습니다.

## 5. Report

라우팅 줄 다음에 대상과 트랙마다 한국어 한 줄을 출력합니다.

```text
<target path> / <track>: <완료|점검만|중단> - <evidence: command and result, or the stop reason>
```

## Sources

> Checked 2026-11-07. 이 파일은 이 패키지 자체의 절차이며, 파일이 이름을 든 도구 선택은 사용자가 밝힌 표준입니다.

| Claim | Source |
|---|---|
| oxlint, Prettier, rustfmt, clippy를 공통 린트·포맷 표준으로 삼고, setup과 performance 작업을 이 스킬의 아키텍처 작업에 합친다는 결정 | user instruction, 2026-11-07 |
| setup → architecture → performance 순서, 포맷 단계 규칙, 측정-변경-측정 루프 | 이 패키지가 고른 절차이며 검증된 최적값이 아닙니다 |
