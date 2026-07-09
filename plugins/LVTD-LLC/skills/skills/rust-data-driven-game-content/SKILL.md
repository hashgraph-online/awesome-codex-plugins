---
name: rust-data-driven-game-content
description: Move Rust game monsters, items, loot, effects, spawn weights, level gates, and balance numbers into validated data files using Serde-friendly schemas. Use when replacing hard-coded spawn functions, adding RON or JSON content templates, or making game content editable without recompiling.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Data Driven Game Content
  category: Rust
  tags: rust,gamedev,serde,ron,data-driven
---

# Rust Data Driven Game Content

Use this skill to move game content out of Rust code and into validated data
files. Keep schemas small, explicit, and aligned with components the game can
actually spawn.

## Core Workflow

1. Identify repeated hard-coded spawn data.
2. Design a Serde-friendly schema for entities, effects, spawn levels, and
   weights.
3. Load data at startup or level generation with clear errors.
4. Convert templates into component bundles through one spawn boundary.
5. Add validation for missing fields, impossible levels, invalid effects, and
   empty spawn tables.
6. Keep balance changes in data and behavior changes in Rust systems.

## Read Next

Read `references/data-driven-content-patterns.md` for schema design,
RON/Serde notes, spawn weighting, validation, and review checks.

## Source Notes

Guidance is transformed and paraphrased from *Hands-On Rust* Chapters 13, 14,
and 15 and from the official companion source repository. Current crate context
was checked against Serde and RON docs. Verify the target project's chosen data
format and dependency versions before editing.
