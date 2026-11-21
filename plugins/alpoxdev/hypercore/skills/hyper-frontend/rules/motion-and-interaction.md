# Motion and Interaction

Read this rule when the work adds or changes an animation, a transition, a gesture, hover or press feedback, or any behavior that reacts to input. It decides whether motion should exist, how it is built, and how it stays safe. It sets no style; the project's motion tokens and library decide the look.

## Contents

1. Purpose Map
2. Build Rules
3. Safety
4. Responsiveness to Input
5. Dependencies

## 1. Purpose Map

Every animation maps to one row before it is written:

| Trigger | State change | What the user learns |
|---|---|---|
| The user action or system event that starts it | The before and after states | The information the motion carries: feedback, continuity, hierarchy, or progress |

An animation with no row is decoration and is left out. A hover that changes nothing, motion on a non-interactive element, and a looping effect with no informational job are the usual offenders. Subtraction must keep the required content and behavior.

## 2. Build Rules

- Animate properties that do not change layout (`transform`, `opacity`). Animating `width`, `height`, `top`, `left`, or margins moves neighbors and costs layout work every frame; express the same movement as a transform.
- Use the project's duration and easing tokens. When none exist, define them once in the project's token file instead of scattering literals.
- Make transitions interruptible and reversible: reversing mid-flight continues from the current value, and rapid input never leaves a stuck or contradictory state.
- Hover is an enhancement. Information or an action reachable only on hover is unreachable on touch and by keyboard; give it a focus and tap equivalent.
- Keep the DOM order equal to the reading and focus order. Visual reordering with transforms or absolute positioning must not change what keyboard and screen-reader users meet first.

## 3. Safety

- Wrap non-essential motion in `prefers-reduced-motion`. Reduced does not mean removed information: replace a slide with an instant change or a fade, and keep every state change visible.
- Any motion that starts on its own, lasts more than five seconds, and sits beside other content (a carousel, a marquee, a looping background) needs a visible way to pause, stop, or hide it (WCAG 2.2.2).
- Pause or stop continuous effects when they are off-screen or the tab is hidden.
- Nothing flashes more than three times in one second.
- A sticky or fixed element must not hide the focused control; scroll the target into view with margin for it (WCAG 2.4.11).

## 4. Responsiveness to Input

- Acknowledge a press, tap, or key immediately: the next frame shows a pressed, loading, or selected state. A response slower than the interaction budget (200 ms or less is the good INP range) needs visible progress.
- Never block input for the length of an animation. Disable a control only while its action is genuinely pending, and keep its box unchanged ([layout-and-states.md](layout-and-states.md) §5).
- Pointer targets are at least 24 by 24 CSS px, with larger targets for touch (WCAG 2.5.8).
- A drag or swipe has a single-pointer alternative such as a button (WCAG 2.5.7).

## 5. Dependencies

- Reuse the animation approach the project already uses (CSS, the framework's transition API, an installed library). Match its patterns before inventing one.
- Do not add an animation library, shader, or particle dependency unless the request names it. When a heavier effect is requested, say what it costs in bundle size and main-thread work and ask for the budget.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The `prefers-reduced-motion` media feature | <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion> |
| Pause, Stop, Hide for moving content (2.2.2); Target Size (Minimum) (2.5.8); Dragging Movements (2.5.7); Focus Not Obscured (Minimum) (2.4.11); Three Flashes (2.3.1) | <https://www.w3.org/TR/WCAG22/> |
| A good INP is 200 milliseconds or less; a good CLS is 0.1 or less | <https://web.dev/articles/vitals> |
| The purpose map, transform-only motion, interruptibility, and the dependency rule | `dbc-hbin/omp-ulw@74df40f frontend` shared axioms and interaction guidance (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` for the purpose map, the transform-only rule, and the dependency rule: they are this package's chosen defaults, and a project's explicit motion language outranks them. The WCAG, MDN, and web.dev facts are `PRIMARY`. The claim that transform and opacity avoid layout work is stated as a build rule, not cited to a source checked on the date above.
