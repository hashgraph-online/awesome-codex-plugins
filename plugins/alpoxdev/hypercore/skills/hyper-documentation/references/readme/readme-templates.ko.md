# README Templates

**Purpose**: 프로젝트 형태별로 바로 쓸 수 있는 섹션 스켈레톤. 일치하는 블록을 복사한 뒤 자리 표시자를 프로젝트에서 검증한 값으로 교체한다.

> 아래 템플릿은 영어로 쓰여 있다. 헤딩과 산문은 기본적으로 한국어로 번역하고, 코드 블록은 그대로 둔다. 사용자가 명시적으로 다른 언어를 요청했거나 기존 대상 README 언어를 보존해야 할 때만 다른 언어를 사용한다.

## 목차

- CLI
- Library
- Web app
- Monorepo
- Plugin
- Framework
- Docs site
- Service / API
- 자리 표시자에 대한 노트
- Sources

## CLI

```markdown
# <name>

> <한 줄 설명>

## Install

\`\`\`bash
<package-manager-install>
\`\`\`

## Quickstart

\`\`\`bash
<name> <subcommand> [options]
\`\`\`

## Commands

| Command | Description |
|---|---|
| `<name> <cmd>` | <기능 설명> |

## Configuration

- `<env var>` — <목적, 기본값>

## Examples

\`\`\`bash
<현실적인 예시>
\`\`\`

## Development

\`\`\`bash
<dev script>
<test script>
\`\`\`

## License

<SPDX 또는 텍스트>
```

## Library

```markdown
# <name>

> <한 줄 설명>

## Install

\`\`\`bash
<레지스트리 설치>
\`\`\`

## Usage

\`\`\`ts
import { <api> } from "<name>";

<작은 현실적인 예시>
\`\`\`

## API

- `<exportedName>(args)` — <반환값 설명>

## Compatibility

- Node: <범위>
- Browsers: <해당하면>

## Development

\`\`\`bash
<dev/test 스크립트>
\`\`\`

## License

<SPDX 또는 텍스트>
```

## Web app

```markdown
# <name>

> <한 줄 설명>

## Stack

- <프레임워크 + 버전>
- <DB / 상태 / 스타일링>

## Local development

\`\`\`bash
<install>
<dev>
\`\`\`

앱은 <url>에서 실행된다.

## Environment

| Variable | Required | Description |
|---|---|---|
| `<KEY>` | yes/no | <목적> |

## Build and deploy

\`\`\`bash
<build>
<start>
\`\`\`

## Project structure

\`\`\`text
<주요 폴더만>
\`\`\`

## License

<SPDX 또는 텍스트>
```

## Monorepo

```markdown
# <repo name>

> <한 줄 설명>

## Packages

| Package | Purpose | Path |
|---|---|---|
| `<pkg>` | <목적> | `packages/<pkg>` |

## Local development

\`\`\`bash
<루트에서 install>
<워크스페이스 인식 dev/test 명령>
\`\`\`

## Contributing

패키지별 문서는 각 패키지 README를 참고한다.

## License

<SPDX 또는 텍스트>
```

## Plugin

```markdown
# <name>

> <한 줄 설명>

## Compatibility

- <지원되는 호스트 플랫폼>

## Install

\`\`\`text
<프로젝트 자체 문서에서 도출한 호스트 플랫폼 설치 명령>
\`\`\`

## Usage

<호스트 환경에서 플러그인을 호출하는 방식>

## Configuration

<매니페스트에서 도출한 설정 옵션>

## License

<SPDX 또는 텍스트>
```

## Framework

```markdown
# <name>

> <한 줄 설명>

## Quickstart

\`\`\`bash
<create 명령>
\`\`\`

## Core concepts

- <개념> — <한 줄 설명> (깊은 문서로 링크)

## Templates / starters

| Template | Description |
|---|---|
| `<template>` | <목적> |

## Documentation

<문서 사이트 또는 docs 폴더 링크>

## License

<SPDX 또는 텍스트>
```

## Docs site

```markdown
# <name>

> <한 줄 설명>

## Local development

\`\`\`bash
<install>
<dev>
\`\`\`

## Content structure

- `<folder>/` — <문서화 대상>

## Build and deploy

\`\`\`bash
<build>
\`\`\`

## Contributing

<짧은 노트 + 기여 가이드 링크>

## License

<SPDX 또는 텍스트>
```

## Service / API

```markdown
# <name>

> <한 줄 설명>

## Run locally

\`\`\`bash
<install>
<run>
\`\`\`

## Environment

| Variable | Required | Description |
|---|---|---|
| `<KEY>` | yes/no | <목적> |

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | health probe |

## Deployment

<짧은 노트 또는 링크>

## License

<SPDX 또는 텍스트>
```

## 자리 표시자에 대한 노트

- 모든 `<placeholder>`는 저장소에서 검증한 값으로 교체한다.
- 프로젝트가 지원하지 않는 섹션(테스트 없음, env var 없음, 배포된 패키지 없음)은 통째로 버린다.
- 진짜로 구분해 보여줄 만한 별개 플로우가 없으면 섹션당 예시는 하나로 유지한다.

## Sources

> 외부 출처 없음. 내용 확인 2026-09-21.

이 템플릿은 `rules/readme/section-design.md`의 섹션 정책에서 파생한 저장소 자체 스켈레톤이다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
