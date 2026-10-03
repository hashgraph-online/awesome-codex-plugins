---
name: video
description: Make trailers, music videos, cutscenes and page recordings for a Homie studio — a gameplay trailer captured from the studio's own running game and cut on the beat of its music; a recording of any web page while a script drives it (clicks, taps, keys, typing, scrolls, waits; Play and a few moves on the studio's own game page; a site walkthrough or product demo) in real time with honest frames; or generated footage from fal (Seedance and friends) through the creator's OWN fal account under a hard budget with a receipt for every call, drawn over with a JavaScript look and kinetic type, sync-checked, reviewed on contact sheets, delivered 16:9 and 9:16, and published as a video page on the studio's site (big files in the studio's own R2 when it has storage). Use when someone in a studio asks for a trailer, a teaser, a music video, a cutscene, a clip for social media, "a video of my game", a demo, a walkthrough or tutorial video of a site or app, or a recording of a page.
compatibility: Node 22, ffmpeg and Chrome. Generated footage uses the creator's own fal account (FAL_KEY); fal's own MCP server (https://mcp.fal.ai/mcp-relay) finds models and reads prices.
metadata:
  providers: fal
---

# Video for a studio

A studio is the folder with `studio.json`. Videos live in `videos/<slug>/`, listed in
`videos/manifest.json`; a published entry is a page at `/videos/<slug>/` on the studio's site,
playing the 16:9 cut (the 9:16 cut on a portrait phone). Everything runs through
`scripts/video.mjs` in this skill's folder (Claude Code:
`node "${CLAUDE_PLUGIN_ROOT}/skills/video/scripts/video.mjs" <command>`), from inside the studio.
It needs Node 22, ffmpeg and Chrome; `--json` on every command.

Check disk before any capture or render (`df -h .`): keep 10 GB free. Raw frames are deleted
once encoded. Finish in this turn: start the local site with the app's background-task tool
(not `nohup ... &` inside a command, which dies with the command) and wait on it.

## The rules that come first

`references/HONESTY.md` has them in full. In short:

- **No fabricated gameplay.** Anything shown as the game is captured from the game running. A
  generated shot is never passed off as gameplay, and a trailer that mixes both says which is
  which. Bots are bots: never imply a crowd that was not there.
- **No real people, no real brands.** No likeness, voice or name of a real person, no real logo,
  product or copyrighted character, in prompts, references or type.
- **Money only with a budget.** Every paid call is priced first, fits inside the cap the person
  set, and leaves a receipt the moment the provider accepts it.

## Which video

- **A gameplay trailer** (15 to 60 s): real footage of the studio's own game, cut on the beat of
  the studio's music. No provider, no money. Recipe: section A below, detail in
  `references/TRAILER.md`.
- **A music video, a cutscene, a teaser with generated footage**: fal models under a budget,
  then drawn over. Section B, detail in `references/METHOD.md`.
- **A recording of a page while it is used**: the studio's own game page (land, press Play, play a
  little), a site walkthrough, a product demo, a tutorial. A steps file drives it. Section C, detail in
  `references/RECORD.md`.

Both start with `node <video.mjs> check` (ffmpeg, Chrome, the studio; fal only if a key is set).

## A. A gameplay trailer

```sh
npm run dev                                                    # background task; the site at http://127.0.0.1:8787
node <video.mjs> capture <slug> --game <id> --url http://127.0.0.1:8787 --seconds 60
node <video.mjs> card <slug> --name title --text "<GAME NAME>" --sub "<one line>" --game <id>   # the game's palette and font
node <video.mjs> card <slug> --name end --text "Play free" --sub "<site>/<id>/play" --small "Real gameplay. Empty seats are filled by bots."
node <video.mjs> edl <slug> --length 30 --song <music slug> --title "<GAME NAME>"
node <video.mjs> cut <slug>
node <video.mjs> sync <slug>
node <video.mjs> sheet <slug> --in videos/<slug>/<slug>.mp4
```

