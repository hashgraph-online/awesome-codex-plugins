---
name: skill-sync-publisher
description: Safely validate, publish, and track a local SKILL.md directory across GitHub, Awesome Codex Plugins, HOL Registry, skills.sh, SkillsMP, LobeHub, ClawHub, and Cursor Directory. Use when the user asks to publish, update, register, or synchronize an agent skill across marketplaces.
---

# Skill Sync Publisher

Use the bundled CLI to preflight and synchronize one local skill directory. The
source GitHub repository is canonical; registry entries are projections of that
source. Read `references/platform-matrix.md` before working with a platform and
`references/security-policy.md` when preflight reports a security finding.

## Safety rules

- Start with `python3 scripts/sync.py preflight <skill-dir>` or `--dry-run`.
- Never collect or store passwords, tokens, cookies, or private keys.
- Ask before the first submission to each platform. Persist choices per GitHub
  repository, skill path, and platform in the user state file, not the repo.
- Require the user to complete login before running an authenticated identity
  check. A failed check blocks only that platform.
- Show the exact diff and commit scope before GitHub commit/push.
- Use official CLIs when available. For directory sites without a supported
  API/CLI, create a browser/manual handoff instead of inventing an endpoint.
- Never touch unrelated dirty files, force-push, or roll back successful targets.

## Commands

Run `bin/skill-sync` from the repository root:

```text
bin/skill-sync init <skill-dir>
bin/skill-sync preflight <skill-dir>
bin/skill-sync layout --check
bin/skill-sync layout --write
bin/skill-sync sync <skill-dir> --dry-run --json
bin/skill-sync sync <skill-dir> --platform github,clawhub
bin/skill-sync sync <skill-dir> --resume
bin/skill-sync status <skill-dir> --refresh
bin/skill-sync reset-choice <skill-dir> <platform>
bin/skill-sync reset-all <skill-dir>
bin/skill-sync forget <skill-dir>
```

`skills/skill-sync-publisher/` is the canonical skill content. Root `SKILL.md`
and `agents/openai.yaml` are generated mirrors; use `layout --write` after a
canonical change and `layout --check` in CI.

`sync` is confirmation-gated by default. `--yes` is intended for an already
reviewed, authenticated automation job; it does not bypass platform choice or
security blockers. The CLI returns non-zero if a selected platform fails or is
blocked.

## Platform behavior

- GitHub: commit and push only the target skill files after confirmation.
- Awesome Codex Plugins: create or update a PR only when a valid plugin manifest
  exists; ordinary skills are blocked unless explicitly projected.
- HOL Registry: use the official `npx @hol-org/registry` quote/publish flow and
  require `REGISTRY_BROKER_API_KEY` before an authenticated publish.
- ClawHub: use `clawhub whoami`, dry-run, then the manifest version as semver.
- skills.sh, SkillsMP, LobeHub, Cursor Directory: verify public GitHub source
  and produce/check an index or browser handoff; `planned` is not success.

Never publish to an unselected platform, duplicate an open PR, or claim that a
manual directory submission is complete before the user confirms it.
