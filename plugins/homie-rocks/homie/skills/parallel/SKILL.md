---
name: parallel
description: Build a planned game with several agents at once — game logic and netcode, levels, art, sound, the landing page — each in its own folders, then one merge, a two-browser check, a playtest and a blind review. Use only when parallel work is requested and the host supports it. Use after the plan step, or when someone asks to "build it in parallel", "use more agents", "split the work" or "go faster".
---

# Build in parallel

One agent building step by step is slower but uses the least. Several agents, each on its own part of
the game at the same time, finish sooner and use more. The person chooses.

## 1. Only when requested

Use one agent by default. Do not turn implementation staffing into a question for the person.
When parallel work is requested and the host supports it, choose the number of agents from the
independent work available, within the agreed usage budget. Say the allocation briefly and proceed.

## 2. Split the work: one folder each

Every agent writes only in its own folders. Pick the parts the codex calls for:

| Part | Writes only in | Reads | Hands back |
| --- | --- | --- | --- |
| Game logic and netcode | `games/<id>/src/` (not `src/levels/`) | the codex's Concept, Rooms and players, Controls; `node_modules/@homie-rocks/studio/netplay/NETPLAY.md` | rules, bots, rounds, input, the netplay shape |
| Levels and content | `games/<id>/src/levels/` | the codex's World and Characters | levels, waves or maps as data the game logic loads |
| Art | `games/<id>/public/art/`, `games/<id>/art/` | the codex's Art direction and Characters; the `art` skill | sprites, backdrops, the cover, at the sizes the contract names |
| Sound | `games/<id>/public/sound/`, `music/<slug>/` | the codex's Music and sound; the `sound` skill | the named sound effects and the theme |
| Landing page | `games/<id>/hero/`, `site/partials/game-<id>.html` | the codex's Concept and Art direction; the `game` skill's landing | hero footage once the game runs, the landing's words as a proposal |

**Shared files have one owner: you, the lead.** `game.json`, `CODEX.md`, `index.html`, `package.json`,
`studio.json` and `site/theme.json` are written only in the merge. A part that needs one changed says so
in its report.

**Write the contract into the codex before anyone starts**, so the parts meet without talking: the sound
names the game logic calls (`pickup`, `hit`, `win`), the art files and their sizes, the shape of a level.
Each goes in its section (Music and sound, Art direction, World), with a dated line under Latest.

## 3. Brief each agent

Give every agent the same shape of brief:

- **Goal**: its part, in a paragraph, from the codex (`games/<id>/CODEX.md`, which it reads first).
- **Its folders**: where it may write; everything else is read-only; never another part's folder.
- **The contract**: names, paths and shapes from the codex.
- **How to check its part alone**: `npm run build` passes; the `sound` skill's measure; the `art` skill's
  look at its pictures; for levels, the game loads them.
- **Not its job**: running the dev server, deploying, committing, installing packages, ending the
  progress feed, editing the shared files.
- **Progress**: `npx --no-install homie-studio progress check <part> running --label "<Part>"` when it
  starts, `pass` or `fail` when it ends (you opened the feed with `progress start`).
- **Its report**: what it made, the files, what the shared files need, and anything it could not decide.

In Claude Code (2.1.287 or later), the Homie mod's parts pane (`/parts`; it opens by itself when two
agents run) shows each agent's time, tool calls, files and last step, and the feed's check for each part,
so the person can watch the parts without asking you.

Commit first, so the tree is clean and each part's work is easy to see and to undo. Start them in one
message so they run at the same time (Claude Code: several Agent calls in one reply),
and wait for every report before merging. Money (painted art, generated video, songs) stays inside the
budget the person set, split between the parts that spend; each spend goes on the feed with
`progress spend`.

## 4. Merge, check, playtest, review

1. Read every report. Apply what the shared files need (wire the sound names and art paths into
   `game.json` and the code, the landing words into `game.json` `landing`).
2. `npm run build`, and fix what does not fit together yourself.
3. `npm run dev` in the background, then `npx --no-install homie-studio check <id> --url
   http://127.0.0.1:8787`: two browsers, one room, a finished round.
4. The `playtest` skill: the instruments, then its blind review by a fresh agent that has not seen the
   code, the codex or any report (`playtest` skill: `references/REVIEWER.md`). It ranks what is weak; fix
   the top of the list, and check again.
5. Update the codex: tick the milestone, a dated line under Latest for what changed, redraw it
   (`homie-studio codex <id>`, and the artifact if there is one), and end the feed (`progress end passed`).
6. Commit once, after the merge (`git add -A && git commit` in the studio).

## When a part goes wrong

A part that fails its own check, or writes outside its folders, is redone, not patched over: put its
folders back as they were at the last commit (`git restore -- <folder>`; `git clean -nd -- <folder>` lists
the new files it made there, and `git clean -fd -- <folder>` removes them), then brief it again with what
went wrong. Two failures in a row: do that part yourself, step by step.
