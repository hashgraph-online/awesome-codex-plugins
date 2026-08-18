# Executable spec for the /reverse-engineer skill — spec reconstruction (BC1 Corpus).
# /reverse-engineer reconstructs product specs from an existing system — in repo mode it
# maps the code into a feature catalog and specs; in binary mode it analyzes a binary with a
# security audit. Hexagon: supporting; consumes: a target codebase or binary; produces:
# a feature catalog, code map, and specs. (soc-qk4b)

Feature: Reverse-engineer reconstructs specs from an existing system
  As an agent onboarding or auditing an unfamiliar system
  I want its behavior reconstructed into a feature catalog and specs
  So that work can proceed from a real map instead of guesswork

  Background:
    Given a target system provided as a repository or a binary

  Scenario: Repo mode produces a feature catalog and code map
    When the target is a code repository
    Then it maps the code into a feature catalog, code map, and specs

  Scenario: Binary mode includes a security audit
    When the target is a binary
    Then it analyzes the binary and includes a security audit in the output

  Scenario: Output is a reusable spec set
    When reconstruction completes
    Then it emits a feature catalog, code map, and specs as durable artifacts

  Scenario: A steal-map is a separate checked decision
    Given a validated mechanical teardown
    When the caller compares its registry with the live destination repository
    Then the caller authors steal-map.md with evidence-backed verdict rows
    And the complete-output validator rejects a missing or malformed steal-map

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

  Scenario: An earlier-default output directory remains explicit and usable
    Given an existing teardown under .agents/research
    When that exact directory is supplied with --output-dir
    Then the teardown writes and validates in that directory
    And it does not move existing artifacts into the current scratch default
