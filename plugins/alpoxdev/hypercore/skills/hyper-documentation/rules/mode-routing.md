# Mode Routing

> Pick exactly one mode from the requested output, then load only that mode's files.

**Purpose**: Decide which of the four modes owns the request, or send the request out of this skill. **Read when**: every run, before the selected mode's first phase.

## 1. Modes

| Mode | Requested output | Typical words | Mode contract |
|---|---|---|---|
| `readme` | A project `README.md`, or a package `README.md` inside a monorepo, written from the codebase | README, 리드미, "프로젝트 소개 문서", install/usage section | `rules/readme/mode-contract.md` |
| `agents-md` | A root or nested `AGENTS.md`, its adjacent `rules/*.md` split, and its `AGENTS.ko.md` mirror | AGENTS.md, "에이전트 지침 파일", nested AGENTS.md | `rules/agents-md/mode-contract.md` |
| `prompt` | A reusable role, system, developer, agent, or task prompt; a prompt template or prompt pack; a prompt eval fixture, judge contract, or regression suite | prompt, 프롬프트, system prompt, template, prompt pack, eval fixture | `rules/prompt/mode-contract.md` |
| `docs` | Any other AI-readable document: an instruction base, agent guide, runbook, operating procedure, specification, policy or rule pack, or harness documentation | 런북, 가이드, 운영 절차, 명세, 규칙 팩, runbook, rule pack | `rules/docs/mode-contract.md` |

## 2. Selection Order

Apply these in order; the first match wins.

1. The request names `README.md` as the output: `readme`.
2. The request names `AGENTS.md`, `AGENTS.ko.md`, a nested `AGENTS.md`, or the `rules/*.md` split of one: `agents-md`.
3. The request names `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` as the output: `agents-md`, boundary only. State that this skill produces `AGENTS.md` and `AGENTS.ko.md` alone, offer that output, and do not create, edit, symlink, rename, or delete the requested file.
4. The output will be reused as an instruction contract or an eval target: `prompt`.
5. The output is any other structured document that an agent or maintainer loads and follows: `docs`.

## 3. Tie-Breaks

- **Two outputs in one request** ("README랑 AGENTS.md 둘 다"): run the modes one after another in the order the user listed them. Each mode keeps its own contract, gates, and report section; never merge two contracts into one pass.
- **"Document this project" with no file named**: a project landing page for people who install or use the code is `readme`; an operating guide, runbook, or instruction base is `docs`. When neither the request nor the repository decides it and the wrong choice would redo the work, ask one question with both readings and a recommendation.
- **Prompt or document**: choose `prompt` only when the output will be reused as an instruction contract or an eval target. A guide *about* prompt engineering is `docs`.
- **Prompts inside a skill folder**: `prompt` owns only the prompt files the request names. The skill folder itself is out of scope (§4).
- **Runtime rule pack**: anchored in `AGENTS.md` is `agents-md`; any other runtime rule pack is `docs`.
- **A one-sentence wording fix for the current reply**: answer directly; it is not a reusable prompt.

## 4. Out of Scope

Route these away by the shape of their output, not by naming another owner:

- A reusable skill folder (`SKILL.md` plus its rules, references, scripts, and assets).
- `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, release notes, or a version bump.
- Answer-only research or a one-off answer with no saved artifact.
- Product code, configuration, or tests, where documentation is a by-product.
- A product planning package (PRD, feature spec, user flow, wireframe) or a pre-implementation plan.
- A search-visibility audit or marketing-page optimization.
- Committing, pushing, or publishing a finished document. The document is authored here; the version-control action that follows is a separate step.

## 5. Route Line

Before the selected mode's first phase, print one Korean line:

```text
모드: <readme|agents-md|prompt|docs> / 근거: <the request phrase or file that selected it>
```

For a §2.3 boundary request, print `모드: agents-md (경계 안내만)`. For a §4 request, print the output shape and stop without loading a mode.

## Sources

> No external sources were used. Content checked 2026-11-07.

| Claim | Source |
|---|---|
| The four modes, the selection order, and the tie-breaks | this package's design, adopted on 2026-11-07 when four single-output documentation workflows were merged into this skill by user instruction |
| The prompt-versus-document rule and the prompt-in-skill-folder rule | the former prompt routing rule of this package, carried over unchanged in substance |
| The `CLAUDE.md` boundary | `rules/agents-md/mode-contract.md` (this package) |
