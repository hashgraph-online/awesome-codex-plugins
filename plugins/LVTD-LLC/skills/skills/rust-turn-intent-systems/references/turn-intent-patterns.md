# Turn and Intent System Patterns

Use this file when implementing tactical turns, action order, or decoupled
input/AI resolution.

## Turn State Shape

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum TurnState {
    AwaitingInput,
    PlayerTurn,
    MonsterTurn,
    GameOver,
    Victory,
}
```

Rules:

- Use one enum for mutually exclusive phases.
- Keep terminal states explicit.
- Do not let input systems run during monster resolution.
- Do not let monsters move while awaiting player input.
- Advance state from one end-turn system or function.

## Phase Scheduling

| Phase | Systems to run | Notes |
|---|---|---|
| AwaitingInput | input, render, UI | Input may create player intents |
| PlayerTurn | combat, movement, item use, end turn, render | Resolve player-created intents |
| MonsterTurn | AI intent creation, combat, movement, end turn, render | Resolve monster-created intents |
| GameOver | result screen, restart input | Do not run world simulation |
| Victory | result screen, next-level/restart input | Do not run world simulation |

## Intent Components

```rust
struct WantsToMove {
    entity: Entity,
    destination: Point,
}

struct WantsToAttack {
    attacker: Entity,
    victim: Entity,
}

struct WantsToUseItem {
    user: Entity,
    item: Entity,
}
```

Intent rules:

- Decision systems create intents.
- Resolution systems consume intents.
- Store enough data to resolve the action without re-reading input.
- Delete or clear intents after processing.
- Prefer one shared movement system over separate player and monster movement
  implementations.

## Resolution Order

Use explicit ordering when systems depend on one another:

1. Input or AI creates intents.
2. Combat intent resolves attacks that should happen before movement.
3. Movement intent moves valid entities.
4. Item use applies effects and removes consumed items.
5. Death cleanup removes entities with no health.
6. Win/loss detection updates turn state.
7. End-turn system advances to the next phase.

Adjust order to match the game's rules, but keep it documented in the schedule.

## Wait Actions

Waiting is an action, not a missing input.

- Add an explicit wait key or AI wait decision.
- Let waiting create a phase transition just like movement.
- If waiting heals, recharges, or consumes time, put that logic in a system.
- Ensure waiting cannot bypass danger unless that is an intentional rule.

## Win and Loss States

- Detect player death after combat/death cleanup.
- Detect victory after movement or pickup resolution.
- Use terminal turn states to show game over or victory screens.
- Reset the world through a single reset path.

## Review Checklist

- [ ] Turn phases are represented by one enum or state machine.
- [ ] Input cannot resolve movement directly when intents are expected.
- [ ] AI and player actions share resolution systems.
- [ ] Intents are removed after processing.
- [ ] Schedule order matches the game's stated rules.
- [ ] Win/loss detection cannot be skipped by phase ordering.
- [ ] Restart/reset clears stale intents and world state.

## Common Smells

| Smell | Fix |
|---|---|
| Player movement and monster movement duplicate collision rules | Emit shared `WantsToMove` intents |
| Intent persists for multiple turns | Delete intent after resolution |
| Systems run in every phase | Split schedules or branch by `TurnState` |
| Game over still simulates monsters | Add terminal state routing |
| Wait key does nothing observable | Model wait as an action with rules |
