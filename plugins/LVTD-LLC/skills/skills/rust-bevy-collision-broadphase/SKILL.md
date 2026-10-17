---
name: rust-bevy-collision-broadphase
description: Design and review Bevy 2D collision broadphase systems with AABB bounds, spatial indexes, typed collision events, and benchmark-driven test beds. Use when replacing O(n^2) collision checks, adding spatial partitioning, diagnosing Bevy collision performance, or separating broadphase, narrowphase, and response systems in Rust games.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Bevy Collision Broadphase
  category: Rust
  tags: rust,bevy,gamedev,collision,performance
---

# Rust Bevy Collision Broadphase

Use this skill to make Bevy collision detection scale without mixing detection,
response, rendering, and gameplay rules into one system.

## Core Workflow

1. Identify the collision shapes, movement model, entity counts, and layers.
2. Keep collider data small and independent from sprites, textures, and game
   rules.
3. Choose the cheapest broadphase that fits the scene: brute force for tiny
   counts, spatial hash for uniform worlds, quad tree for clustered worlds.
4. Emit candidate or collision events; let separate systems decide response.
5. Test edge contacts, fast movement, layer filters, despawn cases, and
   deterministic ordering.
6. Benchmark before and after changing the broadphase.

## Read Next

| Task | Load |
|------|------|
| Pick or review a broadphase | `guidelines.md`, `references/broadphase-patterns.md` |
| Optimize an existing collision system | `workflows/optimize-collision.md` |
| Route a specific symptom | `guidelines.md` |

## Source Notes

Guidance is transformed and paraphrased from Herbert Wolverson,
*Advanced Hands-On Rust*, especially Chapter 8 on obstacles and collision
detection and Chapter 12 on optimization. The examples are original skeletons
intended to preserve the transferable technique, not the book's project code.
