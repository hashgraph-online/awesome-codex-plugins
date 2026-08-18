# Documentation Quality Metrics Knowledge

Documentation quality is whether the doc fulfills its purpose for its readers. Measurement should start with the decision the team needs to make.

Source basis: *Docs for Developers*, Chapter 9, "Measuring documentation quality"; *The Product Is Docs*, Chapter 11, "Measuring Success."

## Measurement Purpose

Measurement reduces uncertainty so the team can make a decision. Counting only becomes useful measurement when the result can change what the team does. Before collecting data, state the decision, the uncertainty, the amount of precision needed, and the action the team will take for different outcomes.

Small samples, estimates, and simple repeated experiments can be enough when they meaningfully reduce uncertainty. Do not spend more effort increasing precision than the decision deserves.

## Functional Quality

| Dimension | Meaning |
|-----------|---------|
| Accessible | More users can understand and navigate the content |
| Purposeful | The doc has a clear reader goal and supports it |
| Findable | Users can locate the doc and related next steps |
| Accurate | Technical details, examples, and links are correct and current |
| Complete | The doc includes prerequisites, task details, expected outcomes, and next steps for its scope |

## Structural Quality

| Dimension | Meaning |
|-----------|---------|
| Clear | The reader can follow concepts, steps, and outcomes |
| Concise | The doc avoids unnecessary material |
| Consistent | Terms, patterns, formats, and voice are stable |

## Metric Sources

- Web analytics: visitors, views, paths, search terms, exits, time on page.
- Docs behavior: searches with no result, link clicks, feedback, page ratings.
- Support data: ticket volume, categories, repeated questions.
- Technical checks: link checks, sample tests, API schema drift, lint results.
- User outcomes: Time to Hello World, onboarding completion, task success.
- Qualitative inputs: interviews, usability tests, friction logs, comments.

## Success Criteria

Success is contextual. Decide what the organization and docs team are optimizing for before choosing metrics:

- Customer productivity or time to useful outcome.
- Reduced support burden or future support-cost avoidance.
- Customer satisfaction or perceived documentation value.
- Content quality, freshness, reuse, localization efficiency, or platform ROI.
- Team productivity, collaboration, or process improvement.
- Findability and ability to move from search to answer.

Treat support case deflection carefully because it measures an absence and usually depends on inference. Pair it with search success, support trends, customer surveys, and qualitative evidence instead of reporting it as a precise standalone number.

## Common Misconceptions

- **Myth**: A single metric can prove doc quality.
  **Reality**: Use clusters of metrics plus qualitative evidence.
- **Myth**: High traffic means a doc is good.
  **Reality**: It may indicate importance, confusion, or discoverability.
- **Myth**: Structural polish fixes functional failure.
  **Reality**: A concise inaccurate doc is still poor documentation.
- **Myth**: Counting is the same as measurement.
  **Reality**: Counts need a decision, context, and possible action before they are meaningful.
- **Myth**: More precise data is always better.
  **Reality**: Extra precision is waste if it does not reduce uncertainty enough to change a decision.
- **Myth**: Support deflection can be measured exactly.
  **Reality**: It is often inferred from several signals and should be reported with caveats.

## Rules And Checks

Use these rules when auditing docs or designing measurement plans.

## Core Rules

1. **Start with the decision** - Ask what the team will change based on the measurement.
2. **Tie metrics to goals** - Map organization goals, user goals, and doc goals separately.
3. **Audit functional quality first** - Accessibility, purpose, findability, accuracy, and completeness outrank prose polish.
4. **Use metric clusters** - Pair traffic with search, feedback, support, task success, or technical checks.
5. **Create a baseline** - Current values matter more than isolated numbers.
6. **Add context** - Segment by audience, release, doc type, source, or product area.
7. **Mix qualitative and quantitative data** - Numbers show where to look; user evidence helps explain why.
8. **Beware vanity metrics** - Pageviews, time on page, and ratings can mislead without intent.
9. **Measure maintainability** - Link health, sample test status, freshness, and owner review are quality signals.
10. **Measure to reduce uncertainty** - Define what the team needs to know before acting.
11. **Use small experiments when enough** - A quick sample or before/after check can guide process changes.
12. **Pair counts with action** - Every metric should have an owner and a likely response.
13. **Report inference honestly** - For deflection, satisfaction, and productivity, name assumptions and confidence limits.

## Quick Metric Map

| Question | Possible Signals |
|----------|------------------|
| Can users find the doc? | Internal search, navigation paths, search terms, backlinks |
| Does the doc help users start? | Time to Hello World, setup completion, support tickets |
| Is the doc accurate? | Sample tests, link checks, API drift, reviewer status |
| Is the doc understandable? | Feedback themes, usability tests, readability checks |
| Does docs work reduce support load? | Ticket trends, deflection patterns, repeated issue volume |
| Is a process change helping? | Before/after samples, writer survey range, cycle time, review completion |
| Where should remediation start? | Dissatisfaction signals correlated with traffic, support impact, or task criticality |

## Red Flags

- A dashboard reports metrics with no decision owner.
- Pageviews are treated as success for troubleshooting docs.
- The team optimizes readability score while examples fail.
- Metrics ignore docs that are low traffic but high risk.
- No baseline exists before a docs change.
- The team measures what is easy to count but cannot name the decision.
- Dashboard numbers go up or down and no one knows what action follows.
- A support-deflection number is reported without assumptions or uncertainty.


## Examples And Patterns

Use these examples as metric-plan patterns.

## Metric Cluster

Question: Are new users succeeding with the quickstart?

Useful signals:

- Time to Hello World.
- Completion rate for setup steps.
- Search terms from the quickstart page.
- Support tickets tagged setup or auth.
- Page feedback about missing prerequisites.
- Test status for commands and code samples.

Avoid relying only on:

- Pageviews.
- Average time on page.
- A single thumbs-up/thumbs-down score.

## Decision-First Measurement Pattern

```text
Decision: Should the team spend two weeks restructuring onboarding docs?
Uncertainty: Are new users failing because they cannot find prerequisites or because setup commands are wrong?
Low-cost measures: Review five recent support cases, sample failed searches, inspect page feedback, run the quickstart once
Action threshold: If evidence clusters around missing prerequisites, update onboarding IA and quickstart prerequisites first
Caveat: This will not prove full support deflection, but it can reduce uncertainty enough to choose the next work
```

## Quality Finding Pattern

```text
Finding: The quickstart is purposeful but incomplete.
Evidence: It states a clear outcome, but omits required dashboard access and expected output after the first API call.
Impact: New users can follow the steps but cannot verify success.
Fix: Add prerequisites and expected response body; test the sample before release.
Metric to watch: Setup-related support tickets and quickstart feedback for "missing prerequisite."
```

## Goal Mapping

| Goal Type | Example Goal | Possible Measurement |
|-----------|--------------|----------------------|
| Organization | Reduce onboarding support load | Setup-ticket trend |
| User | Create first test charge | Time to Hello World |
| Doc | Make auth prerequisites clear | Feedback themes and checklist audit |
