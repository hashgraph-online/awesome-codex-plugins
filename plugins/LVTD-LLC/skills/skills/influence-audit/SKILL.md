---
name: influence-audit
description: Use when auditing landing pages, emails, sales scripts, pricing flows, fundraising asks, product UX, or negotiations for persuasion mechanisms, pressure tactics, manipulation risk, fake urgency, fake social proof, authority misuse, or ethical rewrites.
license: MIT
metadata:
  version: "0.1.0"
  displayName: Influence Audit
  category: Marketing
  tags: influence,persuasion,ethics,audit
---

# Influence Audit

Audit persuasion by identifying which shortcut cues are present, whether those cues are truthful, and what a less manipulative version would look like. The central distinction is honest decision support versus counterfeit evidence.

## Quick Start

1. Read `guidelines.md` to choose the smallest useful reference set.
2. Load `references/audit/knowledge.md` for concepts and `references/audit/rules.md` for operating rules.
3. Use `workflows/audit-influence-risk.md` for repeatable tasks.
4. For audits, surface both the active influence cue and the ethical rewrite.

## Contents

| File | Purpose |
| --- | --- |
| references/audit/knowledge.md | Core concepts and source-grounded definitions |
| references/audit/rules.md | Rules, boundaries, and practical guidelines |
| references/audit/examples.md | Bad/better examples for applied situations |
| references/audit/smells.md | Red flags and anti-patterns to detect |
| references/audit/checklist.md | Fast review checklist |
| workflows/audit-influence-risk.md | Review a persuasion surface for mechanisms, evidence quality, user autonomy, and safer rewrites. |

## Operating Principles

- Use only honest evidence. Do not invent popularity, scarcity, credentials, endorsements, or social connection.
- Separate helping a good decision from pushing a shortcut response. If the cue is counterfeit, treat it as a red flag.
- When rewriting, preserve user agency: add context, alternatives, and enough time to decide when stakes are meaningful.

## Output Pattern

1. **Diagnosis** - name the influence principle or cue.
2. **Evidence Check** - state what proof supports or is missing from the cue.
3. **Risk** - explain manipulation, trust, or decision-quality risk.
4. **Rewrite or Recommendation** - provide an ethical alternative.

## Validation

Use the prompts in `evals/evals.json` as smoke tests. A good result identifies the relevant Influence principle, preserves user agency, and avoids fabricated evidence or coercive pressure.
