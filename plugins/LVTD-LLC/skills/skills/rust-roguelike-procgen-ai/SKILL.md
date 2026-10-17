---
name: rust-roguelike-procgen-ai
description: Design and review Rust roguelike procedural maps, map-builder traits, generator harnesses, field-of-view, spatial memory, Dijkstra/pathfinding, and simple monster AI. Use when adding dungeon generation, FOV, map memory, chasing behavior, or visibility-constrained AI to a Rust game.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Roguelike Procgen AI
  category: Rust
  tags: rust,gamedev,roguelike,procgen,pathfinding
---

# Rust Roguelike Procgen AI

Use this skill to add procedural map variety and tactical AI without losing
testability. Keep generators behind a common interface, validate generated
maps, and make AI depend on what entities can perceive.

## Core Workflow

1. Define a map builder output type with map, starts, exits, and spawn points.
2. Put each generator behind a shared trait or equivalent interface.
3. Validate reachability and spawn legality before using a generated map.
4. Add a small output harness or snapshot path for generator inspection.
5. Implement FOV and pathfinding through map traits or adapter functions.
6. Gate monster knowledge through visibility or memory rules.

## Read Next

Read `references/procgen-ai-patterns.md` for generator interfaces, FOV,
pathfinding, map memory, AI checks, and test harness patterns.

## Source Notes

Guidance is transformed and paraphrased from *Hands-On Rust* Chapters 9, 10,
11, and 12 and from the official companion source repository. Current crate
context was checked against `bracket-lib` docs, including its pathfinding and
geometry support.
