---
name: tailwind-reference-adapter
description: Use when the user provides a local TailwindUI or Tailwind Plus folder as visual reference material for a HeroUI React/Tailwind v4 implementation.
---

# Tailwind Reference Adapter

This skill treats TailwindUI v4.1 and Tailwind Plus content as licensed local reference-only material, not as plugin source.

## Input Artifacts

- Local TailwindUI/Tailwind Plus root path
- Product, IA, interaction, visual, and HeroUI component contracts
- `10-visual-confirmation-plan.md`

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/04-visual/tailwind-reference-index.md`

## Required MCP Tool

- `inspect_tailwind_ui_reference`
- `plan_tailwind_hero_ui_adoption`
- `select_hero_ui_components`

## Hard Stops

- Do not copy TailwindUI source code into the plugin or generated project.
- Do not bundle TailwindUI templates, assets, previews, Catalyst UI Kit source, or screenshots into the plugin.
- Do not use Catalyst, Headless UI, or TailwindUI primitives when HeroUI has an official component.
- Do not let TailwindUI override HeroUI Official Component First.

## Pressure Test Responsibility

- Missing local reference path must block only TailwindUI enrichment, not the base HeroUI workflow.
- Direct source-copy requests must block.
- Catalyst primitive adoption must block when HeroUI has an official component.
- Tailwind v4 class usage must remain layout/supportive around HeroUI components.

## Next Gate

- `visual-design-orchestrator` may consume the reference index as inspiration for Pencil/Figma boards, while implementation still uses HeroUI official components.
