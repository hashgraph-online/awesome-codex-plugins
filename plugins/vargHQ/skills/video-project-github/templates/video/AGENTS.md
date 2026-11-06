# {{name}}

AI video project. The person is not technical: say "saved", "version" and "go back", never commit, branch or push.

## Every session

1. Read `STATUS.md` and `brief.md`. 2. Run `python3 tools/repo.py status`. 3. If media is missing, run `python3 tools/repo.py restore`.

## Where things go

Skills that say `moodboard.md`, `script.md`, `cast/<id>.md` or `cues.json` mean these folders.

| Step | Folder | What is there |
|---|---|---|
| The ask | `brief.md` | The request, the spend cap and the person's notes, word for word with the date. Add, never rewrite |
| Inputs | `inputs/` | What the person gave: footage, logo, photos. Read only, never edit or overwrite |
| References | `refs/` | `refs.md`, frames |
| Look | `look/` | `moodboard.md`, `board.html`, test stills |
| Story | `story/` | `script.md`, `STORYBOARD.md`, `facts.md` |
| Sound | `sound/` | `plan.md`, `lines.md`, `cues.json`, `beats.json`, voice and music takes, `mix.wav`. Picture is cut to this |
| Cast and props | `cast/` | `<id>.md` (the passport, copied word for word into prompts), `board.md`, sheets |
| Blockout | `blockout/` | three.js or Blender scene, stills |
| Shots | `shots/` | `shots.md`, `runs.md`, `sh010/shot.md` (prompt, camera, refs, approved take), `sh010/takes/sh010_t01.mp4` |
| Edit | `edit/` | The timeline as text: a HyperFrames or Remotion project. Media it uses is copied into its `assets/` or `public/` |
| Review | `review/` | `notes.md` (timestamped notes), `review.md` (measured checks) |
| Renders | `renders/` | `film_v003.mp4`. Rebuilt from text, not saved. `ship` publishes the keepers |

## Rules

- Shots are `sh010`, `sh020`: tens, so a new shot can go in between. Takes are `sh010_t03.mp4`. Renders are `film_v003.mp4`. Never "final".
- Never overwrite a take. A new try is the next number.
- After every paid generation: `python3 tools/repo.py media note <file> --prompt-file shots/sh010/shot.md --model <id> --seed <n> --cost <usd> --job <id> --url <link>`.
- Save after each finished piece of work: `python3 tools/repo.py save "what changed"`. Rewrite `STATUS.md` first.
- When the person approves a step: `python3 tools/repo.py approve story "their words"`.
- A risky idea or a second agent: `python3 tools/repo.py try <name>`, then `keep` or `drop`.
- Use `tools/repo.py` for all saving, going back and sharing (`--help` lists it). Never run `git reset --hard`, `git clean`, `git push --force` or `git rebase`.
- Keys live only in `.env`, read from the environment. Never write a key in any other file or in a commit message.
- `python3 tools/repo.py back <version>` undoes anything. It adds a new version and loses nothing.
- When this file and the actual files disagree, follow the actual files and tell the person what you found.
