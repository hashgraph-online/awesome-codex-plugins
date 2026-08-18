# Roguelike Procgen and AI Patterns

Use this file when implementing map generation, visibility, pathfinding, or
simple tactical monster behavior.

## Map Builder Result

```rust
struct BuiltLevel {
    map: Map,
    player_start: Point,
    exit: Option<Point>,
    goal_item: Option<Point>,
    spawn_points: Vec<Point>,
}
```

Rules:

- Return all placement decisions from the builder.
- Do not spawn ECS entities directly inside low-level terrain algorithms.
- Keep generated spawn points walkable, reachable, and non-overlapping.
- Store enough metadata for next-level transitions or victory placement.

## Generator Interface

```rust
trait MapArchitect {
    fn build(&mut self, rng: &mut Rng) -> BuiltLevel;
}
```

Good generator candidates:

- Rooms and corridors for designed-looking dungeons.
- Cellular automata for organic caves, forests, or ruins.
- Drunkard's walk for winding caverns.
- Prefabs for hand-authored set pieces.
- Theme-specific builders for maps that need different visual language.

## Generator Validation

- Verify the player start is walkable.
- Verify exit or goal is reachable.
- Verify spawn points are reachable and inside bounds.
- Verify enough floor area exists for the intended content.
- Add a maximum-iteration guard for random algorithms.
- Prefer deterministic seeds in tests and debug output.

## Output Harness Pattern

Create a small harness when tuning generators:

- Build one map from a chosen generator and seed.
- Render it without starting the full game.
- Optionally save text, image, or snapshot output.
- Run multiple seeds and summarize failure rates.
- Keep harness code outside the shipping gameplay loop.

## FOV Rules

- Add an opacity function to the map adapter.
- Store visible tiles in a set-like collection.
- Recompute FOV only when position, radius, or map opacity changes.
- Mark FOV dirty after movement or map mutation.
- Render only currently visible tiles for entities the player can see.
- Store explored tiles separately from currently visible tiles.

## Spatial Memory

Use memory to separate "seen before" from "visible now":

| State | Rendering | Gameplay meaning |
|---|---|---|
| Unknown | Hidden | Player has not discovered this tile |
| Remembered | Dim or muted | Player saw it before, but it may be stale |
| Visible | Full brightness | Player can currently perceive it |

## Pathfinding and AI

- Implement or adapt the map traits/functions required by the pathfinding
  library.
- Make passability and opacity separate; windows, doors, and bars may differ.
- Use Dijkstra maps or equivalent distance fields when many monsters chase the
  same target.
- Use A* or single-target search when one entity needs one route.
- Gate chase behavior on FOV if monsters should not be omniscient.
- Let monsters lose target lock if the player leaves sight unless the design
  intentionally includes memory or scent.

## Review Checklist

- [ ] Every generator implements the same interface.
- [ ] Generated maps are validated before play starts.
- [ ] Random loops have termination guards.
- [ ] FOV is recalculated only when dirty.
- [ ] Passability and opacity are not treated as the same concept.
- [ ] Monster AI uses perception rules rather than global player position by
      default.
- [ ] Generator output can be inspected without playing the whole game.

## Common Smells

| Smell | Fix |
|---|---|
| Player can spawn sealed in a room | Run reachability validation |
| Generator tuning requires manual play | Add output harness or snapshots |
| Monsters always know the player location | Gate target acquisition through FOV |
| FOV recalculates every frame for all entities | Add dirty flags |
| Algorithm-specific data leaks everywhere | Return a common `BuiltLevel` |
