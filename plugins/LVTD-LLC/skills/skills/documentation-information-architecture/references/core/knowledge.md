# Documentation IA Knowledge

Information architecture helps readers build a mental model of a documentation set and move from question to answer without unnecessary searching.

Source basis: *Docs for Developers*, Chapter 10, "Organizing documentation"; *The Product Is Docs*, Chapter 17, "Tools and Content Delivery," plus related audience, learning-objective, maintenance, and SaaS guidance from Chapters 3, 9, 10, and 25.

## Structure Patterns

| Pattern | Use |
|---------|-----|
| Sequence | Ordered learning path, onboarding, migration, or setup |
| Hierarchy | Parent-child organization by product area, task group, or concept set |
| Web | Cross-linked related content for non-linear exploration |

Most docs sites combine these patterns: a hierarchy for navigation, sequences for onboarding, and web links for related tasks.

## Navigation Elements

- Site navigation.
- Landing pages.
- Breadcrumbs.
- Side navigation.
- Prerequisites and next steps.
- Related links.
- Metadata, labels, and search facets.
- Redirects during migration.

## Content Inventory Actions

| Label | Meaning |
|-------|---------|
| Keep | Current, useful, and in the right place |
| Remove | Stale, unused, unsupported, or harmful |
| Review | Needs owner or source validation |
| Merge | Overlaps with another page |
| Split | Contains multiple user goals or doc types |
| Move | Useful but in the wrong location |
| Create | Gap required by user tasks |

## Platform And Tool Selection

Documentation platforms shape what readers can find and what writers can maintain. Start with prioritized requirements, not tool features. Consider:

| Area | Questions |
|------|-----------|
| Reader usability | Does search work, does layout adapt to devices, is content accessible, can readers leave feedback, and can offline or PDF output stay readable? |
| Content model | Does the tool support the topic size, reuse, versioning, localization, media, metadata, and structured authoring the docs require? |
| Migration | Can existing content move without destructive conversion, URL loss, metadata loss, or a major information redesign surprise? |
| Integration | Does the tool fit source control, issue tracking, release notes, API generation, analytics, authentication, or product help links? |
| Maintenance | Can writers manage links, redirects, version branches, reviews, ownership, and freshness checks? |
| Support burden | Who can configure, extend, troubleshoot, and maintain the platform? |
| Portability | Can content leave the platform in a usable, human-readable format if the team changes tools later? |
| Cost | Do pricing, training, subscription, and maintenance costs match how much of the tool the team will actually use? |

Before changing tools, test whether the real problem is broken process, unclear ownership, poor IA, missing metadata, or stale content. A new platform can amplify bad process.

## Common Misconceptions

- **Myth**: More navigation cues always improve findability.
  **Reality**: Too many cues create noise and decision fatigue.
- **Myth**: IA should mirror engineering architecture.
  **Reality**: IA should mirror reader tasks and mental models.
- **Myth**: Migration is done when pages move.
  **Reality**: Redirects, metadata, search, links, and user validation are part of migration.
- **Myth**: A better docs platform fixes broken docs process.
  **Reality**: Tooling helps when requirements and workflows are understood; it can worsen unclear ownership or IA.
- **Myth**: More platform features mean better reader experience.
  **Reality**: Unused or complex features can increase authoring cost and distract from delivering useful content.

## Rules And Checks

Use these rules when auditing or redesigning documentation information architecture.

## Core Rules

1. **Start with user tasks** - Organize around what readers need to do, learn, decide, or fix.
2. **Inventory before redesign** - Know what exists before proposing structure.
3. **Label content actions** - Keep, remove, review, merge, split, move, or create.
4. **Use landing pages for routing** - A landing page should get readers to the right place quickly.
5. **Avoid excessive depth** - Deep hierarchies bury content; shallow hierarchies can become noisy.
6. **Use navigation cues economically** - Add cues that solve real orientation problems.
7. **Preserve redirects** - Migrations need redirect plans and link validation.
8. **Document IA decisions** - Future maintainers need to know why content belongs where it does.
9. **Plan maintenance** - Owners, metadata, and review triggers prevent drift.
10. **Define platform requirements from user and author needs** - Reader usability, author workflow, migration, metrics, and support matter before feature lists.
11. **Favor portability** - Avoid proprietary lock-in unless benefits clearly outweigh migration risk.
12. **Check support capacity** - A flexible platform still fails if no one can maintain it.
13. **Fix process problems before tooling problems** - Do not expect a tool migration to repair unclear ownership, review, or IA.

## Quick Checks

| Question | Good Answer |
|----------|-------------|
| Where should a new user start? | Clear entry point or sequence |
| Where should an experienced user look up details? | Findable reference path |
| Is content duplicated? | Merged or clearly scoped pages |
| What happens to moved pages? | Redirect and link update plan |
| How will IA stay current? | Owner, metadata, and review cadence |
| What does the platform need to support? | Prioritized reader, author, maintenance, integration, and migration requirements |
| What happens if the tool changes later? | Portable content model and export path |

## Red Flags

- Top-level navigation is a product org chart.
- A landing page contains long prose but weak routing.
- Pages with different purposes are nested because they share a keyword.
- Migration omits redirects, metadata, or search impact.
- No one can explain why a page belongs in its section.
- The tool decision starts with vendor features before requirements.
- Content depends on a proprietary format with no practical export path.
- No team owns platform customization, support, or failure recovery.


## Examples And Patterns

Use these examples as IA decision patterns.

## Structure Choice

Scenario: Organize docs for a payments API.

| User Need | IA Pattern |
|-----------|------------|
| Complete first integration | Sequence: quickstart steps |
| Find object and endpoint details | Hierarchy: API reference by resource |
| Explore related webhook tasks | Web: related links between guides |
| Choose product path | Landing page: route by use case |

## Inventory Row Pattern

```text
Page: /docs/webhooks/signatures
Current role: How-to guide
User task: Verify incoming webhook signatures
Status: Keep and update
Action: Add prerequisites, move conceptual explanation to overview, link troubleshooting page
Owner: Developer docs
Redirect needed: No
```

## Split Decision

Weak page: "Webhooks" includes concept overview, event reference, setup tutorial, errors, retries, and migration notes.

Better IA:

- `webhooks/overview` for concepts and lifecycle.
- `webhooks/quickstart` for first delivery.
- `webhooks/signatures` for verification task.
- `reference/events` for event schema.
- `webhooks/troubleshooting` for failed delivery and invalid signatures.

## Platform Requirement Pattern

```text
Reader requirements: Fast search, stable URLs, mobile-friendly layout, page feedback, version selector
Author requirements: Markdown source, pull-request review, link checking, reusable snippets, generated API refs
Migration requirements: Redirect map, metadata export, old URL preservation, content inventory actions
Support requirements: Named owner for theme, build, search, redirects, and access control
Decision guardrail: Do not migrate until process issues around ownership and review are documented
```
