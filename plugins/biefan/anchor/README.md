# Anchor

Engineering discipline pack for Claude Code & Codex CLI: a skill + 11 slash commands + 4 safety hooks that keep AI on-task on long tasks, enforce E2E verification, multi-pass vulnerability scanning, condition-based codex review, and project-CLAUDE.md pitfall writeback.

- **Upstream repo**: https://github.com/biefan/anchor
- **Release tag**: v1.3.1
- **License**: MIT

## What's in the bundle

This is the mirror bundle for awesome-codex-plugins. For the full repo (including hook scripts, references, evals, and install.sh), see the upstream link above. To install:

```bash
git clone https://github.com/biefan/anchor.git ~/anchor
cd ~/anchor
./install.sh
```

`install.sh` is cross-CLI: it copies the skill + 7 commands to `~/.claude/` and (if codex CLI is on PATH) to `~/.codex/`, and auto-merges hooks into `~/.claude/settings.json` (idempotent, with backup, `--no-hooks` to skip).

## What it does

| Layer | Mechanism |
|---|---|
| **Skill (soft rules)** | `SKILL.md` — 7 core rules: clarify intent, lock task scope, read project contracts, smallest-correct-diff, parallelize agents, condition-based codex review, pitfall writeback. |
| **11 slash commands** | `/ec /lock /pit /scan /done /next /recap /init-claude-md /status /ship /diff /cleanup` |
| **4 hooks (hard enforcement)** | `SessionStart` injects project state; `Stop` blocks "stop" in autonomous mode while tasks remain; `PreToolUse` blocks irreversible bash patterns (force-push, hard-reset, drop, mkfs, dd-to-device, recursive-777, curl-pipe-bash); `PostToolUse` runs the language-appropriate linter after Edit/Write. |

## Validation

- CI: green (`shellcheck` + `jsonlint` + `install.sh` smoke test on clean Ubuntu)
- Stress tests: `evals/stress/03-debug-failing-tests` scored 6/1/1 (pass/fail/N/A) via codex-as-judge
- See [CHANGELOG.md](https://github.com/biefan/anchor/blob/main/CHANGELOG.md) for release notes across v1.0 - v1.3.1

## License

MIT
