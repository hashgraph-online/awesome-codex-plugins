---
name: saas-documentation
description: Plan and write SaaS documentation for managed services, continuous releases, provider/customer responsibility boundaries, UI/browser constraints, runbooks, support enablement, and release readiness. Use when documenting cloud products, hosted services, admin consoles, fleet-wide changes, service operations, incident or runbook procedures, SaaS release notes, customer-controlled settings, or internal docs that support customer experience.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: SaaS Documentation
  category: Writing
  tags: developer-docs,technical-writing,documentation,saas,operations
---

# SaaS Documentation

Use this skill to plan, draft, and review documentation for SaaS and managed-service products. It covers public customer docs and internal operational docs that affect the customer experience.

This skill is derived from paraphrased guidance in Christopher Gales and the Splunk Documentation Team's *The Product Is Docs: Writing Technical Documentation in a Product Development Group*, especially Chapter 25, "Writing SaaS Documentation," Chapter 10, "Maintaining Existing Content," Chapter 18, "Working with Customer Support," and Chapter 2, "Agile." Do not copy book prose into user outputs. Source: https://link.springer.com/book/10.1007/978-1-4842-7217-6

## Quick Start

1. Load `guidelines.md` to choose the smallest useful reference set.
2. Identify whether the docs are public customer docs, internal service docs, release notes, runbooks, or support enablement.
3. Define what the provider manages and what the customer controls.
4. Use `workflows/plan-saas-docs.md` for customer-facing documentation plans.
5. Use `workflows/create-saas-runbook.md` for operational or support procedures.
6. Return customer impact, prerequisites, responsibilities, release timing, owners, and review needs.

## Default Output

When working on SaaS documentation, return:

1. **Audience and surface** - customer, admin, support, operations, field, or internal team.
2. **Responsibility boundary** - provider-managed, customer-controlled, shared, or unsupported.
3. **Customer impact** - action required, risk, timing, permissions, billing, security, or availability.
4. **Doc set recommendation** - public topic, release note, support article, runbook, enablement note, or escalation path.
5. **Operational readiness** - owners, review, incident path, support signals, and update triggers.
6. **Open questions** - unresolved behavior, launch timing, support process, or ownership.

## Contents

| Need | Start Here |
|------|------------|
| Understand SaaS documentation concepts | `references/core/knowledge.md` |
| Plan SaaS customer-facing docs | `workflows/plan-saas-docs.md` |
| Create support or operations runbooks | `workflows/create-saas-runbook.md` |
| Route by task or symptom | `guidelines.md` |

## Core Posture

- Treat documentation as part of the managed service.
- Make provider and customer responsibilities explicit.
- Document fleet-wide change with customer impact and action, not just feature description.
- Treat internal runbooks and support enablement as customer-experience infrastructure.
- Keep SaaS docs current with release, operations, and support signals.
