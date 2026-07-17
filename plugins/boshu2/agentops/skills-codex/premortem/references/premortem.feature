Feature: Premortem optionally challenges one frozen plan
  Scenario: A fresh judge returns advisory findings
    Given a bead or caller intent with a runtime-derived digest and author context ID
    When a distinct fresh judge challenges its acceptance, scope, and evidence
    Then Premortem returns findings with checked and not-checked scope
    And an empty finding set grants no lifecycle permission

  Scenario: Premortem stops after the review
    Given any advisory finding set
    When the review is complete
    Then Premortem does not implement, validate, retry, schedule, claim, operate Git, release, or deliver
    And the caller owns whether to revise the plan or invoke RPI
