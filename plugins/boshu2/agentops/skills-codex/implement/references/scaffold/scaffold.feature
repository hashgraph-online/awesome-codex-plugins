# Executable spec for bounded project/component/CI scaffolding.

Feature: Implementation scaffolding generates project, component, and CI structure
  As a developer starting new work
  I want consistent boilerplate generated from a bounded request
  So that new projects, components, and pipelines start from a known-good shape

  Background:
    Given a scaffold request naming a target

  Scenario: A new project is scaffolded by language and name
    When the caller asks to scaffold a project by language and name
    Then it creates the project files and directory structure for that language

  Scenario: A component is generated into an existing project
    When the caller asks to scaffold a named component of a given type
    Then it generates the component of that type

  Scenario: A CI pipeline is scaffolded for a platform
    When the caller asks to scaffold CI for that platform
    Then it sets up the CI pipeline for that platform

  Scenario: Existing paths are preserved
    Given the requested target contains an existing file
    When scaffolding runs without explicit overwrite authorization
    Then the existing file is not replaced
