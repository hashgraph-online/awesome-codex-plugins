# Behavioral mimicry — animation timing

Practical guidance on calibrating the timing and physics of animations so they mimic physical behavior helpfully without slowing the interaction down.

## Standard timings

A useful starting set, drawn from years of platform design guidelines (Apple, Google, etc.):

- **Micro-interactions: 100–200ms.** Button hover, focus state, small color shifts. Fast enough that users don't perceive a delay.
- **State transitions: 200–300ms.** Panel expansion, tab switch, modal appearance. Long enough to communicate the transition; short enough to not slow frequent interactions.
- **Major state changes: 400–500ms.** Full-screen transitions, navigation between sections. Long enough for the user to track what changed.
- **Page-level transitions: 500–800ms.** Loading states, route changes. Reserved for less-frequent interactions where the user benefits from clear acknowledgment.

These are starting points, not absolutes. Specific products may need different timing based on the audience, the frequency of interaction, and the device class.

## Easing curves

The shape of the animation matters as much as its duration.

- **Linear:** moves at constant speed. Feels mechanical; rarely the right choice for physical mimicry.
- **Ease-in:** starts slow, accelerates. Mimics objects starting from rest.
- **Ease-out:** starts fast, decelerates. Mimics objects coming to a stop. Often the most "natural" feeling for UI transitions.
- **Ease-in-out:** slow at both ends, fast in the middle. Mimics objects in transit between stable positions. Standard for many UI transitions.
- **Spring/bounce:** overshoots the target slightly and settles back. Mimics elastic or playful behavior. Used for emphasis or for explicitly-physical metaphors (rubber-band scroll).

Pick a small set of curves and apply them consistently. Inconsistent easing is one of the easiest signs of an under-designed motion system.

## Physical metaphors and their timing

Different physical metaphors call for different timings.

**Falling/dropping:** ease-in (gravity accelerates). Brief — physical objects fall quickly. 200–300ms.

**Sliding (low friction):** ease-out (object slides and decelerates). 250–400ms depending on distance.

**Sliding (high friction):** linear or ease-in (object resists motion). Slower, 400–600ms. Use for "heavy" interactions where the user should feel the weight.

**Bouncing/elastic:** spring with some overshoot. 300–500ms total, with the overshoot being a small fraction.

**Rotating:** linear or ease-in-out depending on the metaphor. Wheels and dials usually have momentum (ease-out); fixed rotations (page-turn) usually use ease-in-out.

**Fading:** linear or ease-out. Fades are often ambient and shouldn't draw attention to themselves; linear is fine.

## Pacing for repeated interactions

The most important calibration question: how often will this interaction happen?

For interactions a user will perform many times per session (sending a message, scrolling a list, switching tabs), the animation should be short — under 200ms ideally, and certainly under 300ms. Even tiny delays accumulate over hundreds of interactions per session.

For interactions performed occasionally (opening a settings panel, switching pages, completing a checkout), the animation can afford to be longer — up to 500ms or more — because the cost is paid once and the additional clarity may be worth it.

For interactions performed rarely (onboarding, completing a major milestone), the animation can be much longer (500ms to 2s) and can include richer choreography because the moment deserves emphasis.

## When animation is too slow

Signs that animations are slowing the interaction down:

- Users complain about the product "feeling slow" even when measured task times are fast.
- Users develop habits like clicking the same button twice (because the first click's animation made them think nothing happened).
- Power users ask for an option to disable animations.
- Heavy users start using keyboard shortcuts to bypass UI animations.

If you see these signs, audit your animation timing. Cutting all animations by 30% often produces dramatic perceived-speed improvements with no loss of clarity.

## When animation is too fast

Signs that animations are too snappy:

- Users miss state changes (didn't notice the panel opened).
- Users think the system did the wrong thing because they didn't see the transition.
- Users have trouble tracking what changed during major state shifts.

If you see these signs, the animations need to slow down enough to be perceived. The fix is usually adding 100–200ms to specific transitions, not all of them.

## Reduced motion

Many users have accessibility settings for reduced motion (avoiding triggering vestibular issues or simply preferring less animation). Honor these settings: when reduced motion is requested, replace bounce/spring/elaborate transitions with simple fades or instant changes.

The reduced-motion path should still be considered designed, not just "no animation." A clean fade conveys state change clearly; an instant snap with no transition can be jarring.

## Anti-patterns

**Same timing for everything.** Picking 500ms as the global animation timing and applying it to micro-interactions, transitions, and major state changes alike. Frequent interactions feel slow; rare ones feel rushed.

**Inconsistent easing.** Some animations are ease-out, others spring, others linear, with no apparent pattern. The motion system feels patched together.

**Overlapping animations that compound.** Multiple animations triggered in close succession that all run on top of each other, creating visual chaos. Sequence them or simplify.

**Animations that aren't interruptible.** A 500ms transition that locks user input until it completes. Frequent users get frustrated by being unable to act during the animation. Animations should generally be interruptible — if the user clicks something else mid-animation, the previous animation should snap to its end and the new one should begin.

**Bouncing things that don't need to bounce.** Spring/bounce animations are fun in moderation but visually noisy in excess. Reserve them for moments that warrant emphasis.

**Ignoring reduced-motion preferences.** Users who've set accessibility preferences shouldn't be forced through your animations. Honor the settings and provide a designed experience for the reduced-motion path.

## Test pattern

Record your interface during normal use. Watch the recording at 0.5x speed. Are there animations that are unnecessarily long? At 2x speed, do you miss transitions? The right calibration is somewhere in between.

Then have someone use the product who hasn't seen it. Watch their face. If they're squinting or pausing during transitions, things may be too slow. If they're clicking the same button twice or asking what happened, things may be too fast.

## Cross-reference

For the parent principle on mimicking physical behavior, see `mimicry-behavioral`. For animation as feedback design, see `feedback-loop-states-and-latency`.
