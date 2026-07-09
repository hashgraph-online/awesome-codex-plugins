# Executable spec for the /scope skill — edit-scope guardrail (BC5 Runtime).
# /scope declares which directories are in scope for the current work session and
# hard-blocks edits outside them via a PreToolUse hook, so a session cannot drift
# into files it never claimed. Hexagon: driven-adapter; consumes: a declared
# directory set; produces: scope/lock state + blocked-edit reasons on stderr. (soc-qk4b)

Feature: Scope hard-blocks edits outside the declared directories
  As an agent working a bounded change
  I want edits confined to directories I declared in scope
  So that a session cannot silently modify files it never claimed

  Background:
    Given a work session that can declare an in-scope directory set

  Scenario: Declaring scope records the allowed directories
    When /scope declares one or more directories
    Then those directories become the in-scope set and the lock state reflects them

  Scenario: An edit inside scope proceeds
    Given a declared in-scope directory
    When a file inside it is edited
    Then the edit is allowed

  Scenario: An edit outside scope is hard-blocked with a reason
    Given a declared scope
    When a file outside the in-scope set is edited
    Then the PreToolUse hook blocks the edit and reports the blocked-edit reason on stderr

  Scenario: Scope state is reportable and releasable
    When /scope is queried
    Then it reports the current scope and lock state
    And releasing scope removes the block on out-of-scope edits
