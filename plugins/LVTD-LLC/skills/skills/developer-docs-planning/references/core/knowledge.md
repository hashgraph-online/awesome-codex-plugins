# Documentation Planning Knowledge

Developer documentation plans connect user goals to the right content types, scope, sequence, owners, and review path.

Source basis: *Docs for Developers*, Chapter 2, "Planning your documentation"; *The Product Is Docs*, Chapter 2, "Agile," Chapter 6, "Documentation Decisions," Chapter 13, "Research for Technical Writers," Chapter 14, "Scenario-driven Information Development," and Chapter 22, "Working with Product Management."

## Content Types

| Type | Best For |
|------|----------|
| Code comments | Explaining local implementation decisions, tradeoffs, and non-obvious code behavior |
| README | Project overview, setup, contribution basics, links to deeper docs |
| Getting started | First successful experience and product evaluation |
| Conceptual docs | Explaining a model, domain concept, architecture, or why something works |
| Tutorial | Guided learning path toward a known result |
| How-to guide | Completing a specific real-world task |
| API reference | Accurate details for endpoints, methods, parameters, types, status codes, and errors |
| Glossary | Consistent definitions for product or domain terms |
| Troubleshooting | Recognizing symptoms and recovering from known failures |
| Changelog | What changed and when |
| Release notes | What changed, why it matters, who is affected, and what action is required |

## Documentation Plan

A useful plan answers:

- Who is the reader?
- What goal does the doc support?
- Which content type fits the goal?
- What source of truth keeps it accurate?
- Who owns review and approval?
- What blocks publication?
- How will the team know the doc worked?

## Content Outline

Use an outline to expose missing prerequisites, overloaded pages, bad sequencing, and unclear ownership before drafting.

## Documentation Decisions

Some planning work is a decision before it is an outline. A useful documentation decision record states:

- The decision to make.
- The audience and user goal affected.
- Product facts, release timing, and known constraints.
- Available resources, existing docs, support signals, usage data, and feedback.
- Options considered and why one option is recommended.
- Assumptions that need review.
- How the decision will be communicated and revisited.

Make partial-information decisions explicit. Waiting for perfect information can block release work, but hiding assumptions creates brittle docs.

## Feature Research

Research should uncover fact and meaning, not just implementation detail. Start with background reading, then verify primary facts through the product, code, issue tracker, design notes, SMEs, product management, QA, support, and customers when possible.

Good research answers:

- What user problem or decision does this feature affect?
- What defaults, limits, permissions, performance costs, security implications, and data risks matter?
- What can be verified hands-on?
- Which facts need a named source of truth?
- Which implementation details have user-facing consequences?
- Which oddities should become product defects instead of documentation burden?

## Scenario-Driven Planning

A scenario is an end-to-end, real-world use case that shows how a reader solves a problem with the product. It is not a basic tutorial, a marketing case study, or comprehensive product coverage.

Use scenarios when conceptual docs and procedures are accurate but still do not show how the product fits a real job. Plan the scenario around a specific audience, starting point, goal, realistic data, supported workflow, and validation route.

## Agile Planning Hooks

Documentation is part of the product experience and should be visible in the same planning system as product work. For scrum-aligned work, plan docs tasks, review, QA, and user feedback as part of the feature lifecycle. For docs work that does not fit a single sprint, such as learning objectives, maintenance, troubleshooting, or cross-feature tutorials, track the information needs in Agile tools while running the documentation project at the cadence it actually requires.

## Common Misconceptions

- **Myth**: A README can replace all developer docs.
  **Reality**: A README can route, summarize, and bootstrap; deeper tasks often need separate docs.
- **Myth**: Reference docs teach new users.
  **Reality**: Reference docs answer specific lookup questions; onboarding usually needs guided context.
- **Myth**: More content types always mean better docs.
  **Reality**: Each added doc increases maintenance load and should map to a real user task.
- **Myth**: A feature specification tells writers everything they need.
  **Reality**: Specs often explain implementation; docs planning still needs user goals, consequences, constraints, and validation.
- **Myth**: Agile means docs should always finish in the same sprint as code.
  **Reality**: Docs should be visible in Agile planning, but some information development spans multiple sprints or teams.

## Rules And Checks

Use these rules when deciding what developer documentation to create.

## Core Rules

