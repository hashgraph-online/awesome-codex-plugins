---
name: developer-docs-technical-research
description: Research product and feature facts for developer documentation by mapping source-of-truth owners, validating behavior hands-on, interviewing SMEs, and turning uncertainty into doc-ready notes. Use when feature specs are incomplete, implementation details need user-facing meaning, SMEs disagree, or docs require evidence before planning, drafting, release notes, API docs, tutorials, scenarios, or troubleshooting content.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Developer Docs Technical Research
  category: Writing
  tags: developer-docs,technical-writing,documentation,research,sme-interviews
---

# Developer Docs Technical Research

Use this skill to investigate product behavior before planning or writing developer documentation. It turns specs, code, prototypes, tickets, SMEs, and hands-on tests into traceable research notes.

This skill is derived from paraphrased guidance in Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 13, "Research for Technical Writers," Chapter 16, "Technical Verification," Chapter 19, "Working with Engineers," and Chapter 22, "Working with Product Management." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. State the documentation question, audience, feature, release context, and risk.
3. Build a source map from code, product surfaces, specs, tickets, SMEs, QA, support, and existing docs.
4. Use `workflows/research-feature-docs.md` when feature behavior or user consequences are unclear.
5. Use `workflows/interview-doc-sources.md` when the main work is extracting facts from SMEs.
6. Return verified facts, assumptions, contradictions, source owners, and open questions.

## Default Output

When completing a documentation research pass, return:

1. **Research brief** - doc question, audience, scope, and decision needed.
2. **Verified facts** - behavior, limits, defaults, prerequisites, permissions, errors, and examples with source.
3. **User consequences** - what readers can do, decide, risk, or misunderstand.
4. **Source map** - authoritative owner or artifact for each important fact.
5. **Contradictions and gaps** - unresolved disagreements, missing access, or untested behavior.
6. **Recommended docs action** - plan, draft, defer, file product issue, or request review.

## Contents

| Need | Start Here |
|------|------------|
| Understand technical research concepts | `references/core/knowledge.md` |
| Build a feature research plan | `workflows/research-feature-docs.md` |
| Interview engineers, PMs, QA, support, or field teams | `workflows/interview-doc-sources.md` |
| Route by task or symptom | `guidelines.md` |

## Core Posture

- Research user-facing consequences, not only implementation.
- Verify directly when the product, API, CLI, UI, or environment is available.
- Treat named owners and durable artifacts as the source of truth.
- Keep uncertainty visible until it is resolved.
- File product or UX defects when documentation would be forced to explain avoidable confusion.
