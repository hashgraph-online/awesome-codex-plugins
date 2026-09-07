Feature: Postmortem tests retrospective causal claims
  As an engineer learning from a validated outcome
  I want causal hypotheses challenged against evidence and counterfactuals
  So that retrospective stories do not become unsupported doctrine

  Scenario: An explicit causal question receives bounded analysis
    Given an immutable Validate verdict
    And an explicit retrospective causal question
    When Postmortem reconstructs the evidence-backed timeline
    Then it distinguishes supported claims, rejected claims, and unknowns
    And it cites evidence and counterfactuals

  Scenario: Postmortem does not repeat validation
    Given the acceptance verdict is already immutable
    When Postmortem begins
    Then it does not re-run acceptance validation
    And it does not change proof, bookkeeping, planning, tracker, or delivery state
