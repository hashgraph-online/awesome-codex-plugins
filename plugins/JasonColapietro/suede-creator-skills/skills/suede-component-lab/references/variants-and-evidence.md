# Comparable variants and useful evidence

Use variants to resolve a scoped product question: which composition makes the
next action clearer, which density supports the task, or which placement keeps
recovery visible on mobile. Cosmetic novelty alone does not establish a need.

## Set up a comparison

Keep the current implementation as the baseline. Name one primary axis and
build only the alternatives needed to compare it. A change in density, layout,
type hierarchy, or emphasis must be part of the authorized brief; preserve
everything outside that axis. Approved offer, claims, and sales copy remain
constant unless a conversion case for rewriting them is already approved.

Render the real component in its actual safe surrounding context: production
layout, neighboring content, tokens, and fonts, with all effects isolated.
Use supported props/composition and local test adapters. If the component
cannot express the proposed variant without product changes, distinguish the
required implementation from the fixture work and stay within authorization.
Never present rebuilt markup as evidence about the production component.

Render one full-size variant at a time or comparable full-size stages. Match
viewport, state, data, zoom, theme, and interaction before judging differences.
Give each direction a descriptive label and deterministic local selector. The
selector is workbench UI, not a new product feature. Its names and state must
not leak into production artifacts.

## Judge the product question

Separate three kinds of statements:

- **Standard:** a relevant accessibility requirement or platform constraint,
  named precisely with the checked evidence and applicable scope.
- **Project convention:** a documented token, component rule, approved brand
  decision, or supported interaction pattern in this project.
- **Suggestion:** a possible improvement or preference, with a testable user
  benefit. Do not present this as a defect or a measured conversion gain.

Compare task completion, visible next action, error recovery, focus order and
visibility, content reachability, responsiveness, and reuse of shared primitives.
A candidate's contrast, focus, and keyboard defects cannot be traded away for
a visual match. Flag an inaccessible reference and use the smallest accessible
solution within scope. Follow project motion intent and reduced-motion behavior;
fixed scaling, stagger, or easing values are not universal quality criteria.

| Candidate | Named axis | Observed task effect | Cost or remaining evidence |
|---|---|---|---|
| Baseline | Existing composition | State the actual result at the tested sizes | Record known issue or retained strength. |
| Alternative | One authorized change | Cite the matched captures and interaction | Distinguish maintenance cost from an unmeasured hypothesis. |

Recommend from evidence when asked, or when it advances the requested decision.
If alternatives perform equivalently in the tested task, say so. Do not invent
an experiment result, rank purely by taste, or multiply options to create the
appearance of work.

## Evidence and remediation record

Each finding should name the affected fixture, user impact, source path/line,
reproduction sequence, viewport, observed result, and evidence file. Record
source-supported concerns separately from rendered findings. For a diff review,
pin exact base/head/scope and use these labels consistently:

- **Introduced:** the problematic behavior is new in the reviewed change.
- **Regression:** behavior that previously worked now fails; cite base evidence.
- **Pre-existing:** the same problem exists at the comparison base.

If only a head artifact is supplied, do not invent a base SHA or regression
claim. Mark attribution unknown and explain the missing comparison evidence.
Group repeated symptoms under a shared token, primitive, or state-machine root
cause; list affected cases beneath the one cause rather than duplicating issues.

When a fix is authorized, capture the failure, change the smallest shared cause,
rerender at matching viewport/state, and inspect again. Check nearby cases that
the shared change can affect. Continue until the stated outcome is established
or report the concrete blocker, attempts, and remaining evidence. Source tests
alone cannot prove rendered behavior.

The handoff distinguishes four outcomes: harness created, cases rendered,
interactions exercised, and product fix verified. State which actually happened.
Include the created-path manifest, production-exclusion check, isolated action
counts or request evidence, cleanup status, commands/results, and coverage gaps.
These checks establish the tested scope, not complete security or accessibility
certification and not a measured conversion lift.
