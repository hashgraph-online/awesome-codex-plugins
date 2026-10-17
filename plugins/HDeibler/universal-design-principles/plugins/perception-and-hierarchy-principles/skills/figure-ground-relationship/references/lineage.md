# Figure-Ground Relationship — origins and research lineage

## The Gestalt school and Edgar Rubin

Figure-ground perception was first systematically studied by the Danish psychologist Edgar Rubin in his 1915 doctoral dissertation. Rubin observed that the visual field is automatically organized into figure (the perceived object) and ground (the surrounding space), with the two playing distinct perceptual roles. The figure is perceived as having form, location, and meaning; the ground is perceived as continuing behind the figure, formless and undifferentiated.

The most famous illustration is the Rubin vase, which Rubin used in his dissertation. The image can be perceived as a black vase against a white background, or as two white faces in profile against a black background. The image flips between the two interpretations because neither is unambiguously the figure — the cues are evenly balanced.

Rubin identified several characteristics of figure perception:

- The figure has shape; the ground is shapeless.
- The figure is in front of the ground.
- The ground continues behind the figure.
- The figure is more memorable; the ground is forgettable.
- The contour belongs to the figure, not to the ground.

Rubin's work was incorporated into the Gestalt school's broader theory of perceptual organization and remains foundational to vision science.

## Cues that determine figure-ground sorting

Subsequent research has identified the specific cues that the visual system uses to decide what's figure and what's ground:

**Surroundedness.** An element surrounded on all sides by another element tends to be perceived as figure (the small one being figure, the larger surrounding one being ground).

**Size.** Smaller elements are perceived as figure against larger backgrounds. The 1922 study by Wolfgang Köhler confirmed that this is a strong cue.

**Orientation and verticality.** Vertical and horizontal elements are perceived as figure more readily than diagonals.

**Bottom-of-field.** Elements in the lower visual field tend to be perceived as figure (a heuristic from real-world perception, where ground is usually below).

**Symmetry.** Symmetric shapes are more likely to be perceived as figure.

**Familiarity.** Recognizable shapes are more likely to be perceived as figure.

**Closedness.** Closed contours are perceived as figure; open contours as ground.

**Convexity.** Convex shapes (bulging outward) are perceived as figure more readily than concave shapes.

**Lower contrast or texture.** The element with more visual information (texture, color, detail) tends to be figure.

When cues align, figure-ground is unambiguous. When cues conflict (as in the Rubin vase), perception flips between interpretations.

## In design history

Figure-ground has been a fundamental concern of graphic design since the field's emergence:

- **Information hierarchy in print.** A page with a clear focal element (a hero image, a large headline) and supporting text uses figure-ground to direct attention. The Bauhaus tradition emphasized clean figure-ground separation as a design virtue.
- **Logo design.** Logos that exploit figure-ground reversal (the FedEx arrow in negative space, the WWF panda) use the principle as a design device, sometimes deliberately ambiguous.
- **Poster design.** A poster with a clear central figure and uncluttered ground reads from a distance; a poster where everything competes for attention reads as visual noise.
- **Mapping and information visualization.** Maps that distinguish foreground content (the active layer) from background reference (the topographic base) use figure-ground sorting to guide attention.

## In modern UI

Figure-ground operates throughout modern interface design:

- **Modal dialogs.** A modal becomes figure; the page beneath becomes ground. The scrim (semi-transparent overlay) makes the figure-ground separation visible.
- **Hover and focus states.** Hovered or focused elements come forward (figure); other elements recede (ground).
- **Active vs. inactive workspaces.** The active workspace is figure; inactive workspaces are ground (often shown with reduced opacity or muted color).
- **Notifications and toasts.** A notification is figure; the underlying content is ground (briefly, until the notification dismisses).
- **Layered interfaces.** Material Design's "elevation" system formalizes figure-ground through z-axis layering: higher elevation = closer to the user = more figure-like.

The systematization of figure-ground in design systems (elevation tokens, scrim opacities, focus-state styles) is a recent development that recognizes how often the principle is applied and how valuable consistency across surfaces is.

## Empirical findings worth remembering

The research on figure-ground perception converges on:

- **Sorting is automatic and pre-attentive.** It happens within ~100ms of visual exposure. Designs that work with the automatic sorting feel clear; designs that fight it feel confusing.
- **Figure is more memorable than ground.** Users remember what was figure; they often can't remember what was in the ground at all.
- **Attention follows figure.** The figure gets the attention; the ground gets minimal processing.
- **Figure-ground can be ambiguous.** When cues are balanced, perception flips. Use this deliberately for ambiguous-on-purpose designs (like the Rubin vase or a clever logo); avoid it when you want clear primacy.
- **Reversed figure-ground feels wrong.** When the chrome is more prominent than the content, users feel something is off even if they can't articulate it.

## Related concepts

**Layering.** Explicit visual layering (z-index, elevation, shadow) is the modern UI mechanism for expressing figure-ground.

**Hierarchy.** Visual hierarchy depends on figure-ground sorting at multiple levels — the most important element is figure within its level; that level is figure within the larger context.

**Attention and salience.** What stands out (visually salient) becomes figure; what doesn't, becomes ground.

**Affordance.** Interactive elements typically read as figure (they invite attention and action); non-interactive elements should read as ground.

## Sources informing this principle

- Rubin, E. (1915). *Synsoplevede Figurer* (Visually Experienced Figures). His doctoral dissertation introducing the figure-ground concept.
- Wertheimer, M. (1923). Untersuchungen zur Lehre von der Gestalt II.
- Köhler, W. (1922). On the role of color and brightness in figure-ground perception.
- Palmer, S. E. (1999). *Vision Science: Photons to Phenomenology*.
- Ware, C. (2012). *Information Visualization: Perception for Design*.
- Lidwell, W., Holden, K., & Butler, J. (2003). *Universal Principles of Design*.
- Material Design (Google) elevation specifications.
- Apple Human Interface Guidelines on layering and modality.
