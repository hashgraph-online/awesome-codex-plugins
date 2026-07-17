# Executable spec for skill-builder's deep audit mode (absorbed from the retired /skill-auditor) —
# skill template audit (BC1 Corpus / Skill Catalog).
# The audit checks an existing SKILL.md against the unified template: Pass 1 gates
# through heal.sh --strict, Pass 2 runs additional structural checks, then it emits a
# density report and a productization score. Hexagon: supporting; consumes: a SKILL.md +
# the template; produces: audit-report.json. (soc-qk4b)

Feature: Skill-auditor scores a skill against the unified template
  As a catalog maintainer
  I want each skill audited for hygiene and structure
  So that drift from the template is caught before it ships

  Background:
    Given an existing SKILL.md and the unified template

  Scenario: Pass 1 delegates hygiene to heal.sh
    When /skill-auditor runs
    Then Pass 1 delegates the hygiene checks to heal.sh --strict by exit code

  Scenario: Pass 2 runs the additional structural checks
    When Pass 1 completes
    Then Pass 2 runs the additional template-conformance checks

  Scenario: A density report and productization score are emitted
    When both passes complete
    Then it emits an advisory density report and a productization score in audit-report.json
