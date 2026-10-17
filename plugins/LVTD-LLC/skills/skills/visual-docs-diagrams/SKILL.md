---
name: visual-docs-diagrams
description: Design and review visual content for developer documentation, including screenshots, architecture diagrams, boxes-and-arrows diagrams, flowcharts, swimlanes, video decisions, accessibility, performance, annotations, and visual maintenance. Use when creating or auditing diagrams, screenshots, visual explanations, or media in technical docs.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Visual Docs Diagrams
  category: Writing
  tags: developer-docs,technical-writing,documentation,diagrams,accessibility
---

# Visual Docs Diagrams

Use this skill to decide whether developer docs need visuals and to design or review those visuals for comprehension, accessibility, performance, and maintainability.

This skill is derived from *Docs for Developers: An Engineer's Field Guide to Technical Writing*, especially Chapter 6, "Adding visual content." The guidance is transformed and paraphrased; do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Define what the visual must help the reader understand or do.
3. Choose screenshot, diagram, flowchart, swimlane, or text-only based on the task.
4. Use `workflows/design-technical-visual.md` for full visual design or review.
5. Check accessibility, performance, placement, source files, and maintenance before finalizing.

## Default Output

When designing or reviewing visual docs, return:

1. **Visual purpose** - what the reader must understand faster or better.
2. **Recommended visual type** - screenshot, boxes-and-arrows, flowchart, swimlane, video, or no visual.
3. **Design notes** - scope, labels, annotations, contrast, placement, and format.
4. **Accessibility and performance checks** - alt text, captions, transcripts, SVG/image size, responsiveness.
5. **Maintenance plan** - source file, owner, update trigger, and review cadence.

## Contents

| Need | Start Here |
|------|------------|
| Understand visual types | `references/core/knowledge.md` |
| Apply visual rules | `references/core/knowledge.md` |
| See visual decision examples | `references/core/knowledge.md` |
| Design or review a visual | `workflows/design-technical-visual.md` |
| Route by task | `guidelines.md` |

## Core Posture

- Use visuals to supplement text, not replace critical instructions.
- Prefer one idea or level of detail per visual.
- Treat accessibility and maintenance as part of visual design, not post-production polish.
- Avoid video unless the motion itself is necessary and maintenance is realistic.
