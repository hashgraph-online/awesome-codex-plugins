# Executable spec for the behavior-first-planning skill (BC3 Loop).
# The skill turns an intent into beads that each carry a runnable acceptance test
# defining "done": intent → frozen Gherkin behaviors → EXECUTED-red acceptance
# tests → derived spec → an acceptance-gated bead DAG. The invariant it enforces:
# no runnable acceptance test, no bead. Hexagon: domain; consumes: standards;
# produces: behaviors.md + acceptance-tests/ + spec.md + acceptance-gated beads.
# (age-3va.2)

Feature: Behavior-first planning produces beads with runnable done-criteria
  As the loop's planning step
  I want every bead born with a failing acceptance test as its contract
  So that "done" is deterministic ground truth, never an implementer's self-grade

  Scenario: Intent becomes frozen, testable Gherkin behaviors
    Given an intent to plan
    When the behaviors phase runs
    Then it emits Given/When/Then scenarios covering happy, edge, and error paths
    And the behaviors are frozen as the definition of done before any design

  Scenario: Acceptance tests are observed RED, not asserted
    Given a frozen set of behaviors
    When each scenario is turned into a runnable acceptance test
    Then the suite is RUN and reported red because the feature is not built yet
    And a test that already passes or crashes on a harness error is flagged

  Scenario: Spec is derived to make the tests pass
    Given frozen behaviors and executed-red acceptance tests
    When the spec phase runs
    Then the architecture is derived solely to make those tests pass, not free-form

  Scenario: Every bead carries a runnable acceptance test or is rejected
    Given a derived spec
    When the bead DAG is built
    Then each bead carries a real scenario_ref and an invocable acceptance_test
    And a bead whose acceptance is prose or an unrun test is rejected by the gate
    And the gate confirms coverage-complete and cycle-free before any tracker write

  Scenario: An independent reviewer gates the tracker write
    Given a proposed bead set that is not yet in the tracker
    When the closing validation runs
    Then an independent fresh-context reviewer scores crank-readiness
    And the beads are written only on a clearing verdict, never on a self-grade
