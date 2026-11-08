# README Templates

**Purpose**: Ready-to-use section skeletons by project type. Copy the matching block, then replace placeholders with verified evidence from the project.

> All templates below are written in English. Translate headings and prose into Korean by default; keep code blocks intact. Use another language only when the user explicitly requests it or an existing target README must preserve its current language.

## Contents

- CLI
- Library
- Web app
- Monorepo
- Plugin
- Framework
- Docs site
- Service / API
- Notes on placeholders
- Sources

## CLI

```markdown
# <name>

> <one-line description>

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
| `<name> <cmd>` | <what it does> |

## Configuration

- `<env var>` — <purpose, default>

## Examples

\`\`\`bash
<realistic example>
\`\`\`

## Development

\`\`\`bash
<dev script>
<test script>
\`\`\`

## License

<SPDX or text>
```

## Library

```markdown
# <name>

> <one-line description>

## Install

\`\`\`bash
<install from registry>
\`\`\`

## Usage

\`\`\`ts
import { <api> } from "<name>";

<small realistic example>
\`\`\`

## API

- `<exportedName>(args)` — <what it returns>

## Compatibility

- Node: <range>
- Browsers: <if applicable>

## Development

\`\`\`bash
<dev/test scripts>
\`\`\`

## License

<SPDX or text>
```

## Web app

```markdown
# <name>

> <one-line description>

## Stack

- <framework + version>
- <database / state / styling>

## Local development

\`\`\`bash
<install>
<dev>
\`\`\`

The app runs at <url>.

## Environment

| Variable | Required | Description |
|---|---|---|
| `<KEY>` | yes/no | <purpose> |

## Build and deploy

\`\`\`bash
<build>
<start>
\`\`\`

## Project structure

\`\`\`text
<key folders only>
\`\`\`

## License

<SPDX or text>
```

## Monorepo

```markdown
# <repo name>

> <one-line description>

## Packages

| Package | Purpose | Path |
|---|---|---|
| `<pkg>` | <purpose> | `packages/<pkg>` |

## Local development

\`\`\`bash
<install at root>
<workspace-aware dev/test command>
\`\`\`

## Contributing

See per-package READMEs for package-specific docs.

## License

<SPDX or text>
```

## Plugin

```markdown
# <name>

> <one-line description>

## Compatibility

- <host platforms supported>

## Install

\`\`\`text
<host-platform install command derived from project's own docs>
\`\`\`

## Usage

<how to invoke the plugin in the host environment>

## Configuration

<config options derived from the manifest>

## License

<SPDX or text>
```

## Framework

```markdown
# <name>

> <one-line description>

## Quickstart

\`\`\`bash
<create command>
\`\`\`

## Core concepts

- <concept> — <one-line explanation> (link to deeper doc)

## Templates / starters

| Template | Description |
|---|---|
| `<template>` | <purpose> |

## Documentation

<link to docs site or docs folder>

## License

<SPDX or text>
```

## Docs site

```markdown
# <name>

> <one-line description>

## Local development

\`\`\`bash
<install>
<dev>
\`\`\`

## Content structure

- `<folder>/` — <what it documents>

## Build and deploy

\`\`\`bash
<build>
\`\`\`

## Contributing

<short note + link to contribution guide>

## License

<SPDX or text>
```

## Service / API

```markdown
# <name>

> <one-line description>

## Run locally

\`\`\`bash
<install>
<run>
\`\`\`

## Environment

| Variable | Required | Description |
|---|---|---|
| `<KEY>` | yes/no | <purpose> |

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | health probe |

## Deployment

<short note or link>

## License

<SPDX or text>
```

## Notes on placeholders

- Replace every `<placeholder>` with a value verified from the repo.
- Drop entire sections that the project does not support (no tests, no env vars, no published package).
- Keep at most one example per section unless the project genuinely has distinct flows worth showing separately.

## Sources

> No external sources; content checked 2026-09-21.

These templates are repository-authored skeletons derived from the section policy in `rules/readme/section-design.md`. They make no external claim, so no external source is cited.
