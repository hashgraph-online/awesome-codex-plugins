# Developer Docs Drafting Knowledge

Good developer docs give readers a clear path through a task or concept. Structure matters because many readers skim, search, copy commands, and jump between sections.

Source basis: *Docs for Developers*, Chapter 3, "Drafting documentation"; *The Product Is Docs*, Chapter 9, "Learning Objectives," Chapter 14, "Scenario-driven Information Development," and Chapter 25, "Writing SaaS Documentation."

## Drafting Components

| Component | Purpose |
|-----------|---------|
| Title | States the reader goal or content purpose |
| Opening | Sets context, audience, prerequisites, and outcome |
| Outline | Orders ideas before prose hardens |
| Headings | Let readers scan and recover their place |
| Paragraphs | Explain context and decisions in short units |
| Procedures | Guide actions in a numbered sequence |
| Lists | Group related items for scanning |
| Callouts | Surface exceptional warnings, cautions, or notes |
| Templates | Make repeated doc types faster and more consistent |

## Procedures

Procedures work best when they include:

- Starting state.
- Numbered steps.
- One main action per step.
- Required inputs or commands.
- Expected result or verification.
- Next step or recovery route.

## Skimming

Readers often scan before committing. Put important information early, use specific headings, break large blocks, and avoid hiding required details in notes or long paragraphs.

## Learning Objective Route

Draft from starting point to destination. The opening should tell readers whether they are in the right place, what they need before they start, and what they will be able to do or decide by the end. Keep extra background, variations, and implementation detail off the main route unless they affect the objective.

## Scenario Walkthroughs

A scenario walkthrough shows how a specific audience solves a realistic problem end to end. It should:

- Name the audience and problem early.
- Provide a concrete starting point and sample context.
- Walk one supported route to the result.
- Include only adjacent concepts that affect the scenario.
- Link to reference docs for options and variations.
- Validate the workflow with product, QA, support, or customer-facing teams.

Avoid turning a scenario into a feature tour, a marketing success story, or comprehensive product documentation.

## Self-Contained SaaS Topics

SaaS readers may arrive from search, support links, or release notes with little context. Help them orient quickly:

- State whether the topic is for administrators, end users, superusers, or internal operators.
- Explain what the service provider manages and what the customer controls.
- Put permissions and plan or browser requirements before the first action.
- Use consistent prerequisites, next steps, related links, and verification sections.
- Keep topics limited, but include enough context that readers do not have to chase a chain of pages to complete the task.

## Common Misconceptions

- **Myth**: Drafting starts with prose.
  **Reality**: A short outline often prevents missing steps and bad order.
- **Myth**: Callouts make important information more visible.
  **Reality**: Overused callouts train readers to ignore them.
- **Myth**: Longer explanations are always more helpful.
  **Reality**: Unfocused detail can block the task.
- **Myth**: A scenario should show every option the product supports.
  **Reality**: A scenario should guide one realistic path and link to reference material for variations.
- **Myth**: A self-contained topic must explain the whole product.
  **Reality**: It should provide enough context for the task while preserving a clear boundary.

## Rules And Checks

Use these rules when writing or rewriting developer documentation.

## Core Rules

1. **Use one primary goal per doc** - A page can support secondary needs, but one goal should control title, order, and depth.
2. **Make the title actionable or specific** - Prefer reader outcomes over internal feature names when possible.
3. **Outline before prose** - Check order, missing steps, prerequisites, and overload before drafting paragraphs.
4. **Put important information first** - Lead with outcome, prerequisites, warnings, or decision points that affect success.
5. **Write specific headings** - Headings should reveal what the section helps the reader do or understand.
6. **Keep paragraphs short** - Use paragraphs for context and reasoning, not for long procedural chains.
7. **Use numbered steps for ordered actions** - Use bullets for unordered options, requirements, or concepts.
8. **One action per step** - Split steps that ask the reader to do multiple independent things.
9. **End procedures with verification** - Tell readers how to know the action worked.
10. **Use callouts sparingly** - Reserve warnings and cautions for material that changes reader safety or success.
11. **Lead with user problem in scenarios** - Mention product features in the context of the problem they solve.
12. **Keep the route narrow** - Put prerequisites, required concepts, and supported steps on the page; link out for scenery.
13. **Label SaaS responsibility boundaries** - Make provider-managed, customer-managed, and permission-gated work explicit.
14. **Signpost jump-in readers** - Use specific headings, next steps, and related links so readers can recover context quickly.

## Quick Reference

| Element | Check |
|---------|-------|
| Title | Names the goal or precise topic |
| Opening | Gives outcome, audience, and prerequisites |
| Learning objective | Names observable reader outcome |
| Heading | Skimmable and specific |
| Step | Actionable, atomic, and ordered |
| List | Grouped by one clear principle |
| Callout | Exceptional and not overloaded |
| Ending | Gives verification or next step |

## Red Flags

- A reader must read several paragraphs before learning what they will accomplish.
- Required setup is hidden after the first command.
- A numbered step contains "and" between unrelated actions.
- Headings are generic, such as "Overview" repeated across many pages.
- The doc has many notes but no clear path.
- The scenario starts by listing product features instead of the user's problem.
- The topic assumes SaaS readers know whether they or the provider own an action.


## Examples And Patterns

Use these examples as revision patterns.

## Title Revision

Weak:

```text
Webhook Signatures
```

Better:

```text
Verify webhook signatures in Node.js
```

Why it works: The stronger title names the action, object, and implementation context.

## Procedure Step Revision

Weak:

```text
1. Install the package and set your API key, then run the server.
```

Better:

```text
1. Install the package:
   npm install @example/webhooks
2. Set `EXAMPLE_API_KEY` to your test API key.
3. Start the local server:
   npm run dev
```

Why it works: Each step has one action, and commands are easy to copy.

## Callout Decision

Weak:

```text
Note: You need Node.js 20 or later.
```

Better:

```text
Prerequisite: Node.js 20 or later.
```

Why it works: Required setup belongs in the main path, not a note.

## Skimmable Outline Pattern

```text
# Verify webhook signatures in Node.js
## Before you begin
## Install the SDK
## Configure the signing secret
## Verify incoming requests
## Test a valid webhook
## Troubleshoot failed verification
```

## Scenario Outline Pattern

```text
# Investigate failed logins and notify the security channel
## Who this is for
## Before you begin
## Review the failed-login signal
## Create the alert rule
## Send a test event
## Verify the notification
## Troubleshoot missing notifications
## Related alert options
```

## SaaS Responsibility Pattern

```text
This task is for workspace administrators. Your service provider manages alert processing and storage. You manage alert rules, notification targets, and test events. You need admin access and a supported browser before you begin.
```
