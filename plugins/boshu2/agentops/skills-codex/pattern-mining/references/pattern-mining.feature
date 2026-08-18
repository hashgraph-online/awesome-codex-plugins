Feature: Evidence threshold for reusable patterns

  @covered-by:tests/scripts/agentops-native-skills.bats::three-exemplar
  Scenario: A recurring shape earns promotion
    Given three distinct implementation exemplars
    When invariants, variations, and incidental details are separated
    And a separate holdout and back-application pass
    Then the pattern evidence is routed through operationalize

  @covered-by:tests/scripts/agentops-native-skills.bats::hypothesis
  Scenario: Weak pattern evidence remains provisional
    Given the exemplar floor is not met or the holdout does not pass
    When the candidate pattern is evaluated
    Then it is recorded as a bounded hypothesis
    And it cannot route directly to reusable packaging
