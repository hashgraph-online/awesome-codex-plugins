# Game Design Docs Guide

## Document Types

- Game brief: compact source of truth for player promise, target platform, target player, scope, and constraints.
- System spec: rules, state, data, edge cases, tuning parameters, and tests for one gameplay system.
- Feature contract: what to build now, exclusions, acceptance criteria, and telemetry.
- Content schema: data fields, authoring rules, examples, validation, and asset references.
- Tuning sheet: parameters, ranges, rationale, change history, and metrics.
- Playtest report: research questions, evidence, severity, decisions, and follow-up tasks.
- Decision log: important choices, reasons, tradeoffs, and links.

## AI-Agent Documentation Rules

- Put current intent at the top.
- Use explicit exclusions so the agent does not overbuild.
- Include acceptance criteria and test commands.
- Mark speculative ideas as speculative.
- Keep one source of truth for each system.
- Prefer tables for parameters and state machines.
- Include examples for data formats.
- Record why a decision was made when future reversal would be tempting.

## Document Health Checks

A useful game design doc is:

- short enough to read before coding
- concrete enough to implement
- current enough to trust
- structured enough to diff
- connected to tests or playtest evidence
- honest about unknowns

## Source Notes

- Book source: Jesse Schell, *The Art of Game Design: A Book of Lenses, Third Edition*, chapter 27 (`https://www.routledge.com/The-Art-of-Game-Design-A-Book-of-Lenses-Third-Edition/Schell/p/book/9781138632059`).
