# Stabilize Physics Workflow

Use this workflow when Bevy movement or collision behavior changes with frame
rate or becomes unreliable at high speed.

## Prerequisites

- A reproduction scene or movement test.
- Target Bevy version and schedule names.
- Known movement speeds and collision shapes.

**Reference**: `references/fixed-step-patterns.md`

## Workflow Steps

### Step 1: Reproduce and Measure

**Goal**: Confirm the failure mode.

- [ ] Run the scene at different frame-rate limits if possible.
- [ ] Record movement distance over the same wall-clock duration.
- [ ] Record whether misses happen only at high speed.

### Step 2: Separate Input From Simulation

**Goal**: Avoid losing responsiveness while stabilizing simulation.

- [ ] Sample input in the regular update schedule.
- [ ] Store input as intent.
- [ ] Consume intent in fixed-step simulation.

### Step 3: Make Movement Explicit

**Goal**: Remove hidden movement side effects.

- [ ] Add velocity or acceleration components.
- [ ] Apply fixed delta in the fixed-step system.
- [ ] Predict the next position before mutating authoritative transforms.

### Step 4: Handle Collision Reliability

**Goal**: Stop fast movers from tunneling.

- [ ] Add swept checks, substeps, or fixed collision prediction.
- [ ] Emit collision events for response systems.
- [ ] Keep deterministic pair and response ordering where needed.

### Step 5: Smooth Presentation

**Goal**: Improve feel without breaking simulation.

- [ ] Add interpolation or tweening on visual entities only.
- [ ] Keep authoritative physics state unchanged by presentation smoothing.
- [ ] Smoke test camera, sprite, and particle behavior.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Using render delta for physics | Behavior changes with FPS | Use fixed delta |
| Animation owns transform | Visual polish changes gameplay | Separate authority and presentation |
| End-position collision only | Fast movers tunnel | Sweep or substep |

## Exit Criteria

- [ ] Movement distance is stable across frame-rate changes.
- [ ] Collision misses are addressed or bounded by tests.
- [ ] Presentation smoothing does not mutate physics authority.
