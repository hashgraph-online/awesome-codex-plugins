# Executable spec for the /evolve skill — the goal-driven compounding loop (BC3 Loop).
# /evolve runs autonomously over /rpi: each cycle a mechanical pre-cycle gate decides
# continue/halt, the work-selection ladder picks the highest-value bounded item, one
# slice ships gated (revert on red), and the loop NEVER self-halts — only operator
# markers stop it. Hexagon: supporting; consumes: rpi, goals, post-mortem, compile;
# produces: git-changes + goals-fitness-delta. (soc-qk4b.2; see ADR-0007/ADR-0008)

Feature: Evolve runs a goal-driven compounding loop
  As the autonomous improvement loop
  I want each cycle gated, work-selected by ladder, and shipped as a bounded slice
  So that the repo compounds toward GOALS.md without the agent ever self-halting

  Background:
    Given an operator-set intent (GOALS.md, ADRs, the bead queue)

  Scenario: A mechanical pre-cycle gate decides continue or halt
    When a cycle starts
    Then scripts/evolve/halt-check.sh runs first
    And the loop continues unless an operator marker / goal-regression / prior-FAIL fires

  Scenario: Work selection walks the ladder
    When the loop selects work
    Then it prefers harvested next-work, then ready beads, then failing goals, then generators
    And it declines operator-shape work (epics/release/decisions) per ADR-0008

  Scenario: One bounded slice per cycle, reverted on red
    When the loop works a selected item
    Then it ships a single bounded slice via /rpi, gated by build + test + lint
    And it reverts the slice rather than landing red

  Scenario: The loop never self-halts
    When the loop is blocked or out of bounded work
    Then it logs `ao loop blocked` and continues or operator-waits
    And it never writes a STOP/DORMANT marker itself (operator-only, ADR-0007)
