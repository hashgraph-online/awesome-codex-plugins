---
name: launch-film
description: Make a 20 to 40 second launch film (an MP4 at 1920x1080 with music and sound effects) for a product from its website or App Store page, using its real logo, colors, fonts and screens. Use it when the user asks for a launch video, product video, promo, teaser or announcement clip for a site or an app and gives its address. It also makes launch pictures at the sizes stores and sites ask for (Product Hunt gallery, og:image, X, Google Play feature graphic, Chrome Web Store tiles), and checks any rendered video by measuring it (size, length, black or frozen stretches, silence, loudness, clipping, cuts on the beat). Everything runs locally with Chrome and ffmpeg; no account or API key.
---

# launch-film

A launch film made from the product itself: its logo cut from its own page, its colors and typefaces, its real screens in a browser window or a phone, and the words its site already uses. You plan the film as a short JSON file, render it, check it, and hand over the MP4, with launch pictures when the user wants them.

The tool is the `launch-film` npm package. It needs Node 22 or newer, Chrome or Chromium, and ffmpeg and ffprobe 4.4 or newer. Check them first:

```bash
npx -y launch-film@0.3.2 doctor
```

If ffmpeg or ffprobe is missing, cannot be started or is older than 4.4, tell the user how to install ffmpeg, which comes with ffprobe (`brew install ffmpeg` on a Mac, `sudo apt install ffmpeg` on Ubuntu 22.04, Debian 12 or newer), and stop. doctor also starts Chrome once: if it finds no Chrome, or says that Chrome could not start its sandbox or did not start, tell the user what it says and stop. Each program's line says what is wrong with it. A command that cannot start ffmpeg, ffprobe or Chrome stops before any work with a message that starts `launch-film needs ffmpeg` (or ffprobe, or Chrome) and names the setting or the PATH entry that gave it, what is wrong with it and how to point to one that works. A message that starts `launch-film could not run its stand-ins` or `launch-film cannot put its stand-ins` (the temp folder cannot hold the programs that keep a page from starting one of the machine's, or the machine was too busy to run them), `launch-film cannot start Chrome from the temp folder` (the temp folder's path is too long for Chrome), or `launch-film could not start` says what to do as well. Pass any of these on to the user and stop.

## 1. Get the brand and a first plan

```bash
npx -y launch-film@0.3.2 plan <url> --out film/<name>
```

Give the product's website, or its App Store or Google Play listing (then the listing's icon, screenshots and rating are used, with the colors, fonts and logo of the site it names). Not a social profile: easybrandkit refuses those.

This takes 30 to 90 seconds. It runs easybrandkit (logos, colors, fonts, first screen, store screenshots) into `film/<name>/brand/`, reads the words on the page into `words.json`, and writes `film.json`: a first plan that needs no brief.

Then read, in this order:

- `film/<name>/brand/BRAND.md` and look at `brand/card.png`: is the logo right, are the colors the brand's?
- `film/<name>/words.json`: the page's title, description, headings and the line under each heading.
- `film/<name>/film.json`: the plan.

If the brand looks wrong (a cookie wall, a login page, no logo), tell the user what you got and ask for the logo file or the right page. A note that the page tried to open an address that is not a web address, such as mailto:, means the site asked the browser to start a program: on Linux none was started, and on a Mac or Windows the note says a program may have opened, so tell the user. Do not go on with a wrong brand. If the site answered easybrandkit with a bot check, there is no kit: ask the user for the logo file and the main colors instead of guessing.

