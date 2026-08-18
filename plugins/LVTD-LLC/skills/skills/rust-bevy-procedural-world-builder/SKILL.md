---
name: rust-bevy-procedural-world-builder
description: Build and review Bevy procedural world generation with grid resources, deterministic seeds, reachability checks, chunk or room spawning, background generation boundaries, and gameplay-safe entity materialization. Use when creating tile maps, dungeon-like spaces, mining bases, or generated levels in Rust Bevy games.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Bevy Procedural World Builder
  category: Rust
  tags: rust,bevy,gamedev,procedural-generation,world-building
---

# Rust Bevy Procedural World Builder

Use this skill to turn procedural generation into a testable data pipeline:
generate data first, validate it, then materialize entities safely in Bevy.

## Core Workflow

1. Represent the world as data before spawning sprites or entities.
2. Make randomness explicit with seeds and generation parameters.
3. Validate constraints such as bounds, reachability, spawn safety, and resource
   placement.
4. Spawn Bevy entities from generated data in batches or chunks.
5. Keep background generation isolated from Bevy world mutation.
6. Profile generation and rendering separately before optimizing.

## Read Next

| Task | Load |
|------|------|
| Add generated rooms, terrain, or bases | `guidelines.md`, `workflows/build-procedural-world.md` |
| Review generation data structures | `references/procedural-world-patterns.md` |
| Move expensive generation off the main thread | `references/procedural-world-patterns.md` |

## Source Notes

Guidance is transformed and paraphrased from Herbert Wolverson,
*Advanced Hands-On Rust*, especially Chapters 10 through 13 on building and
optimizing a generated Mars-base game. Examples are original skeletons.
