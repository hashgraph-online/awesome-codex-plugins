# These scenarios test source-contract regressions only. Live discovery,
# replacement, probes and challenge require fresh task observation and judgment.
Feature: Plan source preserves optional methods and native intent authority
  @covered-by:tests/scripts/skill-validator-liveness.bats
  Scenario: A model-authored packet contract is rejected
    Given the shipped Plan source passes its static validator
    When a model-authored plan packet reference is added to a copy
    Then the copied validator fails

  @covered-by:tests/scripts/skill-validator-liveness.bats
  Scenario: Optional evidence routing cannot restore compulsory ceremony
    Given Plan's routing reference permits a question-driven probe
    When the old every-plan control requirement is added to a copy
    Then the copied validator fails

  @covered-by:tests/scripts/skill-validator-liveness.bats
  Scenario: A native recovery pointer does not become a second work ledger
    Given Plan permits active assignment references and a next discriminator in native handoff
    When a copy includes factual owner and next-action references
    Then its static validator passes
    But restoring the blanket ban on those recovery facts makes the validator fail
