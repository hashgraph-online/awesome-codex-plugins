---
name: rust-game-slice-planning
description: Plan small, playable Rust game implementation slices from a short design brief, MVP, stretch goals, and acceptance checks. Use when starting a Rust game, scoping a prototype, converting a game idea into work items, or preventing an AI coding agent from overbuilding.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust Game Slice Planning
  category: Rust
  tags: rust,gamedev,planning,mvp,scope
---

# Rust Game Slice Planning

Use this skill to turn a Rust game idea into small, playable implementation
slices. Optimize for visible progress, limited scope, and an MVP that can be
finished before optional polish work begins.

## Core Workflow

1. Write or recover a short design brief: title, short description, core loop,
   MVP, stretch goals, technical constraints, and target controls.
2. Separate "must ship" mechanics from stretch goals. Keep the first milestone
   to the smallest playable loop.
3. Convert the MVP into ordered slices. Each slice should compile, run, and add
   one visible player-facing capability.
4. Give each slice acceptance checks that an agent can verify locally.
5. Defer content expansion, visuals, extra systems, and balance work until the
   current slice is complete.

## Read Next

Read `references/slice-planning.md` for the design brief template, slice order,
and anti-overbuilding checks.

## Source Notes

Guidance is transformed and paraphrased from Herbert Wolverson's *Hands-On
Rust*, especially Chapter 4 and Appendix A2, and from the official companion
source repository. This is not official material from the author or publisher.
