# Fixed Step Patterns

Patterns for Bevy movement and physics that should not depend on render frame
rate.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| Fixed step | Simulation tick that advances by a constant delta. |
| Authoritative position | Position owned by physics/gameplay, not by animation. |
| Intent | Input-derived desired action consumed by simulation. |
| Swept movement | Collision check across a movement segment, not just at the end. |
| Interpolation | Visual smoothing between previous and current simulation positions. |
| Tweening | Presentation animation over time, separate from simulation authority. |

## Core Rules

1. Apply deterministic movement in fixed-step schedules.
2. Sample input separately from simulation.
3. Store velocity and intent explicitly.
4. Check future movement before committing the transform.
5. Keep collision response deterministic and event-driven.
6. Smooth visuals without rewriting authoritative simulation state.
7. Test movement with multiple frame rates or tick counts.

## Pattern: Intent and Velocity

```rust
#[derive(Component, Default)]
struct MovementIntent {
    direction: Vec2,
}

#[derive(Component, Default)]
struct Velocity(Vec2);
```

Input systems update `MovementIntent`. Fixed-step systems translate intent into
velocity and update the authoritative transform.

## Pattern: Predict Before Commit

```rust
fn integrate_motion(
    time: Res<Time<Fixed>>,
    mut query: Query<(&Velocity, &mut Transform, &Collider)>,
) {
    for (velocity, mut transform, collider) in &mut query {
        let next = transform.translation.truncate() + velocity.0 * time.delta_secs();
        if can_move_to(next, collider) {
            transform.translation = next.extend(transform.translation.z);
        }
    }
}
```

Replace `can_move_to` with the project's collision query or broadphase. The
important pattern is to evaluate the future position before mutating state.

## Pattern: Visual Smoothing

```rust
#[derive(Component)]
struct VisualFollower {
    target: Entity,
    smoothing: f32,
}
```

Keep the physics entity authoritative. Smooth a visual child or companion
entity toward it when fixed ticks are visible to the player.

## Review Checklist

- [ ] Simulation movement does not multiply by render-frame delta.
- [ ] Input sampling and fixed simulation have clear boundaries.
- [ ] Fast movers are checked with swept bounds, substeps, or predictive tests.
- [ ] Animation/tween code does not own physics authority.
- [ ] Collision response is deterministic for equal inputs.
- [ ] Tests or smoke checks cover different frame rates.
