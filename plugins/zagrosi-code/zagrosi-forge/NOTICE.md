# NOTICE

## Attribution

Zagrosi Forge provides shared workflows for Codex and Claude Code, inspired by
Pierce Lamb's MIT-licensed Deep Trilogy Claude Code plugins:

| Upstream Project | Repository |
|------------------|------------|
| Deep Project | https://github.com/piercelamb/deep-project |
| Deep Plan | https://github.com/piercelamb/deep-plan |
| Deep Implement | https://github.com/piercelamb/deep-implement |

## Adapted Ideas

The following high-level ideas informed this package:

- decomposing broad project briefs into smaller planning units
- generating implementation plans before code changes
- sectionizing work into implementation-ready markdown files
- encouraging test-first implementation and code review
- preserving durable workflow artifacts on disk

## Zagrosi Forge Changes

This package adapts those ideas into shared skills and a verified Python runtime:

- Codex and Claude Code plugin metadata pointing to the same `skills/` tree
- compact plans at every depth, with review performed by the active agent
- resumable state inferred from files on disk
- deterministic Python helper commands in `scripts/zagrosi_skills.py`
- Forge metadata via `FORGE_META`
- quality profiles, strict gates, SARIF/JSONL export, trace exports, and
  dependency-aware section helpers
- backward-compatible parsing and helper aliases for migrated `deep-*` artifacts

## License

Zagrosi Forge is distributed under the MIT License. See [LICENSE](LICENSE).
