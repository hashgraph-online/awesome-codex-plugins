# ECS Gameplay Patterns

Use this file when implementing gameplay with entities, components, systems,
resources, and schedules.

## ECS Concepts

| Concept | Role | Rule of thumb |
|---|---|---|
| Entity | Identity for a thing in the world | No behavior by itself |
| Component | Data attached to an entity | Small struct, no game loop ownership |
| System | Logic over matching components | One responsibility |
| Resource | Shared singleton data | Map, camera, input state, turn state |
| Schedule | Ordered system execution | Encode dependencies and flush points |

## Component Rules

- Make components describe capability or state: `Position`, `Renderable`,
  `Health`, `Player`, `Enemy`, `BlocksTile`, `WantsToMove`.
- Keep components plain and easy to clone/debug when practical.
- Use marker components for identity or capability when no fields are needed.
- Avoid putting large engine handles into many components.
- Do not hide game logic inside component methods if systems need to coordinate
  multiple entities.

## Spawner Pattern

```rust
fn spawn_player(world: &mut World, pos: Point) {
    world.push((
        Player,
        pos,
        Renderable { glyph: '@', layer: 1 },
        Health { current: 10, max: 10 },
    ));
}
```

Spawner rules:

- Construct complete entity bundles in one place.
- Keep random selection in the spawner or content layer, not in rendering.
- Use data-driven templates once hard-coded spawn functions start duplicating
  fields.

## System Rules

- Query only the components the system reads or writes.
- Prefer many small systems over one large "update everything" system.
- Give systems names that describe their action: `movement`, `combat`,
  `entity_render`, `map_render`, `end_turn`.
- Use command buffers or deferred commands for structural changes during
  iteration.
- Flush after systems that create/delete entities if the next system must see
  those changes.
- Keep rendering systems read-only where possible.

## Schedule Pattern

```rust
fn build_schedule() -> Schedule {
    Schedule::builder()
        .add_system(input_system())
        .flush()
        .add_system(movement_system())
        .add_system(collision_system())
        .flush()
        .add_system(map_render_system())
        .add_system(entity_render_system())
        .build()
}
```

Adapt the exact API to the ECS crate in use.

## Resource Rules

- Use resources for singleton state shared by systems: map, camera, input,
  random number generator, turn state, asset registry.
- Keep resources small enough to reason about borrowing.
- Avoid using one giant resource as a hidden global game object.
- If many systems mutate the same resource, reconsider ownership or ordering.

## Rendering With ECS

- Terrain rendering often reads a map resource and camera resource.
- Entity rendering usually queries `Position` plus `Renderable`.
- Keep draw commands batched or ordered by layer if the engine supports it.
- UI/HUD systems should read game state, not mutate combat or movement.

## Porting Notes

- Legion: use worlds, resources, queries, systems, schedules, and command
  buffers.
- Bevy ECS: use normal Rust components, resources, schedules, queries, and
  systems through Bevy's APIs.
- Specs/hecs/other ECS crates: preserve the same boundaries even when API names
  differ.

## Review Checklist

- [ ] Every component has a clear data responsibility.
- [ ] Entity construction is centralized in spawners/factories.
- [ ] Systems have narrow read/write sets.
- [ ] Structural changes happen through safe deferred mechanisms where needed.
- [ ] Schedule order explains gameplay dependencies.
- [ ] Rendering systems do not mutate gameplay state.
- [ ] New entity types reuse existing components before adding new systems.

## Common Smells

| Smell | Fix |
|---|---|
| Component contains a whole subsystem | Split data into smaller components/resources |
| One system handles input, movement, combat, and rendering | Split by responsibility |
| Query asks for components it does not use | Narrow the query |
| Entity deletion during iteration causes borrow issues | Use command buffers/deferred commands |
| Same spawn fields repeated everywhere | Introduce templates or spawn helpers |
