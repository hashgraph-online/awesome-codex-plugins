---
name: launch-film
description: Make a 20 to 40 second launch film (an MP4 at 1920x1080 with music and sound effects) for a product from its website or App Store page, using its real logo, colors, fonts and screens. Use it when the user asks for a launch video, product video, promo, teaser or announcement clip for a site or an app and gives its address. It also makes launch pictures at the sizes stores and sites ask for (Product Hunt gallery, og:image, X, Google Play feature graphic, Chrome Web Store tiles), and checks any rendered video by measuring it (size, length, black or frozen stretches, silence, loudness, clipping, cuts on the beat). Everything runs locally with Chrome and ffmpeg; no account or API key.
---

# launch-film

A launch film made from the product itself: its logo cut from its own page, its colors and typefaces, its real screens in a browser window or a phone, and the words its site already uses. You plan the film as a short JSON file, render it, check it, and hand over the MP4, with launch pictures when the user wants them.

The tool is the `launch-film` npm package. It needs Node 22 or newer, Chrome or Chromium, and ffmpeg. Check them first:

```bash
npx -y launch-film@0.2.1 doctor
```

If ffmpeg is missing, tell the user how to install it (`brew install ffmpeg` on a Mac, `sudo apt install ffmpeg` on Debian or Ubuntu) and stop.

## 1. Get the brand and a first plan

```bash
npx -y launch-film@0.2.1 plan <url> --out film/<name>
```

Give the product's website, or its App Store or Google Play listing (then the listing's icon, screenshots and rating are used, with the colors, fonts and logo of the site it names). Not a social profile: easybrandkit refuses those.

This takes 30 to 90 seconds. It runs easybrandkit (logos, colors, fonts, first screen, store screenshots) into `film/<name>/brand/`, reads the words on the page into `words.json`, and writes `film.json`: a first plan that needs no brief.

Then read, in this order:

- `film/<name>/brand/BRAND.md` and look at `brand/card.png`: is the logo right, are the colors the brand's?
- `film/<name>/words.json`: the page's title, description, headings and the line under each heading.
- `film/<name>/film.json`: the plan.

If the brand looks wrong (a cookie wall, a login page, no logo), tell the user what you got and ask for the logo file or the right page. Do not go on with a wrong brand. If the site answered easybrandkit with a bot check, there is no kit: ask the user for the logo file and the main colors instead of guessing.

If launch-film says easybrandkit could not be fetched, npx could not download it (no network, or a registry without it): tell the user they can install it with `npm install -g easybrandkit`, and use `--easybrandkit <path to easybrandkit's scripts/easybrandkit.js>` when they have a copy.

## 2. Pick a look

```bash
npx -y launch-film@0.2.1 looks
```

The plan already picked one from the brand: `launch` (dark stage, depth, one bright accent) for dark sites and developer tools, `aurora` (frosted glass over soft color) for vivid consumer and AI products, `gridline` (Swiss grid on paper) for light B2B sites, `pop` (full color fields, stickers) for consumer apps, `journal` (serif headlines on warm paper) for editorial brands. Change `"look"` in film.json if the user asked for a style or another one fits better.

## 3. Write the scenes

film.json holds `look`, `aspect` (`16:9` or `9:16`) and `clips`, played in order. Each clip has a `kind` and a length in `bars` of the look's music (one bar is about 2 seconds; cuts land on the beat). You may give `seconds` instead.

