# Executable spec for the /doc skill — repo documentation (supporting role).
# /doc reads the project (source, existing docs) to detect its type, then generates and validates
# documentation appropriate to that type — API docs for code projects, structure for informational
# ones. Hexagon: supporting; consumes repo-context; produces documentation. (soc-qk4b)

Feature: Doc generates and validates project documentation
  As the documentation step
  I want docs generated from the repo and existing docs validated against it
  So that documentation matches the project's type and current state

  Scenario: project type is detected before generating
    When /doc runs
    Then it inspects the repo and classifies it (coding project needing API docs vs informational)

  Scenario: generated docs fit the project type
    When /doc generates documentation
    Then the output suits the detected type (API reference for code, structure for informational)
    And it is drawn from the repo's actual source and existing docs

  Scenario: validation checks docs against the repo
    When /doc validates existing documentation
    Then it reports gaps or staleness measured against the current source

  Scenario: mixed-language coverage follows the selected entities
    Given the caller selects a Python public function and an exported Go function for a coverage check
    And the Python module contains quoted data unrelated to the function's documentation
    When /doc checks whether the selected APIs are documented
    Then it inspects each declaration and its associated docstring, comment or reference page
    And the unrelated quoted data contributes no documented entity
    And any ratio uses the same explicitly enumerated entity set for numerator and denominator
    And unknown or unexamined status is disclosed without a percentage

  Scenario: documenting one API creates only the requested document
    Given the caller requests an authentication API update in an existing reference page
    When /doc reads the implementation and callers and updates that page
    Then it verifies the documented inputs, outputs, errors and examples against the source
    And it returns the changed page, check results and unresolved gaps
    And it creates no coverage ledger, repository-wide audit or separate report
