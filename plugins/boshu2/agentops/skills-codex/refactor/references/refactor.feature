# Executable spec for the refactor skill — one behavior-preserving transformation (supporting role).
# refactor applies ONE caller-selected structural transformation, runs the focused check plus the
# smallest justified regression check, and reports the diff, commands, results, and behavior not
# checked. It does not commit, revert, retry, validate, or route subsequent work — a red result is
# evidence returned to the caller, who owns version control and what happens next. Hexagon:
# supporting; consumes repo-context (the code it transforms); produces code-changes.

Feature: Refactor executes one behavior-preserving transformation and reports evidence
  As the behavior-preserving transformation step
  I want one bounded structural change proven behavior-identical
  So that structure improves without silently changing observable behavior

  Scenario: one bounded transformation, then report
    When refactor applies one caller-selected transformation
    Then it runs the focused check and the smallest justified regression check
    And it reports the diff summary, commands, results, and behavior not checked
    And it does not commit the change or route any subsequent work

  Scenario: a red result is reported, not reverted
    When the focused or regression check comes back red
    Then refactor returns that result to the caller as evidence
    And it does not automatically revert, narrow, or retry the transformation

  Scenario: neutrality gate rejects new or vanished red
    When the same pre-existing failures do not hold before and after
    Then refactor reports the behavior difference rather than accepting the change
    And a test that stopped running counts as a behavior change

  Scenario: seams are probed in disposable isolation before cutting
    When more than one candidate seam exists for the transformation
    Then refactor probes at most two seams in disposable isolation and keeps only the knowledge
    And it reports both findings to the caller rather than trying a third
