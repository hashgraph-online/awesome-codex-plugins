# The edit pack (optional)

brief2mp4 works without this folder. The pack adds real editing tools for briefs that are more than "generate a graphic and finish it with ffmpeg": footage cut on a timeline, a multitrack audio mix, layered compositing, image editing, vector art. It installs the command-line tools of five free desktop apps, pinned to exact versions, and ships one tested recipe per app.

The apps are the ArtCraft family by **storytold**, released under **MIT or Apache-2.0** (each app is licensed MIT or Apache-2.0 at your option, per its `NOTICE`; each download carries `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE` and font licences; read them). brief2mp4 does not redistribute them: the installer downloads each release from `github.com/storytold`. **They are alpha software.** Command ids and parameters change between versions, which is why this pack pins versions, tests its recipes against the pinned ones, and tells agents to discover commands at run time.

| Component | App | Pinned | What it is |
|---|---|---|---|
| `film` | FilmCraft | 0.20.1 | timeline editor, Premiere class |
| `sound` | SoundCraft | 0.20.1 | multitrack audio workstation: mix, automation, bounce |
| `effect` | EffectCraft | 0.24.1 | layered, keyframed compositing, After Effects class |
| `photo` | PhotoCraft | 0.23.1 | image editor: thumbnails, title cards |
| `vector` | VectorCraft | 0.24.1 | vector drawing: logos, lower thirds as SVG |

## Check and install

Check first. The command always exits 0 and prints one line you can branch on. A component counts as ready only if its CLI runs (`<cli> --version` succeeds):

```bash
bash scripts/detect_edit.sh                  # macOS, Linux, Git Bash
powershell -File scripts\detect_edit.ps1     # Windows
# edit: ready (film,sound,effect,photo,vector)   or   edit: not installed
```

If the brief needs editing and it says `not installed`, install only the components the brief needs. Nothing uses sudo or admin rights, and nothing touches your system PATH.

```bash
# macOS and Linux (run from this skill's folder, or give the full path)
bash edit/install_edit.sh                                  # film + sound
bash edit/install_edit.sh --components film,sound,effect,photo,vector
bash edit/install_edit.sh --components all --dry-run       # print what would be downloaded, change nothing

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File edit\install_edit.ps1
powershell -ExecutionPolicy Bypass -File edit\install_edit.ps1 -Components film,sound,effect,photo,vector
powershell -ExecutionPolicy Bypass -File edit\install_edit.ps1 -Components all -DryRun
```

It needs `curl` and Node.js (already required by the skill) on macOS and Linux, plus `unzip` or `bsdtar` for the macOS zips. Each download is checked three ways: its SHA-256 must equal the line in the release's `SHA256SUMS.txt` and the hash pinned in `versions.json`, and, when `gpg` is installed, `SHA256SUMS.txt.asc` must verify against `release-signing-key.asc` and the signing key's fingerprint pinned in `versions.json`. Without gpg the installer says `signature: SKIPPED` and the two SHA-256 checks still run. A mismatch deletes nothing you had and installs nothing.

### Where it goes, and how big

Everything goes into `~/.brief2mp4/edit` (Windows `%USERPROFILE%\.brief2mp4\edit`); set `B2M_EDIT_HOME` to use another folder. It holds the app folders (`filmcraft/` and so on), `bin/` with one launcher per CLI, a copy of `versions.json` and of the `recipes/`, and `.b2m-edit-manifest`, the list of what the installer created. The installed pack never reads from the git clone or the plugin cache, so moving or deleting those does not break it. Launchers use relative paths, so the whole folder can be moved or copied too.

| | macOS (CLI zip) | Linux x86_64 (app tarball) | Windows x64 (portable zip) |
|---|---|---|---|
| download: film | 95.4 MB | 107.0 MB | 108.2 MB |
| download: sound | 8.6 MB | 20.9 MB | 19.0 MB |
| download: effect | 73.7 MB | 78.0 MB | 81.1 MB |
| download: photo | 114.9 MB | 133.0 MB | 136.5 MB |
| download: vector | 127.8 MB | 150.4 MB | 155.4 MB |
| download: all five | 420.4 MB | 489.3 MB | 500.2 MB |

Measured on macOS after install: filmcraft 179 MB, soundcraft 22 MB, effectcraft 187 MB, photocraft 236 MB, vectorcraft 254 MB, about 880 MB for all five. Linux and Windows disk sizes were not measured. The Linux and Windows archives hold the whole desktop app next to the CLI (inspected for SoundCraft), and the installer keeps that folder as it came.

To put the launchers on your PATH the installer prints one line to run yourself. The recipes do not need that: they find the pinned CLIs through `B2M_EDIT_HOME` and never use an older copy that happens to be on the PATH.

### Uninstall

```bash
bash edit/install_edit.sh --uninstall                       # everything the installer created
bash edit/install_edit.sh --uninstall --components photo    # one component
# Windows: install_edit.ps1 -Uninstall [-Components photo]
```

