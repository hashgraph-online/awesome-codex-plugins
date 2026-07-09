# Executable spec for the /validate skill — the unified validator (driving-adapter).
# /validate takes any artifact (plan, spec, code, PR, fitness gate) and emits a verdict.v1:
# PASS, WARN, or FAIL with rationale and findings. The artifact shape is selected by --mode,
# and the mode set is budget-capped. Hexagon: driving-adapter; consumes validation; produces
# result.json; customer-of validation. (soc-qk4b)

Feature: Validate produces a PASS/WARN/FAIL verdict for any artifact
  As the unified validator
  I want any artifact judged to a verdict.v1 with rationale and findings
  So that plans, code, PRs, and gates all share one verdict contract

  Scenario: an artifact is validated to a verdict
    When /validate runs on an artifact (plan, spec, code, PR, or fitness gate)
    Then it emits a PASS, WARN, or FAIL verdict with rationale and findings
    And the verdict conforms to the verdict.v1 schema

  Scenario: the mode selects the validation shape
    When /validate runs with --mode
    Then --mode=pr produces a PR-shape verdict (diff review + acceptance check)
    And --mode=pre-impl --target=fitness validates the fitness gate against GOALS.md

  Scenario: the mode set is budget-capped
    Then /validate exposes at most 8 modes
    And adding a 9th requires demoting an existing mode or refusing the addition
