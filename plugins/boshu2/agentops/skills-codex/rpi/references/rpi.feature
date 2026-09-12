Feature: Optional fixed-dispatch reference adapter remains bounded
  @covered-by:skills/rpi/tests/test_run_once.py::test_anti_ceremony_guard_runs_once_before_plan
  Scenario: Guard CONTINUE preserves the core phase order
    Given one intent
    When the fixed-dispatch adapter is explicitly selected
    Then the anti-ceremony guard is invoked exactly once before Plan
    And Plan and Implement are each dispatched at most once in that order, and fresh Validate repeats only inside the bounded repair phase
    And the final report contains no next action

  @covered-by:skills/rpi/tests/test_run_once.py::test_anti_ceremony_stop_dispatches_no_core_phase
  Scenario: Guard STOP admits no core phase
    Given the anti-ceremony guard returns STOP with its required response fields
    When the fixed-dispatch adapter is explicitly selected
    Then Plan, Implement, and Validate are not dispatched
    And RPI reports NOT_PLANNED and stops

  @covered-by:skills/rpi/tests/test_run_once.py::test_fail_from_one_experiment_feeds_the_repair_phase
  Scenario: Validation failure enters the bounded repair phase
    Given Validate returns FAIL or NOT_PROVEN with findings
    When the convergence law admits another round
    Then the adapter evaluates supplied repair evidence, without runtime dispatch or delivery

  @covered-by:skills/rpi/tests/test_run_once.py::test_repair_stops_when_a_closed_finding_reopens
  Scenario: The convergence law stops a repair spiral
    Given a repair round reopens a closed finding id or has no new acceptance-relevant proof
    When RPI evaluates the law
    Then RPI stops and reports the current status with the open findings

  @covered-by:skills/rpi/tests/test_run_once.py::test_discovered_preexisting_defects_may_grow_count_with_real_progress
  Scenario: Discovery is distinct from regression
    Given a repair closes a named acceptance gap with a new digest-bound receipt
    And new findings are proven to exist on the prior exact subject
    When the new findings increase the open count
    Then RPI retains them and admits bounded repair without declaring a regression

  @covered-by:skills/rpi/tests/test_run_once.py::test_new_finding_cannot_hide_behind_another_resolved_gap
  Scenario: Unknown cause requires causal examination
    Given a repair closes one acceptance gap but exposes a new finding of unknown cause
    When RPI evaluates the law
    Then RPI stops even if the open count did not grow

  @covered-by:skills/rpi/scripts/validate.sh
  Scenario: Interactive output does not require a machine artifact
    Given RPI has received one fresh validation result
    When RPI responds to an interactive caller
    Then the response leads with status and the caller-visible outcome
    And it includes only the strongest proof and material unchecked scope
    And no hidden rpi-report.v1 or verdict.v2 is created
    And a machine artifact is emitted only when a caller or declared consumer requested it
