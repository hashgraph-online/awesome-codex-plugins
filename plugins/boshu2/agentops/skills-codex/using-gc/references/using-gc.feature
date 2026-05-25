# Executable spec for the using-gc skill — running AgentOps on the Gas City (gc)
# substrate (BC5 Runtime). using-gc GUIDES agents on the gc CLI exactly like the
# bd protocol guides them: gc is a guided out-of-session dependency, ao does NOT
# wrap gc. Hexagon: generic; consumes: nothing; produces: documentation. (ag-p4p)

Feature: using-gc guides an agent to run AgentOps on the Gas City substrate
  As an agent that needs the AgentOps loop to run out of session
  I want a guide to the gc primitives and the AgentOps-on-GC workflow
  So that I can stand up the reference City and dispatch work without inventing gc usage

  Background:
    Given the using-gc skill and the reference pack at packs/agentops/

  @covered-by:tests/scripts/using-gc-skill.bats::skill exists with meta frontmatter
  Scenario: The skill declares itself as a guided gc workflow, not an ao wrapper
    When an agent reads using-gc
    Then it learns gc is a guided out-of-session dependency, not wrapped by ao

  @covered-by:tests/scripts/using-gc-skill.bats::skill names the core gc primitives
  Scenario: The skill names the gc primitives an agent must know
    When an agent reads the primitives section
    Then it sees City, Rig, Pack, Agent, Order, Formula, mayor, and refinery defined

  @covered-by:tests/scripts/using-gc-skill.bats::skill documents the mayor-driven dispatch loop
  Scenario: An agent can run the reference City end to end with guided gc commands
    When an agent follows the workflow section
    Then it can gc start the City, gc rig add a repo, and run the mayor dispatch loop
    And the dispatch loop is bd ready then gc sling then ao rpi

  @covered-by:tests/scripts/using-gc-skill.bats::skill is honest about the order-auto-dispatch gap
  Scenario: The skill is honest about the order-auto-dispatch gap
    When an agent reads the dispatch posture
    Then it learns dispatch is mayor-driven today
    And it learns order-auto-dispatch is an upstream-GC gap tracked as soc-5jwah

  @covered-by:tests/scripts/using-gc-skill.bats::skill links every reference doc
  Scenario: Every reference file is linked from the skill
    When the skill hygiene gate runs
    Then every file under references/ is linked in SKILL.md
