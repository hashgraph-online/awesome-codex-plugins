Feature: Skill Builder creates an explicitly incomplete source and owned projections
  Scenario: A small adapter starts without optional helper files
    When build.sh from-scratch creates a named package
    Then SKILL.md is its only created source file
    And its report says authoring_state scaffold and semantics_evaluated false
    And the source carries metadata.authoring_state scaffold
    And strict source checking reports INCOMPLETE_SCAFFOLD

  Scenario: Completed concise behavior needs no decorative sections
    Given an author states applicability, inputs, authority, result, done and failure
    And removes the explicit scaffold state after authoring
    When the source is checked, projected and audited
    Then missing optional helpers and heading labels do not block conformance
    And a fresh reviewer still judges semantic completeness

  Scenario: External observation remains clean-room
    When absorb-external receives an existing input file
    Then it records the source hint and creates blank placeholders
    And it copies no external name, prose, prompt, script or example

  Scenario: A report destination is explicit
    When no report path is supplied
    Then build JSON is returned on stdout without a workspace receipt
    When a new report path in a protected external non-Git directory is supplied
    Then Go writes the compatible report with a one-file source list
