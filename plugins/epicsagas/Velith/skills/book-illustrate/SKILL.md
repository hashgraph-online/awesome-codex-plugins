---
name: book-illustrate
description: "Alias for /book-visuals limited to diffusion illustrations (scene, header, spot art). Kept for compatibility; new work should use /book-visuals, which also covers diagrams, charts, technical drawings, photos, and the art bible."
argument-hint: "[project-dir] [--execute]"
---

# Interior Illustrations

This command is now a thin entry point into the book visual system. Run the illustration subset of `/book-visuals`:

1. If `art-bible.md` does not exist or has no `## Look lock`, run `/book-visuals plan` then `/book-visuals lock` first. Illustrations produced without a locked look will not match each other or the cover.
2. Invoke `illustrator` for the chapters in scope. It chooses moments, compiles model-agnostic prompts via `velith.mjs images compile`, generates if an image tool is available and `--execute` was given, runs vision QA, and places references.
3. Run `node ${CLAUDE_PLUGIN_ROOT}/velith.mjs images check [project-dir]` and have `art-director` do the consistency review.

Full reference, image types, constraints, and directory layout: `${CLAUDE_PLUGIN_ROOT}/skills/book-visuals/SKILL.md`.

Legacy note: projects that kept illustrations in `publish/illustrations/` still build; `images check` reports them as unmanaged until they are moved to `visuals/illustrations/` and added to the manifest.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
