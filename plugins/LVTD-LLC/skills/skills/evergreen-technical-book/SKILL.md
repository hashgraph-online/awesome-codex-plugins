---
name: evergreen-technical-book
description: Keep technical nonfiction durable by separating timeless concepts, decision frameworks, and reader outcomes from fast-changing tool walkthroughs, UI steps, versions, vendor details, and companion resources. Use when scoping, outlining, revising, or updating technical books, self-hosting guides, software manuals, DevOps books, or other technical manuscripts that risk becoming outdated.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Evergreen Technical Book
  category: Writing
  tags: writing,books,nonfiction,technical-writing,evergreen
---

# Evergreen Technical Book

## Core Lens

Technical books become durable when the printed or stable manuscript teaches long-lived principles, decision frames, mental models, and workflows while volatile commands, UI walkthroughs, vendor details, and version-specific steps live in updateable companion resources.

Use this skill to:

- Decide what belongs in a technical book versus a website, repo, worksheet, video, or checklist.
- Reduce version drift without making the book abstract.
- Design update policies for companion resources.
- Keep self-hosting, DevOps, software, or infrastructure books useful for years.
- Revise drafts that are overloaded with tool minutia.

## Reference Routing

| Need | Read |
|------|------|
| Evergreen concepts and terminology | `references/core/knowledge.md` |
| Durability and split rules | `references/core/rules.md` |
| Book vs companion examples | `references/core/examples.md` |
| Fast durability checklist | `references/core/checklist.md` |
| Split book and companion resources | `workflows/split-book-and-companion.md` |

## Workflow

### 1. Identify The Durable Promise

State the reader outcome that should remain valuable for several years.

If the promise depends on one vendor, one UI, or one narrow tool version, decide whether the book is intentionally edition-based or should be reframed.

### 2. Classify Content By Half-Life

Tag each major section or artifact:

- **Durable**: concepts, tradeoffs, failure modes, principles, mental models.
- **Semi-durable**: workflows, architecture patterns, checklists, example configurations.
- **Volatile**: UI clicks, prices, vendor policies, exact package versions, screenshots, short-lived tools.

### 3. Split The Content

Keep the book concrete, but move volatile detail to companion resources when it would quickly date the manuscript.

The book should still deliver the core promise without requiring an upsell, hidden resource, or fragile link.

### 4. Design Companion Resources

For each companion item, define:

- Purpose.
- Owner.
- Update trigger.
- Stable URL or repository path.
- Version or last-reviewed note.
- How the book references it without breaking if it changes.

### 5. Add Update Hooks

Create a maintenance plan:

- Versioned examples.
- Changelog or last-reviewed dates.
- Issue/report path for readers.
- Periodic review cadence.
- Replacement policy for stale tools.

## Output Format

When helping with an evergreen technical book, return:

1. Durability diagnosis.
2. Book vs companion split table.
3. Recommended scope cuts or moves.
4. Companion resource plan.
5. Update policy and review cadence.
6. Manuscript wording for volatile references.

## Quality Bar

Do not solve drift by making the book vague. Keep the reader's path concrete while making volatile details easy to update and easy to skip when they age.
