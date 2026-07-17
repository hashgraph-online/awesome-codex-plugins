Feature: Research answers one bounded question
  Scenario: Load-bearing claims are cited
    Given a bounded question and required evidence
    When Research examines the smallest relevant sources
    Then observations and inferences are distinguished
    And every load-bearing claim cites authoritative evidence

  Scenario: Research stops at the evidence boundary
    Given a cited answer with checked and unchecked scope
    When Research reports the result
    Then it does not approve work, select a next action, retry, or mutate lifecycle state

  Scenario: Multiple caller-supplied reports are synthesized once
    Given several identified reports that address one bounded question
    When Research compares their load-bearing claims
    Then every claim preserves its report identity and evidence reference
    And agreement, contradiction, and unknown are reported separately
    And Research emits one synthesis without creating an umbrella or starting a new runtime
