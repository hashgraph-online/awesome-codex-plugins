Feature: Implement runs one bounded experiment
  @covered-by:skills/implement/scripts/validate.sh::test_runtime_derives_subject
  Scenario: Behavior change follows RED GREEN refactor
    Given one resolved bead or caller intent
    When Implement changes the subject
    Then the first acceptance check fails for the expected missing behavior
    And the smallest change makes it green
    And refactoring preserves the acceptance test

  @covered-by:skills/implement/scripts/validate.sh::test_runtime_derives_subject
  Scenario: Incomplete changed path coverage stays honest
    Given complete changed paths cannot be established
    Then the runtime receipt records incomplete coverage
    And Implement does not infer missing paths
