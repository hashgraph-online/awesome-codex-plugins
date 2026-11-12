---
name: video-project-github
description: >-
  Keep an AI video project, or any agent-built project, in a private GitHub repo, even when the person has never used
  git. The agent does everything: creates the private repo, keeps keys out, saves a version after every approved step,
  stores big video and audio outside git so GitHub's 100 MB limit never hits, and restores the whole project byte for
  byte on a new laptop. Sets up the folder layout for mood boards, script, sound, characters, blockout, shots and the
  edit as text (HyperFrames, Remotion, ffmpeg), records the prompt, model, seed and cost of every take, and gives an
  undo for anything. Use for "put this on GitHub", "back up my video project", "don't lose my work", "undo", "go back
  to the old version", "move to a new computer", "organize my project folder", "file structure for an AI video",
  "edit video in the terminal", "git for video". Not for one-off clips with no later edits, or for teams already happy
  with their own git setup.
license: MIT
metadata:
  author: vargHQ
  version: "1.0.1"
  openclaw:
    requires:
      bins:
        - git
        - gh
        - python3
    homepage: https://github.com/vargHQ/skills/tree/main/video-project-github
compatibility: >-
  Any agent with a shell: Claude Code, Codex, Cursor, Gemini CLI. Needs git, the GitHub CLI (gh) and Python 3.9+, on
  macOS, Linux or Windows, and a free GitHub account. No paid services, no extra accounts. The person clicks once to sign in.
allowed-tools: Bash(git:*) Bash(gh:*) Bash(python3:*) Read Write Edit
---

# Keep a video project in a private GitHub repo

