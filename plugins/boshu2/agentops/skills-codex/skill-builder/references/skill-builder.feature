# Executable spec for the /skill-builder skill — skill scaffolding (BC1 Corpus / Skill Catalog).
# /skill-builder scaffolds a new SKILL.md (or absorbs an existing one) against the unified
# AgentOps template, then generates the Codex parity bundle, self-audits, and overlays a
# factory score. Hexagon: supporting; consumes: a build request + the unified template;
# produces: a new skill + build-report.json. (soc-qk4b)

Feature: Skill-builder materializes template-conformant skills
  As an author adding a skill to the catalog
  I want it scaffolded from the unified template and parity-checked
  So that every new skill is well-formed and Codex-mirrored from the start

  Background:
    Given the unified AgentOps SKILL.md template

  Scenario: A mode is dispatched for build or absorb
    When /skill-builder runs
    Then it dispatches the requested mode (scaffold a new skill or absorb an existing one)

  Scenario: The skill is materialized from the template
    When the build proceeds
    Then it produces a SKILL.md conformant to the unified template

  Scenario: The Codex parity bundle is generated
    When the skill is materialized
    Then it generates the matching skills-codex bundle and hashes

  Scenario: The build self-audits and scores before reporting
    When materialization completes
    Then it self-audits the result and overlays a factory score in build-report.json
