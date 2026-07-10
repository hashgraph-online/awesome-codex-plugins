# Broadphase Patterns

Core concepts and review checks for 2D Bevy collision broadphases.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| Collider | Minimal gameplay shape used for collision, independent of sprite art. |
| AABB | Axis-aligned bounding box used for cheap overlap tests. |
| Broadphase | Fast pass that produces likely collision pairs. |
| Narrowphase | Accurate pass that confirms or rejects broadphase candidates. |
| Collision layer | Filter that prevents irrelevant pairs from being checked. |
| Swept bounds | Bounds covering both current and predicted position for fast movers. |

## Core Rules

1. Keep detection and response separate.
   - Detection emits candidates or confirmed collisions.
   - Response applies damage, bounce, despawn, score, sound, or particles.
2. Use the simplest broadphase that removes the measured bottleneck.
   - Brute force is acceptable for small counts.
   - Spatial hashes work well when positions distribute across a grid.
   - Quad trees work well when objects cluster unevenly.
3. Store collider data in components that do not depend on rendering assets.
4. Filter by layer before expensive shape checks.
5. Make pair ordering deterministic when gameplay depends on repeatable output.
6. Remove despawned entities from indexes before emitting events.
7. Benchmark the hot scenario, not a tiny test scene.

## Pattern: Collider Component

```rust
#[derive(Component, Clone, Copy)]
struct Collider {
    half_size: Vec2,
    layer: CollisionLayer,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum CollisionLayer {
    Player,
    Enemy,
    Terrain,
    Pickup,
}
```

Use this pattern when the sprite dimensions are not the real collision shape or
when layers must be filtered before pair testing.

## Pattern: Candidate Events

```rust
#[derive(Event)]
struct CollisionCandidate {
    a: Entity,
    b: Entity,
}

#[derive(Event)]
struct CollisionConfirmed {
    a: Entity,
    b: Entity,
    normal: Vec2,
}
```

Emit candidates from broadphase systems and confirmed collisions from
narrowphase systems. Gameplay systems should consume confirmed events.

## Pattern Selection

| Scene shape | First choice |
|-------------|--------------|
| Under a few dozen colliders | Brute force with good tests |
| Large tile-aligned world | Spatial hash keyed by grid cell |
| Large clustered object set | Quad tree or bounding volume tree |
| Very fast movers | Swept AABB or fixed substeps before index tuning |

## Review Checklist

- [ ] Collision shapes are explicit and not inferred from sprite art at runtime.
- [ ] Broadphase produces candidate pairs without gameplay side effects.
- [ ] Narrowphase owns precise overlap tests.
- [ ] Collision layers skip impossible pairs early.
- [ ] Tests cover touching edges, corners, no-overlap, and despawned entities.
- [ ] Benchmarks include the highest expected obstacle/projectile counts.
