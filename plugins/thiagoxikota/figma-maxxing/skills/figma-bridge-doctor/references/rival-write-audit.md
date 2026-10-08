# Rival-write audit

Loaded from the `figma-bridge-doctor` SKILL.md after the bridge reconnects in the middle of write work, and by the disjoint-pages lock override of the `figma-preflight` skill. Mandatory in both cases.

## After reconnecting in a WRITE session: rival-write audit (mandatory)

Field note, 2026-06: during the disconnect window the plugin may have served ANOTHER Claude Code session (even one running the same prompt), which wrote into the file. After reconnecting in the middle of write work:

1. List `page.children` and compare with your inventory from before the drop.
2. Look for nodes with names from YOUR plan that you did not create (ids outside your sequence = rival write).
3. Move rival debris into a container named `_archive` (create it if the file has none) and prefix each moved node's name with `[parallel session]`. Never delete it.
4. Tell the user that another live Claude Code window exists and can steal the bridge again (field note, 2026-06: the plugin served one server at a time and whoever re-triggered last won; see "The mental model" in SKILL.md for the later, conflicting notes).
5. Do not rely on the file lock (`figma_lock.py`, in the `figma-preflight` skill's `scripts/` directory) to detect this: two sessions that claim with the same agent name and the same task id are indistinguishable to the lock.

**Do not adopt a rival write into a deliverable, even if it turned out well** (validated 2026-06-15: a parallel session dropped a clean cutout image onto a slide; it was adopted because it fit the theme, against step 3). Default = archive + flag. If you adopt it anyway: (a) verify the node at FULL RES (crop + read the image, not a downscaled 0.8x preview screenshot), (b) confirm no more rival writes are coming in, (c) tell the user explicitly that the element came from another session. Silently adopting it into a deck that goes to a stakeholder is a provenance hole.

**If the rival write RE-INJECTS after you archive it, it is a live loop, not a one-shot** (validated 2026-06-15: one emblem was archived and the parallel session cloned another onto the same slide seconds later). You cannot win by cleaning node by node against a live writer. Do this: (1) clean ONCE (archive or remove the duplicate, the original already preserved), (2) confirm it is clean via `figma_execute` (children with no foreign node), (3) export IMMEDIATELY: `download_assets` (official Figma MCP server) renders the current state, and the **count of `rawImages` is a detector of a rival image node**: a slide with 1 legitimate image returns 1 rawImage; if a rival image node had entered, it would return 2. (4) escalate to the user to CLOSE the other Claude Code window: without that, the live Figma file keeps being polluted even with a clean export.
