# Find references as one /goal prompt

The whole skill as one prompt. In Claude Code, paste it after `/goal`: the agent keeps working until the
"Done when" list holds. In other agents, paste it as the task. It does not need this skill installed.

A `/goal` agent cannot stop half-way to wait for you, so the prompt has it pick the references itself and hand
you a board at the end. You choose the idea on the board.

## Before you run it (optional, once)

```bash
claude mcp add --transport http refs https://refs.video/mcp                 # launch films and ads, free search
claude mcp add --transport http framethrower https://framethrower.ai/api/mcp # film, ad and animation frames; sign in with /mcp
npx skills add vargHQ/skills --skill media-download                          # Pinterest and YouTube downloads
```

Without them the agent still runs and says which sources it could not reach.

## The prompt

```text
/goal Find references and 10 visual ideas for this video: [what it is, who it's for, platform and aspect ratio, length, brand, 1–2 things I love, 1 thing I hate].

Go through these 7 sources in order and save what you open to refs/:
1. varg how to (curl -s "https://varg.ai/how-to/api/search?q=<format and look>"): style and prompt cards that already worked for this format. Search results carry no numbers: open the best 2–3 cards (add .md to the link) and copy their installs, stars or bookmarks.
2. X, last 7 days: posts in this format or look. Filter with min_faves:, then rank by bookmarks yourself. The prompt is in the post, its link or the author's first reply. Write likes, bookmarks, views and date into trends.md. No X access? Use web search and say so.
3. Refs (refs.video/mcp): launch films, demos and ads like this one. Free search gives title, length, summary and thumbnail; the shot-by-shot data needs a Refs account.
4. FrameThrower (framethrower.ai/api/mcp): film frames by light, lens, shot size, color and mood, plus its ads and animation libraries.
5. Film-Grab, Shot Cafe, Eyecannndy, ShotDeck: they block bots, so never fetch them. Write search links for me into links.md: film-grab.com/?s=<query>, shot.cafe/tag/<tag>, eyecannndy.com/technique/<technique>, shotdeck.com (search needs a login).
6. Pinterest and Are.na: search by attribute, not subject ("<film> still", "<decade> film grain", "<character> cosplay"). Download Pinterest images with gallery-dl; for Are.na, search it and put the channels in links.md.
7. YouTube: music videos, trailers, title sequences, game cinematics and ads people remember. Pull a 5–15 s clip with yt-dlp only where motion or pacing matters.

Find four kinds of reference: style (palette, light, texture, type), film (framing, lens, camera move), pop culture (moments people recognize) and trends (what people saved this week).

Rules: open every reference you keep and never describe a frame you didn't see. Borrow the look, never actors, characters, logos or recognizable people. Found frames are for words and judging, not for feeding an image or video model. Skip the first, obvious pick (for a sci-fi look, not Blade Runner). Copy every number exactly as the source shows it.

Done when:
- refs.md has 12+ references you opened: 3+ style, 3+ film, 2+ pop culture, 3+ trends from the last 7 days with their numbers. Each has its link, what it lends (palette, framing, light, lens, texture, motion), one job and what it must not copy.
- links.md has the searches only I can open.
- ideas.md has 10 visual ideas. Each combines 2+ references of different kinds and has a look line, the first shot, why now (a trend with its numbers, a different one per idea where you can; wild ideas may skip it) and the risk. 3 are close to this week's trends, 4 are stretches, 3 are wild. None falls back to centered text, a gradient background and everything fading in.
- board.html shows every reference and idea, numbered, with sources, so I can pick.
- You listed every source you could not reach.
```
