---
name: rust-game-polish-release
description: Finish and package small Rust games with MVP lock, playability checks, resource packaging, release builds, smoke tests, and disciplined post-MVP polish. Use when preparing a Rust game prototype for sharing, packaging bracket-lib assets, or deciding what finishing work belongs before release.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Game Polish Release
  category: Rust
  tags: rust,gamedev,release,packaging,polish
---

# Rust Game Polish Release

Use this skill to finish a small Rust game without destabilizing the MVP. Lock
the playable loop first, then package assets, run release checks, and add only
the polish that improves clarity or shareability.

## Core Workflow

1. Confirm the MVP loop is playable from launch to win/loss or exit.
2. Freeze core mechanics before adding content and visual polish.
3. Verify resources load from the release layout.
4. Run formatting, linting, tests, and release build commands.
5. Smoke test controls, restart, level transitions, and exit behavior.
6. Write a small release checklist instead of making last-minute architecture
   changes.

## Read Next

Read `references/polish-release-patterns.md` for release gates, packaging
checks, and safe polish triage.

## Source Notes

Guidance is transformed and paraphrased from *Hands-On Rust* Chapter 16 and
the book's recurring slice-based development pattern. Packaging details should
be adapted to the target engine, OS, and distribution channel.
