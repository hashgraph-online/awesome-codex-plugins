---
name: figure-ground-cues
description: 'Apply specific visual cues to control figure-ground perception — shadow, elevation, scale, contrast, saturation, opacity, and texture. Use when designing layered interfaces, focus states, hover treatments, or any context where one element should clearly stand forward against others. Each cue contributes a portion of the figure-ground signal; combining cues strengthens the effect. The skill is selecting and calibrating cues for the desired level of separation.'
---

# Figure-Ground — visual cues

The figure-ground sorting that the user's perception performs depends on specific visual cues. As a designer, you choose which cues to use and how strongly to apply them, calibrated to the desired separation between figure and ground.

The major cues, with notes on their relative strength:

## Shadow / elevation

Strongest single cue for figure-ground in modern UI. A drop shadow under an element makes it appear closer to the viewer (figure), with the rest of the layout receding. Multiple levels of shadow create multiple levels of elevation.

Common implementations:
- Cards with subtle shadow (2–4px blur) for moderate elevation.
- Floating action buttons with stronger shadow (8–12px blur) for higher elevation.
- Modals with very prominent shadow + scrim for highest elevation.

Material Design formalized this into a system of "elevation levels" (0, 1, 2, 4, 8, 16, 24 dp) each with a specific shadow recipe. The system makes consistent figure-ground separation across a product easier to maintain.

## Scrim / overlay

A semi-transparent layer over the ground that makes the ground visibly recede. Most commonly used with modals: the modal sits above the scrim, the scrim sits above the page.

Calibration:
- Light scrim (10–20% opacity) for soft separation.
- Medium scrim (40–60% opacity) for clear modal-style separation.
- Dark scrim (70%+ opacity) for full focus on the figure (image lightboxes, video players).

## Scale

Larger elements tend to come forward as figure, especially when they're surrounded by smaller elements. A hero card among supporting cards reads as figure through scale.

But this can flip: a tiny element on a vast background can also read as figure (the small floating action button on a large canvas is figure despite its size). The cue depends on context.

## Contrast and saturation

Higher contrast and more saturated colors come forward; lower contrast and muted colors recede. The active workspace at full saturation; inactive workspaces with muted colors.

This cue is subtle — it's often used in combination with others rather than alone. But it's powerful for distinguishing active from inactive content.

## Opacity

Semi-transparent elements recede; fully opaque elements come forward. Reducing the opacity of inactive content (50–70% opacity) is a quick way to send it to the background.

Be careful not to reduce opacity to the point of illegibility. Even "ground" content should usually remain readable.

## Sharpness vs. blur

Sharp, in-focus elements come forward; blurred elements recede. iOS uses background blur extensively — a modal's background is blurred, signaling that it's behind the modal.

Blur is a strong cue but expensive computationally. Use deliberately, not casually.

## Texture and detail

More detailed elements come forward; smoother, less detailed elements recede. A photographic background with text overlaid feels different than a solid background with text — the texture of the photo competes with the text for figure status.

## Outlines and borders

A clear, visible border around an element helps it read as a closed figure. Borderless elements may merge into their background.

But heavy borders can feel "heavy" or dated. Modern design often prefers shadow over border for figure separation.

## Position in z-axis (layering)

Elements layered on top of others occlude them, which is a strong figure cue. The element on top is figure; the element behind is ground.

Implementation in CSS: z-index controls the layering order. In design systems: explicit layering levels (cards, popovers, modals, toasts each at their own z-axis level).

## Combining cues

The cues compound. A modal that uses shadow AND scrim AND opacity reduction on the background is more clearly figure than a modal using only one of these.

For elements that need to clearly come forward (modals, popovers, focus states), combine cues. For elements that should subtly come forward (hover states, mild emphasis), use a single cue or a combination of subtle ones.

Avoid combining too many cues at high intensity — the result can feel theatrical. Match the cue strength to the actual importance of the figure.

## Worked examples

### A modal with full figure-ground

A modal opens. Cues applied:
- Scrim: 50% opacity black overlay between modal and page.
- Modal elevation: prominent shadow (16px blur, 40% opacity).
- Modal background: pure white (sharp contrast against the dark scrim).
- Page beneath: visible through scrim but clearly receding.

The user's perception is unambiguous: the modal is figure, the page is ground. Attention naturally goes to the modal.

### A card hover with subtle figure-ground

A card in a grid is hovered. Cues applied:
- Shadow increases (from 2px blur to 4px blur).
- Slight scale increase (1.02×).
- Subtle background shift (0.5% lighter).

The card subtly comes forward. Other cards remain at baseline. The user gets gentle feedback about where their attention is, without dramatic visual change.

### Active workspace differentiated from inactive

In a multi-workspace app, the active workspace is rendered with full saturation; inactive workspaces are at 60% opacity with muted colors. The active workspace is clearly figure.

When the user switches workspaces, the cues swap: the new active workspace becomes figure, the previously active workspace becomes ground.

### Background photo competing with text

A hero section uses a photo background with text overlaid. Without intervention, the photo's detail and color compete with the text — figure-ground is ambiguous.

Add a dark gradient over the photo (figure-ground cue: scrim) to push the photo further into the background. The text now clearly reads as figure.

### A card with too many cues

A card has: a thick border, a heavy drop shadow, a colored background, a glow effect, AND scaling on hover. The card screams. It feels theatrical, almost cartoonish.

The fix: reduce to one or two strong cues. A subtle shadow + a clean white background + a slight border on hover is enough. The figure-ground separation works without the theatrics.

## Anti-patterns

**Insufficient cues.** A modal that uses only a thin border and no shadow or scrim. The figure-ground separation is too weak; the modal blurs into the page.

**Mixed cues that fight.** A modal with shadow (suggests it's in front) but with reduced opacity (suggests it's receding). Users get conflicting signals.

**Overdone cues.** Heavy shadows on every card; high-contrast borders everywhere; aggressive scale changes on hover. The cues lose meaning when applied universally.

**Inconsistent cues across surfaces.** Modals styled with shadow + scrim in one place; modals styled with just a border in another. Users can't form expectations about modality.

**Cues that hurt accessibility.** Reducing opacity so low that text becomes hard to read; using color-only cues that fail for color-blind users.

**Reversed cues.** Chrome (sidebar, header) styled with stronger figure cues than the content. Users look at the chrome instead of focusing on their work.

## Heuristic checklist

When designing figure-ground separation, ask: **What should be figure, and what should be ground?** Be deliberate. **Which cues am I using to communicate the sorting?** List them. **Are the cues consistent within the product?** Inconsistent cues confuse users. **Is the separation strong enough?** Test by glancing at the design — what comes forward? **Is the separation too aggressive?** Theatrical cues feel wrong; calibrate to the actual importance.

## Related sub-skills

- `figure-ground-relationship` — parent principle on figure-ground perception.
- `figure-ground-overlays-and-modals` — sibling skill on the most common figure-ground problem.
- `hierarchy` — figure-ground is a primary mechanism for hierarchy.
- `signal-to-noise` — figure should be high-signal; ground low-noise.
- `color` — color choice is one figure-ground cue.

## See also

- `references/elevation-systems.md` — practical guidance on building consistent elevation/figure-ground systems across a product.
