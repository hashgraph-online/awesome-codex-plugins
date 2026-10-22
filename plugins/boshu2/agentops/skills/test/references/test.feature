Feature: Tests establish accepted observable behavior
  Scenario: Existing acceptance examples drive tests
    Given the caller describes a Job's expected behavior in a bead
    When tests are generated
    Then they observe that behavior using established domain terms
    And no feature file is required just to invoke the skill

  Scenario: New behavior is developed test first
    When the caller selects TDD for missing behavior
    Then the focused test fails for the expected missing behavior before implementation
    And the implemented behavior passes the same test

  Scenario: Coverage is a selected measurement
    When the caller requests important coverage gaps to be filled
    Then before and after measurements accompany the valuable new tests
    And a coverage increase alone does not prove acceptance

  Scenario: Routine test writing stays proportional
    When a useful test is added for existing correct behavior
    Then a green baseline is reported honestly
    And no report file or per-test mutation ceremony is required
