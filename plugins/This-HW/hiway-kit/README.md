# hiway-kit

> Turn any task into production-ready code. Specialized agents handle planning, implementation, code review, and security scanning for any stack.

## Install

Pick **one** (installing both loads every skill twice and mixes versions):

```bash
# Anthropic's directory — built into Claude Code
/plugin install hiway-kit@anthropic-plugin-directory
# or: this repository as a marketplace (marketplace name: hiway-kit)
/plugin marketplace add This-HW/hiway-kit
/plugin install hiway-kit@hiway-kit
```

From 5.9.1 the directory gets a **reduced edition**: Anthropic's directory accepts command hooks,
script files and some agent frontmatter keys only from Verified organizations, so that edition has
no hooks, no Python tools, no `code-intel`, `session-history` or `harness-export` skills (they need
those tools), and agents run without worktree isolation. Until a newer version passes the
directory's review it serves 5.5.1. Install from the repository marketplace for the full kit.

Other harnesses (Codex, Antigravity, Gemini CLI) and what each one supports:
[repository README](https://github.com/This-HW/hiway-kit#where-it-runs).

> The published plugin is **`hiway-kit`** — the full kit is 15 agents + 17 skills + 12 rules + hooks.
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
- **PreToolUse** — Blocks reads and edits of sensitive files such as `.env`, SSH/cloud credential directories, key files and credential/secret data files and modules like `credentials.json` or `secrets.py` (`protect-sensitive.py`); source, SQL and docs that only use such a word in a compound name (`credential_collector.py`) are allowed and are outside this guard. It only matches the *path* the agent is about to open and refuses it — it never opens, reads or transmits those files, and it makes no network calls. Credential paths appear in its source because they are the blocklist. <!-- doc-ref-ok: 외부 사용자 레포의 예시 파일명 -->
- **PostToolUse** — Auto-formats the edited file (`auto-format.py`): ruff only when the project configures it (`ruff.toml`, `.ruff.toml` or `[tool.ruff]` in `pyproject.toml`), prettier/eslint only when the project has their config and has them installed, gofmt only inside a Go module (`go.mod`), rustfmt only with `rustfmt.toml`. A project without them is left as is
- **Stop** — Lints edited Python files (same ruff condition) and runs the tests you edited; on failure, the turn continues so the agent fixes it

To turn hooks off, set `HIWAY_KIT_DISABLE_HOOKS` to a comma-separated list (`session-start`, `session-check`, `protect-sensitive`, `auto-format`, `stop-validator`) or `all` in the `env` of your project's `.claude/settings.json` or `.claude/settings.local.json`. Do not edit the cached `hooks.json` — an update restores it. Codex does not read these settings files; there the variable has to be in the environment Codex starts with (not verified).

The hooks do not upload data to the publisher. Programs invoked by hooks and helpers can
write files or access the network; read-only code queries do not sandbox language servers
or project build scripts. Use code intelligence only in trusted workspaces.

## License

MIT — [github.com/This-HW/hiway-kit](https://github.com/This-HW/hiway-kit)
