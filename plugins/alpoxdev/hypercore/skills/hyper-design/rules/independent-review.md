# Independent Review

Read before the review phase of `design`, `restyle`, `mockup`, `audit`, and `verify`. This file owns who reviews, what the reviewer receives, what a finding must cite, and how findings are answered.

## 1. Why the Builder Does Not Grade Alone

A model judging its own output favors text and images that look like what it would have produced, which is exactly the median this skill is trying to avoid. Unstructured screenshot critique by a model also falls short of human reviewers, and improves when each comment is tied to a region of the screen. So the review is separated from the build, starved of the builder's reasoning, and held to evidence.

## 2. Reviewer

| Capability | Review mode | Report value |
|---|---|---|
| A subagent or a second session can be started | Fresh reviewer with only the inputs in §3 | `subagent` |
| No subagent capability | The same agent, after finishing the build, reads only the inputs in §3 in a new pass and answers each question in §4 before looking at its own notes | `self (degraded)` |
| The user reviews | The user's comments are findings; record them verbatim | `user` |

Never give the reviewer the builder's rationale, the `brief.md` reasoning sections, or a list of what the builder believes is good.

## 3. Reviewer Inputs

- the one-sentence brief, the visitor mode, and the Design Read line with its dials (not the rest of `brief.md`)
- rendered captures at the checked widths and states, or, without rendering, the changed source paths
- `rules/craft-floor.md` §9 and the "You see / You do" table in §5 below
- for mockups, the failure modes in `references/mockup-craft.md` §2

## 4. Questions, in Order

1. Could this be any product in its category? Name what is specific to this product, or report that nothing is.
2. Where does the eye land first, second, third, and is that the order the task needs?
3. Which element has no job: a decoration, a container, a label, a motion?
4. Which values break the system: a one-off color, size, space, radius, or duration?
5. Which states are missing or look unfinished?
6. Which floor items fail, with the measured value?
7. Does the result match its declared dials (ENERGY, RHYTHM, MOTION), and is there one focal point, one accent, and one identity motif?
8. If the logo and product name were swapped out, would anything here still belong to this product?

Fix the largest visible failure first, then re-check from the top.

## 5. You See / You Do

| You see | You do |
|---|---|
| Every section is the same card grid | Give each section its job and the layout that job needs |
| An eyebrow label over every heading | Keep labels that carry state or sequence; remove the rest |
| Gray text that is hard to read | Raise contrast to the floor; express hierarchy with size and weight |
| Equal weight everywhere | Make one thing primary per view |
| A gradient, glow, or orb with no job | Remove it, or tie it to the brand or a state |
| Motion on every element | Keep feedback motion and one authored moment; remove the rest |
| A happy path only | Design loading, empty, and error |
| Placeholder proof (logos, metrics, testimonials) | Remove it, or mark it as placeholder |
| A window shrunk into a card with even margins (mockup) | Crop it and let it run off an edge |

## 6. Finding Format

Each review finding cites:

- the region (capture file and area, or file and line)
- the rule ID from `references/anti-pattern-catalog.md` or the floor item from `rules/craft-floor.md`
- the measured or observed value
- a severity from `rules/evidence-and-severity.md`

A finding without a region and a rule is a comment, not a finding; record it but do not act on it. Present critique findings as a `| Before | After | Why |` table in the report.

## 7. Answering Findings

- `high` (P0/P1) findings are fixed within the correction budget, or answered with a reason the user can check.
- A finding that conflicts with the brief or a documented brand decision is answered with that evidence, not obeyed.
- A reviewer reply is evidence. "Looks great, ship it" is not a pass; only the checklist and the cited findings decide.
- A rule satisfied by deleting function (removing all motion, all states, a real badge) is a degenerate fix; restore what carried meaning.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| LLM evaluators score low-perplexity outputs higher than humans do | <https://arxiv.org/abs/2410.21819> (2024-10-29) |
| Self-recognition correlates with self-preference in LLM evaluators | <https://arxiv.org/abs/2404.13076> (2024-04-15) |
| LLM UI critique falls short of experienced designers; few-shot and visual prompting improve it | <https://arxiv.org/abs/2407.08850> (2024-07-11) |
| Comments tied to screen regions halve the gap to human critique on one metric | <https://arxiv.org/abs/2412.16829> (2024-12-22) |
| A fresh-eye reviewer gets frames and the checklist, never the builder's plan; fix the largest visible failure first | <https://github.com/benjitaylor/skills> (`stageshow` folder, commit `299140f`) (MIT) |
| A detector score rose while hand ratings fell; a motion rule produced motion collapse | <https://solodesign.cc/blog/ai-design-slop-the-tells/> (2026-06-06) |
| A `Before / After / Why` table as the review format | <https://github.com/emilkowalski/skills> (commit `c8a7962`) (MIT) |
| The dial-consistency question and the swap-the-logo test | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop/SKILL.md` Core Principle and Delivery Gate Block 3; MIT) |

### Evidence grade

The bias results are measured on text, not on interfaces; applying them to UI review is an inference. The reviewer protocol is this package's design.