> Step 10 of 10 in [How to make a video with an AI agent in ten steps](https://varg.ai/how-to/make-a-video-in-ten-steps). The full guide, with every test and source: https://varg.ai/how-to/keep-a-video-project-in-github (as Markdown: add `.md`).

People want an undo button and a backup, not version control. This skill gives them both and never asks them to learn git.

**How it works.** Text (scripts, prompts, storyboards, the edit as HTML or TSX) goes in git, where every change is one
readable line. Media stays out of git: `scripts/repo.py` lists each file by hash in `media.lock.jsonl` and uploads the
bytes to Releases of the same private repo. One GitHub login covers everything, and a new laptop gets it all back.

`<skill>` below is this skill's folder. Once a project exists it carries its own copy at `tools/repo.py`, so any agent
on any machine can continue without this skill. You do not need to read the script: `--help` lists the commands and every
message says what to do next.

## When not to use this

- One clip with no later edits: keep the file. Nothing here is needed.
- The person already has a git setup that works, with LFS or their own storage: keep it and take only the layout and naming from `references/layout.md`.
- A file over 2 GB, or more than about 50 GB in total: read `references/media-storage.md` first.
- No shell and no Python: use the prompt in `references/paste-prompt.md`, which does the same by hand.

## Step 1: check the machine

```bash
python3 <skill>/scripts/repo.py doctor
```

Install what it lists; it gives the exact command. If GitHub sign-in is missing, run `gh auth login --web --git-protocol https`
in the background: it prints a one-time code and waits. Show the person the code and the link (https://github.com/login/device),
and tell them: "Open this link, paste the code, click Authorize." If your tool cannot keep it running, ask them to run the command
themselves (in Claude Code, by typing `! gh auth login --web --git-protocol https`). Never ask for a password or a token, and never
accept one in chat. If they have no account, send them to https://github.com/signup first.

## Step 2: start, or bring in what exists

New project:

```bash
python3 <skill>/scripts/repo.py new <name>          # add --kind code for a code project
cd <name> && python3 tools/repo.py connect
```

Existing folder (run inside it). Look at the plan before applying:

```bash
python3 <skill>/scripts/repo.py adopt               # prints the plan, changes nothing
python3 <skill>/scripts/repo.py adopt --apply
python3 tools/repo.py connect
```

The scanner catches common key formats, not all of them, so check for yourself: open every script and config file in the folder and look for
hard-coded credentials, flagged or not. For each one add `NAME=value` to `.env`, put `$NAME` (or `process.env.NAME`) in the file, and run
again. Tell the person which keys you found, without printing their values. A key that was ever shared or in an earlier version is burned:
they should make a new one at the provider.
`adopt` never moves or deletes their files. Offer to sort them into the standard folders afterwards, and do it only if they agree.

`connect` creates the repo as private and checks that GitHub reports it private. Then prove the backup works before saying it is safe:

```bash
python3 tools/repo.py proof
```

It clones into a temporary folder, restores everything, compares every hash and deletes the folder.

## Step 3: while working

| When | Run |
|---|---|
| A piece of work is finished, or before anything risky | Rewrite `STATUS.md`, then `python3 tools/repo.py save "what changed"` |
| The person approves a step | `python3 tools/repo.py approve story "their words"` |
| A paid generation returns | `python3 tools/repo.py media note <file> --prompt-file <shot.md> --model <id> --seed <n> --cost <usd> --job <id> --url <link>` |
| A risky idea, or a second agent at the same time | `python3 tools/repo.py try <name>`, work in the folder it prints, then `keep <name>` or `drop <name>` |
| "Undo", "go back", "I liked the old one" | `python3 tools/repo.py versions`, then `back <number>`, or `back <number> <file>` for one file |
| A render is finished | `python3 tools/repo.py ship renders/film_v003.mp4 --note "first cut"` |
| Someone needs access | `python3 tools/repo.py invite <their GitHub name>` |
| New computer | `gh repo clone <name> && cd <name> && python3 tools/repo.py restore` |
| "Is it really safe?" | `python3 tools/repo.py proof` |

In the whole-video order from `how-to-make-ai-video`, run `approve` at every STOP. Run `save` before any paid call.

## How to talk to the person

Never say commit, push, branch, merge, tag, LFS or repository unless they use the word first.

| Say | Means |
|---|---|
| saved, version 12 | a commit |
| backed up to GitHub | pushed |
| go back to version 8 | `back 8` |
| a side copy to try it | `try` |
| your private project on GitHub | the repo |

End each save with one line: "Saved as version 12, backed up. Say 'go back' any time." When finished, tell them the link, that only
they can see it, what is not in GitHub (keys, on purpose), and how to get it back on a new laptop.

## The folders

```text
my-film/
├── AGENTS.md          rules for any agent (CLAUDE.md points here)
├── STATUS.md          where we stopped, what is next
├── brief.md           the ask, spend cap, every note word for word with the date
├── media.lock.jsonl   every media file by hash, with prompt, model, seed, cost
├── inputs/            what the person gave. Read only
├── refs/              refs.md, frames
├── look/              moodboard.md, board.html, test stills
├── story/             script.md, STORYBOARD.md
├── sound/             plan.md, cues.json, beats.json, mix.wav
├── cast/              <id>.md passports, sheets
├── blockout/          three.js or Blender scene, stills
├── shots/sh010/       shot.md, takes/sh010_t01.mp4
├── edit/              the timeline as text: a HyperFrames or Remotion project
├── review/            notes.md, review.md
├── renders/           film_v003.mp4. Not saved, rebuilt from text
└── tools/repo.py
```

Shots go in tens (`sh010`, `sh020`) so a shot can go in between. A new take is the next number and never overwrites. Renders are
versioned and never called "final". Why this shape, and how it maps to film practice: `references/layout.md`.

## Rules that stop the expensive mistakes

- Write `.gitignore` before the first `git add`. `new` and `adopt` do this. Git never forgets a file once it is in a pushed version.
- Never run `git reset --hard`, `git clean`, `git push --force`, `git rebase` or `git filter-repo` unless the person asked and agreed to the loss.
- Never put a project in `~/Downloads`, and never start an agent there: a downloaded `AGENTS.md` is read as instructions. Avoid iCloud and Dropbox folders too: sync tools can damage `.git`.
- Local git is not a backup. A save counts only after it says "Backed up to GitHub".
- You do not need a second GitHub account for the agent. If you want one, [GitHub's terms](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) allow one free personal account per person plus one free machine account, used only for running a machine.
- If a save stops, read what it says and fix that. Never work around the check with `--no-verify` or `git add -f`.

## Editing in the terminal

The timeline is a text file, so a cut is a one-line change you can read, undo and compare. Table of editor concepts and their
terminal equivalents, HyperFrames and Remotion setup, and the first-edit trap: `references/terminal-editing.md`.

## The same result every time

Code renders repeat; AI generations do not. Keep the bytes of every approved take, pin tool versions, and separate who makes from who
judges. The checklist and the measurements behind it: `references/repeatable-results.md`.

## If something fails

Exact errors and fixes: `references/troubleshooting.md`. Sources and benchmarks: `references/evidence.md`.

## Ranking takes or deliverables with a model

Scripts check facts, a person decides taste, and an LLM filters and finds defects. Criteria, evidence only and a tie as an allowed answer: `references/llm-judge.md`.
