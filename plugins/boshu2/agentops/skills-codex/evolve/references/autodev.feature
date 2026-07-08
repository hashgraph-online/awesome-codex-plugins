# Executable spec for /evolve's PROGRAM.md / AUTODEV.md contract-management surface
# (absorbed from the retired /autodev skill). The contract declares mutable/immutable scope,
# validation commands, escalation rules, and stop conditions; the loop runs UNATTENDED only
# within that contract. Contract management does not replace the /evolve or /rpi loops —
# they consume it. Loop discipline still applies under autonomy. (soc-qk4b)

Feature: Autodev runs the operating loop unattended within a declared contract
  As the bounded autonomous-development manager
  I want the loop to run unattended only inside an explicit contract
  So that autonomy stays scoped, validated, and stoppable

  Scenario: a contract bounds the unattended loop
    Given a PROGRAM.md or AUTODEV.md declaring mutable/immutable scope, validation commands,
      escalation rules, and stop conditions
    When the contract-bounded loop runs
    Then it executes the loop only within that contract

  Scenario: contract management does not replace evolve or rpi
    When the contract-management surface operates
    Then it creates/inspects/validates the contract and hands execution to /evolve and /rpi
    And it does not reimplement the evolve or rpi loops

  Scenario: loop discipline holds under autonomy
    When the loop runs a wave unattended
    Then no parallel wave runs without the wave-validity check
    And no slice closes without a passing test mapped to a Given/When/Then
    And captured learnings go through the promotion ratchet, not a landfill
