---
name: game-playtest-planning
description: Plan, run, and interpret game playtests. Use when validating prototypes, onboarding, difficulty, mechanics, UI clarity, retention, or fun; when writing playtest scripts, surveys, observation plans, or telemetry requirements.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Game Playtest Planning
  category: Game Development
  tags: game-design,playtesting,user-research,telemetry,validation
---

# Game Playtest Planning

Use this skill to turn uncertainty into a playtest that can guide build decisions. A useful playtest starts with decisions the team is willing to make based on evidence.

## Source Traceability

Primary source: *The Art of Game Design: A Book of Lenses, Third Edition* by Jesse Schell, especially chapter 28 on playtesting. The workflow is transformed and paraphrased.

Supporting sources include Games User Research playtest guidance and Nielsen Norman Group usability-testing methods.

## Workflow

1. Define what decision the playtest should inform.
2. Choose participants who match the design question.
3. Pick the method: observation, think-aloud, task test, blind first-session, survey, telemetry review, or comparative test.
4. Write a protocol that avoids leading the player.
5. Capture observation, telemetry, player interpretation, and post-test reflection separately.
6. Convert findings into prioritized design changes.

## Required Output

- `Research Questions`: what must be learned.
- `Participant Plan`: who to test and why.
- `Protocol`: setup, tasks, moderator script, data to collect, and debrief.
- `Telemetry`: events and metrics to instrument.
- `Analysis Plan`: severity rubric, decision rules, and next design actions.

## Local References

Before producing a playtest plan, read:

- `references/core/guide.md`
- `workflows/playtest-protocol.md`
