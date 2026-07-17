Feature: Validate writes one fresh verdict over exact content
  @covered-by:skills/validate/scripts/test_validate.py::test_verdict_identity_floor_and_idempotence
  Scenario: Identity gaps stay unproven
    Given missing, colliding, or unattested author and validator identities
    When Validate judges the subject
    Then the verdict is NOT_PROVEN

  @covered-by:skills/validate/scripts/test_validate.py::test_pass_without_evidence_is_downgraded
  Scenario: Evidence-free PASS stays unproven
    Given a claimed PASS without checked scope or criterion evidence
    When Validate persists the verdict
    Then the verdict is NOT_PROVEN

  @covered-by:skills/validate/scripts/test_validate.py::test_runtime_scope_failure_forces_fail
  Scenario: Scope failure is distinct from missing proof
    Given complete changed-path coverage
    When a proven path is outside the intent-source write scope
    Then the verdict is FAIL

  @covered-by:skills/validate/scripts/test_validate.py::test_intent_snapshot_is_content_addressed_and_idempotent
  Scenario: Tracker-less intent remains readable
    Given the caller conversation is the resolved intent
    When the runtime snapshots its exact bytes
    Then the snapshot path is its SHA-256 identity

  @covered-by:skills/validate/scripts/test_validate.py::test_verdict_identity_floor_and_idempotence
  Scenario: Validation stops after persistence
    Given any PASS, FAIL, or NOT_PROVEN verdict
    When Validate atomically persists it
    Then Validate returns the artifact digest and path
    And performs no repair, retry, Git, closure, release, or delivery action
