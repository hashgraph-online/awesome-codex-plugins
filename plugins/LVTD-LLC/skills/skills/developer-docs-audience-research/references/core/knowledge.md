# Audience Research Knowledge

Developer-docs audience research prevents the team from writing from internal memory. The goal is to identify what readers are trying to do, what they already know, what blocks them, and what evidence supports those beliefs.

Source basis: *Docs for Developers*, Chapter 1, "Understanding your audience"; *The Product Is Docs*, Chapter 3, "Audience," Chapter 9, "Learning Objectives," and Chapter 25, "Writing SaaS Documentation."

## Key Concepts

### Curse Of Knowledge

The more familiar a team is with a product, the easier it is to omit details that new or occasional users need. Audience research makes those hidden assumptions visible.

### User Goals And Business Goals

Docs should connect user success with product or organizational outcomes. A doc may help a reader install a tool, evaluate an API, fix an error, migrate safely, or decide whether the product fits.

### Developer Characteristics

Useful audience sketches include:

- Role and responsibility.
- Programming languages and frameworks.
- Operating system, tools, and environment.
- Product familiarity.
- Domain expertise.
- Time pressure, risk tolerance, and support access.

### User Questions

Collect questions in practical buckets:

- What is this product and should I use it?
- What do I need before I begin?
- How do I complete this task?
- What API, CLI, config, or object do I use?
- What went wrong and how do I recover?
- What changes between versions or plans?

### Research Artifacts

| Artifact | Use It For |
|----------|------------|
| Audience definition | Describing a reusable audience type by skills, goals, constraints, and scope |
| Persona | Summarizing a recurring user type |
| User story | Expressing a goal as "As a..., I want..., so..." |
| Journey map | Mapping steps, emotions, blockers, and touchpoints |
| Friction log | Capturing what slows or blocks a real product walk-through |

### Audience Definition Versus Persona

An audience definition describes a class of readers and the knowledge, responsibilities, goals, and boundaries that shape their documentation needs. A persona is a concrete representative of one audience type. Use personas to reason about a specific user context; use audience definitions to train writers, set topic scope, choose learning objectives, and help readers recognize whether content is for them.

### Learning Objectives

A learning objective states what the reader should be able to know, decide, or do after using the documentation. Use objectives to connect real-world user goals to topic scope.

| Objective Type | Reader Outcome |
|----------------|----------------|
| Awareness | The reader can identify, describe, or paraphrase a concept, feature, option, or limitation |
| Comprehension | The reader can compare options, explain tradeoffs, or choose the right approach for a scenario |
| Applicable skill | The reader can complete and repeat a task successfully |

Strong objectives have a starting point, destination, and exit criteria. They use observable verbs such as identify, choose, configure, verify, migrate, diagnose, or explain. Avoid objectives that only say "understand" unless you also state how the reader will demonstrate that understanding.

### SaaS Audience Boundaries

SaaS docs often need sharper audience labels because users may be administrators, end users, superusers, support engineers, or internal operators. State what the service provider manages, what the customer can control, and what permissions the reader needs before they start.

## Common Misconceptions

- **Myth**: Experienced developers need less documentation.
  **Reality**: Experienced developers may need less explanation, but they still need accurate entry points, constraints, examples, and reference details.
- **Myth**: Internal stakeholders can define user needs alone.
  **Reality**: Stakeholders can supply hypotheses; users or user evidence validate them.
- **Myth**: A persona is complete because it has a job title.
  **Reality**: The useful part is the task, context, tools, constraints, and success criteria.
- **Myth**: A learning objective is the same as a user goal.
  **Reality**: A user goal is the real-world outcome; a learning objective names the knowledge, decision, or skill the docs must build to support that outcome.

## Rules And Checks

Use these rules when defining or validating the audience for developer documentation.

## Core Rules

1. **Start with the job, not the demographic** - Define what the reader is trying to accomplish before describing who they are.
2. **Write down the goal** - Preserve the target user goal so planning, drafting, and measurement can refer back to it.
3. **Separate users from stakeholders** - Product, engineering, and support goals matter, but they are not substitutes for user needs.
4. **Prioritize the primary audience** - A doc that tries to serve every reader usually serves none well.
5. **Document assumptions** - Mark assumptions about skill, tools, permissions, prior knowledge, or environment.
6. **Validate with evidence** - Use user conversations, support tickets, search logs, analytics, forum posts, or friction logs.
7. **Focus on needs before wants** - Users may request features or formats, but the underlying need should drive the doc.
8. **Capture blockers** - Setup failures, unclear prerequisites, missing permissions, and ambiguous errors are audience data.
9. **Use audience definitions before personas** - Define the reusable reader type before inventing a representative individual.
10. **Set one primary learning objective per topic** - Let the objective decide what belongs in the topic and what should be linked elsewhere.
11. **Name the starting point** - State prerequisite knowledge, access, environment, and context so readers can tell whether the topic fits them.
12. **Make exit criteria observable** - Readers should know how to tell that they can apply the concept, make the decision, or complete the task.

## Quick Checks

| Question | Good Answer |
|----------|-------------|
| Who is the primary reader? | A role plus task context, not just "developer" |
| What must they accomplish? | A concrete outcome |
| What do they already know? | Explicit assumptions with evidence or caveats |
| What will stop them? | Known setup, concept, permission, or product blockers |
| What should they know or do after reading? | An observable learning objective |
| Where do they start? | Prerequisites, prior knowledge, access, and context |
| How will this be validated? | A concrete data source or user contact |

## Red Flags

- The audience is defined only by seniority or job title.
- The doc plan starts with internal feature order.
- The team cannot name the reader's first successful outcome.
- No one has watched or simulated a first-time user path.
- The doc assumes tools, access, or context that are never stated.
- The objective is "understand X" with no observable result.
- SaaS docs do not distinguish customer-controlled work from provider-managed work.


## Examples And Patterns

Use these examples as compact patterns, not as fixed templates.

## Weak Audience Definition

> Audience: developers using the API.

Problems:

- No task or success outcome.
- No skill level or environment.
- No constraints, blockers, or evidence.

## Better Audience Definition

> Primary audience: backend engineers adding hosted payments to an existing Node.js checkout. They know HTTP APIs and npm, but may not know our auth model, webhook signing, or test-mode dashboard. Their first success is a local payment flow that creates a test charge and handles the success webhook.

Why it works:

- Names the role, task, stack, prior knowledge, missing concepts, and first outcome.

## User Story Pattern

```text
As a backend engineer integrating hosted payments,
I want a minimal checkout flow with webhook verification,
so that I can prove the integration works before touching production.
```

## Learning Objective Pattern

```text
Audience: SaaS workspace admin with dashboard access but no command-line access
User goal: Route failed-login alerts to the incident channel
Starting point: Admin can create alert rules and knows the target channel
Learning objective: After reading, the admin can choose the right alert trigger, configure the rule, and verify that a test event reaches the channel
Exit criteria: Rule exists, test event fires, notification appears in the expected channel
Scope boundary: Do not explain internal alert-processing architecture unless it changes the admin's decision
```

## Friction Log Entry Pattern

```text
Step: Create test API key
Expected: Key is visible in dashboard after selecting test mode
Observed: Dashboard defaults to live mode and the docs do not mention the toggle
Impact: User may copy a live key or think the setup failed
Doc fix: Add prerequisite step and screenshot annotation near setup instructions
```
