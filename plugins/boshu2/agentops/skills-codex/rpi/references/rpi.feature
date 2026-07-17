Feature: RPI runs one bounded experiment
  @covered-by:skills/rpi/tests/test_run_once.py::test_each_phase_runs_once_and_pass_reports
  Scenario: Core phases run once and stop
    Given one intent
    When RPI is invoked
    Then Plan, Implement, and fresh Validate are each dispatched at most once
    And the final report contains no next action

  @covered-by:skills/rpi/tests/test_run_once.py::test_fail_reports_and_stops_without_another_dispatch
  Scenario: Validation failure does not loop
    Given Validate returns FAIL or NOT_PROVEN
    When RPI reports the verdict
    Then RPI stops without repair, replan, helper, retry, or delivery
