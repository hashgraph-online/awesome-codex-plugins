# State Flow Patterns

Patterns for Bevy application states, plugins, cleanup, and transitions.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| App state | Coarse phase such as Loading, Menu, Playing, Paused, GameOver. |
| Plugin boundary | A package of systems/resources/events for one feature or phase. |
| Entry system | Setup that runs once when a state starts. |
| Exit system | Cleanup that runs once when a state ends. |
| Cleanup marker | Component placed on entities that belong to one state. |
| Run condition | Predicate that restricts systems to the correct state. |

## Core Rules

1. Model durable game phases explicitly.
2. Put phase setup in `OnEnter` and teardown in `OnExit`.
3. Add marker components to state-owned entities at spawn time.
4. Keep update systems filtered by state.
5. Keep transition triggers small and visible.
6. Do not use rendering or input systems as hidden state machines.
7. Test entering, leaving, and re-entering each state.

## Pattern: State Enum

```rust
#[derive(States, Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
enum AppState {
    #[default]
    Loading,
    Menu,
    Playing,
    Paused,
    GameOver,
}
```

Use coarse states for phases the player could name. Use resources or local
substates for smaller details that do not affect scheduling.

## Pattern: Cleanup Marker

```rust
#[derive(Component)]
struct MenuEntity;

fn cleanup_menu(mut commands: Commands, query: Query<Entity, With<MenuEntity>>) {
    for entity in &query {
        commands.entity(entity).despawn_recursive();
    }
}
```

Attach `MenuEntity` when spawning menu UI. Register cleanup in `OnExit(Menu)`.

## Pattern: Plugin Registration

```rust
struct MenuPlugin;

impl Plugin for MenuPlugin {
    fn build(&self, app: &mut App) {
        app.add_systems(OnEnter(AppState::Menu), spawn_menu)
            .add_systems(
                Update,
                menu_input.run_if(in_state(AppState::Menu)),
            )
            .add_systems(OnExit(AppState::Menu), cleanup_menu);
    }
}
```

Keep each plugin responsible for its systems, resources, events, and cleanup.

## Review Checklist

- [ ] Every spawned state-owned entity has a cleanup marker.
- [ ] Systems that should only run in one phase have run conditions.
- [ ] Transitions are visible and intentional.
- [ ] Re-entering the state does not duplicate persistent resources.
- [ ] Plugin registration order is not carrying hidden behavior.
- [ ] Tests or smoke checks cover repeated state transitions.
