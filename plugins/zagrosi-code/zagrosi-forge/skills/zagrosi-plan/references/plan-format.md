# Plan format

Start `codex-plan.md` with actual values:

```markdown
<!-- FORGE_META
{"artifact_type":"implementation_plan","workflow":"zagrosi-plan","depth_mode":"<depth>","source":"<relative-path>","requirement_ids":["REQ-..."]}
END_FORGE_META -->
```

Cover only:

1. outcome, requirements, acceptance, non-goals
2. decision evidence and assumptions
3. exact paths, behavior, interfaces/data/errors, compatibility/migration
4. section ownership, dependencies, shared sequencing, safe parallelism
5. each `REQ-*` -> test path/case, expected RED, command, acceptance signal
6. material failure -> mitigation, owner, rollback or stop condition

Prefer identifiers and tables. Omit repository summaries, repeated source,
production code, routine explanation, and placeholders.
