# Craft Flow

Implementation guidance for an authorized UI task. SKILL.md owns mode, permission, confirmation and verification policy; this file describes the craft passes inside that policy. An audit reports findings; a plan proposes work. Neither advances into implementation.

## 1. Establish the smallest useful brief

Read the target, neighboring components, tokens and actual framework. PRODUCT.md and DESIGN.md are useful evidence when present, not prerequisites. A bounded repair retains existing identity and needs no discovery interview, palette selection, mock generation or separate plan approval.

For genuinely new or changed direction, state audience, task, hierarchy, behavior and brand constraints to the depth needed. Ask only about missing decisions that materially change the result. A supplied direction or explicit delegation can settle the choice; tool availability does not create extra mandatory approval gates. If choosing a greenfield stack is not already authorized or specified, ask through a discovered question tool or ordinary chat.

Reuse the project's framework, icon set and component system. Do not start a parallel build or edit generated output to bypass its source pipeline.

## 2. Load only the craft guidance needed

Use the canonical command registry through MCP or `scripts/command-metadata.json` on the filesystem. Begin with one to four relevant references, not the whole library:

| Need | Reference |
| --- | --- |
| Layout, spacing, type | `design-principles` |
| Authorized new visual language | `aesthetic-systems`, optionally `differentiation-playbook` |
| Forms, navigation, states | `interaction-design` |
| Motion | `motion-and-interaction` |
| Engineering and verification | `engineering-and-performance`, `verification-and-recovery` |
| Truthful content and advisory critique | `avoid-ai-slop` |

Examples are proposals, not permission to replace approved tokens or popular fonts.

## 3. Explore direction only when it answers a question

Mock generation and named references are optional tools for an unresolved design decision. Discover the host's capabilities; without image generation, continue from the brief and local product evidence. Never upload private material or install tooling merely because a reference workflow suggests it.

If the user adopts a mock or reference, record the important composition, hierarchy, density, assets and distinctive motifs. It is a visual target, not a complete specification of accessibility, copy, responsive behavior or recovery. Resolve conflicts explicitly; a user can revise their direction.

## 4. Build a coherent authorized slice

Implement in passes: structure, visual system, relevant states, motion/media and responsiveness. Preserve event handling, navigation and data contracts unless their change was requested.

- **Content:** source real names, statistics and assets; label demonstration fixtures visibly. No fake controls or missing requested behavior.
- **Semantics:** headings, landmarks, labels, accessible names, form associations and state announcements as applicable.
- **Visual system:** reuse tokens, deliberate spacing, readable type, stable wrapping and cause-level overflow fixes.
- **States:** implement only reachable loading, empty, error, success, disabled, focus and recovery states. Stress real data extremes where relevant.
- **Input:** keyboard, touch, focus restoration and non-hover paths; reduced-motion alternatives preserve information.
- **Media:** verify approved assets exist, check licensing, use meaningful alternatives and appropriate dimensions/loading. An unverified guessed URL is not an asset.
- **Engineering:** source changes follow the actual build pipeline. Run discovered validation commands only when host policy permits; missing checks remain gaps.
- **Motion:** spend effects on feedback or explanation, keep interaction interruptible, measure expensive effects on target devices.

When discovery changes scope or an adopted requirement, surface the conflict before expanding the change.

## 5. Inspect and repair within the budget

Use the host's browser or native preview; reuse an existing preview. Capture and inspect the affected states at sizes/input modalities from the product's policy. A screenshot path without viewing its contents is not visual evidence. Without rendering capability, complete safe source work and report UI NOT_VERIFIED rather than inventing inspection.

Compare against the actual brief, not a generic studio checklist. Fix only material observed defects; do not manufacture iterations. Capture relevant checks after the final edit, using the verification plan and `verification-and-recovery`. Static detector output is supplemental defect evidence, not rendered readiness.

## 6. Present the result

State what changed, states and environments exercised, evidence, accepted deviations and remaining gaps. Separate task completion from UI readiness. Do not let a polished presentation hide incomplete requirements or unavailable checks.

## Hand-off plans another agent can execute

A hand-off is self-contained: the executor may have none of this conversation's context. Include scope/authority, target files and symbols, exact proposed token values/durations/curves where needed, applicable states and an acceptance check for each requirement. "Add a subtle entrance" hides a design decision; "opacity 0→1 and translateY(12px)→0 over 200ms var(--ease-out)" is an executable proposal. Label suggestions as advisory, preserve approved requirements, and keep each slice bounded with its own evidence.
