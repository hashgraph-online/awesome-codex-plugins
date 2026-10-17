---
name: rust-legion-ecs-gameplay
description: Design and review Rust ECS gameplay code using Legion-style entities, components, resources, systems, schedules, queries, command buffers, and spawners. Use when building ECS-driven Rust game features, migrating game state into ECS, or debugging system ordering and component composition.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Legion ECS Gameplay
  category: Rust
  tags: rust,gamedev,ecs,legion,components
---

# Rust Legion ECS Gameplay

Use this skill to build ECS gameplay code in Rust, especially in projects using
Legion or a Legion-like architecture. Keep components as data, systems as
focused logic, and resources as shared singleton state.

## Core Workflow

1. Identify entities, components, systems, and resources from the feature.
2. Add data-only components before adding systems that consume them.
3. Put entity construction in spawner functions or factories.
4. Use queries that request only the components a system needs.
5. Sequence systems with schedules and flush points when later systems must
   observe structural changes.
6. Verify behavior through one small gameplay path before adding more entity
   types.

## Read Next

Read `references/ecs-gameplay-patterns.md` for component design, system
ordering, spawners, rendering systems, and ECS review checks.

## Source Notes

Guidance is transformed and paraphrased from *Hands-On Rust* Chapter 6 and
the official companion source repository. Current crate context was checked
against Legion and Bevy ECS docs. If the target project uses Bevy, hecs, specs,
or another ECS, adapt the architecture instead of forcing Legion APIs.
