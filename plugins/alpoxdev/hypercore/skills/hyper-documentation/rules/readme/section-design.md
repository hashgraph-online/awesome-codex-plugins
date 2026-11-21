# Section Design

**Purpose**: Choose README sections, order, depth, and language from the project profile.

## 1. Section policy by project type

| Type | Required | Recommended | Skip unless asked |
|---|---|---|---|
| **CLI** | Title, install, quickstart, commands, examples, license | Configuration, environment variables, exit codes | Architecture diagrams, internal API |
| **Library** | Title, install, usage, API surface, examples, license | TypeScript types, peer deps, supported runtimes | Internal module map |
| **Web app** | Title, dev quickstart, environment, build/deploy, license | Tech stack, project structure, contributing | Marketing copy |
| **Monorepo** | Title, repo overview, package list, dev quickstart, license | Per-package READMEs, shared scripts | Long architecture essays |
| **Plugin** | Title, install (host platform), usage, configuration, license | Compatibility matrix, examples per host | Internal extension points |
| **Framework** | Title, install (`create-*`), quickstart, core concepts (linked), license | Templates, ecosystem | Full doc site contents |
| **Docs site** | Title, what it documents, local dev, contribution flow, license | Build/deploy, content structure | Generated content trees |
| **Service / API** | Title, run locally, environment, endpoints summary, license | Deployment, observability | Internal request handlers |

When multiple types apply, pick the dominant one and add only the extra section a secondary type genuinely requires.

## 2. Order conventions

Default order, top to bottom:

1. Title + one-line description
2. Badges (only when verifiable)
3. Features (3-7 bullets max, one line each)
4. Install
5. Quickstart / Usage
6. Configuration / Environment
7. Commands / API surface
8. Examples (use collapsed `<details>` if long)
9. Development (scripts, test, lint)
10. Project structure (only when non-trivial)
11. Contributing (only if a process is documented)
12. License

Do not bury install. New readers should reach the install command without scrolling past long context.

## 3. Heading and code style

- Use sentence case for headings unless project docs already use Title Case throughout.
- Use fenced code blocks with the right language tag (`bash`, `ts`, `py`, `rs`, `json`, `yaml`).
- Show shell prompts only when copying from a transcript (`$` for user, `#` for root). Otherwise omit.
- Keep example code under ~12 lines per block; link to a longer example file if needed.
- Use the same casing the codebase uses for command names, folder names, and config keys.

## 4. Language and tone

- Write README prose in Korean by default. Use another language only when the user explicitly requests it or when an existing target README must preserve its current language for consistency.
- Use the same terminology the codebase uses (folder names, command names, config keys are quoted exactly).
- State capability over marketing: "Renders Mermaid diagrams to SVG without dependencies" beats "blazing-fast diagram engine".
- Use one term per concept across the README.
- Keep sentences short. Prefer lists and tables over paragraphs when content is enumerable.

## 5. Badges

Add badges only when:

- the badge source is real (a published npm version, a configured CI workflow, a registered SPDX license), and
- the project already publishes them or the user explicitly asks for them.

Do not add coverage, downloads, or build-status badges if no source can be linked. A missing badge is better than a broken one.

## 6. Quickstart contract

The quickstart should:

- be runnable end to end after install,
- use the smallest realistic example,
- avoid placeholder values (`YOUR_TOKEN`, `<replace-me>`) when a default works,
- prefer a single command or 3-5 lines of code over a long walkthrough.

If the project genuinely needs setup (env vars, accounts, external services), state it in one short paragraph and link to the deeper guide.

## 7. Section trimming

Drop sections that have no real content:

- No tests configured -> skip "Testing".
- No published package -> skip "Install from registry"; keep "From source" only.
- No contributing process documented -> use a short link to the issue tracker instead of fabricating one.
- No deploy pipeline documented -> skip "Deployment" rather than guessing.

A short, accurate README beats a long padded one.

## 8. Monorepo-specific guidance

For monorepos, the root README orients readers across packages; per-package READMEs go deep on a single package.

- Root README: list packages with one-line purpose and folder path; show the workspace-aware install/dev command at the root.
- Package README: treat the package as its own project and apply the matching type policy from the table above.
- Avoid duplicating per-package install instructions in the root README; link instead.

## Sources

> No external sources; content checked 2026-09-21.

This rule states the repository-local section-design policy for README authoring. It makes no external claim, so no external source is cited.
