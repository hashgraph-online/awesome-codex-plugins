# The project layout

One project per repo. A second film is a second repo, so its history, access and backups stay separate.

```text
my-film/
├── AGENTS.md          rules for any agent. CLAUDE.md is one line: @AGENTS.md
├── README.md          for people: what this is, how to get it back
├── STATUS.md          where we stopped, what is next. Rewritten before every save
├── brief.md           the ask, spend cap, every note word for word with the date. Add, never rewrite
├── media.lock.jsonl   every media file by hash, with prompt, model, seed, cost, job
├── .env.example       key names only. The real .env is never saved
├── inputs/            what the person gave: footage, logo, photos. Read only
├── refs/              refs.md, frames
├── look/              moodboard.md, board.html, test stills
├── story/             script.md, STORYBOARD.md, facts.md
├── sound/             plan.md, lines.md, cues.json, beats.json, voice and music takes, mix.wav
├── cast/              mara.md (the passport), board.md, sheets
├── blockout/          three.js or Blender scene, stills
├── shots/             shots.md, runs.md
│   └── sh010/         shot.md, takes/sh010_t01.mp4
├── edit/              HyperFrames or Remotion project: the timeline as text
│   └── assets/        copies of the approved takes the cut uses
├── review/            notes.md, review.md
├── renders/           film_v003.mp4. Ignored: rebuilt from text
└── tools/             repo.py, hooks
```

## Why this shape

- **One folder per production step.** Each is one step of the whole-video order in `how-to-make-ai-video`, and the names match what the other skills write (`cast/<id>.md` from `character-passport`, `sound/plan.md` and `cues.json` from `video-sound`, `shots.md` from `video-animate`). `script.md` and `moodboard.md` live in `story/` and `look/`, and the table in `AGENTS.md` tells agents so.
- **`inputs/` is read only.** Originals are never edited, which is how post houses treat camera files. An agent that "cleans up" your footage has nothing to clean.
- **The edit is its own project.** HyperFrames treats media outside the project folder as a lint error (`missing_local_asset`), so approved takes are copied into `edit/assets/`. The copy costs nothing: the media list stores each hash once.
- **Prompts live next to their shot**, not in a `prompts/` folder away from it. Everything about `sh040` is in one place.
- **No `old/`, `final2/` or `backup/` folders.** Versions replace them, and an old copy in the folder is a trap: an agent may edit it instead of the real file.

## Naming

These come from how film projects are run. [Blender Studio's rules](https://studio.blender.org/tools/naming-conventions/introduction) are the clearest public version: "No caps, no gaps", with shots incremented by 10.

| Thing | Name | Rule |
|---|---|---|
| Shot | `sh010`, `sh020`, later `sh015` | Tens, so one can go in between. For a long film, sequence and shot: `sq010_sh0030` |
| Take | `sh010_t03.mp4` | A new try is the next number. Never overwrite |
| Render | `film_v003.mp4` | Version numbers on renders and exports only |
| Work files | `moodboard.md` | No version in the name. Blender Studio: "version (v001, v002) only for renders and exports, not for work files as they have a history on Git". This is what ends `final_v3_REAL.mp4` |
| Files | lowercase, no spaces | Spaces break shell commands. `STORYBOARD.md` and the root files keep their usual names |

Netflix's shot names follow the same logic at a larger scale: show, episode, sequence, VFX ID, then task and version, as in `AGM_104_065_010_comp_NFX_v005` (quoted second-hand; the official page would not load).

## What goes where

| Kind | Where | Examples |
|---|---|---|
| Words and code | git | scripts, prompts, `beats.json`, compositions, notes |
| Paid or irreplaceable media | Releases, listed in `media.lock.jsonl` | takes, stills, voice, music, inputs |
| Rebuilt on demand | ignored | `renders/`, `node_modules/`, `.hyperframes/`, proxies |
| Secrets | `.env` on this computer only | API keys |

A paid clip is not "regenerable". The same prompt and seed is not promised to give the same clip (see `repeatable-results.md`), so ignoring takes can mean paying twice for something you can no longer get. Of 91 public agent-video repos we checked, 90% ignore media or renders, and only 5.5% use LFS and 4.4% object storage. The count covers public repos only.

## What a layout does and does not do

We tested this on one finished 12-shot project in four layouts: a flat mess, sorted by file type, this kind of per-step layout with the folder table in `AGENTS.md`, and the same without the table. (The tested version numbered its folders; we dropped the numbers afterwards to match the other skills' names.) Four tasks (find what made a take, change a cut, change a character everywhere, list unused takes), 3 repeats, 2 agents, 96 runs. **95 passed, with no pattern by layout, and steps and tokens stayed within noise.** The one failure was on the by-type layout, where an agent edited the storyboard instead of the cut.

So a tidy layout is not what makes an agent succeed at this size: search finds things. That agrees with the [ETH study](https://arxiv.org/abs/2602.11988), where repo overviews did not speed up navigation either. We did not test large projects.

Keep the layout anyway, for these reasons:

- A person can see how far along the project is and find a file without an agent.
- A new project has no files to learn from, so the table is the only place that says where things go. That part we did not measure.
- Every project looks the same, so moving between them costs nothing.

What the runs do support is keeping rules and commands in `AGENTS.md`, because agents obey what is written there. Keep it short and hand-written, and keep one sentence: when the file and the actual files disagree, follow the files. In a [320-run study](https://arxiv.org/abs/2610.30571), agents followed a stale instruction file in 90% of choices, and that sentence moved them to following the code in 91%.

## A code project

`repo.py new <name> --kind code` uses the same tooling with `src/`, `tests/`, `docs/`, `features.json` (what the product must do, how to check it, done or not) and `STATUS.md`. Fill in the run and test commands in `AGENTS.md`. That is the recipe from [Anthropic's long-running agent post](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): read notes, run the checks, do one feature, test it, save. The post reports no controlled result, so treat it as a sound habit rather than a measured gain.

## Sorting an existing folder

`adopt` never moves anything. If the person agrees to sort it: use the table above, run `git mv` for text and plain `mv` for media, update the paths in the cut, then `save`. A moved file keeps its notes in the media list. Move in one pass and check the cut still renders before saving.
