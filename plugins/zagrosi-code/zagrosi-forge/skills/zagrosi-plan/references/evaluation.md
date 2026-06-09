# Forge Evaluation

Use this when comparing Forge outputs, auditing example quality, or preparing a
release. Evaluation should be based on artifacts and gates, not preference.

## Core Metrics

- Plan depth: word targets, contracts, architecture rationale, migration,
  rollout, rollback, and acceptance.
- Evidence quality: inspected files, commands, test discovery, runtime
  detection, and explicit assumptions.
- Traceability: every REQ-* appears in plan, TDD plan, and sections.
- Implementation readiness: section file ownership, tests-first detail,
  dependencies, rollback, and commands.
- Review integration: findings accepted, rejected, or deferred with rationale.

## Commands

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py forge-score --planning-dir "{planning_dir}" --depth standard --strict
python3 {plugin_root}/scripts/zagrosi_skills.py lint-evidence --planning-dir "{planning_dir}" --strict
python3 {plugin_root}/scripts/zagrosi_skills.py lint-implementation-readiness --planning-dir "{planning_dir}" --strict
python3 {plugin_root}/scripts/zagrosi_skills.py eval-suite --examples-dir examples --output examples/evals/latest.json
```

## Benchmark Notes

When comparing against another planning system, keep the same input brief,
same codebase snapshot, same allowed tools, and same depth expectation. Do not
give one system hidden context that the other system lacks.