- When the trailer is done, stop the local site with `npx --no-install homie-studio dev --stop`
  (it stops exactly this studio's server), never with a name pattern like `pkill -f wrangler`.
- Port 8787 taken by another site (curl it: a different studio's title answers)? Run
  `npx --no-install homie-studio dev --port <free port>` and use that address.
- `capture` records the game's big screen (`/<id>/tv`: a spectator in a live public room, bots in
  empty seats) off a headless GPU Chrome for real seconds, with the game's own WebAudio sound on
  the same clock (the browser is muted; nothing plays out loud). It presses nothing. The live
  site works too (`--url` the studio's address); a local run keeps strangers out of the shot.
  A heavy game paints few frames at 1920x1080 (it prints "fps from the page" and a note when that
  is well under the film's 30): capture again with `--scale 0.67` (a 1280x720 page, scaled up to
  1920x1080 when it is encoded) or a lower `--fps`. One game measured 8 fps at 1080p and 39 at 720p.
- The bed is the studio's own song (`--song`, from the `music` skill) or the game's sound alone.
  No song yet: the `sound` skill synthesizes a theme for free (its bar grid cuts the trailer the same
  way), or the `music` skill renders one with ElevenLabs (credits: ask).
- `edl` finds the song's bar lines, picks the busiest moments of the capture (motion, not guesses),
  and writes `work/edl.json`: a title card of one bar, shots of one bar each, the end card on what
  is left. Title and end cards made with `card … --game <id>` wear the game's palette and display font
  (`games/<id>/style.json`, the `style` skill's decisions). Every cut lands on a bar line. Read it and change it: order, which moments, where the
  song starts (`--bed-from-bar`).
- `cut` renders both deliveries: 16:9 (1920x1080) and 9:16 (1080x1920, the whole game frame over a
  blurred fill, never a crop that hides the action), 30 fps, the song and the game's sound mixed,
  -14 LUFS, BT.709 tags, faststart, and a poster frame.
- `sync` checks every cut: the picture must change within one frame of the sound's onset.
  `sheet` makes a contact sheet: **open it and look** before anyone else sees the video.
- `node <skill folder>/scripts/qa.mjs videos/<slug>/<slug>.mp4` checks the delivered file itself: every
  frame decodes, phone-safe encoding, faststart, no black or frozen stretches, loudness and true peak,
  under the site's 25 MiB. Fix every FAIL before `add`. Delivery, capture and honesty traps:
  `references/DELIVERY.md`.

## B. Generated footage: a music video, a cutscene

**The provider, only now.** fal through the person's own account: they create a key at
https://fal.ai/dashboard/keys and set `FAL_KEY` in the environment Claude or Codex runs in
(never pasted into the chat, never written into the studio). `check` tests it for free.
**fal's own MCP server** is the way to find models and read their input schemas and prices
(`search_models`, `recommend_model`, `get_model_schema`, `get_pricing`): use it rather than memory,
because video endpoints retire and reprice monthly. Not connected? Offer it, and the person signs in
on fal's own page (no key): in Claude Code `claude mcp add --transport http --scope user fal
https://mcp.fal.ai/mcp-relay`, then `/mcp`; in Codex `codex mcp add fal --url
https://mcp.fal.ai/mcp-relay`, then `codex mcp login fal`. **Paid calls go through `video.mjs gen`,
never the MCP's `run_model` or `submit_job`**: `gen` prices, caps, receipts and resumes; the MCP call
does none of that (the Homie mod in Claude Code, and Homie's hooks in Codex, hold one as a call whose cost cannot be read first).

**The budget, before the first call.** Plan the shots, price one of each kind, add them up, and
ask the person for a cap in dollars:

```sh
node <video.mjs> price --model <fal model> --input <input.json>       # free: fal's own unit price x this input
node <video.mjs> budget <slug> --cap <dollars they agreed to>
node <video.mjs> gen <slug> --model <model> --input <input.json> --out work/<file> --dry-run
node <video.mjs> gen <slug> --model <model> --input <input.json> --out work/<file> --yes
```

`gen` refuses with no budget, refuses past the cap, and asks again without `--yes`. The receipt is
written the moment fal accepts the job (`videos/<slug>/budget.json`, `videos/receipts.jsonl`).
Running the same `gen` again resumes the job from `<out>.request`; it never pays twice. Strings
`"@file:<path>"` in the input are uploaded to fal's storage first (free). A model whose billing
unit the script cannot count is refused, not guessed: price it by hand from the model page. Spend
the riskiest shot first (the pilot), look at it, then the rest.

**The method** (`references/METHOD.md` has every step):

1. A **style sheet** (`videos/<slug>/STYLE.md`): palette, line, type, what the look risks.
2. **Character and set sheets** with an image model, one call each, checked against the style.
3. A **shot list on the beat grid**: `node <video.mjs> grid <slug> --song <music slug>` gives the
   song's beats, bars and every sung word's time; each shot starts and ends on a bar line.
4. **Bases**: reference-to-video with the sheets as image references and the song's cut for that
   shot as the audio reference (`slice`), so mouths and hits land on the music. 480p or 720p is
   enough under a draw-over.
5. **Sync check** on every base: `lag <slug> --base <clip> --ref <cut>`. A clip that sings its
   reference plays it back at 0 ms; anything else is regenerated or shifted.
6. **Draw-over and kinetic type**: `film init <slug>`, `film frames <slug> --base <clip> --id <shot>`,
   edit `film/shots.json` and `film/look.js`, then `film render <slug>` (and `--mode v` for 9:16).
   Every frame is a function of time, rendered frame-exactly in a headless browser.
7. **The sync loop**: `words <slug> --in <cut>` (a frame at every sung word, labelled) and
   `sync <slug> --in <cut> --at <hit times>`. Fix and re-render until every word and hit lands.
8. **Contact-sheet review**: `sheet <slug> --in <cut> --every 1`. Look at every cell. Then
   `scripts/qa.mjs <cut>` on each delivery (`references/DELIVERY.md`: continuity, faces, green screens).
9. **Deliver** 16:9 and 9:16 (the film's two modes), then the page (below).

## C. A page recording: a script drives the page

```sh
npm run dev                                                    # background task; the site at http://127.0.0.1:8787
node <video.mjs> record <slug> --steps <steps.json> --url http://127.0.0.1:8787 [--device phone] [--name <take>]
node <video.mjs> sheet <slug> --in videos/<slug>/work/record/recording.mp4
```

- The steps file says where to start and what to do, one step after another: `click`, `tap`, `drag`,
  `hover`, `key`, `keys`, `type`, `scroll`, `goto`, `wait`, and `waitFor` a selector, a text or a state
  (`"js"`), in the page or in the game's own frame (`"frame": "game"`). Any step can carry a
  `"caption"`. `references/examples/studio-play.json` records a studio's own game from its landing:
  Play, then the arrow keys; `studio-play-phone.json` the same on a phone with the game's touch stick.
  Both are tested against a real studio. Every step: `references/RECORD.md`. A Game Lab's side by side
  (New beside Today, slowed down, stepped through its phases) is a page too:
  the `lab` skill's `references/record-lab.json` records it from the lab's own address.
- It runs in real time on a headless GPU Chrome: nothing sped up, nothing cut. Every frame is one the
  page drew; a moment it did not repaint is held and counted, never interpolated. A visible cursor and
  press rings show where the script pointed (`--no-cursor` drops them); the take's honesty line says so.
- `recording.json` has each step's second, what its frame received (keys, presses, touches: delivered,
  not judged), the page's and the game's real frame rates and the renderer. Under 20 fps or on a
  software renderer it warns: that take shows a slow computer, not the page.
- Then `sheet` and look; `add <slug> --file videos/<slug>/work/record/recording.mp4 --kind clip
  --title "…"` (copy its `captions.vtt` to `videos/<slug>/captions.vtt` first) and `publish`. Or cut
  it into a trailer like any capture.
- Outside a studio: `node <skill folder>/scripts/record-page.mjs --steps <steps.json> --out <folder>`
  records any address (it needs Chrome, ffmpeg and puppeteer-core).

## The game's landing

A published trailer with `--for-game <id>` plays, muted, in the hero of that game's landing page when the
game has no hero loop of its own, and the landing links to it ("Watch the trailer"). The best hero is a
short silent loop of real play in `games/<id>/hero/` (the `game` skill, "Its landing page", cuts it from a
`capture`).

## The page

```sh
node <video.mjs> add <slug> --title "<Title>" --blurb "<one line>" --kind trailer|music-video|cutscene [--for-game <id>] [--for-song <music slug>] --publish
node <video.mjs> publish <slug>
```

A studio needs no storage for this: the site serves each file itself, up to 25 MiB a file, and
`cut` and `film render` hold their deliveries under that (a longer video gets a lower bitrate).
Bigger masters stay in the studio folder. A studio with storage (`storage add`: R2 on the studio's
own Cloudflare account, which asks the person for a payment method first) keeps its big media there
by default: the deploy uploads each delivery (over 1 MiB, or left out of git), reads it back and
checks it by SHA-256 before the site stops carrying it, and the page plays it at the same address.
Cuts can then run at 12 Mbit/s. R2 has no egress fees; storage is free up to 10 GB-month, then
US$0.015 per GB-month.

`add` writes the manifest entry: the 16:9 cut the player plays, the 9:16 cut, the poster,
captions if there is a `captions.vtt`, the credits (the models used, the song's credits), the
honesty line from the capture (or the recording), and the money spent. `publish` redeploys (with
storage, the deploy moves the big files to R2 first, each checked by SHA-256), and checks the page
(200) and the video (a byte range, 206: phones seek with them) at its address. A studio not online
yet: the `publish` skill first.

## Tell the person

The page link, the length, both files, what it cost (from the receipts) against the cap, what
is generated and what is captured, and what the sync check and the contact sheet showed. Commit
`videos/` (big media stays out of git; the manifest, edl, shot list, film code and receipts go in).

## Never

- Never show generated footage as gameplay, or a bot as a person.
- Never put a real person, a real brand or a copyrighted character in a prompt, a reference or
  the type.
- Never spend without a budget, past it, or without a receipt; never print or store a key.
