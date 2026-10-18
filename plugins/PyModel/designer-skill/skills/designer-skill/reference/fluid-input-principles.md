# Fluid Input Principles

Interfaces feel fluid when they respond to the *gesture*, not to the gesture's completion. These principles come from public interface-design teaching — Apple's "Designing Fluid Interfaces" (WWDC 2018) is the canonical articulation — translated here for web and cross-platform work. Timing values, curves and spring parameters live in `motion-and-interaction`; this file owns when and how interaction connects to motion.

## 1. Respond during input, not after it

Feedback begins at `pointerdown`, not `click`. The click event fires on release, so any visual response bound to it lands a perceptible beat after the finger lands. Practical form:

- Press states (`scale`, shadow, highlight) on `:active` / `pointerdown`; the full action still commits on click/activation semantics — do not move *commitment* to pointer-down, only *acknowledgment*.
- Keyboard equivalents respond on keydown where the platform does (held keys, continuous actions).
- Never let the acknowledgment wait on async work: acknowledge instantly, then resolve (optimistic UI belongs to `ux/22-performance-ux`).

The acknowledgment is not the action: committing destructive work on pointer-down causes accidental activation. Acknowledge early, commit on the standard activation event.

## 2. Continuity: one object, many states

An element is the *same object* across its states — a card becomes a detail view, a thumbnail becomes a lightbox — and the transition should read as movement of that object, not an exit plus an unrelated entrance. Prefer transitions that preserve identity: shared-element/`layout` transitions, morphing the actual element, animating from the trigger's position (`transform-origin` set to the anchor). When the platform lacks shared-element support, fade-and-move the new state from the old one's anchor rather than popping it at the center. Discrete jumps force the user to re-anchor; continuity is what makes an interface feel physical.

## 3. Inherit velocity

A gesture's speed belongs to the resulting motion. Release a drag while moving fast, and the element continues in that direction (with the gesture's velocity as its initial velocity); release slow or reverse, and it returns. Where springs are available, feed the tracked velocity into the spring rather than starting it from rest — this is the single largest difference between "animated" and "physical". Velocity thresholds decide outcomes (dismiss past the threshold *or* flung fast enough), per the gesture rules in `motion-and-interaction`.

## 4. Design for interruption

Real users do not wait for animations. Every transition must be:

- **Retargetable** — a new input mid-flight redirects the motion instead of queueing behind it. CSS transitions retarget naturally; keyframe animations and JS timelines that restart from zero do not. For rapidly re-triggered UI (toggles, toasts, hovers) use transitions or springs that accept new targets.
- **Reversible** — interrupting an entrance with a dismissal starts from the current position, not the origin. Springs give this for free (they keep velocity across interruption); durations-based systems need explicit from-current-value handling.
- **Non-blocking** — an animation never gates the interaction: pointer events stay live, and no `animationend` listener stands between the user and a state the UI could show now. Essential state changes must not depend on animation events (reduced-motion and failures drop them).

## 5. Springs when interruption matters

Springs settle on physical parameters (stiffness/damping) rather than a fixed duration, which is exactly why they interrupt well: the target can change mid-flight and the motion re-plans without a seam. Use them for gesture-driven and interruptible motion; duration-based easing remains fine for fire-and-forget feedback (the choice and parameters: `motion-and-interaction` §5). Test interruption explicitly: trigger, reverse, re-trigger in quick succession and confirm no jump, queue, or dead state.

## Verification

Each principle is observable: press feedback precedes release; transitioned elements land where the gesture left them; interrupted motion continues from its current position. These are rendered checks — record them with the same evidence discipline as any visual claim, and mark them not-run when no browser or device is available.