launch-film opens the address given on any port when its host is an IPv4 address or a name with a dot, and the pages on its scheme, host and port; `localhost` and `[::1]` are refused before any work, so give `http://127.0.0.1:<port>/`, or for a server that listens on `::1` alone, as one started on localhost can, a name under localhost such as `http://dev.localhost:<port>/`. Every other address it or the Chrome that reads the page opens, a redirect, a page's move, the page a kit given with `--brand` names, the site an App Store listing names, the listing's pictures and the typefaces, it opens only on port 80 or 443 of the public internet, never at an address of the user's machine or on one of its networks. If a plan says the page could not be read because it is on another port, is not on the public internet, is at an address of the machine or one `MAKERSMCP_REFUSE_ADDRESSES` refuses, that page was not opened: when it is the page a kit names, tell the user that address and why it was not opened, and plan again with it as the address only once the user says it is their own site, never for one `MAKERSMCP_REFUSE_ADDRESSES` refuses, which is refused as the address too; or give the page's words with `--words`. Where the page refused is the address given itself, as one `MAKERSMCP_REFUSE_ADDRESSES` names or one at a name whose answers mix, the plan stops before easybrandkit starts: only a kit made elsewhere with `--brand` together with the page's words with `--words` plans then, as either alone is refused the same way. A refusal that says an address is "on a host whose name answers with an address on the public internet, <address>, and with one ..." means that name leads both to the public internet and elsewhere: tell the user to have the machine answer that name with the address they mean alone, as a line in its hosts file does. A last line that says `MAKERSMCP_REFUSE_ADDRESSES holds` means that setting does not parse: tell the user, who sets it. A note `While launch-film read <page>, the browser asked for <address>, which <reason>: it was not reached.`, or the same from easybrandkit, passed on from the kit, names what the page, or the browser by itself, asked for besides at an address launch-film does not open, and the plan was made without it. Only where it names the user's own site under development on another port, as its scripts or data, tell the user, who can serve the site whole from one port and plan again. A page whose content all comes from another port shows easybrandkit nothing, and the plan stops with its `still shows no content after 30 s`: do not plan it again as it is, but tell the user to serve the site whole from one port, as a build of its assets, and then plan again. If no page can be read on a network that reaches the web only through a proxy (`HTTPS_PROXY` or the like), that is why: launch-film and its Chrome use no proxy, so plan where the web is reached directly, or give a kit made elsewhere with `--brand` and the page's words with `--words`. A site whose server drops many attempts to connect can hold a plan for about a minute and a half, and its note then says Chrome did not answer, which there means the site, not the machine: the plan goes on with the page's HTML, and where that could not be fetched either, give the page's words with `--words`. When easybrandkit says to give it more time with `--timeout`, which a plan does not take, run `npx -y easybrandkit@0.4.3 <url> --timeout 240 --out <kit>` and then plan with `--brand <kit>`. A line that says Chrome could not read the page because it does not send its requests through launch-film's proxy, or because its WebRTC sends UDP past it, means a Chrome policy or a program that starts Chrome changed how it connects: the plan went on with the page's HTML, so tell the user.

The site an App Store listing names is read with easybrandkit 0.4.3 or later, which is also the first to refuse what `MAKERSMCP_REFUSE_ADDRESSES` names: where easybrandkit could not read the listing itself, an older one, on PATH or given with `--easybrandkit`, leaves the film of that App Store page to the listing alone, and the plan says `Unknown option: --named-by`. If launch-film says easybrandkit could not be fetched, npx could not download it (no network, or a registry without it): tell the user they can install it with `npm install -g easybrandkit`, and use `--easybrandkit <path to easybrandkit's skills/easybrandkit/scripts/easybrandkit.js>` when they have a copy.

## 2. Pick a look

```bash
npx -y launch-film@0.3.2 looks
```

The plan already picked one from the brand: `launch` (dark stage, depth, one bright accent) for dark sites and developer tools, `aurora` (frosted glass over soft color) for vivid consumer and AI products, `gridline` (Swiss grid on paper) for light B2B sites, `pop` (full color fields, stickers) for consumer apps, `journal` (serif headlines on warm paper) for editorial brands. Change `"look"` in film.json if the user asked for a style or another one fits better.

## 3. Write the scenes

film.json holds `look`, `aspect` (`16:9` or `9:16`), `music` and `clips`, played in order. `music` is `true` for the look's own bed, `false` for none, `{ "volume": 0.55 }` for the bed at another level (0 to 2), or the path of a track, from film.json's folder or absolute, at least as long as the film. Each clip has a `kind` and a length in `bars` of the look's music (one bar is about 2 seconds; cuts land on the beat). You may give `seconds` instead.

