Feature: RPI runs one bounded experiment
  @covered-by:skills/rpi/tests/test_run_once.py::test_anti_ceremony_guard_runs_once_before_plan
  Scenario: Guard CONTINUE preserves the single-pass core order
    Given one intent
    When RPI is invoked
    Then the anti-ceremony guard is invoked exactly once before Plan
    And Plan, Implement, and fresh Validate are each dispatched at most once in that order
    And the final report contains no next action

  @covered-by:skills/rpi/tests/test_run_once.py::test_anti_ceremony_stop_dispatches_no_core_phase
  Scenario: Guard STOP admits no core phase
    Given the anti-ceremony guard returns STOP with its required response fields
    When RPI is invoked
    Then Plan, Implement, and Validate are not dispatched
    And RPI reports NOT_PLANNED and stops

  @covered-by:skills/rpi/tests/test_run_once.py::test_fail_reports_and_stops_without_another_dispatch
  Scenario: Validation failure does not loop
    Given Validate returns FAIL or NOT_PROVEN
    When RPI reports the verdict
    Then RPI stops without repair, replan, helper, retry, or delivery

  @covered-by:skills/rpi/scripts/validate.sh
  Scenario: Interactive output does not require a machine artifact
    Given RPI has received one fresh validation result
    When RPI responds to an interactive caller
    Then the response leads with status and the caller-visible outcome
    And it includes only the strongest proof and material unchecked scope
    And no hidden rpi-report.v1 or verdict.v2 is created
    And a machine artifact is emitted only when a caller or declared consumer requested it
