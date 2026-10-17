# Game Polish and Release Patterns

Use this file when a Rust game is close to playable and needs finishing work.

## Release Gate

Do not start packaging until these are true:

- [ ] Game launches without debug setup.
- [ ] Player can reach the core loop from the initial screen.
- [ ] Player can win, lose, finish a level, or exit cleanly.
- [ ] Restart or replay path works if the game includes one.
- [ ] Required assets load from the expected runtime path.
- [ ] Known crashes have either been fixed or intentionally documented.

## MVP Lock

Once the MVP loop works:

- Fix bugs before adding systems.
- Add content only through existing systems.
- Prefer clearer feedback over new mechanics.
- Move speculative ideas to a post-release list.
- Avoid changing dependencies unless a release-blocking issue requires it.

## Useful Polish

Prioritize polish that helps players understand and finish the game:

| Polish | Why it matters |
|---|---|
| Start/menu text | Makes controls and goal discoverable |
| HUD/state feedback | Explains health, score, depth, inventory, or turn state |
| Game over/victory screen | Confirms the run ended intentionally |
| Restart flow | Supports quick retesting and replay |
| Basic sound/visual cues | Shows important state changes |
| Resource-path checks | Prevents packaged builds from missing assets |

## Packaging Checks

- Run `cargo fmt`.
- Run `cargo clippy` with the project's configured flags.
- Run `cargo test` if tests exist.
- Run `cargo build --release`.
- Launch the release binary, not only `cargo run`.
- Confirm asset folders are beside or embedded in the build as required.
- Test from a clean working directory or temporary copy if resource paths are
  fragile.

## Asset Rules

- Keep required runtime assets in one documented folder.
- Avoid absolute paths.
- If the engine supports embedded resources, decide whether embedding or
  copying assets is better for the release target.
- Verify font, sprite, audio, data, and template files in release mode.
- Include license/attribution files for third-party assets when required.

## Release Smoke Test

```markdown
## Smoke Test

- [ ] Launch release binary
- [ ] Start game
- [ ] Move/interact with primary controls
- [ ] Trigger one hazard or enemy interaction
- [ ] Trigger one reward, pickup, score, or level transition
- [ ] Reach win/loss/exit path
- [ ] Restart or quit cleanly
```

## Common Mistakes

| Mistake | Do instead |
|---|---|
| Adding new mechanics during release week | Put them in post-release backlog |
| Testing only debug builds | Launch the release binary |
| Assuming asset paths work after packaging | Test from the packaged layout |
| Rebalancing without smoke checks | Re-run the whole core loop |
| Fixing warnings by hiding them | Fix real issues, document intentional exceptions |
