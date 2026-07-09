---
name: rust-tilemap-camera-rendering
description: Design and review Rust tile maps, map indexing, collision checks, map builders, camera-relative rendering, layered drawing, and tile themes. Use when building 2D grid worlds, roguelike maps, tile cameras, or bracket-lib style rendering systems.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Tilemap Camera Rendering
  category: Rust
  tags: rust,gamedev,tilemap,camera,rendering
---

# Rust Tilemap Camera Rendering

Use this skill to build grid-based maps and camera-relative rendering in Rust.
Keep map storage, coordinate conversion, movement validation, and draw order
explicit before adding richer art or themes.

## Core Workflow

1. Define map dimensions, tile types, and coordinate/index conversion.
2. Add bounds and walkability checks before player or entity movement.
3. Keep map generation behind a builder or constructor boundary.
4. Render visible tiles through a camera-relative coordinate transform.
5. Draw layers in deterministic order: base terrain, entities, effects, UI.
6. Add themes only after the map and camera rules are stable.

## Read Next

Read `references/tilemap-camera-patterns.md` for data shapes, render order,
camera math, and review checks.

## Source Notes

Guidance is transformed and paraphrased from *Hands-On Rust* Chapters 5 and
12 and from the official companion source repository. The examples are
original teaching skeletons derived from the architecture, not copied book
listings.
