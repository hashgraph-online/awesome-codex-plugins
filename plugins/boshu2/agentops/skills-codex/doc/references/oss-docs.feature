# Executable spec for /doc --mode=oss — OSS documentation scaffold/audit (BC4 Factory).
# /doc --mode=oss prepares a repo for open-source release: it AUDITS which standard docs exist/are
# missing (reading the repo), SCAFFOLDS the missing ones without clobbering, and tailors content
# to the project type. Hexagon: supporting (doc factory); consumes repo-context (audit reads the repo); produces
# documentation. (soc-qk4b)

Feature: OSS-docs audits and scaffolds open-source documentation
  As open-source release prep
  I want the standard docs audited and the missing ones scaffolded to project type
  So that a repo reaches OSS-release doc completeness without overwriting existing work

  Scenario: audit reports which standard docs exist or are missing
    When /doc --mode=oss audit runs
    Then it reads the repo and reports which standard OSS docs exist and which are missing

  Scenario: scaffold creates only the missing standard files
    When /doc --mode=oss scaffold runs
    Then it creates the missing standard files
    And it does not overwrite docs that already exist

  Scenario: an authorized refresh proceeds without repeated confirmation
    Given the caller has requested updates to named existing documentation
    When the proposed edits remain within that request
    Then it updates the authorized files without asking again
    And it checks the resulting documentation

  Scenario: missing-only setup preserves existing content
    Given the caller requested only missing-document setup
    When the target already contains documentation
    Then it leaves existing files unchanged

  Scenario: generated content is tailored to the project type
    When /doc --mode=oss generates a doc
    Then the content is tailored to the detected project type, not a generic stub
