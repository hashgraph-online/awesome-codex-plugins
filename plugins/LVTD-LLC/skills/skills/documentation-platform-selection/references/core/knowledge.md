# Documentation Platform Selection Knowledge

Documentation platforms shape what readers can find and what writers can maintain. A good tool decision starts with requirements and operating reality.

Source basis: *The Product Is Docs*, Chapter 17, "Tools and Content Delivery," plus related maintenance and audience guidance from Chapters 3 and 10.

## Key Concepts

### Reader Experience Requirements

**Definition**: The capabilities readers need to find, understand, trust, and use documentation.

Examples include search, navigation, accessibility, responsive layout, versioning, feedback, stable URLs, localization, and offline or PDF output.

### Author Workflow Requirements

**Definition**: The capabilities writers and reviewers need to create, review, publish, and maintain docs efficiently.

Examples include source control, review workflow, preview, reusable snippets, media handling, link checks, generated reference, ownership metadata, and publishing controls.

### Content Model

**Definition**: The structure and format a platform uses for topics, metadata, reuse, references, versions, and assets.

The content model determines whether the team can scale, migrate, localize, reuse, and audit content.

### Platform Support Burden

**Definition**: The setup, customization, troubleshooting, search tuning, build, access control, and maintenance work required to keep the platform healthy.

Flexible tools can be powerful and expensive to support. Simple tools can be reliable and limiting.

### Portability

**Definition**: The ability to export content, metadata, URLs, redirects, and assets into a usable format when the platform changes.

Portability protects long-lived documentation from tool churn and vendor lock-in.

## Requirement Categories

| Category | Questions |
|----------|-----------|
| Reader usability | Can readers search, navigate, skim, filter, access, and give feedback? |
| Content model | Does it support topic size, reuse, metadata, media, localization, versioning, generated refs, and structured authoring? |
| Authoring workflow | Does it support review, preview, source control, collaboration, roles, branch strategy, and approvals? |
| Integrations | Does it fit issue tracking, analytics, API generation, product links, authentication, CI, and deployment? |
| Maintenance | Can owners manage links, redirects, freshness, version branches, ownership, and stale content? |
| Migration | Can existing content move with URLs, metadata, assets, redirects, and search behavior intact? |
| Portability | Can content leave the platform in a useful format? |
| Support burden | Who will configure, extend, troubleshoot, and maintain it? |
| Cost | Do subscription, implementation, training, and maintenance costs match expected use? |

## Core Rules

1. **Define outcomes before options** - Requirements come before vendor comparison.
2. **Separate tool problems from process problems** - Poor ownership, stale content, weak IA, and missing review can survive any migration.
3. **Score against prioritized requirements** - Not all features matter equally.
4. **Test real content** - Pilot with representative docs, media, redirects, generated content, and review workflow.
5. **Include maintenance work** - A platform decision includes ownership, support, troubleshooting, and upgrades.
6. **Plan migration as a product change** - Preserve URLs, redirects, metadata, search, and user paths.
7. **Prefer portable content** - Avoid lock-in unless benefits clearly justify the future migration cost.
8. **Check author adoption** - A powerful workflow that writers cannot or will not use will fail.
9. **Plan reader validation** - Search and navigation claims need evidence from actual content and user tasks.
10. **Treat custom platforms carefully** - Custom code creates product ownership and support obligations.
11. **Document the decision** - Future maintainers need to know why the tool was chosen and what tradeoffs were accepted.
12. **Avoid feature excitement** - A long feature list is not a strategy.

## Option Types

| Option | Strengths | Watch |
|--------|-----------|-------|
| Docs-as-code static site | Review workflow, version control, portability, automation | Requires Git/build comfort and platform ownership |
| CMS or help center | Nontechnical authoring, publishing controls, support integration | Portability, customization limits, content model constraints |
| Wiki | Low-friction internal collaboration | Ownership, structure, lifecycle, public delivery, search consistency |
| DITA or structured authoring | Reuse, controlled content, localization, large-scale governance | Training, tooling cost, authoring complexity |
| API reference generator | Accurate reference from schema or code | Needs human context, examples, concepts, and review |
| Custom platform | Tailored reader and product integration | Engineering support, roadmap, maintenance, and migration risk |

## Common Misconceptions

- **Myth**: Better tooling fixes poor documentation.
  **Reality**: Tooling helps only when ownership, IA, review, and maintenance are understood.
- **Myth**: Migration is complete when content renders in the new platform.
  **Reality**: URLs, redirects, metadata, search, analytics, assets, ownership, and workflow also move.
- **Myth**: More features mean a better platform.
  **Reality**: Unused features add cost, training, and maintenance burden.
- **Myth**: Generated docs eliminate writing work.
  **Reality**: Generated references still need context, examples, validation, and user-oriented organization.

## Red Flags

- The decision starts with a favored vendor instead of requirements.
- Search is blamed when content structure, titles, metadata, or stale pages are the real problem.
- No one owns theme, build, redirects, search tuning, access, or incident response.
- The export path loses metadata, IDs, links, or reusable content.
- The pilot uses a tiny easy page rather than representative content.
- Migration omits redirect maps and old URL behavior.
- The tool requires author workflow changes that the team has not agreed to.

## Patterns

### Requirement Pattern

```text
Reader: Find versioned API and task docs from product UI and search
Author: Markdown source, PR review, preview links, link checks, reusable snippets
Content: Concepts, how-to guides, generated OpenAPI reference, release notes
Integration: GitHub, CI, analytics, product deep links, SSO for private docs
Maintenance: Redirects, owner metadata, quarterly freshness, broken-link reports
Migration: Preserve top 500 URLs and redirect removed pages
Portability: Human-readable Markdown export with metadata
Support: Platform owner for build, theme, search, auth, and deploy
```

### Decision Pattern

```text
Recommendation: Pilot docs-as-code static site before committing migration
Why: Best fit for PR review, generated API refs, portability, and CI checks
Risks: Writers need Git workflow training; search requires tuning
Process fixes first: Add owner metadata and stale-content review before migration
Pilot content: API overview, one how-to, generated reference, release notes
Success: Writers can publish through PR, old URLs redirect, search finds pilot tasks
```
