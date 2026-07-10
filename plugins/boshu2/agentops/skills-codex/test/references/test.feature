# Executable spec for the /test skill — test generation + coverage (supporting role).
# /test loads the language's test standards, generates REAL tests for existing code, runs them to
# verify they pass (it does not stop at a plan), and fills coverage gaps — writing artifacts to
# .agents/test/. Hexagon: supporting; consumes standards (test conventions) + repo-context (the
# code under test); produces result.json. (soc-qk4b)

Feature: Test generates real, passing tests and coverage
  As the test-generation step
  I want tests generated to the project's standards and verified by running them
  So that coverage improves with real passing tests, not a plan

  Scenario: standards and language are loaded before generating
    When /test runs
    Then it detects the language and loads the test standards (AI-native test shape) for it

  Scenario: generate produces real tests that are run and verified
    When /test generate runs on existing code
    Then it writes real tests, runs them, and verifies they pass
    And it does not output a plan and stop

  Scenario: coverage analyzes and fills gaps
    When /test coverage runs
    Then it analyzes coverage gaps and fills them, writing a coverage report to .agents/test/
