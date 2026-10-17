Feature: Memory learning stays off the critical path
  Scenario: Missing learning never changes a verdict
    Given a durable verdict collection
    When Memory mining is not requested
    Then candidate validity is unchanged

  Scenario: Learning remains advisory
    When Memory mining detects recurring evidence
    Then it cites distinct verdict and finding digests
    And it does not promote a rule or choose continuation
