# Fitts's Law: research and formulations

A reference complementing `fitts-law` SKILL.md with the academic grounding, common formulations, and the conditions under which the law applies.

## The original paper

**Fitts, P. M.** (1954). "The information capacity of the human motor system in controlling the amplitude of movement." *Journal of Experimental Psychology*, 47(6), 381–391.

Fitts's setup was a peg-in-hole task: subjects moved a stylus between two targets of varying width and varying separation. He measured movement time across many target combinations and found a linear relationship between movement time and the *index of difficulty*:

```
ID = log₂(2D / W)
T = a + b · ID
```

Where D is distance and W is target width. The information-theoretic interpretation (Fitts was working in the heyday of Shannon's information theory): the index of difficulty measures the "bits" of information required to specify a target's position with the precision needed to hit it.

## Modern formulations

Several refinements have emerged since 1954:

### MacKenzie's Shannon formulation (1992)

```
T = a + b · log₂(D / W + 1)
```

The "+1" eliminates negative ID values when W > D and better matches data when targets are very large or very close. This is the form most commonly cited in HCI literature now.

### Welford's formulation (1968)

```
T = a + b · log₂(D / W + 0.5)
```

A precursor to MacKenzie's; rarely used in current HCI work but still appears in motor-control literature.

### Effective width

A practical refinement: in real tasks, users sometimes hit slightly outside the target boundary. Computing W from actual hit distribution (effective width) rather than nominal target width gives more accurate Fitts's Law fits. Used in HCI experimental studies.

## Conditions under which Fitts's Law applies

The classic Fitts's task assumes:

- **A single, aimed movement** with a known starting point and known target.
- **Visual targets** that are unambiguous (clear edges, single color).
- **Practiced users** — not the first time they've used the device.
- **Indoor, controlled lighting and ergonomics.**
- **Discrete tap/select actions**, not continuous motion.

When these conditions hold (most software UI), Fitts's Law predicts movement time with high reliability. When they don't (drag operations, very small/distant targets, novel input devices), the law still applies but constants change and data fits become noisier.

## Cross-input findings

Fitts's Law has been validated across:

- Mouse (the original HCI domain).
- Trackpad — slightly higher constants (slower than mouse).
- Touchscreen (finger) — much larger W minimums, generally faster traversal because no fine positioning before final approach.
- Stylus on tablet — closer to mouse performance with smaller W minimums.
- Eye-tracking — applies, but with different constants and a saccade-vs.-fixation dynamic.
- Mid-air gesture (VR controllers, leap motion) — applies; constants vary by display geometry.

## Quantitative findings

A few useful numbers:

- For a typical desktop mouse, the constant `b` is roughly 100 ms/bit. So an ID of 4 bits (e.g., D = 480 px, W = 30 px → ID = log₂(480/30 + 1) ≈ 4.04) → ~400 ms additional time beyond the base latency.
- Touch is roughly comparable in `b` but with much larger W minimums (~44 px).
- Constants `a` (base latency) range from ~200 ms (mouse, practiced) to ~500 ms (touch with mode-switch).

These numbers aren't exact but they're useful for back-of-envelope estimation.

## When Fitts's Law underpredicts time

- **First-time users.** They don't know where the target is; they spend time searching, not aiming.
- **Mode-switching.** Users moving from typing to mousing pay a "homing" cost not captured in Fitts.
- **Cognitive evaluation of which target.** When the user must read several similar buttons to decide, that reading time isn't Fitts time.
- **Very small targets** (< 10 px). Users overshoot, undershoot, and re-aim — error correction multiplies time.

## Cross-domain examples

### Industrial control panels

Aircraft, automotive, and industrial machinery design have applied Fitts-like principles since long before HCI: critical controls (throttle, brake, emergency stop) are large and at predictable locations; secondary controls are smaller; rare controls are tucked away.

The cockpit "throttle quadrant" arrangement of throttle, mixture, and prop controls has lived through many aircraft generations because the ergonomic rationale is Fitts-grounded.

### Car dashboards

Climate controls, radio, gear lever — sized and placed for operation while driving. Tesla's all-touchscreen approach (eliminating physical controls) has been criticized in part because it forfeits Fitts's Law: physical knobs have edges that the finger can find by feel; touch buttons require visual attention away from the road.

### Sports equipment

A baseball bat's "sweet spot" is in some sense a Fitts problem inverted: you want a *wide* effective target. Bat designs over a century have crept toward shapes that maximize the sweet spot's effective width.

## Resources

- **Fitts, P. M.** (1954). The original paper, available in many HCI anthologies.
- **MacKenzie, I. S.** (1992). "Fitts' law as a research and design tool in human-computer interaction." *Human-Computer Interaction*, 7, 91–139. The standard modern reference.
- **Card, S. K., Moran, T. P., Newell, A.** (1983). *The Psychology of Human-Computer Interaction*.
- **Soukoreff, R. W. & MacKenzie, I. S.** (2004). "Towards a standard for pointing device evaluation." *International Journal of Human-Computer Studies*. Methodology paper for Fitts's experiments.

## Closing

Fitts's Law is one of the most rigorously-validated quantitative laws in HCI — it has held up across input modalities, body parts, displays, and decades. When in doubt about a target sizing or placement decision, the law usually has the answer.
