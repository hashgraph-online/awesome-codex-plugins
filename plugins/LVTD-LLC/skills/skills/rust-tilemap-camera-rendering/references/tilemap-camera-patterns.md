# Tilemap, Camera, and Rendering Patterns

Use this file when a Rust game uses a 2D grid, dungeon map, board, or tile
camera.

## Map Data Shape

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Tile {
    Floor,
    Wall,
}

struct Map {
    width: i32,
    height: i32,
    tiles: Vec<Tile>,
}

impl Map {
    fn idx(&self, x: i32, y: i32) -> Option<usize> {
        if x < 0 || y < 0 || x >= self.width || y >= self.height {
            return None;
        }
        Some((y * self.width + x) as usize)
    }

    fn can_enter(&self, x: i32, y: i32) -> bool {
        self.idx(x, y)
            .map(|i| self.tiles[i] == Tile::Floor)
            .unwrap_or(false)
    }
}
```

## Map Rules

- Store tiles in one vector unless the project already has a spatial storage
  abstraction.
- Keep coordinate-to-index conversion in one method.
- Return `Option<usize>` for fallible coordinate conversion.
- Use `can_enter`, `is_blocked`, or a similar semantic method for movement.
- Keep tile type small and copyable when maps contain many cells.
- Avoid putting entity state directly in the tile vector unless the game is
  intentionally single-occupancy and simple.

## Camera Shape

```rust
struct Camera {
    left: i32,
    top: i32,
    width: i32,
    height: i32,
}

impl Camera {
    fn center_on(&mut self, x: i32, y: i32) {
        self.left = x - self.width / 2;
        self.top = y - self.height / 2;
    }

    fn world_to_screen(&self, x: i32, y: i32) -> (i32, i32) {
        (x - self.left, y - self.top)
    }
}
```

## Rendering Rules

- Render only the camera rectangle for large maps.
- Convert world coordinates to screen coordinates at the render boundary.
- Use `in_bounds` or `idx` before reading a tile.
- Draw terrain before entities.
- Draw UI after world layers.
- Keep art/tile theme decisions out of map generation.
- When using tile fonts or sprites, verify resource paths in release builds.

## Map Builder Boundary

Use a map builder to return all level setup data together:

```rust
struct BuiltMap {
    map: Map,
    player_start: (i32, i32),
    exit: Option<(i32, i32)>,
    spawn_points: Vec<(i32, i32)>,
}
```

Builder responsibilities:

- Create legal terrain.
- Choose player and exit positions.
- Provide spawn points that are walkable and reachable.
- Leave rendering and entity spawning to other code.

## Theme Boundary

Use a theme layer when the same map should render differently:

```rust
trait MapTheme {
    fn glyph_for(&self, tile: Tile) -> char;
    fn tint_for(&self, tile: Tile) -> [f32; 4];
}
```

Theme rules:

- Themes map semantic tiles to visuals.
- Themes should not change collision rules.
- If a visual implies collision, add a tile type or component to represent it.

## Review Checklist

- [ ] Map indexing cannot panic on out-of-bounds coordinates.
- [ ] Movement uses map semantics, not raw tile comparisons scattered around.
- [ ] Camera transform is applied exactly once.
- [ ] Draw order is stable and documented by code structure.
- [ ] Map generation returns enough metadata for spawning and progression.
- [ ] Resource paths are checked in the packaged/release layout.

## Common Smells

| Smell | Fix |
|---|---|
| `x + y * WIDTH` appears everywhere | Centralize index conversion |
| Player can leave the map | Gate movement through `can_enter` |
| Entity appears offset from map | Audit world-to-screen conversion |
| Theme changes game rules | Move rules into tile/component data |
| Map builder spawns entities directly | Return spawn points and let a spawner own entities |
