Feature: Postmortem tests retrospective causal claims
  As an engineer learning from a completed or stopped goal, session or change
  I want causal hypotheses challenged against evidence and counterfactuals
  So that retrospective stories do not become unsupported doctrine

  Scenario: An explicit causal question receives bounded analysis
    Given actual intent, outcome and available native judgment evidence
    And an explicit retrospective causal question
    When Postmortem reconstructs the evidence-backed timeline
    Then it distinguishes supported claims, rejected claims, and unknowns
    And it cites evidence and counterfactuals
    And it distinguishes delivered facts, necessary checks and avoidable rework
    And uncertain time and token accounting remains explicit
    And it returns at most three supported changes or no-change inline by default

  Scenario: Postmortem does not repeat validation
    Given an existing immutable verdict or no saved verdict
    When Postmortem begins
    Then it does not re-run acceptance validation
    And it does not fabricate missing judgment evidence
    And it does not change proof, bookkeeping, planning, tracker, or delivery state
    And it saves a report only on request in protected external non-Git storage

  Scenario: A goal requests code and a retrospective
    Given the caller requires a coding change and a final postmortem
    And required code checks are still pending
    When the caller prepares code acceptance review
    Then the review does not require a provisional postmortem
    And final analysis waits for the known outcome and available judgment
    And the overall goal still requires the requested postmortem

  Scenario: The caller explicitly requests interim analysis
    Given the coding outcome is not yet known
    When the caller requests a retrospective up to a stated cutoff
    Then the analysis names that cutoff and pending checks
    And it does not infer final success or replace later outcome evidence
