---
name: developer-docs-audience-research
description: Research developer documentation audiences by mapping user goals, learning objectives, business goals, developer traits, user questions, personas, user stories, journey maps, and friction logs. Use when planning docs for APIs, SDKs, platforms, CLIs, developer tools, onboarding guides, SaaS docs, or support-heavy docs before writing or restructuring content.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Developer Docs Audience Research
  category: Writing
  tags: developer-docs,technical-writing,documentation,user-research,audience-research
---

# Developer Docs Audience Research

Use this skill to understand who developer documentation is for before planning, writing, or reorganizing docs. It helps agents turn vague audiences into concrete users, goals, questions, journeys, and validation work.

This skill is derived from Jared Bhatti, Zachary Sarah Corleissen, Jen Lambourne, David Nunez, and Heidi Waterhouse's *Docs for Developers: An Engineer's Field Guide to Technical Writing*, especially Chapter 1, "Understanding your audience." It is expanded with paraphrased guidance from Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 3, "Audience," Chapter 9, "Learning Objectives," and Chapter 25, "Writing SaaS Documentation." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Start from the user's doc artifact or product surface, not from a generic audience label.
3. Identify user goals, learning objectives, business goals, user traits, questions, and missing knowledge.
4. Use `workflows/map-doc-audience.md` when the user needs a full audience brief.
5. Mark assumptions and recommend validation through user conversations, support data, analytics, or a friction log.

## Default Output

When researching an audience, return:

1. **Audience snapshot** - primary and secondary users, roles, skill level, environment, and constraints.
2. **Goals** - user goals and business goals that the docs must support.
3. **Learning objective** - starting point, destination, and exit criteria when useful.
4. **User questions** - setup, concept, task, API, troubleshooting, and decision questions.
5. **Research artifacts** - audience definition, persona, user story, journey map, or friction log entries when useful.
6. **Assumptions and gaps** - what is inferred versus verified.
7. **Validation plan** - the next interviews, data sources, or product walk-throughs.

## Contents

| Need | Start Here |
|------|------------|
| Understand audience concepts | `references/core/knowledge.md` |
| Apply research rules | `references/core/knowledge.md` |
| See concise examples | `references/core/knowledge.md` |
| Produce an audience brief | `workflows/map-doc-audience.md` |
| Define learning objectives | `workflows/define-learning-objectives.md` |
| Route by task | `guidelines.md` |

## Core Posture

- Treat "developer" as too broad until narrowed by task, context, skill, and environment.
- Separate what users need from what internal teams want to say.
- Distinguish durable audience definitions from specific personas.
- Prefer evidence over assumptions, but preserve assumptions clearly when evidence is not available yet.
- Let audience findings and learning objectives shape content type, order, depth, examples, and success metrics.
