<div align="center">

# development-skills

**A disciplined engineering workflow for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [Codex CLI](https://github.com/openai/codex).**

Start with brainstorming, let the user decide what matters, keep decisions on disk, and verify claims with evidence.

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

[`shared/development-loop.md`](shared/development-loop.md) is injected at session start and kept short, because long injected rules are followed less.

A request to build, change, fix, or design something starts with `brainstorming`. It sizes the task:

| Task | What happens | Work record |
|---|---|---|
| Small and clear, one obvious solution | The agent goes straight to work and runs the agreed check. | None. |
| Open decisions, or a change across several files, contracts, or data | The agent explores, asks the user the business decisions, checks the design with `rethink`, and presents a plan in four parts for `Approve`, `Edit`, or `Cancel`. | A plan and a decision chronicle. |

Planned work keeps two files:

- `docs/plans/YYYY-MM-DD__<slug>.md` records design, exact work, checks, and current state.
- `docs/chronicles/YYYY-MM-DD__<slug>.md` records the request, reasons, rejected alternatives, and useful failed approaches.

The user makes the functional and business decisions; the agent makes the technical choices, each with its reason.
When the user's design has a CRITICAL or HIGH defect, the agent stops and proposes the better design.
Approved work continues through implementation, verification, independent review, explanation, and documentation alignment.

The agent asks every question with choices through a menu you navigate with the arrow keys.
In Codex the menu works outside Plan mode only after you add `default_mode_request_user_input = true` under `[features]` in `~/.codex/config.toml`.
Codex 0.166.0 still marks that flag as under development; set it back to `false` if a Codex version breaks it.

## Included capabilities

The plugin ships 23 skills:

| Area | Skills |
|---|---|
| Core work | `using-development-skills`, `brainstorming`, `create-test`, `explain-diff`, `staff-review`, `phone-a-friend`, `roast-my-code`, `best-practices`, `rethink`, `bro` |
| Project health | `align-standards`, `refactor-loop`, `evolve-loop`, `align-docs`, `simplify-stuff`, `resolve-merge`, `wrap-up-branch`, `update-deps`, `changelog`, `commit`, `handoff` |
| Evaluation | `ai-agent-bench`, `plugin-feedback` |

`align-standards`, `simplify-stuff`, `wrap-up-branch`, and `phone-a-friend` require manual invocation. `using-development-skills` starts automatically. Other skills run when their descriptions match or you invoke them.

The loops run only when you name them. In Claude Code, start one with `/goal /refactor-loop [focus]` or `/goal /evolve-loop [focus]`: the agent loads the skill, agrees with you on done and verification, then keeps working until it reports `DONE` or `BLOCKED`. In Codex, invoke `$refactor-loop` or `$evolve-loop`; the agent creates the goal itself once done and verification are agreed.

`bro` switches explanations to plain language without dropping necessary facts.
`phone-a-friend` asks the other CLI family for an independent, read-only opinion.
To check whether a change makes agent work better or worse, use the [eval suite](evals/README.md).

One named subagent ships: [`staff-reviewer`](agents/staff-reviewer.md).
Implementation and verification stay in the main context.

## Shared contracts

- [`development-loop.md`](shared/development-loop.md) owns skill selection, decisions, plan approval, standards, and the open points to close.
- [`engineering.md`](shared/engineering.md) owns language-agnostic code and design rules.
- [`writing.md`](shared/writing.md) owns plain natural-language text.
- [`documentation.md`](shared/documentation.md) owns repository document metadata and lifecycle.
- [`review-categories.md`](shared/review-categories.md) owns severity definitions.
- [`unattended-runs.md`](shared/unattended-runs.md) owns autonomous run limits and reporting.

The plugin does not ship language, framework, organization, or product conventions.
It reads those rules from the target repository.

## Hooks

| Hook | Purpose |
|---|---|
| `session-start` | Inject the development loop before the first decision. For Codex, which has no output styles, it also injects the writing contract. |
| `user-prompt` | Add one sentence next to each message, so new work in the middle of a session also starts with `brainstorming`. |
| `auto-format` | Apply a best-effort formatter after an edit. Project checks remain authoritative. |
| `plan-approved` | Continue approved work without asking for the same approval again. |

Claude Code loads [`shared/writing.md`](shared/writing.md) as the plugin output style.
[Codex tool mappings](skills/using-development-skills/references/codex-tools.md) describe client differences.

## Acknowledgments

Inspired by [superpowers](https://github.com/obra/superpowers) by Jesse Vincent.
This project adds brainstorming-first task sizing, persistent decision records, one clean-context reviewer, and language-agnostic contracts.

## Contributing

Open an issue before substantial work, then read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
