# Add State Flow Workflow

Use this workflow when adding or repairing Bevy menu, loading, pause, playing,
or game-over states.

## Prerequisites

- Current Bevy version.
- Existing app/plugin setup.
- Desired states and transition triggers.

**Reference**: `references/state-flow-patterns.md`

## Workflow Steps

### Step 1: Name the Phases

**Goal**: Avoid encoding state as scattered booleans.

- [ ] List player-visible phases.
- [ ] Decide which phases are app states and which are subsystem details.
- [ ] Define the initial state.

### Step 2: Register State and Plugins

**Goal**: Make scheduling boundaries explicit.

- [ ] Add the state enum.
- [ ] Register feature plugins that own their setup/update/cleanup systems.
- [ ] Add run conditions to update systems.

### Step 3: Add Entry and Exit Systems

**Goal**: Ensure each phase owns its entities.

- [ ] Move phase setup into `OnEnter`.
- [ ] Add cleanup markers to spawned phase-owned entities.
- [ ] Despawn those entities in `OnExit`.
- [ ] Reset or preserve resources intentionally.

### Step 4: Wire Transitions

**Goal**: Keep transitions readable and testable.

- [ ] Convert input, UI button, win/loss, and asset-ready conditions into
      explicit transition points.
- [ ] Keep transition systems small.
- [ ] Avoid changing state from unrelated rendering or animation systems.

### Step 5: Verify Re-entry

**Goal**: Catch leaks and duplicate entities.

- [ ] Enter and exit every state at least twice.
- [ ] Confirm UI and gameplay entities are cleaned up.
- [ ] Confirm persistent resources are not reinitialized accidentally.

## Common Mistakes

| Mistake | Why it hurts | Do instead |
|---------|--------------|------------|
| Boolean phase flags | Systems disagree about current phase | Use state scheduling |
| No cleanup marker | Old entities survive transitions | Mark and despawn on exit |
| Transition logic everywhere | Hard to reason about flow | Centralize small transition systems |

## Exit Criteria

- [ ] State enum covers the intended phases.
- [ ] Each phase has entry, update, and exit behavior where needed.
- [ ] Repeated transitions do not leak or duplicate entities.
