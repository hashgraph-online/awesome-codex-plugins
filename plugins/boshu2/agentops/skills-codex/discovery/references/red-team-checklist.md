# Red Team Checklist for Ideation

Use these questions to stress-test approaches during brainstorm Phase 3b.

## Structural Questions

1. **What breaks first?** — Identify the weakest link under stress (load, concurrency, edge cases, adversarial input). If you can't name a specific failure mode, the approach is under-specified.

2. **What's the hidden cost?** — Every approach has costs beyond implementation time: maintenance burden, cognitive load for new contributors, infrastructure requirements, monitoring needs, migration complexity.

3. **What assumption is wrong?** — List the unstated assumptions. Which one, if false, invalidates the approach? Common false assumptions: "the API won't change", "data fits in memory", "users will read the docs", "this library is maintained".

4. **Who disagrees?** — Steel-man the opposing view. A performance engineer and a UX designer will critique the same approach differently. What does the most skeptical qualified person say?

## Scoring

| Red Team Failures | Classification |
|-------------------|---------------|
| 0 | Strong approach |
| 1 | Viable with mitigation |
| 2+ | HIGH RISK — needs rethinking or mitigation plan |

## When All Approaches Are HIGH RISK

If every approach fails 2+ questions, the problem statement may be wrong. Consider:
- Is the goal too broad? Split it.
- Is there a constraint you haven't stated? Surface it.
- Generate a hybrid approach that addresses the specific red team failures.

## Common False Assumptions

| Assumption | Why It Fails |
|-----------|-------------|
| "The API won't change" | External APIs change without notice; pin versions and add contract tests |
| "Data fits in memory" | Works in dev, breaks in prod when dataset grows 10x |
| "Users will read the docs" | They won't; make the happy path obvious and errors informative |
| "This library is maintained" | Check commit history; many popular libraries are effectively abandoned |
| "We can refactor later" | Technical debt compounds; later never comes without explicit scheduling |
| "Performance doesn't matter yet" | Architecture decisions that ignore performance are expensive to fix |
| "The team will adopt it" | New tools need champions, training, and visible wins to gain traction |
