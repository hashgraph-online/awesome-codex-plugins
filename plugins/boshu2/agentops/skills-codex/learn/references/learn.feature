Feature: Learn stays off the critical path
  Scenario: Missing Learn never changes a verdict
    Given a durable verdict collection
    When Learn is not invoked
    Then candidate validity is unchanged

  Scenario: Learning remains advisory
    When Learn detects recurring evidence
    Then it cites distinct verdict and finding digests
    And it does not promote a rule or choose continuation
