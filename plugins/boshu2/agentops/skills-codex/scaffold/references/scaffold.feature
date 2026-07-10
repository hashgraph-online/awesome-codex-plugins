# Executable spec for the /scaffold skill — project/component/CI scaffolding (BC3 Loop).
# /scaffold generates new-project structure, components, and CI pipelines from a single
# entry point, and backs domain-slice scaffolding with `/scaffold domain <name>`
# (there is no `ao scaffold` subcommand). Hexagon: supporting; consumes: a scaffold
# target (language/component/CI/domain); produces: project files + directory structure. (soc-qk4b)

Feature: Scaffold generates project, component, and CI structure
  As a developer starting new work
  I want consistent boilerplate generated from one command
  So that new projects, components, and pipelines start from a known-good shape

  Background:
    Given a scaffold request naming a target

  Scenario: A new project is scaffolded by language and name
    When "/scaffold <language> <name>" runs
    Then it creates the project files and directory structure for that language

  Scenario: A component is generated into an existing project
    When "/scaffold component <type> <name>" runs
    Then it generates the component of that type

  Scenario: A CI pipeline is scaffolded for a platform
    When "/scaffold ci <platform>" runs
    Then it sets up the CI pipeline for that platform

  Scenario: Domain-slice scaffolding routes through the skill
    When domain scaffolding is requested
    Then it writes the domain-slice manifest rather than calling a non-existent "ao scaffold" command
