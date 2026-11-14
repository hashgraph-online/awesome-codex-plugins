# DocSpring Agent Playbook

How we work with coding agents at [DocSpring](https://docspring.com): the engineering principles, AGENTS.md templates
and workflow skills behind our own setup, for Claude Code, Codex, Cursor, Gemini CLI and others. Borrow what fits and
adapt it to your codebase.

Adapted from the instructions and skills DocSpring's coding agents use. We generate PDFs, fill forms and collect
e-signatures, where a wrong value in a document is worse than an error, so the rules lean towards care.

The principles are opinionated: each says what we do, why, and when it doesn't fit. Sections whose headings start
with "If" cover particular stacks and product models (public APIs, generated client libraries, self-hosted installs,
code on customers' pages); skip the ones that don't match yours. Check every command and policy against your own
repository before you adopt it.

## What's here

| Folder | What it is |
| --- | --- |
| [`principles/`](principles/) | The engineering rules behind everything else, each with its reason and how to enforce it |
| [`templates/AGENTS.md`](templates/AGENTS.md) | A root AGENTS.md to copy and fill in |
| [`templates/nested/`](templates/nested/) | Example AGENTS.md files for directories: database, tests, public API, background jobs, UI, CI and more |
| [`guides/`](guides/) | How to write AGENTS.md files and skills that agents actually follow |
| [`skills/`](skills/) | Workflow skills that read your tracker, CI and test setup from your AGENTS.md |

## Skills

| Skill | Use it when |
| --- | --- |
| [`story-kickoff`](skills/story-kickoff/) | Starting a ticket. Investigates before any code is written: checks the ticket's claims against the code, maps callers, stored data and the contracts others rely on, and writes a plan in which every regression test states how it fails today. |
| [`pr-review`](skills/pr-review/) | Reviewing a pull request, or your own branch before you open one. Plans focus areas, investigates them with read-only investigators, keeps every piece of evidence in a review folder, and works through the findings with you; nothing is fixed or posted until you approve it. |
| [`second-opinion-review`](skills/second-opinion-review/) | You want an independent review from another model's CLI (Codex by default), run unattended, kept away from the first reviewer's notes, with every finding verified before you see it. |
| [`fix-ci`](skills/fix-ci/) | CI is red or a PR has review comments. Waits for the whole pipeline, fixes every failure and valid comment in one push, resolves the threads its fixes addressed, and repeats until green. |
| [`ui-qa-pass`](skills/ui-qa-pass/) | A branch changes what people see. QAs the changed screens in the states, themes and widths that matter for the change, fixes what it finds with before and after shots, and reports what it tested, what it didn't, and the decisions left for you. |
| [`session-wrap-up`](skills/session-wrap-up/) | Ending a session. Re-reads the whole transcript to find everything raised but not resolved, and proposes one list with an action for each item. |

The skills read your tracker, code host, CI and test commands from an `## Agent workflow settings` section in your
root AGENTS.md ([`CONFIGURE.md`](CONFIGURE.md) has the block to copy); a skill that needs a missing setting asks once.
What the agent may do without asking is read from your base branch, so a branch or pull request can't approve its own
pushes or comments.
They ship worked adapters for GitHub, GitHub Actions and the Codex CLI; for other tools, write and check your own
adapter.

## What the skills run and send

The skills run the tools your AGENTS.md settings name, and ship no services or telemetry of their own.

- `pr-review`, `fix-ci` and `session-wrap-up` use the GitHub CLI (`gh`) to read and update pull requests, checks and
  comments in your repository. `pr-review` posts nothing until you approve it.
- `story-kickoff` and `session-wrap-up` use your tracker's command to read tickets, and to create or move them when
  you or the settings approve it.
- `second-opinion-review` runs your Codex CLI, which sends the review prompt, the diff and the files Codex reads to
  OpenAI under your Codex account.
- `ui-qa-pass` drives a headless Chromium with Playwright against the app URL you give it. If your repository has
  no browser automation, it shows you the command to install a pinned Playwright version and asks first.
- `session-wrap-up` reads your agent's session transcript from your machine.

Review notes, plans and screenshots are written to the folders your settings name.

## Install

Skills, for any agent the [skills CLI](https://github.com/vercel-labs/skills) supports:

```bash
npx skills add DocSpring/docspring-agent-playbook
```

Claude Code plugin:

```text
/plugin marketplace add DocSpring/docspring-agent-playbook
/plugin install docspring-agent-playbook@docspring-agent-playbook
```

Or copy a skill folder into your agent's skills directory (`.claude/skills/`, `.agents/skills/`). Skills that use
subagents ship the definition in their `agents/` folder: copy it to `.claude/agents/` in Claude Code, or paste its body
into a general-purpose subagent elsewhere.

The templates and principles aren't installed: read them, copy what applies into your own AGENTS.md files, and delete
the rest. Short files work better than complete ones.

## The two rules everything else leans on

**The smallest complete change.** The change reaches every place it must (callers, sibling entry points, the other
client that applies the same rule, tests, docs) and fixes the problems found in the same code, in one PR. The solution
is small: reuse what the codebase already has, and add no option, setting, compatibility path or repair task nobody
asked for. Problems elsewhere get recorded with a recommended next step, not fixed by default.

**A review finding needs a trigger that can really happen.** Be thorough with code the change adds and with anything
that could put a wrong value in your output, lose data or open a security hole; hostile input counts when it reaches
one of those. Don't fix inputs that no real user, file or system produces. Report problems in code the change didn't
touch, without fixing them by default. A fix bigger than the code it reviews goes to a person as a decision.

Both are in [`principles/change-size.md`](principles/change-size.md).

## Credits

Our smallest-complete-change rule was sharpened after evaluating [Ponytail](https://github.com/DietrichGebert/ponytail)
(MIT), whose lean checklist is worth reading alongside it. The pr-review skill builds on one written by our teammate
David Benton.

## Contributing

Issues and pull requests are welcome, especially rules that would have saved you from a real bug. See
[`AGENTS.md`](AGENTS.md) for how this repository is written.

## License

[MIT](LICENSE)
