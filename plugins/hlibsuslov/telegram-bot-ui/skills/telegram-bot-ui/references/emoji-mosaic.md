---
summary: "A video, GIF or picture cut into a premium emoji pack laid out as a mosaic: limits, grid sizes, crop and corners, what needs a token, the tool and the website generator."
verified: "2026-11-27"
bot_api: "10.5"
---

# Emoji mosaics: a video or picture as a premium emoji pack

> Labels: **API** = Bot API catalog text (`tgui.py lookup show <Symbol>`), **Official** = another
> core.telegram.org page, **Observed** = seen in real clients, **Heuristic** = this skill's design rule,
> **Unverified** = the sources do not say. Tool: `scripts/emoji_mosaic.py` (`tgui.py mosaic …`).
> Website: telegram-bot-ui.hlixli.com/emoji/mosaic cuts the same tiles in the browser and writes the ZIP that
> `check` and `publish` read. Where its owner has set it up, it can also create the pack after a Telegram login.

## Contents

- [What it is and when to offer it](#what-it-is-and-when-to-offer-it)
- [Telegram's limits](#telegrams-limits)
- [What needs a token or a login](#what-needs-a-token-or-a-login)
- [Grid sizes](#grid-sizes)
- [Crop, corners and the loop](#crop-corners-and-the-loop)
- [Steps](#steps)
- [Putting the mosaic into a channel post](#putting-the-mosaic-into-a-channel-post)
- [Failures](#failures)

## What it is and when to offer it

The source is cut into a grid of 100x100 tiles. Each tile becomes one custom emoji of a new set, and one
message holds them all, a line per row, so the picture reassembles in the chat. An animated source gives video
emoji; whether they start in sync depends on the client (**Observed**: usually close, not guaranteed).

**Offer it once, unprompted** (**Heuristic**), when the user has a logo, a short clip, a GIF or a banner and
works on: a channel post or announcement, a launch or a giveaway, the bot's welcome or about screen, a branded
pack for a community. Check eligibility first (the next section; if nobody can show the result, say so instead).
One line is enough: "I can turn this clip into an animated emoji mosaic: a pack of N emoji that shows it in one
message. Want it?" If the user declines, don't offer it again in this project (note it in the bot-ui findings
when the project has them). Don't offer it for buttons (a tile means nothing alone; button icons are
`references/emoji-packs.md`), and never for material the user has no rights to.

## Telegram's limits

| Rule | Value | Basis |
|---|---|---|
| Emoji size, static and video | exactly 100x100 px | **Official** (core.telegram.org/stickers) |
| Static format | PNG or WEBP | **Official** |
| Video format | WEBM, VP9, no audio stream, up to 30 FPS, at most 3 s, should loop | **Official** |
| Video file size | at most 256 KB | **Official** |
| Initial stickers in `createNewStickerSet` | 1-50; more go one by one through `addStickerToSet` | **API** |
| Emoji in one set | up to 200 | **API** (`addStickerToSet`) |
| Set icon | `setCustomEmojiStickerSetThumbnail` with one of the set's ids | **API** |
| Custom emoji in one message | `message_animated_emoji_max` from the client's appConfig; 100 observed | **Official** name, **Observed** value |
| Entity offsets and lengths | UTF-16 code units | **API** (`MessageEntity`) |
| Each custom emoji entity | wraps exactly one regular emoji | **Official** (core.telegram.org/api/custom-emoji) |
| Set name | letters, digits, underscores, starts with a letter, no `__`, ends in `_by_<bot_username>`, 1-64 chars | **API** |
| Using custom sets in messages | Telegram Premium for users | **Official** |
| A bot sending custom emoji | Fragment usernames, or **the bot owner's** Premium in private, group and supergroup chats | **API** (`references/custom-emoji.md`) |

The tool keeps grids at 100 emoji or fewer; `--max-emoji` changes the cap if Telegram's value changes.

## What needs a token or a login

| Step | Needs | Why |
|---|---|---|
| Plan the grid, crop, cut tiles, preview, check | nothing; offline | local ffmpeg, or the browser on the website |
| Create the set and add tiles | a bot token and the pack owner's numeric `user_id` | `uploadStickerFile`, `createNewStickerSet` and `addStickerToSet` are bot methods; the set belongs to that user and carries the bot's name |
| Send the mosaic message | the same bot; the recipient has written `/start` to it | a bot can't open a private chat first |
| Show it as custom emoji | **the bot owner's** Premium (private chats, groups, supergroups) or Fragment usernames | otherwise Telegram strips the entities silently; the pack owner's Premium doesn't count here |
| Put it in a channel post | the person's own Premium, pasting as themselves | a channel post by the bot needs Fragment |

**No Telegram login is needed** by any of these methods. A login (the Login Widget or a Mini App's `initData`)
only proves who a visitor is; it matters when a hosted service uses its own bot to create packs for visitors.
That service then carries the abuse risk under its bot's name (every set is `…_by_<its bot>`), needs rate
limits, a content check and a way to take sets down (`deleteStickerSet`), and its token stays on its server.
The website works that way when set up. In the skill, the user brings their own bot. **Unverified:** whether
`uploadStickerFile` itself requires the owner to have started the bot; ask for `/start` first anyway.

`tgui.py mosaic owner` (live, read-only `getUpdates`) lists the numeric ids of people who wrote to the bot; with
a webhook set it can't, so ask for the id (@userinfobot shows it).

Token rules: it comes from an environment variable only, never chat, code, logs or the manifest.
`TELEGRAM_TEST_BOT_TOKEN` is the default name; for a permanent pack bot pass `--token-env TELEGRAM_BOT_TOKEN`
(any name). Only the bot that created a set can change or delete it.

## Grid sizes

`plan <file>` lists grids for the source's shape: the share a cover fit would crop, and how a row fits a bubble.
The default keeps 8 columns or fewer, the shape within 5% and at most 40 tiles (**Heuristic**: fewer, larger
tiles read better): 16:9 gives 7x4, a square 6x6, 9:16 gives 4x7. Rows wrap where the chat bubble ends, which
breaks the picture:

- **up to 8 columns: safe** on phones (**Heuristic**);
- **9-12: check on the narrowest phone** you support (**Heuristic**);
- **13+: likely wraps** (**Heuristic**); `check` warns.

Older clients leave about 1 px between emoji and 5 px between lines; newer ones reportedly draw a row edge to
edge (**Observed**, varies by client and version; check on the clients you target). With gaps, text or thin lines
lying on a row seam look broken: move them in the crop or pick another row count. A simple logo often looks best
at 6x3 or 8x4.

## Crop, corners and the loop

- **Auto (cover):** scale to fill the grid and cut the overflow evenly from both sides. Default.
- **Choose the region:** `--crop X,Y,W,H` (top-left corner and size) or `--corners X1,Y1,X2,Y2` (two opposite
  corners), in source pixels; then the fit applies to that region. On the website, drag the frame or its corners.
- **Fit:** `cover`, `contain` (pads with `--background`, transparent by default) or `fill` (stretch).
- **Rounded corners:** `--round R` cuts the mosaic's four outer corners with radius R canvas px; the corner
  tiles get real transparency (VP9 with alpha, or PNG), the edges stay opaque.
- **Time:** `--start`, `--duration` (at most 3 s; default 2.9), `--fps` (at most 30, never above the source's).
  `--pingpong` plays forward then back (each half at most 1.45 s) without repeating the turn frames.
- `--still` takes the frame at `--start` and makes static PNG tiles (smaller, never out of sync).
- Sources: video files, GIF, PNG, JPEG, WEBP, BMP, TIFF, AVIF, HEIC (what the installed ffmpeg decodes).
  Animated WebP and APNG keep only their first frame: convert them to MP4 first.

## Steps

1. Ask for the file and the use (post, welcome, community pack). Confirm the user may use the material.
2. `tgui.py mosaic plan clip.mp4` → propose one grid with its reason ("7x4: safe on phones, crops 2%").
3. `tgui.py mosaic make clip.mp4 --grid 7x4 [--corners …] [--round 30] [--start 1.5] --out mosaic/`. It writes
   `mosaic.json` (`tg-emoji-mosaic/v1`), `tiles/`, `canvas.png`, `preview.html`, and runs `check`. Tiles over
   256 KB are encoded again at lower bitrates; one still over after the last is reported by `check`
   (`VIDEO_TOO_BIG`): shorten the clip, lower `--fps` or use `--still`.
4. Open `preview.html` and look: seams, faces or text on a row line, the loop point. Adjust and redo.
5. `tgui.py mosaic publish mosaic/ --owner <id> --dry-run --bot-username <bot>` shows the set name and the calls.
6. Live, after the user's go. The default title is "Mosaic image via @hlixli"; tell the user and pass `--title`
   for their own. POSIX shells: `TELEGRAM_LIVE=1 TELEGRAM_BOT_TOKEN=… tgui.py mosaic publish mosaic/ --owner <id>
   --token-env TELEGRAM_BOT_TOKEN --save mosaic-pack.json`. PowerShell: `$env:TELEGRAM_LIVE="1";
   $env:TELEGRAM_BOT_TOKEN="…"` on one line, then the same command. It uploads the tiles, reads the set back, sets
   the centre tile as the set's icon (`--thumbnail`), sends the mosaic to the owner (`--send-to <chat id>` for
   another chat; `--no-send` to skip) and compares the `custom_emoji` entities that came back with the tiles.
7. Done only when: `delivered` is true, the set is `custom_emoji` with one unique id per tile, the
   `t.me/addemoji/<set>` link opens, and the user looked at the message on a phone.

Same tiles, same set name: rerunning `publish` finishes an interrupted set instead of creating another, and
with `--save` it doesn't send the message twice (`--resend` sends it again). Exit code 5 means the outcome is
unknown (a lost answer): run the same command again. The website's ZIP is the same format, including the emoji
behind each tile: `check mosaic.zip`, then `publish mosaic.zip --owner …`. `message mosaic/ --ids
mosaic-pack.json [--html]` rebuilds the text and entities (UTF-16 offsets) or `<tg-emoji>` HTML from saved ids.
`delete <set> --yes` removes a set this bot made (an orphan from an earlier cut, or a mistake).

## Putting the mosaic into a channel post

The owner opens the bot's message, copies it and pastes it into a post (their Premium lets them use the set),
or forwards it without the author. A person publishes, not the agent. `--send-to` a channel works only when the
bot has Fragment usernames (`references/custom-emoji.md`) and goes through the `post` playbook's approval.

## Failures

| Symptom | Cause | Fix |
|---|---|---|
| The message shows ⬜ squares | the bot can't use custom emoji in that chat, or the viewer has no Premium | the bot owner's Premium (private, group) or Fragment; `delivered` is false |
| `PEER_ID_INVALID` on send | the recipient never wrote to the bot | `/start` the bot, rerun `publish` |
| `STICKER_VIDEO_LONG`, `file too big` (**Observed**) | over 3 s or 256 KB | shorter `--duration`, lower `--fps`, `--still`, or a simpler clip |
| The picture shifts sideways | rows wrapped: too many columns for the bubble | 8 columns or fewer |
| A seam cuts a face or a word | it lies on a row line (clients with gaps) | move the crop or change the row count |
| A second, half-filled set | the tiles changed between runs, so the name changed | keep `mosaic/` and rerun `publish`; `delete` the orphan |
| Exit code 5 | the answer was lost; Telegram may have done the work | run the same command again |