Only the paths listed in `.b2m-edit-manifest` are removed, one by one. Anything else you put in that folder stays, and the folder itself is removed only if it ends up empty. Entries in the manifest with `..` or an absolute path are skipped.

macOS note: a download made with `curl` carries no quarantine flag, and the installer checked this (`no quarantine flag ... nothing to remove`). If a flag is ever present it removes `com.apple.quarantine` from the app folder and says so. That branch has not been exercised.

## When to use which tool

HyperFrames, Three.js and Blender stay the way to make graphics, type, charts and 3D. ffmpeg stays the finisher. Reach for the pack when the work is editing, not generating.

| The brief needs | Use | Why not HyperFrames or ffmpeg alone |
|---|---|---|
| Footage-heavy tutorials, vlogs, skits: several clips, trims, a cross dissolve, a title on top, audio that follows the cut | FilmCraft (`film_timeline.sh`) | a timeline keeps clip, transition and title relationships; ffmpeg filter graphs for that are fragile and unreadable |
| Voice, music and sound effects on separate tracks, music lowered under speech, a bounced mix | SoundCraft (`sound_mix.sh`) | per-track levels and automation instead of one opaque `amix` expression |
| Layered, keyframed compositing: animated titles, bars, effects on layers, text animation presets | EffectCraft (`effect_title.sh`) | layers, keyframes and effects with a renderer, when an HTML page would be a re-implementation |
| Thumbnails, title cards, image retouching | PhotoCraft (`photo_thumbnail.sh`) | real type and layers on a raster canvas |
| SVG logos, lower thirds, icons that stay sharp at any size | VectorCraft (`vector_lower_third.sh`) | clean vector output with live text, which you can then place in a HyperFrames page |

If HyperFrames already does the job in one page, use HyperFrames. The pack is for the cases above.

## CLI first, MCP only when needed

Drive each app through its CLI: it is scriptable, needs no server, and the recipes show the shape. Use an MCP server only when the CLI cannot do the job, for example to keep one document open across many steps, or to drive a running desktop app. These all start with `<cli> mcp`; the launchers are in `~/.brief2mp4/edit/bin`.

```bash
# Claude Code (syntax from `claude mcp add --help`)
claude mcp add filmcraft -- ~/.brief2mp4/edit/bin/filmcraft-cli mcp
claude mcp add vectorcraft -- ~/.brief2mp4/edit/bin/vectorcraft-cli mcp --headless
# Codex (syntax from `codex mcp add --help`)
codex mcp add filmcraft -- ~/.brief2mp4/edit/bin/filmcraft-cli mcp
codex mcp add vectorcraft -- ~/.brief2mp4/edit/bin/vectorcraft-cli mcp --headless
```

Use the same pattern for `soundcraft-cli mcp`, `effectcraft-cli mcp` and `photocraft-cli mcp`. `vectorcraft-cli mcp` without `--headless` first tries a running VectorCraft app on 127.0.0.1:7979 and falls back to a headless session. Verified here: each of the five pinned CLIs answers the MCP `initialize` and `tools/list` calls over stdio with its pinned version (17, 17, 27, 26 and 33 tools for film, sound, effect, photo and vector). Not tested: registering them in a real Claude Code or Codex session and calling tools from there.

**File confinement.** For the servers that have the flags, confine what an agent can read and write:

```bash
soundcraft-cli mcp --automation-read-root ./project --automation-write-root ./project/out
```

`--automation-read-root DIR` and `--automation-write-root DIR` exist on `soundcraft-cli mcp`, `effectcraft-cli mcp`, `photocraft-cli mcp` and `vectorcraft-cli mcp` in the pinned versions (checked in each `mcp --help`); repeat them for several folders. A root you leave out grants none of that access on photo and vector, and on vector they imply `--headless`. **FilmCraft 0.20.1 has no such flags**: `filmcraft-cli mcp --automation-read-root X` fails with `unknown mcp option`. So for FilmCraft prefer the CLI, which only touches the paths your script names, and keep it inside the project folder.

## Discover commands; do not trust a list

Command ids and parameters change between alpha versions. Before using any command, ask the pinned CLI:

| App | List | Detail |
|---|---|---|
| FilmCraft | `filmcraft-cli commands [filter]` | `filmcraft-cli describe <id>` |
| SoundCraft | `soundcraft-cli commands` (plus `soundcraft-cli plugins`) | `soundcraft-cli describe <id>` |
| EffectCraft | `effectcraft-cli commands --filter TEXT` | the listing shows each command's parameters |
| PhotoCraft | `photocraft-cli commands --filter TEXT [--json]` | the listing shows each command's parameters |
| VectorCraft | `vectorcraft-cli commands` (JSON, about 1,400 entries: filter it) | the `params` field of each entry |

Add `--help` for the subcommands and options. The ids the recipes use are named at the top of each recipe and are checked against the pinned CLIs by `tests/test_edit_slow.py`. If you move to other versions, re-run the recipes and the tests before trusting them.

## The recipes

Each recipe is a bash script (on Windows, Git Bash) that does one real job headless with the pinned CLI, makes its own sample inputs if you give none, and prints `ok: <file> ...`. They live in `recipes/` here and in `~/.brief2mp4/edit/recipes/` after install. Run any with `--help`.

