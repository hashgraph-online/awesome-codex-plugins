# Docs Feedback Knowledge

Documentation feedback comes from many channels and must be converted into work deliberately. A good triage process protects attention while preserving strong user signals.

Source basis: *Docs for Developers*, Chapter 8, "Gathering and integrating feedback"; *The Product Is Docs*, Chapter 5, "Customer Feedback and Community," Chapter 18, "Working with Customer Support," and Chapter 20, "Working with the Field."

## Feedback Channels

| Channel | Use |
|---------|-----|
| Page-level feedback | Capture specific page problems close to the user's experience |
| Support issues | Detect repeated confusion, missing prerequisites, or troubleshooting gaps |
| Community forums | Identify common questions, user workarounds, terminology, and undocumented scenarios |
| Field and customer-facing teams | Surface sales, professional services, education, and success patterns |
| Sentiment signals | Monitor broad satisfaction but avoid over-interpreting without context |
| Surveys | Ask targeted questions and establish baselines |
| User councils | Learn from strategic users or early adopters |
| Issue trackers | Route actionable doc bugs through normal work systems |

## Triage Dimensions

| Dimension | Question |
|-----------|----------|
| Validity | Is the feedback real, current, and relevant? |
| Ownership | Is this a docs issue, product issue, support issue, or policy issue? |
| Actionability | Can someone reproduce, scope, and fix it? |
| Importance | How many users are affected and how severe is the impact? |
| Follow-up | Who should hear back, and what evidence is still needed? |

## Feedback Response Loop

A feedback channel creates an expectation of action. Even when the final fix requires research, acknowledge useful feedback, explain the next step, and keep the reporter or source team informed when the issue changes. Response timing should be explicit in the team's process; unattended feedback erodes trust.

## Frustrated Customers

Negative feedback is usually about a blocked task, missing information, bad organization, wrong assumptions, or a product limitation. Treat frustration as signal without taking it personally.

Respond by:

- Acknowledging the user's frustration without overpromising.
- Asking for the missing context needed to help.
- Offering the next path when you can.
- Explaining whether the issue needs docs, product, support, or community routing.
- Stepping back or escalating when the exchange is abusive, sensitive, or account-specific.

## Community And Pattern Mining

Community forums, user groups, field conversations, support cases, and education teams reveal repeated questions that page feedback may miss. Convert patterns into docs work when users repeatedly ask the same question, use unsupported workarounds, fail at the same setup step, or describe the product with different terminology than the docs use.

## Common Misconceptions

- **Myth**: Every feedback item should become a docs task.
  **Reality**: Some feedback belongs to product, support, or no action.
- **Myth**: Negative sentiment alone identifies the fix.
  **Reality**: Sentiment needs context, affected page, user goal, and cause.
- **Myth**: Surveys are easy because they are short.
  **Reality**: Bad survey design creates misleading data.
- **Myth**: Angry feedback is unusable.
  **Reality**: The tone may be hard to read, but the underlying blocker can still be valid and urgent.
- **Myth**: Community questions are separate from docs work.
  **Reality**: Repeated community questions often point to missing docs, weak findability, or mismatched terminology.

## Rules And Checks

Use these rules when collecting or triaging developer documentation feedback.

## Core Rules

1. **Capture page and context** - Feedback should preserve URL, section, user goal, and what was wrong or missing.
2. **Validate before fixing** - Check whether the issue is current, reproducible, and relevant.
3. **Route non-doc issues** - Product bugs, pricing confusion, permissions, or policy problems need the right owner.
4. **Make feedback actionable** - Ask for expected behavior, actual behavior, reproduction steps, and possible fix when useful.
5. **Deduplicate** - Search existing issues before creating new work.
6. **Prioritize by user impact** - Blocked users, broken setup, and wrong technical details outrank polish.
7. **Separate trend from anecdote** - One report may be urgent, but patterns change roadmap priority.
8. **Follow up** - Respond when users provided useful detail or when a fix ships.
9. **Acknowledge useful feedback quickly** - Tell the reporter what will happen next even if research is required.
10. **Use frustration as diagnosis** - Look for blocked tasks, missing prerequisites, mental-model mismatch, or product defects.
11. **Route environment-specific questions carefully** - Send account, production, or sensitive problems to support while preserving docs implications.
12. **Harvest patterns from customer-facing teams** - Support, field, education, and community teams can validate whether a docs issue is isolated or systemic.
13. **Protect privacy and confidential information** - Do not expose customer details, release commitments, competitive information, or private community data in public docs work.

## Priority Rubric

| Priority | Use When |
|----------|----------|
| P0 | Docs cause serious harm, outage response confusion, security risk, or widespread blocking failure |
| P1 | Many users are blocked, setup fails, or docs are technically wrong for important workflows |
| P2 | Confusion affects a meaningful segment but has workaround |
| P3 | Minor clarity, formatting, typo, or low-impact improvement |

## Red Flags

- Feedback has no page URL, product version, or user goal.
- The proposed fix is a product request disguised as a docs bug.
- A stale issue stays open because no one decided whether it is valid.
- The triage process ignores support-ticket patterns.
- Users never hear back after reporting high-quality issues.
- The team collects public feedback but has no response owner.
- Repeated community answers never become docs or findability fixes.
- A frustrated user needs support escalation, but docs keeps the conversation in a feedback thread.


## Examples And Patterns

Use these examples as templates for triage and issue creation.

## Page Feedback Issue Template

```text
Title: [Doc title] - [short problem]
Doc URL:
Section:
User goal:
What is wrong or missing:
Expected information:
Actual information:
Possible fix:
Product/version/context:
Reporter contact or channel:
```

## Triage Decision

Feedback:

```text
The webhook verification guide does not work. I keep getting "invalid signature."
```

Triage:

- Validity: Needs reproduction.
- Ownership: Likely docs or SDK sample.
- Actionability: Ask for language, SDK version, copied command, and whether the raw request body was modified.
- Priority: P1 if multiple support cases show the same failure; otherwise P2 until reproduced.
- Next action: Reproduce with published sample and compare error output.

## Frustrated Feedback Response Pattern

```text
Thanks for reporting this. I can see how the current topic blocks the setup path because it does not state which permission is required. I am going to verify the permission with the product owner, update the prerequisite section, and link the support article for accounts that still cannot access the setting. If you can share the product version and the step where access failed, I can confirm the fix against your path.
```

## Pattern Mining Example

```text
Signal: Same webhook signature error appears in page feedback, three support tickets, and two forum threads
Likely issue: Setup guide omits raw-body requirement and troubleshooting page is hard to find
Docs action: Add prerequisite, add troubleshooting symptom, improve related links
Product/support route: Ask SDK owner whether sample can detect modified request bodies
Follow-up: Reply to reporters and forum thread after fix ships
```

## Non-Doc Routing

Feedback:

```text
The dashboard does not let me rotate signing secrets.
```

Decision:

- Route to product or support if the feature is missing or broken.
- Create a docs task only if docs claim the feature exists or fail to explain the current limitation.
