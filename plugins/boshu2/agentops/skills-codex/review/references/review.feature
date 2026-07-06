# Executable spec for the /review skill — diff/codebase review (driving-adapter).
# /review reads a diff or codebase and surfaces what a careful reviewer would: risk-ranked
# findings, mock/stub implementations masquerading as real code, and latent bugs. It judges
# the code, not the agent's process. Hexagon: driving-adapter; consumes github-pr +
# validation; produces result.json; customer-of validation. (soc-qk4b)

Feature: Review surfaces risk, mocks, and bugs in a diff or codebase
  As the diff/codebase reviewer
  I want risk-ranked findings, mock detection, and a bug scan over the change
  So that risky or fake code is caught before it merges

  Scenario: a diff is reviewed for risk
    When /review runs on a diff or PR
    Then it reports findings ranked by risk, not an undifferentiated list

  Scenario: mock and stub implementations are flagged
    When the reviewed code contains a mock, stub, or hardcoded fake standing in for real logic
    Then /review flags it as a mock-not-implementation finding

  Scenario: the change is scanned for bugs
    When /review inspects the changed code
    Then it scans for latent bugs (wrong references, swallowed errors, missing edge cases)

  Scenario: findings are emitted as a structured result
    When the review completes
    Then the findings are written to result.json for downstream consumers