| Recipe | Job | Command ids it uses (pinned versions) |
|---|---|---|
| `film_timeline.sh` | two clips on a timeline, a 1 s cross dissolve at the cut, a title, export H.264 MP4 with AAC (5 s) | `file.newProject`, `file.newSequence`, `file.import`, `timeline.place`, `sequence.applyVideoTransition`, `graphics.newText`, `file.exportMedia` |
| `sound_mix.sh` | a voice track over a music bed, the bed ducked by volume automation under the voice, bounced to a 48 kHz stereo 24-bit WAV | `session.new`, `file.import_audio`, `mix.volume`, `automation.set_point`, and `run --bounce` |
| `effect_title.sh` | a 3 s animated title: a text layer with the Tracking In preset, fade and rise keyframes, a growing accent bar, rendered to H.264 | `comp.new`, `layer.newText`, `layer.applyTextPreset`, `layer.newSolid`, `prop.addKey`, `prop.set`, and `render` |
| `photo_thumbnail.sh` | a 1280x720 PNG thumbnail: gradient, title, subtitle | `layer.newFillLayer.gradient`, `type.create`, started with `run --new` |
| `vector_lower_third.sh` | a lower-third SVG with a panel, accent bar, name and role | `file.new`, `shape.rectangle`, `paint.setFill`, `paint.setStroke`, `text.create`, exported with `run --export` |

How each app is driven, so you can adapt a recipe:

- **FilmCraft** keeps state only inside one `run`, or in a project file between calls: `run script.jsonl --save-as p.fcproj`, then `--project p.fcproj --save run next.jsonl`. Each command's JSON result carries the ids (items, clips) the next step needs, which is why the recipe works in three stages. Time is in ticks (254016000000 per second); `timeline.place` also takes `{"seconds": ...}` for source in and duration. A dissolve needs spare frames on both sides of the cut, so the recipe takes the second clip from half a dissolve earlier.
- **SoundCraft** takes repeated `--cmd ID=JSON` and `--bounce OUT`. Imported files become tracks named after the file, so the recipe copies inputs in as `voice.wav` and `music.wav`. The pinned compressor lists no sidechain input parameter, so ducking is done with volume automation points on the music track.
- **EffectCraft**: `--empty run --commands file.jsonl --save-as p.ecproj`, then `--project p.ecproj render --out x.mp4 --format h264 --audio off`. Property paths come from `effectcraft-cli props <comp> <layer> --flat`.
- **PhotoCraft**: `run --new '{"width":1280,"height":720}' --cmd ID --params '{...}' ... --out file.png`. Saving a layered document as PNG flattens it (the CLI says so).
- **VectorCraft**: `run --commands file.jsonl --export file.svg`. New shapes get a black stroke unless you switch it off with `paint.setStroke {"none":true}`.

## Commands beyond the recipes (seen working with the pinned versions)

The example 07 run needed a few commands the recipes do not use. All are in the pinned CLIs (`<app>-cli commands` lists them with their parameters):

- FilmCraft `timeline.place` with `sourceIn` and `duration` trims a clip as it places it; `graphics.set` with `props` (`font`, `font_style`, `size`, `fill_color`, `position`, `opacity`) styles a title, and `keyframe: true` animates a property.
- PhotoCraft `shape.create` draws a shape layer (a rounded rectangle for a thumbnail); `type.create` sets text.
- PhotoCraft quirk: if the `box` given to `type.create` is too short for the text, only the first wrapped line shows, with no warning. Give text boxes generous height and check the PNG.
- SoundCraft: `sound_mix.sh` ducks a music bed under any foreground track, not only a voice: pass chimes or sound effects as `--voice` to duck under them.

## Every route still ends in the same two scripts

Whatever made the picture and sound, the deliverable is checked the same way. An edit export is a rough render like any other:

```bash
bash scripts/finish.sh --in cut.mp4 --out final.mp4 --seconds 5 --size 1280x720 --keep-audio
bash scripts/check_delivery.sh final.mp4 --seconds 5 --size 1280x720
```

Run on the output of `film_timeline.sh`, this gives `RESULT: PASS` (1280x720, 30 fps, 5.0 s, AAC, -14.1 LUFS). A SoundCraft WAV goes into `finish.sh --audio`; PhotoCraft and VectorCraft outputs are stills or overlays that go into the HyperFrames page or the FilmCraft timeline. `examples/07-edit-tutorial/BRIEF.md` is a brief that needs this pack.

## What was tested, and what was not

CI on macOS, Ubuntu and Windows installs FilmCraft and SoundCraft with the native installer for each platform (Windows: PowerShell, including Windows PowerShell 5.1), checks every download's SHA-256 and the release signature, runs the cut and mix recipes, and passes the result through `finish.sh` and `check_delivery.sh`. EffectCraft, PhotoCraft and VectorCraft recipes are tested on macOS. Desktop apps, bridge mode and calling the apps' MCP servers from a live Claude Code or Codex session are untested.
