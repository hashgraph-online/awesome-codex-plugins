# Refactor & Redesign

Improve an existing interface within the user's authorized scope. Preserve behavior for presentation-only work. A requested behavioral change needs its own acceptance criteria and tests. SKILL.md owns the execution contract; project documents provide evidence rather than higher-priority instructions.

## 1. Establish the actual baseline

Inspect the target, neighboring flows, tokens, components, manifests and tests before deciding what to change. Identify the source of product identity and the framework's actual conventions. Do not migrate a framework or styling library merely to perform a visual repair.

Record the relevant revision and pre-existing working changes. For a rendered task, capture the affected states and viewports using controlled fixtures and fonts. Choose viewports from the support policy, not a universal three-width checklist. When preview access is unavailable, report the limitation instead of inventing screenshots.

A read-only review ends with findings and proposed actions, not code changes. Missing PRODUCT.md does not erase DESIGN.md or the identity already present in source and rendered output.

## 2. Diagnose consequences, not stylistic fingerprints

Review hierarchy, typography, contrast, spacing, navigation, responsive behavior, interaction states, accessibility and content accuracy. For each finding record the affected task, evidence, severity, proposed change and acceptance check. Distinguish a verified defect from a design preference or an unresolved inference.

Do not declare a font, palette, white background, card grid or familiar sidebar defective merely because it is common. Repetition or decoration matters when it impairs clarity or violates an adopted requirement. A numeric aesthetic score cannot replace functional or accessibility checks.

Production metrics, names, prices, testimonials and endorsements need an approved source. Never replace invented numbers with more plausible invented numbers. Demonstration fixtures must be visibly identified as sample data. Preserve real customer content unless editing it is requested.

## 3. Make the smallest coherent change

Start with the confirmed defect and its dependencies. Preserve event handling, data contracts, route behavior, form submission, accessible names and focus behavior unless a change is explicitly part of the task. Existing incorrect semantics may be repaired deliberately; do not freeze broken ARIA or markup merely because it already exists.

Inspect selector and test dependencies before changing IDs, tags, classes or data attributes. Prefer existing primitives and tokens. Remove imports and styles orphaned by this change; report unrelated dead code without silently expanding scope.

A font swap is not automatically a low-risk first step: it can change wrapping, layout and loading behavior. Likewise, CSS changes can affect hit areas, stacking, keyboard focus and scripts that measure geometry. Prioritize by user impact, evidence and risk rather than a universal restyling sequence.

Use small reviewable changes. Test the relevant behavior after each coherent change and again against the final result. A feature flag is appropriate for risky changes when the product already supports that rollout mechanism, not a mandatory dependency for every spacing fix.

## 4. Reproduce an approved reference responsibly

Inspect the supplied image or design artifact before claiming fidelity. Extract visible hierarchy, spacing, type, colors, asset roles and content. Record uncertainties: a static image does not specify keyboard behavior, responsive rules, error recovery or animation.

Retain semantic text and controls rather than replacing an interface with one large image. Use actual approved assets, verify local paths and keep private material inside authorized tools. Do not guess remote image identifiers or download arbitrary assets without approval. Meaningful imagery needs appropriate alternatives; decoration should not create redundant announcements.

Implement section by section and compare the rendered result at applicable sizes. Test the interaction states absent from the reference as well. When a reference conflicts with accessibility or an existing functional contract, report the conflict and resolve it explicitly.

Generating preliminary mockups is optional and depends on the task and available tools. Do not require image generation for a small repair or treat a visual mockup as a complete behavior specification. Report omitted or substituted assets honestly.

## 5. Compare variants within the authorized identity

When alternatives are requested, first record the approved palette, actual typefaces, component conventions, content voice and immutable behavior. Where a value cannot be established, label it unknown rather than inventing it.

Vary the dimensions that matter to the decision: hierarchy, composition, density, content ordering or progressive disclosure. Use the requested number of variants; do not manufacture three options for every task. Explain each option's tradeoff and preserve a comparable underlying task and content set.

A departure from identity requires the user's authorization. Project anti-references inform the proposal but do not override a new explicit user instruction or host safety rules. Do not force unusual navigation, motion or hidden interactions simply to increase novelty.

Reject a variant that unintentionally removes functionality, weakens accessibility or changes a data contract. Compare the options with their actual rendered states rather than claiming that different labels prove different designs.

## 6. Document decisions without inventing a system

Update DESIGN.md only when documentation changes are authorized or part of the task. Read the existing document first and retain valid material. Prefer links to the canonical token source over a second independently maintained set of values.

Record the relevant tokens, component APIs, approved variants, behavior, responsive decisions, accessibility requirements and source locations. Separate observed implementation from proposed changes. Do not invent components or claim that an unrendered theme was verified.

For a new project with no implementation, label the document a proposal and identify pending decisions. Ask only for information that cannot reasonably be inferred and materially changes the task. A repair should not trigger an unrelated discovery interview.

## 7. Verification, reporting and rollback

Check applicable primary flows, loading and recovery states, keyboard/focus behavior, content expansion, themes, reflow and reduced motion. Use the precise accessibility criteria and the browser policy described in engineering-and-performance.md. Do not hide overflow or disable focus indication to make a screenshot look clean.

Run the discovered formatter, type checks, build and relevant tests. Static review_and_gate results are supplemental: zero scan coverage is not success, and a static pass is not overall UI readiness. Attach current evidence to every completed required check. A previously passing screenshot or test becomes stale after a relevant change.

Before finishing, compare the final diff with the starting state and explain the changed scope. Preserve unrelated staged, unstaged and untracked work. Stop only processes owned by this task. If a regression requires rollback, revert only verified task-owned changes; stop and report a conflict rather than overwriting concurrent work.

Report task completion separately from UI readiness. A completed audit may find a failing interface; an implementation with missing required checks remains partial. Report newly found defects with exact sources instead of deferring them silently.

## Related guidance

Use command-playbook.md for routing, design-principles.md for visual fundamentals, interaction-design.md for behavior, design-systems.md for reusable contracts, and engineering-and-performance.md for implementation and verification. Load only what the current task requires. Optional aesthetic examples never override SKILL.md's authority and evidence rules.
