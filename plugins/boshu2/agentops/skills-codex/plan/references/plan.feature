Feature: Plan refines the existing intent source
  @covered-by:skills/plan/scripts/validate.sh::test_no_model_authored_packet
  Scenario: Normal and edge acceptance are bounded
    Given a caller intent
    When Plan shapes the intent
    Then acceptance and write scope are updated in that source or proposed to the caller
    And no AgentOps plan packet is created

  @covered-by:skills/plan/scripts/validate.sh::test_no_model_authored_packet
  Scenario: Advisory decomposition does not create control artifacts
    Given an intent has advisory decomposition
    Then it contains no owner, ready, claim, priority, attempt, wave, queue, lease, admission, next action, closure, release, or delivery state