| kind | what it shows | fields |
| --- | --- | --- |
| `scene` | type in motion: a title card, a headline, feature cards, a number | `scene`: a scene object |
| `screen` | a screenshot in a browser window coming in from depth | `image`, `mode` (`pan`, or `zoom` with `box` [x, y, w, h] in the picture's pixels), `side` |
| `shots` | two or three store screenshots side by side, as they are | `images` (a list) |
| `phone` | a phone's own screen capture in a drawn phone (not a store screenshot: many already show a phone) | `image` |
| `scroll` | a tall page scrolling in a window | `image` |
| `logo` | the logo close with the site's address | `logo` (an easybrandkit logo file) or `icon` (an app icon), `site` |

A scene object has a `type` and its words. List every type and its fields with `npx -y launch-film@0.3.2 types`; icon names come from `npx -y launch-film@0.3.2 icons <word>`. The ones a launch film uses most:

```json
{ "type": "opener", "title": "Acme Notes", "text": "Notes that think with you" }
{ "type": "headline", "title": "Write once and find it *anywhere*" }
{ "type": "features", "items": [
  { "icon": "lightning", "title": "Instant search", "text": "Find any note in a blink" },
  { "icon": "shield-check", "title": "Private by design", "text": "Encrypted end to end" },
  { "icon": "users-three", "title": "Shared spaces", "text": "Plan launches with your team" } ] }
{ "type": "number", "value": "12,000+", "text": "teams use it every day" }
```

Words between asterisks are set in the accent color. Rules for the words:

- Every word on screen comes from the page (`words.json`, BRAND.md) or from the user. Never invent a number, a customer, a quote or a claim.
- You may shorten the page's sentences. Keep each scene readable in its time: about 15 letters a second plus a second and a half.
- Mark one or two words a scene, not more.
- No em dashes or en dashes on screen; use a comma or a period.
- Keep the film between 20 and 40 seconds: an opener first, the logo close last, never two screens in a row.

## 4. Render

```bash
npx -y launch-film@0.3.2 render film/<name>/film.json
```

Clips render two at a time; a 30 second film takes one to three minutes. The film is `film/<name>/film.mp4`. If a clip fails, the message names it: fix film.json and render again. When it says that Chrome did not answer in time or that the page did not load, the machine was too busy: render again with `--jobs 1`. When it says that the system ran out of memory, after "Chrome's page crashed", "Chrome could not capture frame", "Chrome was stopped by SIGKILL" or "ffmpeg was stopped by SIGKILL", render again with `--jobs 1` too, which needs less. When it says that Chrome could not start its sandbox, tell the user what the message says to do, and stop. When it says that a WAV track "has no sound ffmpeg can read" and doctor's ffmpeg line says 9.0.2, the WAV may start with an ID3v2 tag, which that ffmpeg reads as no sound: ask the user to save it again without the tag, or to give it as a FLAC, MP3 or M4A file.

A run that fails or is stopped changes nothing in the folder: the last good plan, brand, film, frames, stills and check stay. Fix the cause and run it again. An earlier file the user made read-only is not replaced: the run names it and stops. That does not hold inside `brand/`: a plan replaces that folder whole, so a plan given a kit with `--brand` takes read-only files there away with the rest. A frames, stills or check folder that is a link takes the new files in the folder it leads to. An earlier file that is a link is replaced by a plain file, and what it led to is left alone; a new file has the mode a new file gets on that system, not the one the earlier file was given.

## 5. Check the film before you hand it over

You can't watch the film or hear it, so measure it:

```bash
npx -y launch-film@0.3.2 check film/<name>/film.mp4 --expect 1920x1080@25 --seconds 20-40 --lufs -14
```

launch-film renders at 25 fps, 1920x1080 (1080x1920 for 9:16). `--seconds 20-40` is the range a launch film keeps to; when the user asked for a length, give that instead (`--seconds 30` allows half a second either way). Clips last whole bars, so a film planned for 30 seconds can come out two seconds short: to hit a length exactly, give the last clip `seconds` in place of `bars` and render again. `--lufs -14` is the loudness YouTube, X and most social apps play at, and a render brings the film's sound to it. If the user has music cues from another tool, add `--cues cues.json` to see whether the cuts land on the beat.

Read `film/<name>/check/CHECK.md` first. It says PASS or FAIL and why, for each check: size, frame rate, length, black, still and silent stretches, loudness, true peak, clipping and cuts on the beat. A warning is something to look at, not always a fault: a title that rests or an end card is a hold, and you can pass the stretches you meant with `--allow 27-30`.

Then look, because a measurement can't read words. Open `check/sheet.png` (a frame from each shot) and `check/wave.png` (the sound over time, with the cuts). For two stills a clip, run `npx -y launch-film@0.3.2 frames film/<name>/film.mp4` and open `frames/sheet.jpg`. Check:

- every word is whole, inside the frame and spelled as written;
- no text lies on other text or runs out of its card;
- the logo is whole, sharp and the brand's own, on a ground it reads on;
- the screens are the product's and not a cookie banner or a login page;
- nothing is blank where something should show.

Fix what you find in film.json and render again. If the loudness or the peaks fail, tell the user what CHECK.md measured instead of rendering again: the render does not change them. Then give the user the MP4's path, its length and look, the check's verdict, and one line on each clip.

## 6. Launch pictures, when the user wants them

```bash
npx -y launch-film@0.3.2 stills film/<name>/film.json --for ph,og,x,play,chrome
```

This makes the pictures a launch needs from the same plan, at the exact size each place asks for, in `film/<name>/stills/`: the Product Hunt gallery (`ph-1.png` up to `ph-6.png`, 1270x760: the first picture, then one for each scene of the film after it) and thumbnail (240x240), `og.png` (1200x630) for link previews, `x.png` (1600x900) for a post on X, `play-feature.png` (1024x500) for Google Play, and the Chrome Web Store tiles (`chrome-small.png` 440x280 and `chrome-marquee.png` 1400x560). Ask for only the ones the user needs with `--for`; a site's address in place of film.json plans the film first.

Read `stills/STILLS.md` and look at every picture with the same list as the frames. The words come from film.json, so fix them there and run `stills` again. Then give the user the folder and say what each file is for.

## Without a plan step

`npx -y launch-film@0.3.2 <url>` does steps 1 to 4 in one go with the first plan, and saves the frames. Use it when the user wants a film quickly and has no wishes about the words, and check the MP4 as in step 5 before you hand it over.

## Options

- `--look <name>`, `--seconds <20-40>`, `--aspect 9:16` on `plan` or the one-go command.
- `--brand <folder>` uses an easybrandkit folder you already have; `--words <file>` a words.json you already have.
- `--no-music`, `--no-sfx` on `plan` or the one-go command, which write `"music": false` and `"sfx": false` into film.json; for a film already planned, set them in film.json and render again.
- The cuts fall on bars of the look's own tempo: launch 112 BPM, aurora 96, gridline 120, pop 124, journal 90. A track's beats meet every cut when a bar of the look holds a whole number of the track's beats, with its hit on a cut: four at the look's tempo, two at half of it, eight at twice it, or five for a 120 BPM track in aurora. So when the user has a track of their own, read its tempo first, before you plan the film and before you fit the track (`npx musicfit@latest <track> --analyze`), and plan the film in a look that fits it, or tell the user some cuts will fall between beats.
- Once the film has rendered, fit the track to it in a folder of its own, with the film's length and the logo close's start from film.timeline.json: `npx musicfit@latest <track> --length 29.333 --hit 24 --fps 25 --out film/<name>/music`. Set `"music"` in film.json to `"music/fitted.wav"` (a path from film.json's folder, or an absolute one) and render again. The track plays in place of the bed at about the bed's level, with its own build and drop, cut at the film's end and faded over the last second, under the sound effects. A track shorter than the film is refused, and the message gives the musicfit command that fits it: the track, the length, the hit and the folder, quoted for the shell. For an earlier fit that the film has outgrown, the command fits the track it was made from again; when that track was not found, the command has a word in quotes such as `'<song.mp3>'` where its path goes: ask the user for it. `check` with `--cues film/<name>/music/cues.json` shows which cuts land on the beat.
- `--jobs 1` renders one clip at a time, on a slow machine or one short of memory: give it when a render says that Chrome did not answer in time, that the page did not load, or that the system ran out of memory.
