# Behavior scenarios for the /reverse-engineer skill, linked by @covered-by: CI runs
# scripts/validate.sh via tests/scripts/reverse-engineer-validate.bats;
# self_test.sh (Go) runs by hand. In repo mode it scans the code surface and
# indexes the docs pages; in binary mode it analyzes a binary, with a security
# audit scaffold only when --security-audit is set.
@covered-by:tests/scripts/reverse-engineer-validate.bats
Feature: Reverse-engineer tears down an external system into a steal-map
  As a maintainer comparing us to an external tool
  I want a source-tagged teardown and a validated steal-map
  So that adoption choices rest on code evidence instead of a README

  Background:
    Given a target system provided as a repository or a binary

  Scenario: Repo mode scans the code surface and indexes the docs
    When the target is a code repository
    Then it writes the CLI, config and artifact contracts from the code
    And it indexes the target's docs pages into the feature catalog

  @covered-by:skills/reverse-engineer/scripts/self_test.sh
  Scenario: Binary mode adds a security audit only on request
    When the target is a binary analyzed with --authorized and --security-audit
    Then it analyzes the binary and writes a security audit scaffold under security/

  Scenario: Output is a reusable spec set
    When reconstruction completes
    Then it emits a feature catalog, code map, and specs as durable artifacts

  Scenario: A steal-map is a separate checked decision
    Given a validated mechanical teardown
    When the caller compares its registry with the live destination repository
    Then the caller authors steal-map.md with evidence-backed verdict rows
    And the complete-output validator rejects a missing or malformed steal-map
    And it rejects a steal row without code evidence

  Scenario: An explicit analysis root cannot drift
    Given --local-clone-dir selects a particular tree
    When the selected tree is non-Git
    Then that exact tree is analyzed instead of the caller's current checkout
    When --upstream-ref also selects a Git commit
    Then a mismatched existing checkout is refused before outputs are trusted

  Scenario: Managed output paths do not follow links
    Given an output parent or managed artifact is a symbolic link
    When reverse engineering starts
    Then it refuses before writing through that link

  @covered-by:skills/reverse-engineer/scripts/self_test.sh::earlier-default
  Scenario: An earlier-default output directory remains explicit and usable
    Given an existing teardown under .agents/research
    When that exact directory is supplied with --output-dir
    Then the teardown writes and validates in that directory
    And it does not move existing artifacts into the current scratch default