1. **Choose by user task** - Match content type to what the reader is trying to do.
2. **Use one primary purpose per doc** - Split or route when a doc tries to teach, reference, troubleshoot, and announce at once.
3. **Plan source of truth early** - API fields, generated references, release notes, and code samples need owners and authoritative sources.
4. **Make prerequisites explicit** - Setup, access, version, plan, permission, and environment requirements belong in the plan.
5. **Separate learning from lookup** - Tutorials and concepts teach; references and changelogs support precise lookup.
6. **Keep plans lightweight** - Use enough structure to reveal gaps, dependencies, and owners.
7. **Flag product complexity** - If the doc outline requires too many caveats or branches, surface product or UX complexity rather than hiding it.
8. **Plan maintenance** - Every doc needs an owner, review signal, or source that keeps it accurate.
9. **State the decision before the plan** - When the team is uncertain, write the decision question before choosing content.
10. **Research user consequences** - Ask what the reader can do, decide, risk, or misunderstand, not only how the feature is implemented.
11. **Try the product when feasible** - Hands-on use reveals missing prerequisites, inconsistent UI paths, and errors that interviews miss.
12. **Use scenarios for real problems** - Reframe feature workflows into user problems and validate that the scenario is supported.
13. **Make docs work visible in Agile tools** - Track docs tasks, review needs, and blockers where the scrum team already plans.

## Content-Type Selection

| Reader Need | Prefer |
|-------------|--------|
| "Can I use this?" | Overview or getting started |
| "How does this concept work?" | Conceptual doc |
| "Teach me the path once" | Tutorial |
| "Help me complete this task" | How-to guide |
| "What does this parameter mean?" | Reference |
| "This failed" | Troubleshooting |
| "What changed?" | Changelog or release notes |

## Red Flags

- The plan follows internal component order rather than user workflow.
- No one can say which doc answers the first user question.
- Reference details will be copied manually from code or schemas.
- Release notes omit impact or action required.
- Troubleshooting docs become a sprawling FAQ without symptoms or fixes.
- A doc decision has no named audience, evidence, or owner.
- Research questions ask only "how does it work?" and never "why does the user care?"
- Scenario docs promise a use case that the product does not support cleanly.
- Docs are excluded from release definition of done, review timing, or sprint planning.


## Examples And Patterns

Use these examples to shape plans and content-type decisions.

## Content-Type Decision

Scenario: A team is launching webhook signing.

| User Need | Recommended Doc | Why |
|-----------|-----------------|-----|
| Understand why signatures exist | Conceptual doc | Explains trust model and threat without code-first distraction |
| Verify signatures in Node.js | How-to guide | User has a specific implementation task |
| Look up header names and errors | API/reference section | Precise lookup details need accuracy |
| Recover from failed verification | Troubleshooting page | Symptom and fix path differ from setup |
| Announce breaking change | Release notes | Users need impact and required action |

## Plan Row Pattern

```text
Doc: Verify webhook signatures in Node.js
Type: How-to guide
Audience: Backend engineer integrating hosted payments
Goal: Verify signature locally and reject invalid payloads
Source of truth: SDK example test + security owner review
Owner: Developer docs
Reviewers: SDK maintainer, security engineer
Blocks: Final header name and error code
Success signal: Fewer support tickets about failed webhook verification
```

## Documentation Decision Pattern

```text
Decision: Create a separate migration guide instead of adding a section to the release notes
Audience: Admins upgrading production workspaces
Evidence: Release changes authentication behavior and support has open upgrade questions
Options: Release-note section, new migration guide, or inline updates across setup docs
Recommendation: New migration guide with release-note link and affected-doc updates
Assumptions: Final error messages and support window need confirmation
Communication: Share plan with PM, support, QA, and docs owner before drafting
```

## Feature Research Question Set

| Area | Ask |
|------|-----|
| User goal | What task, decision, or problem does this feature support? |
| Defaults and limits | What values are default, minimum, maximum, or surprising? |
| Permissions | Who can do this and what access do they need? |
| Risk | Can this affect security, performance, billing, data integrity, or availability? |
| Verification | How can a writer or reviewer prove the documented result? |
| Product fit | Should an odd workflow be fixed in-product instead of documented? |

## Scenario Plan Pattern

```text
Scenario: Investigate failed logins and notify the security channel
Audience: SaaS workspace admin with alert-management permission
Problem: Team needs a repeatable path from signal to notification
Starting point: Login data exists and admin has channel webhook URL
Path: Choose event source -> create search -> configure alert -> send test event -> verify notification
Validation: QA confirms workflow, support confirms common customer need, PM confirms feature fit
Scope boundary: Link to reference for all alert options instead of listing every variation
```

## Split Decision

Weak plan: One long "Webhooks" page with overview, setup, API fields, errors, migration notes, and all language samples.

Better plan:

- Overview: what webhooks are and when to use them.
- How-to guides: verify signatures by supported language.
- Reference: event schema and delivery behavior.
- Troubleshooting: common delivery and verification failures.
- Release notes: behavior changes and required user action.
