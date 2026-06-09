# Forge Depth Standards

Forge planning should match the depth of strong Deep Trilogy artifacts and then
add Codex-native quality gates. The aim is not word count for its own sake; the
aim is that a fresh implementer can build from the artifact without reopening
the original conversation.

## Reference Bar

Observed strong planning artifacts:

- implementation plans: commonly 4,000-11,000 words
- TDD plans: commonly 1,500-3,300 words
- review files: commonly 2,000-3,200 words
- section indexes: commonly 650-1,000 words
- implementation sections: commonly 1,500-4,000 words each
- generated section prompts: around 300+ words, with explicit context files and
  self-contained output rules

## Word Targets

| Artifact | Fast | Standard | Deep |
|----------|------|----------|------|
| `codex-spec.md` | 700+ | 1,200+ | 1,800+ |
| `codex-research.md` | 700+ | 1,500+ | 2,500+ |
| `codex-plan.md` | 900+ | 2,500+ | 5,000+ |
| `codex-plan-tdd.md` | 450+ | 1,200+ | 2,000+ |
| review file | 500+ | 1,000+ | 1,800+ |
| `codex-integration-notes.md` | 500+ | 900+ | 1,500+ |
| `sections/index.md` | 350+ | 700+ | 900+ |
| each `section-*.md` | 250+ | 1,000+ | 1,500+ |

Below target is not automatically wrong for a tiny change, but it must be a
conscious exception. In standard and deep mode, prefer expanding the artifact
until it clears the target before moving on.

## Plan Must Include

`codex-plan.md` should have:

1. Reader note: explicitly says the plan is self-contained.
2. Context in one page: current system, problem, constraints, verified facts.
3. Architecture at a glance: diagram or layered explanation.
4. Rationale: why each major decision was chosen, including rejected options.
5. Data/contracts: schemas, payloads, APIs, config, CLI behavior, permissions.
6. File tree or file-by-file map: exact create/modify paths.
7. Phase plan: batches, dependencies, parallel work, hard gates.
8. Test strategy: unit/integration/e2e, fixtures, mocks, expected failures.
9. Security/privacy/ops: auth, secrets, migration, observability, rollback.
10. Risks/open questions: what can still fail and when to stop for the user.

Use signatures, schemas, and snippets when they remove ambiguity. Do not paste
full production implementations.

## TDD Plan Must Include

`codex-plan-tdd.md` should map each behavior to concrete tests:

- test file paths
- test names or precise descriptions
- fixtures/factories/test data
- expected first failure before implementation
- command to run
- mocks, containers, network boundaries, and skip conditions
- section ownership where a test belongs to one section

## Section Files Must Include

Each `section-NN-name.md` should be implementation-ready:

1. Goal and non-goals.
2. Dependencies on prior sections.
3. Background context copied from the plan.
4. File tree for this section.
5. Tests first with expected failures.
6. Implementation details by file.
7. Public API/signature/schema snippets where useful.
8. Acceptance criteria and verification commands.
9. Risks, edge cases, rollback, and out-of-scope boundaries.
10. Post-implementation documentation or review notes if relevant.

The section must not say "see the plan" for essential behavior. Copy the needed
facts into the section.
