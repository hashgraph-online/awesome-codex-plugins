---
name: documentation-quality-metrics
description: Audit and measure developer documentation quality using functional quality, structural quality, accessibility, purpose, findability, accuracy, completeness, clarity, concision, consistency, analytics, user goals, doc goals, and metric plans. Use when evaluating docs, designing documentation metrics, selecting dashboards, or linking docs work to user and business outcomes.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Documentation Quality Metrics
  category: Writing
  tags: developer-docs,technical-writing,documentation,metrics,quality
---

# Documentation Quality Metrics

Use this skill to evaluate developer documentation quality and choose metrics that answer real questions. It combines editorial quality with analytics and user outcomes.

This skill is derived from *Docs for Developers: An Engineer's Field Guide to Technical Writing*, especially Chapter 9, "Measuring documentation quality." It is expanded with paraphrased guidance from Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 11, "Measuring Success." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Identify the decision the measurement should support.
3. Decide how much uncertainty the team needs to reduce before acting.
4. Audit functional quality before structural polish.
5. Use `workflows/audit-doc-quality.md` for a full quality or metric plan.
6. Prefer metric clusters with baseline and context over isolated numbers.

## Default Output

When auditing quality or designing metrics, return:

1. **Measurement question** - what decision the metric or audit supports.
2. **Uncertainty to reduce** - what the team does not know yet and how precise the answer needs to be.
3. **Functional quality findings** - accessibility, purpose, findability, accuracy, completeness.
4. **Structural quality findings** - clarity, concision, consistency.
5. **Metric plan** - qualitative and quantitative signals, baselines, owners, and limits.
6. **Recommended actions** - fixes, experiments, or data collection.
7. **Caveats** - what the available metrics cannot prove.

## Contents

| Need | Start Here |
|------|------------|
| Understand quality dimensions | `references/core/knowledge.md` |
| Apply audit and metric rules | `references/core/knowledge.md` |
| See metric examples | `references/core/knowledge.md` |
| Run quality audit | `workflows/audit-doc-quality.md` |
| Route by task | `guidelines.md` |

## Core Posture

- Good docs fulfill their purpose for users.
- Functional quality matters before stylistic polish.
- Metrics reduce uncertainty for a decision; counting is not measurement by itself.
- Combine analytics with qualitative evidence; neither tells the full story alone.
