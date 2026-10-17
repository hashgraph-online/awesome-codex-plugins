# Asset Pipeline Patterns

Patterns for organizing Bevy assets as typed, validated runtime resources.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| Asset catalog | Single typed source of asset paths and handles. |
| Loading state | App state where assets are requested and readiness is checked. |
| Handle ownership | The catalog/resource keeps handles; systems clone handles cheaply. |
| Atlas metadata | Frame size, rows, columns, or animation ranges kept near the atlas. |
| Runtime layout | Folder structure used by the final executable, not only the dev tree. |

## Core Rules

1. Centralize asset paths before gameplay depends on them.
2. Keep typed fields for important assets; avoid string lookup for core assets.
3. Load once, clone handles where needed.
4. Treat asset readiness as state, not as a best-effort assumption.
5. Validate the release resource layout, not just `cargo run` from the repo root.
6. Keep third-party asset attribution with the packaged resources when licenses
   require it.

## Pattern: Typed Catalog

```rust
#[derive(Resource, Default)]
struct GameAssets {
    player_sheet: Handle<Image>,
    explosion_audio: Handle<AudioSource>,
    ui_font: Handle<Font>,
}

impl GameAssets {
    fn load(asset_server: &AssetServer) -> Self {
        Self {
            player_sheet: asset_server.load("sprites/player.png"),
            explosion_audio: asset_server.load("audio/explosion.ogg"),
            ui_font: asset_server.load("fonts/ui.ttf"),
        }
    }
}
```

The names are intentionally domain-specific. A catalog should read like the
game's asset contract.

## Pattern: Loading Gate

```rust
fn wait_for_assets(
    assets: Res<GameAssets>,
    asset_server: Res<AssetServer>,
    mut next_state: ResMut<NextState<AppState>>,
) {
    let handles = [
        assets.player_sheet.id().untyped(),
        assets.explosion_audio.id().untyped(),
        assets.ui_font.id().untyped(),
    ];

    if handles.iter().all(|id| asset_server.is_loaded_with_dependencies(*id)) {
        next_state.set(AppState::Playing);
    }
}
```

Adapt the readiness API to the Bevy version in the project. The pattern is to
gate state transitions on handle readiness.

## Packaging Checklist

- [ ] Asset paths are relative to Bevy's expected asset root.
- [ ] Release artifact includes every required folder.
- [ ] The game is smoke tested from outside the repository root.
- [ ] Missing assets produce an obvious failure mode during development.
- [ ] Credits or licenses for third-party assets are included when required.

## Review Smells

| Smell | Risk | Fix |
|-------|------|-----|
| `asset_server.load` inside update loops | Repeated load requests and unclear ownership | Load in setup/loading state |
| String paths in many systems | Path drift and typo risk | Typed catalog resource |
| State changes before readiness | Blank sprites or silent audio | Loading gate |
| Dev-only relative paths | Packaged build breaks | Test runtime layout |
