Feature: Source checks are read-only and repair touches owned projections
  Scenario: Explicit targets are checked
    When heal.sh --check --strict receives a real direct source package
    Then it checks identity, required source fields, linked resources and scaffold state
    And it does not claim semantic completeness
    And it changes no file

  Scenario: Unsafe target spellings are rejected
    When a target uses traversal or symlinks
    Then the operation fails before projecting any target

  Scenario: Projection repair does not author behavior
    When heal.sh --fix receives valid completed source targets
    Then it regenerates only their owned projection bundles and shared catalog
    And invalid source targets remain failing without projection mutation
