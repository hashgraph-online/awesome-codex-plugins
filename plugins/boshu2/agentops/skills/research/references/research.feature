Feature: Research answers one bounded question
  @covered-by:tests/scripts/agentops-native-skills.bats::claim-audit
  Scenario: A claimed state gets a per-item ledger without a verdict
    Given a claim that work is done, shipped or wired in
    When Research audits each stated item against observable evidence
    Then every item is confirmed, a gap or unverifiable with its evidence
    And code no live entry point reaches is not counted as wired in
    And the ledger carries no overall PASS, FAIL, verdict or readiness call
