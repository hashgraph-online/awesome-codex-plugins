# Executable spec for the /product skill — PRODUCT.md authoring (BC1 Corpus).
# /product guides the user through creating or refining a PRODUCT.md (problem, audience,
# differentiator, market position) that unlocks product-aware reviews in /pre-mortem
# and /vibe. Hexagon: domain; consumes: project context + interview answers; produces:
# PRODUCT.md. (soc-qk4b)

Feature: Product authors a PRODUCT.md that unlocks product-aware review
  As a maintainer framing a product
  I want a structured PRODUCT.md derived from real project context
  So that /pre-mortem and /vibe can judge changes against product intent

  Background:
    Given a repository with optional existing PRODUCT.md and manifest files

  Scenario: Context is gathered before the interview
    When /product runs
    Then it reads existing product framing and project manifests as context

  Scenario: An interview drives the generated PRODUCT.md
    When the interview completes
    Then it generates a PRODUCT.md covering problem, audience, and differentiator

  Scenario: PRODUCT.md unlocks product-aware council review
    Given a PRODUCT.md exists
    Then /pre-mortem and /vibe judge changes against the stated product intent

  Scenario: Quick mode produces inline framing without a full interview
    When quick mode is used
    Then a concise PRODUCT.md is produced through the default inline path
