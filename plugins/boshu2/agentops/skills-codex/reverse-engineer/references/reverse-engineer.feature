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
