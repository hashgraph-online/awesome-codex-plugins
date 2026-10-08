# Executable contract for Skill Builder audit; coverage in test_skill_audit.bats
# and skillshealth evidence tests. No skill/provider trial runs during this audit.
Feature: Skill audit separates evidence without an optimization rank
  Scenario: Untested conformant package
    Given a valid package for the selected static profile
    When the default audit runs
    Then static conformance passes
    And effects and behavioral evidence remain NOT_PROVEN
    And no aggregate score or quality verdict is emitted

  Scenario: Layout and irrelevant additions do not improve substantive evidence
    Given equivalent concise layouts and optional unreferenced files
    When the default audit runs
    Then substantive conformance and behavioral results are unchanged
    And necessary prohibitions never become blocking authoring defects

  Scenario: Concrete defects survive decoration
    Given a missing required resource or unsupported portable field
    When labels and irrelevant helpers are added
    Then the concrete conformance defect still fails

  Scenario: Located reachable effects
    Given SKILL.md links a script piping a remote response into a shell
    When the default audit runs
    Then the report locates that conditional execution path
    And safety remains NOT_PROVEN after adding reassuring labels

  Scenario: Explicit legacy field and exit compatibility
    When the audit runs with --legacy
    Then audit-report-legacy.json describes the complete old report
    And the accepted S1 field and exit behavior is preserved
