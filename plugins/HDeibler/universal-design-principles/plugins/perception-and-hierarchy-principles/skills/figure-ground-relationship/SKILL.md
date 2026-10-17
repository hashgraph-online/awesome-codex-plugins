---
name: figure-ground-relationship
description: 'Apply the Gestalt principle of Figure-Ground Relationship — the perceptual separation of what''s perceived as the figure (the focus, the object) from the ground (the surrounding context). Use when designing modals, overlays, focus states, hero elements, hover treatments, layered interfaces, or any context where one element should clearly stand forward against everything else. The user''s perception always sorts the visual field into figure and ground; designs that reinforce the desired sorting feel clear, while designs that fight it feel confusing.'
---

# Figure-Ground Relationship

> **Definition.** Figure-ground relationship is the perceptual principle that the visual field is automatically sorted into "figure" (the object of focus, the thing perceived as standing forward) and "ground" (the context, the thing perceived as receding behind). The sorting is automatic and pre-conscious; the user doesn't choose what's figure and what's ground. The designer's job is to ensure that what should be figure (the active element, the focal point, the modal content) reads as figure, and that what should be ground (the chrome, the inactive content, the background) reads as ground.

The classic illustration is the Rubin vase — a figure that can be perceived either as a vase (with the surroundings as ground) or as two faces in profile (with the vase shape as ground). The image is deliberately ambiguous; the visual system flips between the two interpretations because neither has clear primacy.

In design we usually want unambiguous primacy. The active workspace should clearly be figure; the chrome around it should clearly be ground. The modal should clearly be figure; the page underneath should clearly recede. The hovered item should clearly come forward; the rest should fade.

## The cues that signal figure

The visual system uses several cues to decide what's figure and what's ground.

**Definite, closed shape.** Elements with clear, complete boundaries are perceived as figure. Loose or open shapes are perceived as ground.

**Apparent closeness.** Elements that appear closer (through shadow, scale, or perspective) are perceived as figure. Elements that recede are ground.

**Lower position in the visual field.** Elements positioned in the lower part of the field tend to be perceived as figure (a heuristic from real-world perception, where ground is usually at the bottom).

**Smaller area.** Smaller elements are typically perceived as figure against larger backgrounds, not the reverse.

**Higher contrast or saturation.** Brighter, more saturated, more contrasting elements come forward. Muted, low-contrast elements recede.

**Texture and detail.** More detailed elements come forward; smoother, less detailed elements recede.

**Symmetry.** Symmetric shapes tend to be perceived as figure.

**Overlapping (occlusion).** Elements that occlude others are perceived as in front, hence as figure.

These cues compound. A small, sharply-defined, highly-contrasting element overlaying a large, muted, smoothly-textured background is unambiguously figure.

## Why figure-ground matters

When figure-ground is clear, the user knows where to look without effort. The active task is figure; the rest is ground. Their attention naturally goes to the figure.

When figure-ground is ambiguous, the user has to do attention work — actively deciding what to focus on. This is tiring and slow. Layouts where everything competes for visual primacy feel chaotic; layouts where nothing has primacy feel flat.

When figure-ground is reversed (the wrong element comes forward), the user is misled about where the focus is supposed to be. They may miss the intended focal point and pay attention to something that isn't important.

## Sub-skills in this cluster

- **figure-ground-cues** — The specific visual cues (shadow, scale, contrast, detail) that signal figure vs. ground, and how to apply them deliberately.
- **figure-ground-overlays-and-modals** — The most common figure-ground design problem: overlays, modals, popovers that need to clearly come forward over the underlying page.

## Worked examples

### A modal with clear figure-ground

A modal opens over the page. The page content fades to lower opacity (becomes ground). A scrim (semi-transparent overlay) further separates the page from the modal. The modal itself has a sharp white background, a clear edge with shadow, and full saturation.

The user's perception clearly sorts: modal is figure, page is ground. Attention naturally goes to the modal. When the modal closes, the page returns to figure status.

### A modal with weak figure-ground

A modal opens but the page beneath isn't visually changed (no scrim, no opacity change). The modal has a subtle border but no shadow. The figure-ground separation is weak — the modal feels like another panel on the page rather than a focused overlay.

Users can be unsure where to focus. The modal's interactivity isn't visually emphasized. The figure-ground principle hasn't done its work.

The fix: add a scrim, increase the modal's elevation (more shadow), make the page beneath visibly recede.

### Hover state with figure-ground

When a user hovers over an item in a list, the item gets a slightly lifted appearance — slightly elevated shadow, slightly more saturation, slightly larger. The other items remain ground.

The hover-triggered figure-ground shift signals interactivity and gives the user feedback about where their attention is.

### A dashboard where everything competes

A dashboard has 8 large cards, all with similar styling, similar weight, similar prominence. The user has no clear focal point. Every card feels like figure; nothing feels like ground.

The fix: introduce visual hierarchy through figure-ground cues. Make the most important card larger or more prominent (figure). Keep supporting cards smaller and less emphasized (ground). The user's attention now has a clear target.

### Active vs. inactive workspace

An app has multiple workspaces visible (a current one and recent ones). The current workspace is rendered with full saturation, sharp shapes, and prominent contrast. The recent workspaces are rendered with reduced opacity, slightly muted colors. The figure-ground separation makes the current workspace clearly active.

If both had been styled identically, users would have to read carefully to know which workspace was active. The figure-ground cue does the work.

## Anti-patterns

**Reversed figure-ground.** The chrome (sidebars, headers) styled more prominently than the content. Users look at the chrome instead of the content.

**No figure-ground separation.** Layouts where everything has the same visual weight. Nothing feels primary; users don't know where to focus.

**Modals that don't come forward enough.** Insufficient scrim, no elevation cues. The modal blurs into the page.

**Overlays that come forward too aggressively.** Heavy darkening of the background, dominant overlays that feel intrusive. The figure-ground separation is too aggressive and the user feels assaulted.

**Inconsistent figure-ground treatment across the product.** Modals styled differently in different places; some come forward more than others. Users can't form expectations.

**Background imagery that competes with foreground.** A photo background under text where the text is hard to read because the photo is so visually rich. The figure-ground sorting is unclear.

## Heuristic checklist

When designing a layout, ask: **What should be figure (the focal point) and what should be ground (the context)?** Be explicit about the intended sorting. **Are the visual cues reinforcing the desired sorting?** Shadow, contrast, scale, saturation should align. **At a glance, can the user identify what's primary?** If they have to think about it, the figure-ground is weak. **Does the figure-ground sorting hold up when state changes?** A modal opens, a hover happens, an item gets selected — figure-ground should re-sort cleanly.

## Related principles

- **Gestalt grouping principles generally** — figure-ground is one of the original Gestalt principles.
- **Hierarchy** — figure-ground is a primary mechanism for expressing hierarchy.
- **Signal-to-Noise Ratio** — figure should have high signal; ground should have low.
- **Color** — color choice affects figure-ground (saturated colors come forward, muted recede).
- **Closure** — closed forms are more likely to be perceived as figure.
- **Layering** — explicit visual layering is a tool for figure-ground design.

## See also

- `references/lineage.md` — origins in Gestalt psychology and the Rubin vase.
- `figure-ground-cues/` — sub-skill on the specific visual cues that signal figure vs. ground.
- `figure-ground-overlays-and-modals/` — sub-skill on the most common figure-ground design problem.
