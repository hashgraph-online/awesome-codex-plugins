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
- for a Korean product, `references/korean-break-quality.md`

When no comparison tool exists, a reference comparison is reported `unavailable`, never passed. A reviewer who could not compare reports that line as `unavailable` with the reason, and the pass does not count it as a pass.

## 4. Two Passes

The review runs twice over the same inputs, and each pass owns fixed sections so no question is asked twice or skipped. Pass A runs first.

| Pass | Owns | Does not own |
|---|---|---|
| A. design system and function | questions 1-5, 7, 8 below; `rules/craft-floor.md` §1-5 and §7; the §5 rows about structure, hierarchy, states, and placeholder proof | rendered fidelity, measured values, Korean line breaks |
| B. visual fidelity and Korean breaks | question 6 below; `rules/craft-floor.md` §6 and the rendered items of §9; `references/korean-break-quality.md`; the coverage list and freshness checks of `rules/rendered-evidence.md` | product direction, copy voice, structure |

Section ownership is fixed: a pass may report a finding outside its sections only as a `[product]` note for the other pass, and the other pass decides it.

### 4.1 Questions, in order

1. Could this be any product in its category? Name what is specific to this product, or report that nothing is. (A)
2. Where does the eye land first, second, third, and is that the order the task needs? (A)
3. Which element has no job: a decoration, a container, a label, a motion? (A)
4. Which values break the system: a one-off color, size, space, radius, or duration? (A)
5. Which states are missing or look unfinished? (A)
6. Which floor items fail, with the measured value? (B)
7. Does the result match its declared dials (ENERGY, RHYTHM, MOTION), and is there one focal point, one accent, and one identity motif? (A)
8. If the logo and product name were swapped out, would anything here still belong to this product? (A)

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
- a tag, `[product]` or `[evidence]`

A finding without a region and a rule is a comment, not a finding; record it but do not act on it. Present critique findings as a `| Before | After | Why |` table in the report.

### 6.1 What the tags mean

- `[product]` — the interface itself is wrong. The finding names a product decision and is answered by changing the design or by a documented reason, within the correction budget.
- `[evidence]` — the capture cannot support any claim: a stale capture, a signature or frame-kind failure, a viewport mismatch, a missing surface from the coverage list, or a reference comparison reported `unavailable`. An `[evidence]` finding requires a new capture, not a code change. Fixing the interface first would grade the wrong artifact, so the new capture comes first and the finding is re-raised if it survives.

A finding that mixes both is split in two: the capture defect keeps `[evidence]`, and the interface defect it hid becomes a separate `[product]` finding once a valid capture exists.

## 7. Answering Findings

- `high` (P0/P1) findings are fixed within the correction budget, or answered with a reason the user can check.
- An `[evidence]` finding is closed only by a new capture that passes the freshness and hygiene checks; a code change closes nothing.
- A finding that conflicts with the brief or a documented brand decision is answered with that evidence, not obeyed.
- A reviewer reply is evidence. "Looks great, ship it" is not a pass; only the checklist and the cited findings decide.
- A rule satisfied by deleting function (removing all motion, all states, a real badge) is a degenerate fix; restore what carried meaning.

## Sources

> Checked 2026-11-09.

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
| Two passes with fixed section ownership and every finding tagged `[product]` or `[evidence]`; an `[evidence]` finding needs a new capture | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored in this package's own words; the source repository has no license and no text or code was copied |

### Evidence grade

The bias results are measured on text, not on interfaces; applying them to UI review is an inference. The reviewer protocol, the pass split, and the tag rule are this package's design, re-authored from an unlicensed source.
