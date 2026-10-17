# Skill Sync Publisher

`skill-sync-publisher` validates and synchronizes one local `SKILL.md` package
across GitHub, Awesome Codex Plugins, HOL Registry, skills.sh, SkillsMP,
LobeHub, ClawHub, and Cursor Directory.

The GitHub repository is the canonical source. The CLI remembers platform
choices per skill, never stores credentials, supports dry-runs, and records
partial failures for later resume.

```bash
./bin/skill-sync preflight ./path/to/skill
./bin/skill-sync sync ./path/to/skill --dry-run --json
./bin/skill-sync sync ./path/to/skill
```

Authenticated publishing requires the user to log in first. Directory sites
without a stable publisher API produce a browser/manual handoff instead of an
unverified upload claim.
