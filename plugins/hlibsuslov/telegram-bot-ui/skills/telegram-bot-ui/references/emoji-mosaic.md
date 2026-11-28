---
summary: "A video, GIF or picture cut into a premium emoji pack laid out as a mosaic: limits, tiles in step, how phones lay out rows, grid sizes, crop, what needs a token, the tool and the website."
verified: "2026-11-27"
bot_api: "10.5"
---

# Emoji mosaics: a video or picture as a premium emoji pack

> Labels: **API** = Bot API catalog text (`tgui.py lookup show <Symbol>`), **Official** = another
> core.telegram.org page, **Client code** = read in the open-source clients (Telegram-iOS, Telegram-Android,
> tdesktop/lib_ui, telegram-tt = Web A, tweb = Web K) in Nov 2026, may change with any release,
> **Observed** = seen in real clients, **Heuristic** = this skill's design rule, **Unverified** = the sources do
> not say. Tool: `scripts/emoji_mosaic.py` (`tgui.py mosaic …`).
> Website: telegram-bot-ui.hlixli.com/emoji/mosaic cuts the same tiles in the browser and writes the ZIP that
> `check` and `publish` read. Where its owner has set it up, it can also create the pack after a Telegram login.

## Contents

- [What it is and when to offer it](#what-it-is-and-when-to-offer-it)
- [Telegram's limits](#telegrams-limits)
- [Keeping the tiles in step](#keeping-the-tiles-in-step)
- [How phones lay the message out](#how-phones-lay-the-message-out)
- [What needs a token or a login](#what-needs-a-token-or-a-login)
- [Grid sizes](#grid-sizes)
- [Crop, corners and the loop](#crop-corners-and-the-loop)
- [Steps](#steps)
- [Putting the mosaic into a channel post](#putting-the-mosaic-into-a-channel-post)
- [Failures](#failures)

## What it is and when to offer it

The source is cut into a grid of 100x100 tiles. Each tile becomes one custom emoji of a new set, and one
message holds them all, a line per row, so the picture reassembles in the chat. An animated source gives video
emoji, which stay in step only when every tile has the same frames ([Keeping the tiles in
step](#keeping-the-tiles-in-step)).

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
| Frame rate in practice | a whole number, 30 or less, the same for every tile | **Client code**: Android and iOS truncate `avg_frame_rate`, so 29.97 plays as 29 |
| Video file size, stickers and emoji together | at most 256 KB | **Official** |
| Video file size, emoji | **at most 64 KB** | **Observed**: `createNewStickerSet` with 28 tiles refused with `STICKER_VIDEO_BIG` when the largest was 74.6 KB; an unofficial requirements list (gist.github.com/Gennnji/07398fc106d743e497f241a35eb21efa) gives 64 KB |
| Initial stickers in `createNewStickerSet` | 1-50; more go one by one through `addStickerToSet` | **API** |
| Emoji in one set | up to 200 | **API** (`addStickerToSet`) |
| Set icon | `setCustomEmojiStickerSetThumbnail` with one of the set's ids | **API** |
| Custom emoji in one message | `message_animated_emoji_max` from the client's appConfig; 100 observed | **Official** name, **Observed** value |
| Entity offsets and lengths | UTF-16 code units | **API** (`MessageEntity`) |
| Each custom emoji entity | wraps exactly one regular emoji | **Official** (core.telegram.org/api/custom-emoji) |
| Set name | letters, digits, underscores, starts with a letter, no `__`, ends in `_by_<bot_username>`, 1-64 chars | **API** |
| Using custom sets in messages | Telegram Premium for users | **Official** |
| A bot sending custom emoji | Fragment usernames, or **the bot owner's** Premium in private, group and supergroup chats | **API** (`references/custom-emoji.md`) |
| Row width on a phone | set by the grid, not by the text size, when the message holds only emoji | **Client code** ([How phones lay the message out](#how-phones-lay-the-message-out)) |
| System notifications | show only the fallback emoji, never the custom ones | **Client code** |

The tool keeps grids at 100 emoji or fewer; `--max-emoji` changes the cap if Telegram's value changes. Since a
notification shows only the emoji behind each tile, a mosaic of ⬜ arrives as rows of white squares: pick a
fallback that says something (`--fallback 🎬`), or let the website write one emoji per tile.

## Keeping the tiles in step

Every client plays each custom emoji on its own (**Client code**):

- **It starts each emoji when that emoji has loaded**, and **the loops never realign**. A tile whose loop is
  33 ms longer is one frame further off after every loop; a tile that loads late stays behind for good.
- So all the tiles of one mosaic must share **the frame rate, the frame count and the timestamps**; only the
  bitrate may differ from tile to tile.
- Use **a whole frame rate of 30 or less**: Android and iOS truncate `avg_frame_rate`, so a 29.97 FPS tile plays
  at 29 there.

What `make` does about it: it renders the whole mosaic once at one whole frame rate and cuts every tile from
those frames with the same `-r` and frame count. A tile over 56 KB is encoded again at the next lower bitrate,
160 down to 25 kbps (libvpx-vp9 constrained quality, a variable rate that never drops frames; never a lower frame
rate for one tile), and the smaller file is kept. When a tile can't fit 63 KB even at 25 kbps, **the whole
mosaic** is encoded again at half the frame rate. Then every tile's frames are counted, and one with another count stops the
run. `check` compares the tiles of a folder or ZIP and reports `FRAME_COUNT_DIFFERS`, `FPS_DIFFERS`,
`DURATION_DIFFERS` and `TIMESTAMPS_DIFFER` (errors), `FPS_NOT_WHOLE` (warning). The website's generator encoded
large tiles at half the frame rate until Nov 27, 2026: check an older ZIP and make it again if it fails.

Tiles with transparency (rounded corners, `--fit contain` on a transparent pad, a see-through source) carry a
second VP9 stream, are about twice the size and decode later, so they can start behind the opaque ones
(**Observed**). Leave `--round` at 0 unless the corners matter more than the sync; the website has it off by
default too. `--still` makes static tiles that can't drift.

## How phones lay the message out

**A message of custom emoji only is drawn as big emoji** (**Client code**): the tile size comes from the grid,
not from the reader's text-size setting, and a row wider than the message wraps, so its last tiles drop to a new
line and the picture falls apart.

- **iOS** (`ChatMessageAnimatedStickerItemNode.fontSizeForEmojiString`): tile = floor(94 x m) x 24/17 pt, with
  floor(94 x m) = 94, 78, 64, 49, 43, 35, 30, 25, 22, 19 for max(columns, rows) = 1, 2 … 10 and more. Rows of 5-8
  columns are 282-304 pt wide whatever the grid; a taller grid shrinks every tile.
- **Android** (`Theme.chat_msgTextPaintEmoji`, `MessageObject.checkEmojiOnly`): tile = (120 x k + 4) x 1.2 dp,
  k = 0.46, 0.46, 0.46, 0.34, 0.28, 0.22 for 1-6 emoji and 0.19 from 7, so about 32 dp from 7 emoji.
- **Room for a row** on the narrow phones many people have, an iPhone at 375 pt (mini, SE, Display Zoom) and an
  Android phone at 360 dp: iPhone chats and channels 327 pt, groups 289, forwards 282; Android chats and
  channels 266 dp (a channel or bot post's share button takes 14), groups 228, forwards 234.

**Any text in the message turns it into text mode** (**Client code**): the emoji are drawn at the reader's text
size, Android overlaps the rows by about 20%, and the other clients leave a gap between emoji and between rows.
Web K leaves that gap even in a message of emoji only. The gap is about 1 px between emoji and 5 px between rows
at 22 px, so text or thin lines lying on a seam look broken there. Send the mosaic as a message of its own, with
the words in another message.

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

`plan <file>` lists grids for the source's shape: the share a cover fit would crop and where the rows stay whole
on narrow phones, from the layout above (the same model as the website's `layoutFit` and `wrapsWhere`):

- **everywhere**: whole in chats, channels, groups and forwarded messages;
- **chats**: whole in private chats and channel posts; on a narrow phone the rows wrap in groups or forwards;
- **wraps**: the rows wrap even in a private chat or a channel post on a narrow phone.

It also names the closest grids that stay whole everywhere and in chats. The default grid has at most 8
columns, the shape within 5% when possible, rows that stay whole everywhere when that still gives 9 or more
emoji (else in chats and channels), and then the most emoji up to 40 (**Heuristic**: fewer, larger tiles read
better): 16:9 gives 7x4 (chats), 9:16 4x7 and a square 4x4 (both everywhere). `check` warns
`ROWS_WRAP_OUTSIDE_CHATS` for a chats grid and `ROWS_WRAP` for one that wraps in chats.

| Grid | iPhone tile / row, pt | Android tile / row, dp | Fit | Rows wrap on narrow phones in |
|---|---|---|---|---|
| 4x2, 4x3, 4x4 | 69.2 / 277 | 32.2 / 129 | everywhere | - |
| 4x7 | 42.4 / 169 | 32.2 / 129 | everywhere | - |
| 7x8 | 35.3 / 247 | 32.2 / 225 | everywhere | - |
| 5x3 | 60.7 / 304 | 32.2 / 161 | chats | iPhone groups and forwards |
| 6x3, 6x6 | 49.4 / 296 | 32.2 / 193 | chats | iPhone groups and forwards |
| 7x4 | 42.4 / 296 | 32.2 / 225 | chats | iPhone groups and forwards |
| 8x4, 8x8 | 35.3 / 282 | 32.2 / 257 | chats | iPhone forwards; Android groups and forwards |
| 9x5 | 31.1 / 280 | 32.2 / 289 | wraps | Android chats |
| 10x10 | 26.8 / 268 | 32.2 / 322 | wraps | Android chats |

From 9 columns the rows wrap in Android chats. With 5-8 columns a taller grid helps on iOS (7x8 stays whole
everywhere, 7x4 doesn't). A mosaic meant for groups or for forwarding needs an "everywhere" grid; one for a
channel post can use a "chats" grid. A simple wide logo often looks best at 4x2 (everywhere) or 6x3 (chats).

## Crop, corners and the loop

- **Auto (cover):** scale to fill the grid and cut the overflow evenly from both sides. Default.
- **Choose the region:** `--crop X,Y,W,H` (top-left corner and size) or `--corners X1,Y1,X2,Y2` (two opposite
  corners), in source pixels; then the fit applies to that region. On the website, drag the frame or its corners.
- **Fit:** `cover`, `contain` (pads with `--background`, transparent by default) or `fill` (stretch).
- **Rounded corners:** `--round R` cuts the mosaic's four outer corners with radius R canvas px; the corner
  tiles get real transparency (VP9 with alpha, or PNG), the edges stay opaque. Alpha tiles may start late.
- **Time:** `--start`, `--duration` (at most 3 s; default 2.9), `--fps` (a whole number up to 30, never above
  the source's; halved for the whole mosaic when a tile can't fit). `--pingpong` plays forward then back (each
  half at most 1.45 s) without repeating the turn frames.
- `--still` takes the frame at `--start` and makes static PNG tiles (smaller, never out of sync).
- Sources: video files, GIF, PNG, JPEG, WEBP, BMP, TIFF, AVIF, HEIC (what the installed ffmpeg decodes).
  Animated WebP and APNG keep only their first frame: convert them to MP4 first.

## Steps

1. Ask for the file and the use (post, welcome, community pack; groups or forwarding?). Confirm the user may use
   the material.
2. `tgui.py mosaic plan clip.mp4` → propose one grid with its reason ("7x4: crops 2%, rows stay whole in chats
   and channels; for groups take 4x2"), using the fit that matches where it will be shown.
3. `tgui.py mosaic make clip.mp4 --grid 7x4 [--corners …] [--start 1.5] --out mosaic/`. It writes
   `mosaic.json` (`tg-emoji-mosaic/v1`), `tiles/`, `canvas.png`, `preview.html`, and runs `check`. Tiles over
   56 KB are encoded again at lower bitrates; if one can't fit 63 KB, the whole mosaic goes to half the frame
   rate. One still over 64 KB after that is reported by `check` (`VIDEO_TOO_BIG`): shorten the clip, lower
   `--fps` or use `--still`.
4. Open `preview.html` and look: the mosaic as big emoji at an iPhone's size in a chat, on a dark theme and in a
   group or forward on a small iPhone (rows wrapped as Telegram wraps them), and with the gaps of Web K and text
   mode: seams, faces or text on a row line, the loop point. Adjust and redo.
5. `tgui.py mosaic publish mosaic/ --owner <id> --dry-run --bot-username <bot>` shows the set name and the calls.
6. Live, after the user's go. The default title is "Mosaic image via @hlixli"; tell the user and pass `--title`
   for their own. POSIX shells: `TELEGRAM_LIVE=1 TELEGRAM_BOT_TOKEN=… tgui.py mosaic publish mosaic/ --owner <id>
   --token-env TELEGRAM_BOT_TOKEN --save mosaic-pack.json`. PowerShell: `$env:TELEGRAM_LIVE="1";
   $env:TELEGRAM_BOT_TOKEN="…"` on one line, then the same command. It uploads the tiles, reads the set back, sets
   the centre tile as the set's icon (`--thumbnail`), sends the mosaic to the owner (`--send-to <chat id>` for
   another chat; `--no-send` to skip) and compares the `custom_emoji` entities that came back with the tiles.
7. Done only when: `check` reports no errors (warnings say where rows wrap), `delivered` is true, the set is
   `custom_emoji` with one unique id per tile, the `t.me/addemoji/<set>` link opens, and the user looked at the
   message on a phone, watching a few loops.

Same tiles, same set name: rerunning `publish` finishes an interrupted set instead of creating another, and
with `--save` it doesn't send the message twice (`--resend` sends it again). Exit code 5 means the outcome is
unknown (a lost answer): run the same command again. The website's ZIP is the same format, including the emoji
behind each tile: `check mosaic.zip`, then `publish mosaic.zip --owner …`. `message mosaic/ --ids
mosaic-pack.json [--html]` rebuilds the text and entities (UTF-16 offsets) or `<tg-emoji>` HTML from saved ids.
`delete <set> --yes` removes a set this bot made (an orphan from an earlier cut, or a mistake).

## Putting the mosaic into a channel post

The owner opens the bot's message, copies it and pastes it into a post (their Premium lets them use the set),
or forwards it without the author. The post holds the mosaic alone; its words go in a message before or after,
since any text turns the mosaic into text mode. A person publishes, not the agent. `--send-to` a channel works
only when the bot has Fragment usernames (`references/custom-emoji.md`) and goes through the `post` playbook's
approval.

## Failures

| Symptom | Cause | Fix |
|---|---|---|
| The message shows ⬜ squares | the bot can't use custom emoji in that chat, or the viewer has no Premium | the bot owner's Premium (private, group) or Fragment; `delivered` is false |
| A notification shows only plain emoji | notifications never show custom emoji | expected; pick a meaningful fallback or per-tile emoji |
| `PEER_ID_INVALID` on send | the recipient never wrote to the bot | `/start` the bot, rerun `publish` |
| `STICKER_VIDEO_BIG`, `file too big` (**Observed**) | a tile over about 64 KB: the real limit for video emoji, far below the documented 256 KB (refused at 74.6 KB) | `check` flags tiles over 64 KB; `make` again (it keeps tiles under 63 KB), shorter `--duration`, lower `--fps`, `--still`, or a calmer clip |
| `STICKER_VIDEO_LONG` (**Observed**) | over 3 s | shorter `--duration` |
| Tiles drift apart over a few loops | tiles with different frame counts or frame rates (one re-encoded at a lower rate) | `check` names them; `make` again so every tile has the same frames |
| A few tiles start late and stay behind | they loaded or decoded later: alpha tiles, a slow network | no rounded corners; resend; it can differ from one phone to another |
| The picture shifts sideways | rows wrapped: a row is wider than the message | a grid `plan` marks everywhere (groups, forwards) or chats (chats, channels); a taller grid shrinks iOS tiles |
| Rows overlap (Android) or show gaps | text in the same message: text mode | send the mosaic as a message of its own |
| A seam cuts a face or a word | it lies on a row line (Web K, text mode) | move the crop or change the row count |
| A second, half-filled set | the tiles changed between runs, so the name changed | keep `mosaic/` and rerun `publish`; `delete` the orphan |
| Exit code 5 | the answer was lost; Telegram may have done the work | run the same command again |
