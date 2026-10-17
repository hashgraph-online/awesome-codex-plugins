---
name: rust-bevy-asset-pipeline
description: Build and review Bevy game asset loading pipelines with typed asset catalogs, path validation, loading states, handle ownership, sprite sheets, audio, and runtime resource checks. Use when organizing Bevy assets, replacing hard-coded paths, adding loading screens, diagnosing missing handles, or packaging Rust game resources.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Bevy Asset Pipeline
  category: Rust
  tags: rust,bevy,gamedev,assets,packaging
---

# Rust Bevy Asset Pipeline

Use this skill to make Bevy assets explicit, typed, validated, and packageable.
The goal is to remove scattered string paths and make loading state observable.

## Core Workflow

1. Inventory images, atlases, fonts, sounds, music, and data files.
2. Create a typed catalog resource that owns paths and loaded handles.
3. Validate paths before gameplay systems depend on the assets.
4. Load assets in a dedicated loading state or plugin.
5. Pass handles through resources/components; avoid reloading from gameplay
   systems.
6. Smoke test release packaging from the same runtime layout users will run.

## Read Next

| Task | Load |
|------|------|
| Design a catalog or loading plugin | `guidelines.md`, `references/asset-pipeline-patterns.md` |
| Replace scattered asset paths | `workflows/build-asset-pipeline.md` |
| Diagnose missing assets in packaged builds | `guidelines.md`, `workflows/build-asset-pipeline.md` |

## Source Notes

Guidance is transformed and paraphrased from Herbert Wolverson,
*Advanced Hands-On Rust*, especially Chapter 6 on game assets and the recurring
release-readiness checks across the book. Examples are original skeletons.
