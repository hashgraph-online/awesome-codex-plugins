# Visual parity

Make two UI implementations render pixel-identically, or migrate a styling system with no visible change, proven by image diff against a reference nobody edits.

Use this for exact matches or no-visible-change style migrations. Intended visual changes go to [Feature](feature.md).

Inputs: the components, the current implementation (and target, when matching two), and the render surface.

The reference screenshots define correct. An image diff decides a match; eyeballing does not.

1. **Build the reference first:** a screenshot regression harness covering every state of each component, plus the target when matching two. Render fixture data only, since the images get committed. No reference, no parity claim; this blocks everything else.
2. **Hold the anti-cheating rules.** Harness and reference images stay untouched, and no component is restructured to make a diff pass. If a reference looks wrong, ask the user.
3. **Migrate components in parallel,** each in its own worktree with one `tarique-agent` owner ([principle-separate-before-serializing-shared-state](../../principle-separate-before-serializing-shared-state/SKILL.md)). Shared primitives go first. Without worktree isolation, run them sequentially and note it.
4. **Diff each against its reference** through the UI control skill on the same surface. Any nonzero difference fails; find which pixels differ and why, and loop until zero. Also check each diff for changes screenshots miss, such as focus order, ARIA attributes, or sanitized HTML replaced by raw `innerHTML`.
5. **Follow [Opening a PR](opening-a-pr.md)** per component or safe group.

**Reply** with components migrated, each diff result, the harness location, and what remains.
