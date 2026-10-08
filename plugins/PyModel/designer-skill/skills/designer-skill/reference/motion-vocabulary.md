# Motion Vocabulary

Reverse lookup: the user describes a motion by feel ("the bouncy thing when the popover opens"); this maps the description to the standard term to search for, implement, or request. Terms are generic industry vocabulary; implementations and values live in `motion-and-interaction`.

| The user says | Standard term | Notes |
| --- | --- | --- |
| "The bouncy/wobbly thing when it opens" | **Overshoot / spring with bounce** | Element passes its target and settles back; implement as a spring, keep bounce subtle |
| "It just slides in" / "pushes the page" | **Slide / push transition** | Direction should match the spatial model (drawer from its edge, page push mirrors navigation) |
| "It fades away" / "dissolves" | **Fade / crossfade** | Crossfade = two states blend; a pure fade to nothing is an exit |
| "It grows out of the button" | **Anchor/origin scale** (scale from trigger) | `transform-origin` at the trigger; the default center origin is usually the bug |
| "The card becomes the page" | **Shared-element / container transform** | One element morphs across states; also "morph" |
| "Things pop in one after another" | **Stagger** | Sequential delay per item; keep total time bounded as lists grow |
| "It shakes when I get it wrong" | **Shake / nudge (error feedback)** | Short horizontal oscillation; pair with a message — motion alone is not an error message |
| "The number rolls up" | **Count-up / ticker** | Numeric interpolation; avoid for values that change faster than they animate |
| "It glimmers while loading" | **Shimmer / skeleton** | Placeholder animation; pair with `ux/22-performance-ux` loading states |
| "The background moves slower" | **Parallax** | Layered scroll speeds; decorative — passes the frequency gate or not at all |
| "It snaps into place" | **Settle / magnetic snap** | Motion ends aligned to a grid or anchor; often a spring with high damping |
| "It stretches when I pull and springs back" | **Rubber-band / elastic overscroll** | Resistance past a boundary with spring return; never a hard wall |
| "You can flick it away" | **Swipe-to-dismiss (velocity gesture)** | Dismiss on distance *or* velocity; see gestures in `motion-and-interaction` |
| "The circle expands from where I tapped" | **Ripple / origin reveal** | Feedback anchored at the interaction point |
| "Everything goes blurry and sharpens" | **Blur focus pull** | Depth cue via `filter: blur()`; keep radius bounded (expensive) |
| "The bar fills as you scroll" | **Scroll progress indicator** | Scroll-linked, read-only; `animation-timeline: scroll()` or equivalent |
| "It wobbles when hovering, kind of alive" | **Hover-tracking spring** | Decorative pointer-follow via spring; frequency gate applies |
| "The two screens slide over each other" | **Parallax header / layered transition** | Foreground and background at different rates |
| "It spins forever" | **Indeterminate spinner** | Reserve for genuinely unbounded waits; prefer progress when measurable |
| "The page flips / rotates" | **3D flip (rotateY + preserve-3d)** | High-attention move; overdrive verification applies |

## Using the lookup

- Match the *feel* first, then verify the term against what the interaction must communicate — a named term is a search key, not a design decision. The decision gates (frequency, purpose) in `motion-and-interaction` still apply to whatever the term turns out to be.
- When the user's word has no row, ask for the closest named experience they remember from any app; translating between their words and platform-standard terms is the point of this table.
- Implement the resolved term with the project's existing motion primitives before reaching for a new library (`dependency-selection`); a term naming a library-specific effect ("like Vaul's drawer") is a pointer to behavior, not an instruction to install that library.
