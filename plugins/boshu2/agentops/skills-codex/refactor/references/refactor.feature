# Executable spec for the /refactor skill — safe incremental refactoring (supporting role).
# /refactor transforms code one step at a time with test verification — one transformation, one
# test run, one commit, never batched — preserving behavior. Target mode refactors a chosen unit;
# sweep mode (--sweep) runs /complexity first to pick targets. Hexagon: supporting; consumes
# complexity (sweep targeting) + repo-context (the code it transforms); produces git-changes. (soc-qk4b)

Feature: Refactor executes safe incremental transformations
  As the safe-refactoring step
  I want each transformation verified by tests before the next
  So that refactors never silently change behavior

  Scenario: one transformation, one test run, one commit
    When /refactor applies a transformation
    Then it runs the tests, then commits that single transformation
    And transformations are not batched together

  Scenario: a failing test reverts the transformation
    When a transformation makes a test fail
    Then that transformation is reverted and behavior is preserved

  Scenario: sweep mode targets by complexity
    When /refactor --sweep runs over a directory
    Then it runs /complexity first to identify targets and works highest-complexity first

  Scenario: target mode refactors a chosen unit
    When /refactor runs on a specific file, function, or class
    Then it refactors that unit directly, step by step
