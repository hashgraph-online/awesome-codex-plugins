# vsql-extension-builder

A Claude Code skill that builds a VillageSQL extension end-to-end.

The skill drives a 7-phase persona-driven workflow — requirements,
feasibility, scaffold, implementation, CTO review, UAT, documentation — and
discovers the current VEF API from live SDK headers during Phase 2. No
hardcoded API names; the skill stays correct as the SDK evolves.

## Entry point

The agent loads [`SKILL.md`](SKILL.md). It contains the phase-by-phase
workflow, gate definitions, and the resume protocol for picking up after a
crash or auto-compaction.

## References

Detail loaded on demand by `SKILL.md`:

| File | Used for |
|---|---|
| [`references/philosophy.md`](references/philosophy.md) | Core principles, scope, gate rules |
| [`references/capabilities.md`](references/capabilities.md) | VEF capability probes (headers + behavior) |
| [`references/cto-checklist.md`](references/cto-checklist.md) | Phase 4 critic agent input |
| [`references/patterns.md`](references/patterns.md) | Implementation standards, data patterns, naming |
| [`references/environment.md`](references/environment.md) | Build, test, paths, DDL syntax |

## Invoking

After install (see the [top-level README](../../README.md)), invoke from any
directory:

```
/vsql-extension-builder
```

Or with an initial description:

```
/vsql-extension-builder add a base58 encoding extension
```

The skill clones the new extension as a subdirectory of wherever you invoke
it. The recommended workspace is the
[villagesql-samples](https://github.com/villagesql/villagesql-samples) repo.
