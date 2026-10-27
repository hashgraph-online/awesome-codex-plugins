Feature: Independent challenge of consequential ideas

  @covered-by:tests/scripts/agentops-native-skills.bats::sealed
  Scenario: A one-way door receives sealed challenge evidence
    Given a contested decision is costly to reverse
    When distinct contexts propose before seeing one another and then cross-review
    Then every perspective is cross-reviewed by another
    And dissent and refutation attempts remain in an idea-challenge packet
    And the packet returns to the caller as advisory evidence for Plan
    And it carries no readiness verdict

  @covered-by:tests/scripts/agentops-native-skills.bats::reversible
  Scenario: A two-way door stays lightweight
    Given a choice is cheap to undo
    When its door class is evaluated
    Then it routes to Plan's one fresh challenge
    And no idea-challenge packet or orchestration substrate is produced
