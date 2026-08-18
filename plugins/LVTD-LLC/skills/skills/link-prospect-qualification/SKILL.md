---
name: link-prospect-qualification
description: Qualify, score, filter, and prioritize link-building prospects by relevance, trust, editorial quality, authority, outreach fit, spam risk, and asset readiness. Use when reviewing raw URL lists, deciding which sites are worth outreach, auditing link target quality, segmenting prospects, or rejecting risky link opportunities.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Link Prospect Qualification
  category: Marketing
  tags: seo,link-building,qualification,prospecting,trust
---

# Link Prospect Qualification

Use this skill to turn raw prospect URLs into prioritized outreach segments with evidence, scores, rejection reasons, and next actions.

This skill is derived from Garrett French and Eric Ward's *Ultimate Guide to Link Building* and uses transformed guidance with durable book-topic references. Do not copy book prose into user outputs.

## Quick Start

1. Use the Contents table below to choose the smallest useful reference set.
2. Use `workflows/qualify-link-prospects.md` for a full qualification pass.
3. Apply hard reject gates before scoring.
4. Use automated signals to triage, then manually inspect shortlisted pages.
5. Return priority, standard, nurture, review, and reject buckets with evidence.

## Default Output

When asked to qualify prospects, return:

1. **Summary** - reviewed, priority, standard, nurture, manual review, rejected.
2. **Priority prospects** - URL, type, score, fit, qualification reason, pitch angle, contact path.
3. **Review/nurture prospects** - open questions and needed checks.
4. **Rejected prospects** - reject reason and evidence.
5. **Rubric notes** - relevance, trust, authority, editorial quality, spam risk, and asset readiness.

## Contents

| Need | Start Here |
|------|------------|
| Understand qualification concepts | `references/core/knowledge.md` |
| Apply scoring rules | `references/core/rules.md` |
| See scoring examples | `references/core/examples.md` |
| Run qualification | `workflows/qualify-link-prospects.md` |

## Core Posture

- Metrics triage prospects; human relevance and intent decide.
- Trust comes from people and institutions serving users, not from scores alone.
- Spam risk can override attractive authority metrics.
- A target asset should be internally connected and shareable before outreach.
