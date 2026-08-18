# Build Asset Pipeline Workflow

Use this workflow when a Bevy game needs a reliable asset catalog, loading
state, or release resource check.

## Prerequisites

- Current asset folder layout.
- List of gameplay states that need assets.
- Target Bevy version.

**Reference**: `references/asset-pipeline-patterns.md`

## Workflow Steps

### Step 1: Inventory Assets

**Goal**: Know what must load before gameplay.

- [ ] List sprites, atlases, fonts, audio, music, shaders, and data files.
- [ ] Mark required startup assets versus lazy/level-specific assets.
- [ ] Record license or attribution files that must ship.

### Step 2: Create the Catalog

**Goal**: Replace scattered paths with typed fields.

- [ ] Add a resource for core handles.
- [ ] Load handles in one setup or loading-system path.
- [ ] Keep atlas frame metadata near the atlas handle.
- [ ] Remove duplicate `asset_server.load` calls from gameplay systems.

### Step 3: Gate State Transitions

**Goal**: Prevent gameplay from running before required assets are ready.

- [ ] Add or reuse a loading state.
- [ ] Check readiness for required handles and dependencies.
- [ ] Transition only after required assets are loaded.
- [ ] Show progress only if the project has enough assets to justify it.

### Step 4: Validate Runtime Layout

**Goal**: Catch packaging failures early.

- [ ] Run from the expected release working directory.
- [ ] Confirm every required asset resolves.
- [ ] Confirm licenses/credits ship with third-party assets when needed.

### Step 5: Clean Up Call Sites

**Goal**: Make asset ownership obvious.

- [ ] Systems receive handles through resources or spawned components.
- [ ] Tests or smoke checks cover missing-path behavior where practical.
- [ ] Documentation names the asset root used by releases.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Loading from gameplay systems | Hides ownership and repeats path strings | Load into a catalog |
| Treating handles as loaded data | Can advance too early | Check readiness |
| Testing only from repo root | Misses packaged runtime failures | Smoke test release layout |

## Exit Criteria

- [ ] Asset paths have one source of truth.
- [ ] Required handles are ready before dependent gameplay states run.
- [ ] Packaged build can find its resources.
