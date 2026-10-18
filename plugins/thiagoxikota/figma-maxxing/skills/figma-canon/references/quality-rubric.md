# Quality rubric

Load for post-write self-evaluation. A concrete 0-10 rubric for any Figma canvas change: 5 auto-fail criteria plus 4 weighted dimensions (Layout 0-3, DS conformance 0-3, Hierarchy/Naming 0-2, Product logic & states 0-2). 8/10 is the minimum to declare done.

Self-eval after every write. Below 8/10 = fix before declaring done.

## Auto-fail (score 0/10, revert/fix immediately)

1. **Hardcoded colors**: hex literals where variables/tokens exist
2. **Missing auto layout**: absolute X/Y positioning in frames that should be responsive
3. **Default Figma names**: `Frame 42`, `Rectangle 1`, `Text 3`, `Group 5`
4. **Detached components**: instance unlinked from its main component without strong justification
5. **Layer overlap**: unintentional visual collision due to layout failure

Any one of these = restart that section, do not declare done.

## Scoring matrix (10 points total)

### A. Layout & responsiveness (0-3)

- **3 pts:** Auto Layout at every level. Constraints correct (Fill / Hug). Resizes cleanly.
- **2 pts:** Auto Layout mostly, minor issues in deep nesting or an odd constraint at edge cases.
- **1 pt:** Mix of Auto Layout + absolute positioning. Hard to maintain.
- **0 pts:** Absolute positioning dominant. **AUTO-FAIL.**

### B. Design system conformance (0-3)

- **3 pts:** 100% component instances + semantic tokens for color/type/spacing.
- **2 pts:** Components used, but some properties adjusted off-system (manual spacing override).
- **1 pt:** New unnecessary components created when equivalents already existed.
- **0 pts:** Visual invention. Arbitrary colors/fonts. **AUTO-FAIL.**

### C. Hierarchy & naming (0-2)

- **2 pts:** Clean semantic tree (`ProductCard > card-header > card-title`), max depth 4.
- **1 pt:** Descriptive names but the tree is over-nested or messy.
- **0 pts:** Figma default names. **AUTO-FAIL.**

### D. Product logic & states (0-2)

- **2 pts:** UI reflects product logic. Empty/loading/error states present. Contrast respected.
- **1 pt:** Only happy path. Edge cases missing.
- **0 pts:** UI makes no sense in the user-flow context.

## What 10/10 looks like

Output indistinguishable from the work of a senior Design Systems Engineer:

- Zero tech debt (no loose colors, no unstyled text)
- Maps cleanly to DOM/React layer by layer
- A token change cascades correctly (e.g. a `color/primary` swap does not break contrast)
- Every element has a clear purpose in the user flow

## Self-eval protocol

After every `figma_execute` write:

1. `get_metadata` on the modified frame
2. `get_screenshot` for visual sanity
3. Run this rubric mentally: score A+B+C+D
4. If score < 8: invoke `figma_execute` again to fix BEFORE reporting to the user
5. Cite the score in the report ("8/10, minor B deduction for one off-system spacing")

`get_metadata` and `get_screenshot` are tools of the official Figma MCP server, not of figma-console-mcp. If that server is not connected, do the same two steps (read the modified frame back, then look at a screenshot of it) with the tools you have.

## Composition

- The `figma-slop-check` skill uses this rubric's 0-10 score and cites these auto-fail criteria as its severity rubric
- The `figma-handoff-gate` skill runs after `figma-slop-check` passes, before ship
- See `references/ai-slop-signatures.md` for visual slop patterns (overlapping concern)
