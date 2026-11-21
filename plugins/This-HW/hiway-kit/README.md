# hiway-kit

> Turn any task into production-ready code. Specialized agents handle planning, implementation, code review, and security scanning for any stack.

## Install

Pick **one** (installing both loads every skill and hook twice):

```bash
# Anthropic's directory — built into Claude Code
/plugin install hiway-kit@anthropic-plugin-directory
# or: this repository as a marketplace (marketplace name: hiway-kit)
/plugin marketplace add This-HW/hiway-kit
/plugin install hiway-kit@hiway-kit
```

The directory install has **no hooks** (the directory accepts command hooks only from Verified
organizations): skills, agents and rule files only. Install from the repository marketplace to get
session-start rule injection, the sensitive-path guard, auto-format and stop-time checks.

Other harnesses (Codex, Antigravity, Gemini CLI) and what each one supports:
[repository README](https://github.com/This-HW/hiway-kit#other-harnesses-codex--antigravity--gemini-cli).

> The published plugin is **`hiway-kit`** (15 agents + 17 skills + 12 rules + hooks).
> Project-specific extensions live in a user's own `project-local/` tier, not as separate
> published plugins.

## Key Skills

A selection below — 17 skills total, auto-discovered from `skills/` (not hand-listed here).

| Command                     | Description                                              |
| --------------------------- | -------------------------------------------------------- |
| `/plan-task`                | Structured task planning into a plan file                |
| `/auto-dev`                 | Run a completed plan through development and validation  |
| `/review`                   | Lint + adversarial review + security scan                |
| `/debug`                    | Diagnose an error, fix it, confirm the fix               |
| `/test`                     | Run tests and fix failures                               |
| `/multi-perspective-review` | Multi-perspective deliberation, consensus-driven         |
| `/web-research`             | Research with the search/docs/browser tools you have     |
| `/agent-creator`            | Create a project agent (`.claude/agents/`) with valid frontmatter |

## Agents

15 agents in one flat `agents/` folder, grouped here by role:

| Role       | Examples                                                               |
| ---------- | ---------------------------------------------------------------------- |
| Planning   | `clarify-requirements`, `define-business-logic`, `design-user-journey` |
| Development and review | `implement-code`, `fix-bugs`, `review-code`, `security-scan` |
| Meta       | `devils-advocate`                                                      |

## Hooks (auto-registered in Claude Code)

The blocking and Stop hooks below are Claude Code behavior; on Codex only session-start and auto-format ship.


- **SessionStart** — Injects governance rules, recurring review lessons, and open plan files
- **PreToolUse** — Blocks reads and edits of sensitive files such as `.env`, SSH/cloud credential directories and key files (`protect-sensitive.py`). It only matches the *path* the agent is about to open and refuses it — it never opens, reads or transmits those files, and it makes no network calls. Credential paths appear in its source because they are the blocklist.
- **PostToolUse** — Auto-formats the edited file (`auto-format.py`: ruff for Python; prettier/eslint only when the project has them installed)
- **Stop** — Lints edited Python files and runs the tests you edited; on failure, the turn continues so the agent fixes it

The hooks do not upload data to the publisher. Programs invoked by hooks and helpers can
write files or access the network; read-only code queries do not sandbox language servers
or project build scripts. Use code intelligence only in trusted workspaces.

## License

MIT — [github.com/This-HW/hiway-kit](https://github.com/This-HW/hiway-kit)
