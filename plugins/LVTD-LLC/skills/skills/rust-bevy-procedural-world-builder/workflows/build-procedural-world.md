# Build Procedural World Workflow

Use this workflow when adding generated levels, rooms, bases, terrain, or
resource placement to a Bevy game.

## Prerequisites

- Gameplay constraints for a valid world.
- Desired map size, seed policy, and spawn rules.
- Target performance budget for generation and materialization.

**Reference**: `references/procedural-world-patterns.md`

## Workflow Steps

### Step 1: Define World Data

**Goal**: Make generation independent from rendering.

- [ ] Create plain Rust structs for tiles, rooms, resources, and spawn points.
- [ ] Include seed and generation parameters in the data or metadata.
- [ ] Add indexing helpers with bounds checks.

### Step 2: Generate With Reproducibility

**Goal**: Make bugs replayable.

- [ ] Accept a seed or generate one and log it.
- [ ] Keep generation parameters explicit.
- [ ] Add tests for known seeds and tiny map sizes.

### Step 3: Validate Constraints

**Goal**: Prevent unwinnable or broken worlds.

- [ ] Check player start and required exits are in bounds.
- [ ] Check reachability for critical areas.
- [ ] Check resource, enemy, or objective placement rules.
- [ ] Use bounded retries or structured errors for failures.

### Step 4: Materialize in Bevy

**Goal**: Spawn validated data safely.

- [ ] Convert world data into entities in setup, chunks, or batches.
- [ ] Attach cleanup/chunk markers to spawned entities.
- [ ] Keep generated data resource available for collision, AI, or minimaps.

### Step 5: Optimize the Right Cost

**Goal**: Avoid optimizing the wrong subsystem.

- [ ] Measure data generation time.
- [ ] Measure entity spawn/materialization time.
- [ ] Measure rendering/frame-time impact after spawning.
- [ ] Move only plain data generation to background tasks if needed.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Spawning while generating | Hard to test and hard to thread | Generate data first |
| Hidden random seed | Bugs cannot be reproduced | Log seed and parameters |
| No reachability checks | Worlds can be unwinnable | Validate before spawn |
| Background `Commands` | Violates Bevy world ownership | Send plain data back |

## Exit Criteria

- [ ] Generator output is reproducible.
- [ ] Invalid worlds are caught before gameplay starts.
- [ ] Bevy entity spawning is separate from generation logic.
