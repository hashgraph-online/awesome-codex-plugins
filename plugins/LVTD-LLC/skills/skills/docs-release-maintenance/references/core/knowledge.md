# Docs Release Maintenance Knowledge

Documentation has a lifecycle that should track product and code lifecycles: plan, review, publish, announce, measure, maintain, deprecate, and remove when appropriate.

Source basis: *Docs for Developers*, Chapter 7, "Publishing documentation," and Chapter 11, "Maintaining and deprecating documentation"; *The Product Is Docs*, Chapter 10, "Maintaining Existing Content," Chapter 25, "Writing SaaS Documentation," and Chapter 2, "Agile."

## Release Concepts

| Concept | Meaning |
|---------|---------|
| Publishing timeline | When docs draft, review, approval, publish, and announcement happen |
| Release alignment | Docs ship with or before the software users need to understand |
| Final approver | Person accountable for publication readiness |
| Delivery channel | Where users will find the docs |
| Announcement | How users learn new or changed docs exist |

## Maintenance Concepts

| Concept | Meaning |
|---------|---------|
| Owner | Person or team responsible for accuracy |
| Freshness check | Scheduled or triggered review of content accuracy |
| Link checker | Detects broken internal or external references |
| Linter | Enforces style, structure, or link rules mechanically |
| Generated reference | API or code-derived docs that still need human review |

## Maintenance Triggers

Maintenance can be reactive or proactive. Trigger a refresh when:

- Existing functionality evolves.
- User feedback reports errors, confusion, or missing content.
- Related products, deployment types, dependencies, or teams change.
- Audience, use cases, permissions, or terminology evolve.
- Style, localization, accessibility, or presentation standards change.
- Tooling or docs UI changes affect formatting, search, or navigation.
- Old topics show atrophy: patch buildup, wordiness, brittle structure, excessive links, missing links, stale screenshots, or unclear headings.

## Patch Versus Restructure

Assess scope before adding a quick paragraph or screenshot. A patch is reasonable when the change is local, the existing structure still works, and dependent pages are unaffected. Restructure when the change alters audience, workflow, use cases, conceptual framing, navigation, or dependencies across multiple docs.

Even a small product change can cascade through examples, warnings, screenshots, links, release notes, and related procedures. Use a dependency audit when the fact appears in more than one place or affects a larger workflow.

## SaaS Release And Operations Docs

SaaS release documentation has a different risk profile because many customers can experience the same upgrade or incident at once. Release notes should emphasize breaking changes, changed capabilities, browser or UI restrictions, and customer actions. Internal runbooks, release enablement docs, incident-response notes, and cross-functional process docs can be as important to the customer experience as public docs because they let support and operations teams deliver the managed service consistently.

SaaS docs should also identify what the provider manages, what the customer controls, and what operations or permissions remain the customer's responsibility.

## Deprecation And Deletion

Deprecation warns users that content, feature behavior, or product support is ending. Deletion removes content that is stale, harmful, unsupported, or replaced. Both need alternatives, timing, redirects, and user communication.

## Common Misconceptions

- **Myth**: Docs can be written after launch.
  **Reality**: Users need docs when the release affects them.
- **Myth**: Automation fixes maintenance.
  **Reality**: Automation amplifies whatever process exists, good or bad.
- **Myth**: Removing stale docs is just cleanup.
  **Reality**: Users may still depend on old URLs, migration paths, or warnings.
- **Myth**: A small feature change always needs only a small doc patch.
  **Reality**: The change may affect audience, workflows, screenshots, related docs, and terminology.
- **Myth**: Internal SaaS runbooks are separate from customer documentation quality.
  **Reality**: Internal operational docs shape incident response, upgrades, support speed, and customer trust.

## Rules And Checks

Use these rules when publishing, maintaining, deprecating, or deleting developer docs.

## Core Rules

