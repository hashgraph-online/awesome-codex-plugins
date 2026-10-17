---
name: seo-persona-intent-mapping
description: Map SEO personas, search intent, funnel stage, expected content format, CTA, device context, and localization needs into actionable organic search plans. Use when planning keyword research, SEO content briefs, funnel mapping, search intent analysis, persona-driven content, or when traffic is not converting.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: SEO Persona Intent Mapping
  category: Marketing
  tags: seo,personas,search-intent,content-strategy,conversion
---

# SEO Persona Intent Mapping

Use this skill to turn vague keyword or audience ideas into a search-user map: who is searching, where they are in the buying journey, what content they expect, and what action should follow.

This skill is derived from Eli Schwartz's *Product-Led SEO* and uses transformed guidance with durable book-topic references. Do not copy book prose into user outputs.

## Quick Start

1. Load `guidelines.md` to choose the smallest reference set.
2. Use `workflows/map-persona-intent.md` for a full mapping pass.
3. Build persona rows around search behavior, not demographics.
4. Match each intent to content format, depth, CTA, device, and localization needs.
5. Prioritize the work by customer value and business outcome.

## Default Output

When asked to map personas or intent, return:

1. **Persona segments** - search-behavior-based groups.
2. **Intent and funnel stage** - problem, research, comparison, purchase, support, or retention.
3. **Expected content/product experience** - format and depth.
4. **CTA** - next action appropriate to stage.
5. **Device/localization considerations** - screen, language, country, and cultural cues.
6. **Priority** - business value and evidence.
7. **Open research questions** - what must be validated with users or data.

## Contents

| Need | Start Here |
|------|------------|
| Understand SEO-specific personas | `references/core/knowledge.md` |
| Apply mapping rules | `references/core/rules.md` |
| See mapping examples | `references/core/examples.md` |
| Build a persona-intent table | `workflows/map-persona-intent.md` |
| Route by task | `guidelines.md` |
