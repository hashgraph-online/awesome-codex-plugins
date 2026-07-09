# Executable spec for the /heal-skill skill — skill hygiene repair (BC1 Corpus / Skill Catalog).
# /heal-skill detects and auto-fixes common SKILL.md hygiene issues across skills/ (including
# unlinked references and Codex-parity drift), then reports what it changed. Hexagon:
# supporting; consumes: the skills/ tree; produces: a heal report + auto-fixed skill files. (soc-qk4b)

Feature: Heal-skill repairs skill hygiene across the catalog
  As a catalog maintainer
  I want common hygiene issues detected and auto-fixed
  So that skills stay well-formed without manual sweeps

  Background:
    Given the skills/ directory with one or more skills

  Scenario: The heal script detects hygiene issues
    When /heal-skill runs
    Then it scans skills for hygiene issues including unlinked references

  Scenario: Codex parity drift is flagged
    When the Codex bundle looks wrong
    Then it audits and reports Codex-parity drift

  Scenario: Fixable issues are auto-fixed and reported
    When issues are found
    Then it auto-fixes the fixable ones and reports what changed

  Scenario: Strict mode fails on remaining findings
    When run with --strict
    Then it reports a non-clean result when unresolved findings remain
