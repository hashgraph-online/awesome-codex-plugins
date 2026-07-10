# Executable spec for the `ao autodev` CLI command — the PROGRAM.md contract surface.
# Distinct from autodev.feature (which specs the contract-bounded loop behavior absorbed
# into /evolve): this file specs the
# observable behavior of the `ao autodev {init,validate,show}` subcommands — flags, output
# contract (human + JSON), and error paths. Each scenario links to the Go test in
# cli/cmd/ao/ that proves it. (soc-jnfgi)

Feature: ao autodev manages the PROGRAM.md operational contract
  As an operator bounding autonomous development
  I want to create, validate, and inspect the repo-local PROGRAM.md contract
  So that autonomy stays scoped to a declared, machine-checkable contract

  @covered-by:cli/cmd/ao/autodev_integration_test.go::TestAutodev_Integration_InitCreatesFile
  Scenario: init writes a PROGRAM.md template
    Given no PROGRAM.md exists in the working directory
    When I run `ao autodev init`
    Then a PROGRAM.md file is created with the contract section scaffold

  @covered-by:cli/cmd/ao/autodev_integration_test.go::TestAutodev_Integration_InitRefusesOverwrite
  Scenario: init refuses to clobber an existing contract without --force
    Given a PROGRAM.md already exists
    When I run `ao autodev init`
    Then the command fails and reports that the file already exists

  @covered-by:cli/cmd/ao/autodev_integration_test.go::TestAutodev_Integration_ValidateValidProgram
  Scenario: validate accepts a well-formed contract
    Given a PROGRAM.md declaring objective, mutable/immutable scope, validation commands, and stop conditions
    When I run `ao autodev validate`
    Then the command exits zero and reports the contract as VALID

  @covered-by:cli/cmd/ao/autodev_integration_test.go::TestAutodev_Integration_ValidateInvalidProgram
  Scenario: validate rejects a contract missing required sections
    Given a PROGRAM.md with no contract sections
    When I run `ao autodev validate`
    Then the command exits non-zero and the output reports INVALID with ERROR lines

  @covered-by:cli/cmd/ao/autodev_integration_test.go::TestAutodev_Integration_ValidateNoProgram
  Scenario: validate errors when no contract file is found
    Given neither PROGRAM.md nor AUTODEV.md exists
    When I run `ao autodev validate`
    Then the command exits non-zero with guidance to run `ao autodev init`

  @covered-by:cli/cmd/ao/autodev_integration_test.go::TestAutodev_Integration_ValidateJSON
  Scenario: validate emits a structured JSON result under --output json
    Given a valid PROGRAM.md
    When I run `ao --output json autodev validate`
    Then the output is JSON carrying valid=true, the objective, and the scope counts

  @covered-by:cli/cmd/ao/autodev_test.go::TestCobraAutodevValidateFallsBackToAUTODEVJSON
  Scenario: validate auto-detects AUTODEV.md when PROGRAM.md is absent
    Given only an AUTODEV.md contract exists
    When I run `ao autodev validate`
    Then the command resolves and validates the AUTODEV.md file

  @covered-by:cli/cmd/ao/autodev_integration_test.go::TestAutodev_Integration_ShowProgram
  Scenario: show prints the parsed contract
    Given a PROGRAM.md with scope and validation entries
    When I run `ao autodev show`
    Then the output lists the objective, mutable/immutable scope, validation commands, and stop conditions

  @covered-by:cli/cmd/ao/autodev_test.go::TestCobraAutodevShowPrefersPROGRAMOverAUTODEV
  Scenario: show prefers PROGRAM.md when both contract files exist
    Given both PROGRAM.md and AUTODEV.md exist
    When I run `ao autodev show`
    Then the parsed contract is sourced from PROGRAM.md
