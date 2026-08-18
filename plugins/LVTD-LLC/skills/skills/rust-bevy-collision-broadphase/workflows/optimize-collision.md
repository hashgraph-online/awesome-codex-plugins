# Optimize Collision Workflow

Use this workflow when collision checks are a measurable frame-time bottleneck
or when entity counts are expected to grow.

## Prerequisites

- A runnable Bevy scene or isolated collision crate.
- A representative entity-count scenario.
- Existing tests or a small deterministic harness.

**Reference**: `references/broadphase-patterns.md`

## Workflow Steps

### Step 1: Measure the Baseline

**Goal**: Confirm collision is the hot path.

- [ ] Record frame time or benchmark timing for the current implementation.
- [ ] Capture entity counts, map size, and movement speeds.
- [ ] Identify whether time is spent in broadphase, narrowphase, or response.

### Step 2: Freeze Expected Behavior

**Goal**: Prevent optimization from changing gameplay.

- [ ] Add tests for overlap, no-overlap, edge touch, and corner touch.
- [ ] Add a test for layer filtering.
- [ ] Add a test for despawn/removal behavior if entities are short-lived.

### Step 3: Choose the Broadphase

**Goal**: Pick the minimum structure that addresses the measured shape.

- [ ] Keep brute force if the hot scenario is small.
- [ ] Use a spatial hash for uniform grid-like distribution.
- [ ] Use a quad tree when objects cluster or empty space dominates.
- [ ] Add swept bounds or substeps first if misses come from fast movement.

### Step 4: Split Detection From Response

**Goal**: Keep performance work isolated.

- [ ] Emit candidate pairs from broadphase.
- [ ] Confirm candidates in narrowphase.
- [ ] Move damage, sound, score, despawn, and particles to response systems.

### Step 5: Verify and Benchmark

**Goal**: Prove the change helped.

- [ ] Run the behavior tests.
- [ ] Run the same benchmark as Step 1.
- [ ] Compare candidate count, confirmed collision count, and elapsed time.
- [ ] Document the threshold where the new broadphase becomes worthwhile.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Optimizing without a hot scenario | Can add complexity for no gain | Measure first |
| Indexing sprite rectangles | Couples art changes to physics | Store collider components |
| Resolving during detection | Makes ordering bugs likely | Emit events and respond later |
| Ignoring fast movement | Broadphase still misses thin objects | Use swept bounds or fixed substeps |

## Exit Criteria

Task is complete when:

- [ ] Behavior tests pass.
- [ ] Collision response is not embedded in broadphase code.
- [ ] Benchmark results show the improvement or justify keeping the simple path.
