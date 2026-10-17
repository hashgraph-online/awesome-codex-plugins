# Procedural World Patterns

Patterns for generated world data, validation, and Bevy materialization.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| World data | Plain Rust representation of generated tiles, rooms, resources, or paths. |
| Seed | Reproducible random input for debugging and testing. |
| Constraint validation | Checks that generated worlds satisfy gameplay requirements. |
| Materialization | Spawning Bevy entities from validated generated data. |
| Chunk | Bounded portion of a generated world spawned or despawned together. |
| Background boundary | Thread/task boundary where only plain data crosses back to Bevy. |

## Core Rules

1. Generate data first; spawn Bevy entities second.
2. Make seeds and generation parameters visible in logs or debug UI.
3. Validate reachability and spawn safety before entering gameplay.
4. Keep generated-world tests independent from rendering.
5. Use chunks or batches when a world is too large to spawn in one frame.
6. Do not mutate Bevy `World`, `Commands`, or assets from background threads.
7. Profile generation, entity spawning, and rendering as separate costs.

## Pattern: Plain World Data

```rust
#[derive(Clone, Copy, PartialEq, Eq)]
enum TileKind {
    Empty,
    Floor,
    Wall,
    Resource,
}

struct GeneratedWorld {
    width: u32,
    height: u32,
    seed: u64,
    tiles: Vec<TileKind>,
    player_start: IVec2,
}
```

Plain data makes generation testable and safe to pass across threads.

## Pattern: Validate Before Spawn

```rust
fn validate_world(world: &GeneratedWorld) -> Result<(), WorldGenError> {
    ensure_in_bounds(world.player_start, world)?;
    ensure_reachable_area(world)?;
    ensure_resource_budget(world)?;
    Ok(())
}
```

Validation failures should return structured errors or regenerate with a bounded
retry count.

## Pattern: Background Generation Boundary

```rust
enum WorldGenMessage {
    Ready(GeneratedWorld),
    Failed(WorldGenError),
}
```

Background tasks should produce messages containing plain data or errors. The
main Bevy schedule should receive the data, insert resources, and spawn
entities.

## Review Checklist

- [ ] The generator can reproduce a reported world from seed and parameters.
- [ ] Gameplay constraints are validated before spawning gameplay entities.
- [ ] Background work returns data, not commands or borrowed Bevy state.
- [ ] Large worlds spawn in bounded batches or chunks.
- [ ] Tests cover small maps, impossible constraints, and known seeds.
- [ ] Profiling separates generation time from render/entity costs.
