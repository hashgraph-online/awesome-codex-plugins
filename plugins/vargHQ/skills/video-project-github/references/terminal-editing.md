# Editing in a terminal

You still review like an editor. What changes is what the timeline is: a text file instead of a project file only one app can open. That gives you a readable record of every cut, an undo that survives closing the app, and an agent that can make the change.

| In an editor | Here |
|---|---|
| Project file | `edit/index.html` (HyperFrames), or `src/` (Remotion), or `edl.json` (ffmpeg) |
| Timeline | The same file: every clip has a start and a duration |
| Bin | `shots/*/takes/`, `sound/`, listed in `media.lock.jsonl` |
| Select | `approved:` line in `shot.md`, plus a copy in `edit/assets/` |
| Save as new version | `save "what changed"` |
| Undo after closing the app | `back <version>` |
| Duplicate the sequence to try something | `try <name>`, then `keep` or `drop` |
| Export | `npx hyperframes render --quality looks --output renders/film_v003.mp4` |
| Proxy | `--quality draft`, or `npx hyperframes snapshot` for stills |
| Review comments | `review/notes.md`: `00:14 the bike should be redder` |
| Hand off to a client | `ship renders/film_v003.mp4`, then `invite <their GitHub name>` |

["No serious editor wants to use a chatbox"](https://x.com/konstipaulus/status/1994112076495597975) is a fair objection, and the answer is not to give up the timeline. HyperFrames has a visual Studio on the same file (`npx hyperframes preview`), so you drag clips and the agent reads your change, or the reverse. For a finishing pass in Resolve or Premiere, export with [OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO), FCPXML or a CMX3600 EDL.

## Pick one timeline

| Format | Use it when | Notes |
|---|---|---|
| **HyperFrames** (default) | Motion, type, charts, video and audio together | HTML, Apache-licensed, ships a timeline CLI |
| Remotion | The team writes React | TSX. Check the licence: most companies need a paid one |
| `edl.json` + ffmpeg | Cutting existing footage, no graphics | Record why each cut exists, as [video-use](https://github.com/browser-use/video-use) does: `source, start, end, beat, quote, reason` |
| OTIO, FCPXML, EDL | Handing off to an editor | Exports, not where you work |

Keep the timeline file under GitHub's per-file diff limit of 500 KB, so never inline media as base64.

## HyperFrames in this layout

From the project's root:

```bash
npx hyperframes init edit --non-interactive --skip-transcribe
python3 tools/repo.py save "Edit project started"
# after writing the first composition:
cd edit && npx hyperframes timeline ids && cd ..   # once, and save right away: see the trap below
python3 tools/repo.py save "Timeline ids stamped"
```

`init` writes `package.json` scripts pinned to the exact HyperFrames version, and writes no `.gitignore` of its own; the project's root one already covers `.hyperframes/` and `renders/`. Its own `AGENTS.md` (7.5 KB) stays in `edit/`, where it loads only when an agent works there.

Timeline edits are ordinary commands, and each is a real change you can read:

```bash
npx hyperframes timeline --json              # every clip, its start and end, its file
npx hyperframes timeline move '#shot' 3      # clip starts at 3 s
npx hyperframes timeline trim '#shot' --duration 4
npx hyperframes timeline split '#title' 5
```

**The first-edit trap, measured on 0.9.9.** The first timeline command rewrites the file's formatting and stamps an id on every element, so a one-value change showed as 8 changed lines. After that, a trim or a move was exactly 1 changed line. Run `timeline ids` once and save, so that later changes stay readable.

Rules: media goes inside the project folder (`assets/`), and a path that points outside it is a lint error. `npx hyperframes history` also keeps a fine-grained undo inside `.hyperframes/`. It complements saves and does not replace them, since it stays on this computer.

## What a change looks like

```diff
-  <video id="s6" class="clip" data-start="15.2" data-duration="2.8" src="assets/sh060_t01.mp4">
+  <video id="s6" class="clip" data-start="15.2" data-duration="1.8" src="assets/sh060_t01.mp4">
```

A person can read that. An agent can too, which is why "what changed between the version I liked and this one?" has an exact answer here. Ask it: "Compare version 8 and version 12 of the cut, in plain words."

## What the terminal does not fix

[One film studio's scorecard](https://x.com/designertom/status/2107587128645624006): "Cutting assembly is largely smooth now... Pacing, not quite. Narrative is hit or miss." In [Timeline-Bench](https://arxiv.org/abs/2609.35143) (896 runs) the best agent passed 26.8% of editing tasks, agents claimed full success on 95.5% of the edits that failed a test, and human editors preferred the reference edit in 83.5% of 2,582 blind judgments. So keep looking at the cut yourself, and have checks that need no opinion. See `repeatable-results.md`.
