---
name: rust-bevy-state-flow
description: Design and review Bevy game state flow with plugins, AppState enums, OnEnter and OnExit setup, state-scoped cleanup, menus, pause screens, transitions, and run conditions. Use when adding reusable Bevy game state management, debugging duplicated entities after transitions, or separating menu, loading, playing, paused, and game-over logic.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Bevy State Flow
  category: Rust
  tags: rust,bevy,gamedev,state-management,plugins
---

# Rust Bevy State Flow

Use this skill to make Bevy states explicit and reusable. State flow should
describe when systems run, what is created on entry, and what is cleaned up on
exit.

## Core Workflow

1. Name the user-visible game phases before adding systems.
2. Represent phases with an `AppState` or feature-specific state enum.
3. Put setup in `OnEnter`, cleanup in `OnExit`, and gameplay in state-filtered
   update schedules.
4. Mark state-owned entities with cleanup components.
5. Keep transitions event-driven or command-driven, not hidden in rendering
   systems.
6. Test repeated transitions to catch duplicate entities and stale resources.

## Read Next

| Task | Load |
|------|------|
| Add a menu, pause, loading, or game-over state | `guidelines.md`, `workflows/add-state-flow.md` |
| Review Bevy plugins and state-scoped systems | `references/state-flow-patterns.md` |
| Debug transition leaks | `guidelines.md`, `references/state-flow-patterns.md` |

## Source Notes

Guidance is transformed and paraphrased from Herbert Wolverson,
*Advanced Hands-On Rust*, especially Chapter 5 on reusable game state
management. Examples are original skeletons adapted for modern Bevy patterns.
