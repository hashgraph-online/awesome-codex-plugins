# Executable spec for the /bootstrap skill — project initialization (driving-adapter).
# /bootstrap is the product/operations layer around the `ao quick-start` seed: it initializes
# AgentOps project files PROGRESSIVELY (a bare repo gets the golden path; an existing repo only
# fills gaps) and IDEMPOTENTLY (it never overwrites an existing artifact). Hexagon:
# driving-adapter; consumes goals + product + readme + shared. (soc-qk4b)

Feature: Bootstrap initializes AgentOps project files idempotently
  As repo setup
  I want the project files seeded progressively and without clobbering anything
  So that both bare and established repos reach a complete AgentOps baseline safely

  Scenario: a bare repo gets the golden path
    Given a repo with no AgentOps project files
    When /bootstrap runs
    Then it seeds the golden-path project files

  Scenario: an existing repo only fills gaps
    Given a repo that already has some AgentOps artifacts
    When /bootstrap runs
    Then it adds only the missing artifacts and leaves existing ones untouched

  Scenario: bootstrap is idempotent
    When /bootstrap runs twice
    Then the second run overwrites nothing and produces no spurious changes