| kind | what it shows | fields |
| --- | --- | --- |
| `scene` | type in motion: a title card, a headline, feature cards, a number | `scene`: a scene object |
| `screen` | a screenshot in a browser window coming in from depth | `image`, `mode` (`pan`, or `zoom` with `box` [x, y, w, h] in the picture's pixels), `side` |
| `shots` | two or three store screenshots side by side, as they are | `images` (a list) |
| `phone` | a phone's own screen capture in a drawn phone (not a store screenshot: many already show a phone) | `image` |
| `scroll` | a tall page scrolling in a window | `image` |
| `logo` | the logo close with the site's address | `logo` (an easybrandkit logo file) or `icon` (an app icon), `site` |

A scene object has a `type` and its words. List every type and its fields with `npx -y launch-film@0.2.1 types`; icon names come from `npx -y launch-film@0.2.1 icons <word>`. The ones a launch film uses most:

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
npx -y launch-film@0.2.1 render film/<name>/film.json
```

Clips render two at a time; a 30 second film takes one to three minutes. The film is `film/<name>/film.mp4`. If a clip fails, the message names it: fix film.json and render again.

## 5. Check the film before you hand it over

You can't watch the film or hear it, so measure it:

```bash
npx -y launch-film@0.2.1 check film/<name>/film.mp4 --expect 1920x1080@25 --seconds 20-40 --lufs -14
```

launch-film renders at 25 fps, 1920x1080 (1080x1920 for 9:16). `--seconds 20-40` is the range a launch film keeps to; when the user asked for a length, give that instead (`--seconds 30` allows half a second either way). Clips last whole bars, so a film planned for 30 seconds can come out two seconds short: to hit a length exactly, give the last clip `seconds` in place of `bars` and render again. `--lufs -14` is the loudness YouTube, X and most social apps play at. If the user has music cues from another tool, add `--cues cues.json` to see whether the cuts land on the beat.

Read `film/<name>/check/CHECK.md` first. It says PASS or FAIL and why, for each check: size, frame rate, length, black, still and silent stretches, loudness, true peak, clipping and cuts on the beat. A warning is something to look at, not always a fault: a title that rests or an end card is a hold, and you can pass the stretches you meant with `--allow 27-30`.

Then look, because a measurement can't read words. Open `check/sheet.png` (a frame from each shot) and `check/wave.png` (the sound over time, with the cuts). For two stills a clip, run `npx -y launch-film@0.2.1 frames film/<name>/film.mp4` and open `frames/sheet.jpg`. Check:

- every word is whole, inside the frame and spelled as written;
- no text lies on other text or runs out of its card;
- the logo is whole, sharp and the brand's own, on a ground it reads on;
- the screens are the product's and not a cookie banner or a login page;
- nothing is blank where something should show.

Fix what you find in film.json and render again. If the loudness or the peaks fail, tell the user what CHECK.md measured instead of rendering again: the render does not change them. Then give the user the MP4's path, its length and look, the check's verdict, and one line on each clip.

## 6. Launch pictures, when the user wants them

```bash
npx -y launch-film@0.2.1 stills film/<name>/film.json --for ph,og,x,play,chrome
```

This makes the pictures a launch needs from the same plan, at the exact size each place asks for, in `film/<name>/stills/`: the Product Hunt gallery (`ph-1.png` to `ph-6.png`, 1270x760) and thumbnail (240x240), `og.png` (1200x630) for link previews, `x.png` (1600x900) for a post on X, `play-feature.png` (1024x500) for Google Play, and the Chrome Web Store tiles (`chrome-small.png` 440x280 and `chrome-marquee.png` 1400x560). Ask for only the ones the user needs with `--for`; a site's address in place of film.json plans the film first.

Read `stills/STILLS.md` and look at every picture with the same list as the frames. The words come from film.json, so fix them there and run `stills` again. Then give the user the folder and say what each file is for.

## Without a plan step

`npx -y launch-film@0.2.1 <url>` does steps 1 to 4 in one go with the first plan, and saves the frames. Use it when the user wants a film quickly and has no wishes about the words, and check the MP4 as in step 5 before you hand it over.

## Options

- `--look <name>`, `--seconds <20-40>`, `--aspect 9:16` on `plan` or the one-go command.
- `--brand <folder>` uses an easybrandkit folder you already have; `--words <file>` a words.json you already have.
- `--no-music`, `--no-sfx` on the one-go command; or set `"music": false` and `"sfx": false` in film.json.
- `--jobs 1` renders one clip at a time on a slow machine.
