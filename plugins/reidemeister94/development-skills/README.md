<div align="center">

# development-skills

**A disciplined engineering workflow for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [Codex CLI](https://github.com/openai/codex).**

Use the smallest safe workflow, keep important decisions on disk, and verify claims with evidence.

<a href="https://github.com/reidemeister94/development-skills/releases"><img src="https://img.shields.io/github/v/release/reidemeister94/development-skills?style=flat-square&color=2563EB" alt="Release"/></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/reidemeister94/development-skills?style=flat-square" alt="License"/></a>

</div>

---

## Install

Claude Code:

```text
/plugin marketplace add reidemeister94/development-skills
/plugin install development-skills@development-skills
```

Codex CLI:

```bash
codex plugin marketplace add reidemeister94/development-skills
```

Then open `/plugins`, find `development-skills`, and install it.

The plugin activates for development work.
Hooks run automatically on Claude Code and supported Codex versions.
When Codex does not load plugin hooks, run the relevant formatter manually with [`hooks/auto-format`](hooks/auto-format).

## How it works

[`shared/development-loop.md`](shared/development-loop.md) selects the smallest path that fits the work:

| Path | Use it when | Work record |
|---|---|---|
| Direct | One clear, reversible change has a known proof. | None. |
| Bounded | The result is clear, but several modules or a high-impact contract need review. | Chat summary and independent review when risk requires it. |
| Full | Decisions need lasting reasons, proof needs design, or another session must resume the work. | A plan and decision chronicle. |

The full path keeps two files:

- `docs/plans/YYYY-MM-DD__<slug>.md` records design, exact work, checks, and current state.
- `docs/chronicles/YYYY-MM-DD__<slug>.md` records the request, reasons, rejected alternatives, and useful failed approaches.

The user approves a presented plan before implementation.
Approved work continues through implementation, verification, independent review, explanation when useful, and documentation alignment.

## Included capabilities

The plugin ships 22 skills:

| Area | Skills |
|---|---|
| Core workflow | `using-development-skills`, `brainstorming`, `create-test`, `explain-diff` |
| Review and improvement | `staff-review`, `roast-my-code`, `refactor`, `simplify-stuff`, `rethink` |
| Documentation and Git | `align-docs`, `changelog`, `commit`, `handoff`, `resolve-merge`, `wrap-up-branch` |
| Research and evaluation | `best-practices`, `ai-agent-bench`, `eval-regression`, `phone-a-friend`, `plugin-feedback` |
| Communication and maintenance | `bro`, `update-deps` |

`refactor`, `simplify-stuff`, `phone-a-friend`, and `wrap-up-branch` require explicit invocation.
`bro` switches explanations to plain language without dropping necessary facts.
`phone-a-friend` asks the other CLI family for an independent, read-only opinion.

One named subagent ships: [`staff-reviewer`](agents/staff-reviewer.md).
Implementation and verification stay in the main context.

## Shared contracts

- [`development-loop.md`](shared/development-loop.md) owns scope, authorization, path selection, and completion.
- [`full-path.md`](shared/full-path.md) owns persistent work records and full-path steps.
- [`engineering.md`](shared/engineering.md) owns language-agnostic code and design rules.
- [`writing.md`](shared/writing.md) owns plain natural-language text.
- [`documentation.md`](shared/documentation.md) owns repository document metadata and lifecycle.
- [`review-categories.md`](shared/review-categories.md) owns severity definitions.

The plugin does not ship language, framework, organization, or product conventions.
It reads those rules from the target repository.

## Hooks

| Hook | Purpose |
|---|---|
| `session-start` | Inject the router and writing contract before the first decision. |
| `auto-format` | Apply a best-effort formatter after an edit. |
| `plan-approved` | Continue approved work without asking for the same approval again. |

Claude Code also loads [`shared/writing.md`](shared/writing.md) as the plugin output style.

## Acknowledgments

Inspired by [superpowers](https://github.com/obra/superpowers) by Jesse Vincent.
This project adds risk-based paths, persistent decision records, one clean-context reviewer, and language-agnostic contracts.

## Contributing

Open an issue before substantial work, then read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
