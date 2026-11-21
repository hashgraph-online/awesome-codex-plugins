---
name: macbox
description: Build, test, run, and tap through native iOS apps on a real remote Mac. Use for iOS build, test, and simulator work when this machine can't run Xcode, or when CLAUDE.md or AGENTS.md says to use macbox.
---

# macbox

`macbox` sends this folder to a real Mac, runs Xcode there, and streams the result back.
Each command is one-shot: no TTY, no prompts. The exit code is the answer.
If `macbox` is not installed or not logged in, follow https://api.macbox.build/guide/ first.

## Commands

```
macbox build                  # build for the iOS simulator
macbox test                   # build, then run tests on a fresh simulator
macbox screenshot shot.png    # launch the last build, wait 3 s, save a picture
macbox status                 # minutes left, your Mac, your last job
macbox logs [job]             # follow a job again after a dropped connection
macbox cancel [job]           # stop a job
macbox run                    # build, launch, keep it running; prints a live link
macbox ui describe            # elements on screen, with ids and frames (points)
macbox ui tap --id X          # or --label X, or x y
macbox ui type <text> | swipe x1 y1 x2 y2 | button home | screen out.png
macbox stop                   # end the running app
```

To check a flow works, `run`, then `ui describe` and act on what it shows; repeat.
Give the user the live link: they can watch and tap too.

Flags: `--scheme`, `--workspace`, `--project`, `--device "iPhone 17 Pro"`,
`--only-testing Target/Class/test`, `--wait 5`, `--build <id>`, `--include path`,
`--json`, `--dry-run`. See `macbox help`.

## Exit codes

- `0` it worked.
- `1` the build or tests failed. Read the errors, fix the code, run again.
- `2` bad usage, or a problem on this machine.
- `3` macbox's side or the account (no credit, Mac offline). Don't retry in a loop; tell the user.

## Rules

- The key may already be set (`MACBOX_API_KEY` or `~/.macbox/config`): run `macbox status` before asking. Never ask for secrets in chat.
- Not logged in? Run `macbox login`: it prints a link for the user to sign in with GitHub, then exits. After they say they're done, run `macbox login` again to finish.
- `macbox test` prints `PASS name` / `FAIL name` per test, plus failing log lines.
- `macbox screenshot` launches the last build (builds first if none); `--wait 6` for slow apps.
- Use `--json` for NDJSON ending in a `{"t":"result",...}` line.

## What gets sent

- Files git tracks (submodules too), new files git doesn't ignore, and `.xcconfig` files.
- Not sent: `.git`, `Pods`, `.build`, `DerivedData`, `node_modules`, `.env`. Use `--include path` for those.
- Pods, Swift packages, and XcodeGen projects are resolved on the Mac.
- No git history or tags on the Mac. `--dry-run` lists what is sent.

## Setup scripts

A step Xcode needs first (download frameworks, copy a template config) goes in
`.macbox/setup` (bash, repo root). It runs on the Mac before builds, again only when
it changes; its output stays there. Fetch big binaries here, don't `--include` them.

## Limits

Native iOS, simulator only. No signing, no TestFlight.
Mac apps: `build` and `test` work (unsigned, for macOS); `screenshot` does not.
Private packages needing SSH keys or `~/.netrc` don't work yet.
