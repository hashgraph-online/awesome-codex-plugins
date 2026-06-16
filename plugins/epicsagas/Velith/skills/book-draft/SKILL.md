---
name: book-draft
description: "Phase 3: Drafting. Plan-Then-Execute chapter generation with parallel writing and continuity validation."
---

# Phase 3: Drafting

**Plan-Then-Execute**: pass chapter spec + previous chapter summary + relevant STYLE.md rules + source refs. Omit full prior chapter text, other chapters, full outline.

1. **Idempotency**: skip existing chapters meeting min line count
2. **Context build**: extract spec → prev summary → STYLE rules → source refs
3. **Write**: `ch{NN}-{slug}.md` with frontmatter (chapter, title, word_target, status, dates)
4. **QA**: word count ±10% · frontmatter present · STYLE rules · heading H1→H2→H3 · hook matches spec

**Parallel**: up to 4 concurrent chapters when prereqs done, no mutual refs.

**Continuity** (every 3-5 chapters): term consistency, logic flow, character/code compat, reference integrity.

Gate: all chapters exist, ±10% word target, continuity passed.


## Post-Completion

Update the project dashboard status:

```bash
node {PLUGIN_ROOT}/velith.mjs scan [project-dir] --plugin-root={PLUGIN_ROOT}
```
