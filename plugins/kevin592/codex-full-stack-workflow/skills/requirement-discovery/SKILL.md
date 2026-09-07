---
name: requirement-discovery
description: MUST use before brainstorming, visual companion, Pencil/Figma, or implementation when a user gives a rough product, feature, app, website, landing page, brand site, front-end design draft, or "do not develop yet" goal. Draft the first structured requirement contract and fixed workspace before design or implementation.
---

# Requirement Discovery

This skill turns a rough user goal into the first product-development contract. The user only needs to provide a rough goal, corrections, and confirmations.

The agent must draft information architecture, draft interaction structure, draft state requirements, draft API/data assumptions, and draft acceptance boundaries. Do not ask the user to provide IA, interaction matrices, state matrices, API contracts, or acceptance criteria from scratch.

## Entry Rule

For one-line site or design requests, start here. Examples:

- "I want a high-end coffee brand website, make the front-end design draft first, do not develop."
- "Create a SaaS landing page design."
- "I need an admin dashboard concept."

Do not offer a browser visual companion, open a local URL, start Pencil/Figma, or run a creative-only brainstorming flow before this skill has produced the fixed requirement workspace through `generate_requirement_workspace`. If brainstorming is useful, capture the idea as `AI Assumptions` inside the requirement discovery artifact, then ask at most three focused confirmation questions.

## Input Artifacts

- User rough request
- Existing project context when available
- Prior change record when this is a resumed or changed feature

## Output Artifact

- `docs/full-stack-development/requirements/<feature-slug>/01-intake/requirement-discovery.md`

## Required MCP Tool

- `generate_requirement_workspace`
- `review_artifact_contract`
- `review_stage_gate`

## Hard Stops

- Do not let `brainstorming` replace requirement discovery for product, website, landing page, brand site, or design-draft requests.
- Do not offer browser visual companion or local URL preview before `generate_requirement_workspace`.
- Do not enter Pencil/Figma.
- Do not write implementation code.
- Do not ask more than at most three focused questions before drafting assumptions.
- Do not treat a chat summary as a project artifact.

## Pressure Test Responsibility

- `rough-admin-one-line` must produce a usable draft.
- `over-clarification` must block when the agent asks too many questions without a draft.
- `empty-requirement-discovery` must block.

## Next Gate

- Product scope may proceed only after `review_artifact_contract` passes for requirement discovery.
