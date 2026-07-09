# Bracket-Style Game Loop Patterns

Use this file when implementing or reviewing a Rust game loop with `bracket-lib`
or a similar callback-based 2D engine.

## Compatibility Checks

- Check whether the project already uses `bracket-lib`, `rltk`, Bevy, macroquad,
  ggez, or another engine. Do not mix engines without a reason.
- Inspect `Cargo.toml` before changing versions. Older tutorials may pin old
  crate versions; prefer the project's established version unless upgrading is
  part of the task.
- If using `bracket-lib`, prefer importing through `bracket_lib::prelude::*`
  only in small examples or prelude modules.
- Run the target project's normal verification command after changes.

## Minimal Shape

```rust
use bracket_lib::prelude::*;

enum Mode {
    Menu,
    Playing,
    GameOver,
}

struct State {
    mode: Mode,
    player_y: i32,
    score: i32,
}

impl State {
    fn new() -> Self {
        Self { mode: Mode::Menu, player_y: 10, score: 0 }
    }

    fn reset(&mut self) {
        *self = Self::new();
        self.mode = Mode::Playing;
    }
}

impl GameState for State {
    fn tick(&mut self, ctx: &mut BTerm) {
        ctx.cls();
        match self.mode {
            Mode::Menu => self.tick_menu(ctx),
            Mode::Playing => self.tick_playing(ctx),
            Mode::GameOver => self.tick_game_over(ctx),
        }
    }
}
```

This is a shape, not a rule that every project must copy. Adapt names and data
to the project.

## Game State Rules

- Store frame-to-frame data on the state object, not in local variables inside
  `tick`.
- Keep volatile input reads near the frame update code.
- Keep persistent domain data in named fields or resources.
- Use an enum for mutually exclusive modes: menu, playing, paused, game over,
  victory.
- Use one reset function to rebuild state after death, victory, or restart.
- Return the engine's error type from `main` when setup can fail.

## Tick Function Rules

- Clear or prepare the render target first when the engine expects it.
- Route by mode early.
- Keep `tick` short; delegate to `tick_menu`, `tick_playing`, and rendering
  helpers.
- Process input before movement if input determines movement.
- Process movement before collision checks if collisions depend on destination.
- Render after state has been updated unless the engine uses a retained scene.
- Avoid blocking work in `tick`; a frame callback should not wait on IO or long
  computation.

## Mode Routing

| Mode | Should do | Should not do |
|---|---|---|
| Menu | Draw menu, accept start/quit input | Advance gameplay timers |
| Playing | Read controls, update world, render HUD | Reinitialize all state |
| GameOver | Draw result, accept restart/quit input | Keep damaging the player |
| Victory | Draw result, accept next run input | Spawn new content silently |

## Review Checklist

- [ ] `main` builds the engine context and starts the loop in one obvious path.
- [ ] State initialization and reset are centralized.
- [ ] Every enum mode is handled explicitly.
- [ ] Rendering order is intentional and stable.
- [ ] Input handling cannot accidentally trigger actions in the wrong mode.
- [ ] Frame update code does not perform slow file/network operations.
- [ ] Errors from engine setup are propagated or explained.

## Common Smells

| Smell | Fix |
|---|---|
| `tick` is hundreds of lines | Split by mode and responsibility |
| Several booleans represent modes | Replace with one enum |
| Restart duplicates initialization | Call a single reset constructor |
| Rendering mutates gameplay data | Separate draw helpers from update helpers |
| Tutorial version fails to compile | Inspect crate docs and target version before patching APIs |