1. **Plan docs with the code change** - Include docs in release planning, not as post-release cleanup.
2. **Analyze user impact** - Identify who is affected, what changes, and what action they must take.
3. **Require appropriate review** - Use peer, technical, security, legal, or product review based on risk.
4. **Test before publishing** - Check links, examples, generated refs, screenshots, and release-specific facts.
5. **Publish where users will look** - Delivery location should match user behavior and product entry points.
6. **Announce material changes** - Users need to know when docs explain new, changed, or breaking behavior.
7. **Assign ownership** - Critical docs need owners, metadata, or CODEOWNERS-style review.
8. **Automate known toil** - Use freshness reminders, link checks, linters, and generators where the process is clear.
9. **Deprecate before deleting when users need time** - Provide warning, alternatives, migration guide, and timeline.
10. **Redirect removed content** - Preserve user paths and search behavior where possible.
11. **Assess maintenance scope before patching** - Decide whether the update is local, multi-topic, or structural.
12. **Audit dependencies** - Search related topics, examples, screenshots, warnings, and links when a fact changes.
13. **Use learning objectives to judge stale topics** - If the topic no longer has a clear starting point, destination, or exit criteria, refresh the structure.
14. **Plan major refreshes** - For large rewrites, create a doc plan, isolate drafts when possible, and ship stable increments.
15. **Treat SaaS internal docs as service infrastructure** - Runbooks and release enablement need owners, review, testing, and version control.

## Release Checklist

| Area | Check |
|------|-------|
| Scope | Affected docs and user actions identified |
| Review | Technical and editorial reviewers assigned |
| Testing | Links, samples, screenshots, and generated refs checked |
| Approval | Final approver named |
| Delivery | Publish location and timing confirmed |
| Announcement | Release notes or comms include impact and action |
| Maintenance | Owner and update trigger recorded |
| Dependency audit | Related docs, links, examples, and screenshots checked |
| SaaS impact | Customer-controlled and provider-managed responsibilities clear |

## Red Flags

- Docs are blocked on facts no one owns.
- Release notes say what changed but not who is affected.
- A stale page is deleted without redirect or alternative.
- Generated API docs are trusted without usability review.
- Automation is proposed before handoffs and failure modes are understood.
- Content keeps accumulating patches without a structure review.
- A changed fact appears in multiple docs but only one page was updated.
- SaaS release docs omit fleet-wide upgrade risks or internal support readiness.


## Examples And Patterns

Use these examples as lifecycle planning patterns.

## Release Plan Row

```text
Change: Webhook signature verification becomes required for production endpoints
Affected docs: Webhook overview, Node.js verification guide, API errors, release notes
User impact: Existing integrations must verify signatures before July 15
Reviewers: API owner, security reviewer, developer docs
Tests: Run Node.js sample, check error response, verify dashboard label
Announcement: Release notes and migration guide
Owner after launch: Developer docs with API CODEOWNER review
```

## Freshness Metadata Pattern

```text
Owner: docs-platform
Source of truth: openapi/payments.yaml
Review trigger: API schema change, SDK major release, or quarterly freshness check
Last reviewed: 2026-06-25
```

## Maintenance Refresh Pattern

```text
Trigger: UI now exposes settings that were previously config-file only
Scope: Existing settings reference, setup guide, screenshots, permissions note, and troubleshooting page
Decision: Restructure instead of patch because audience and workflow changed
Dependency audit: Search for setting names, screenshots, old config path, and related warnings
Review: PM for workflow, engineer for behavior, support for common customer confusion
Release timing: Publish with feature release and add release-note link
```

## SaaS Runbook Pattern

```text
Runbook: Restore failed notification delivery for a workspace
Audience: Support and operations engineers
Prerequisites: Incident role, admin tool access, workspace ID, customer-impact check
Customer effect: Notifications may be delayed during replay
Steps: Diagnose queue state, replay failed events, verify delivery, update incident notes
Review trigger: Alerting component change, access policy change, incident involving this workflow
```

## Deprecation Plan Pattern

```text
Content: Legacy webhook signing guide
Reason: Replaced by current signature verification flow
User risk: Existing integrations may still use old signing header
Action: Add deprecation notice, link migration guide, announce in release notes
Deletion timing: After support window ends
Redirect: /docs/webhooks/legacy-signing -> /docs/webhooks/signatures
```
