# Executable spec for the /brainstorm skill — goal clarification (domain role).
# /brainstorm separates WHAT from HOW: it explores the problem space and captures testable
# Gherkin acceptance examples BEFORE planning commits to a solution. It runs upstream of loop
# move 1 (shape intent as BDD). Hexagon: domain; consumes standards; produces result.json +
# verdict.json; shared-kernel with standards. (soc-qk4b)

Feature: Brainstorm separates goals from implementation before planning
  As the pre-planning goal-clarification step
  I want a free-text goal explored as a problem space, then captured as Gherkin
  So that planning starts from clear, testable intent rather than a premature solution

  Scenario: a goal is clarified through the four phases
    When /brainstorm runs on a free-text goal
    Then it works through assess-clarity → understand-idea → explore-approaches → capture-design

  Scenario: approaches are explored as options, not a single solution
    When the explore phase runs
    Then it generates multiple options, compares tradeoffs, and applies adversarial critique
    And it separates the problem (WHAT) from any one solution (HOW)

  Scenario: capture writes testable Gherkin examples
    When the capture phase completes
    Then it produces Given/When/Then acceptance examples for /plan and /discovery
    And capture is not complete until at least one happy path and one critical edge are written

  # Ideation mode — open-ended generate-winnow methodology (ag-yw0). Additive to
  # the goal-clarification flow above; documentation-only spec (this file is
  # allowlisted in scripts/.scenario-linkage-allow). Wiring is asserted by the
  # bats regression test tests/scripts/brainstorm-discovery-ideation.bats.

  Scenario: an open-ended goal triggers ideation mode
    Given a goal like "improve the project" or the --ideate flag or an exploring clarity path with no single goal
    When /brainstorm runs
    Then it enters ideation mode instead of the single-goal four-phase flow
    And the goal-clarification four-phase flow remains available for specific goals

  Scenario: ideation mode generates many and winnows ruthlessly to a ranked five
    When ideation mode runs
    Then it grounds in reality by reading AGENTS.md and open and closed br beads
    And it generates 30 candidate ideas thought through for how-it-works, user-perception, and implementation
    And it winnows to the very best 5 ranked best-to-worst with full rationale
    And it scores survivors against the ten-dimension rubric

  Scenario: ideation mode expands the portfolio to fifteen
    When the top 5 are selected
    Then it generates the next best 10 with rationale for a ranked portfolio of 15
    And it carries how-it-works, user-perception, implementation notes, and rubric scores forward to operationalize
