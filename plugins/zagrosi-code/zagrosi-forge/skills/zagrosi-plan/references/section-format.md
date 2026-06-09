# Section Format

Create `sections/index.md` with parseable blocks at the top:

```markdown
<!-- PROJECT_CONFIG
runtime: python-uv
test_command: uv run pytest
END_PROJECT_CONFIG -->

<!-- SECTION_MANIFEST
section-01-foundation
section-02-core-behavior
section-03-api
END_MANIFEST -->
```

Rules:

- `runtime` and `test_command` are required.
- section names are `section-NN-kebab-case`.
- numbers start at `01` and are sequential.
- keep both blocks before prose.

After the blocks include:

- dependency graph
- execution order grouped into batches
- section summaries with exact ownership boundaries
- notes about sections that can be implemented in parallel
- project notes: runtime, test strategy, harness constraints, known gotchas

Each `section-NN-name.md` should include:

1. status/goal and non-goals
2. dependencies and what those dependencies provide
3. background context copied from `codex-plan.md`
4. file tree for this section
5. tests first: files, cases, fixtures, expected failures
6. implementation details by file path
7. public APIs, signatures, schemas, migrations, payloads, or snippets when
   they remove ambiguity
8. acceptance criteria and verification commands
9. risks, edge cases, rollback notes, and stop conditions

Sections must be self-contained. Copy relevant context from `codex-plan.md`
and `codex-plan-tdd.md` instead of requiring the implementer to read them.

In `standard` mode, target at least 1,000 words per section. In `deep` mode,
target at least 1,500 words. Small documentation-only or cleanup sections can
be shorter only when the section explicitly says why.
