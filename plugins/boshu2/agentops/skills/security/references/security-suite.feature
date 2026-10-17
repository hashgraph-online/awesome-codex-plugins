# Executable spec for the /security skill's composable suite primitives (driven-adapter).
# /security provides repeatable, composable security/internal-testing primitives over
# AUTHORIZED targets — separated into testable steps (collect-static, collect-dynamic,
# collect-contract) that compose into a security report. Hexagon: driven-adapter; consumes
# repo-context; produces suite-summary.json; supplier-to validate. (soc-qk4b)

Feature: Security-suite runs composable security primitives
  As the composable security-analysis toolkit
  I want separable primitives that compose into a security report over authorized targets
  So that security workflows stay testable, reusable, and authorization-bounded

  Scenario: composable primitives produce a security report
    When /security runs the composable suite over a target
    Then it composes primitives (collect-static, collect-dynamic, collect-contract)
    And it writes a suite-summary.json

  Scenario: analysis is authorization-bounded
    When the target is a binary or surface
    Then /security suite primitives are used only on owned or explicitly authorized targets
    And it is not used to bypass legal restrictions or extract third-party proprietary content

  Scenario: the report feeds the validator
    When the suite completes
    Then its report is available to /validate as a supplier (supplier-to validate)
