---
name: launch-film
description: Make a 20 to 40 second launch film (an MP4 at 1920x1080 with music and sound effects) for a product from its website or App Store page, using its real logo, colors, fonts and screens. Use it when the user asks for a launch video, product video, promo, teaser or announcement clip for a site or an app and gives its address. Everything renders locally with Chrome and ffmpeg; no account or API key.
---

# launch-film

A launch film made from the product itself: its logo cut from its own page, its colors and typefaces, its real screens in a browser window or a phone, and the words its site already uses. You plan the film as a short JSON file, render it, look at the frames, and hand over the MP4.

The tool is the `launch-film` npm package. It needs Node 22 or newer, Chrome or Chromium, and ffmpeg. Check them first:

```bash
npx -y launch-film@latest doctor
```

If ffmpeg is missing, tell the user how to install it (`brew install ffmpeg` on a Mac, `sudo apt install ffmpeg` on Debian or Ubuntu) and stop.

## 1. Get the brand and a first plan

```bash
npx -y launch-film@latest plan <url> --out film/<name>
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
npx -y launch-film@latest looks
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

A scene object has a `type` and its words. List every type and its fields with `npx -y launch-film@latest types`; icon names come from `npx -y launch-film@latest icons <word>`. The ones a launch film uses most:

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
npx -y launch-film@latest render film/<name>/film.json
```

Clips render two at a time; a 30 second film takes one to three minutes. The film is `film/<name>/film.mp4`. If a clip fails, the message names it: fix film.json and render again.

## 5. Look at the frames before you hand it over

```bash
npx -y launch-film@latest frames film/<name>/film.mp4
```

Open `film/<name>/frames/sheet.jpg` and the stills next to it, two for each clip. Check:

- every word is whole, inside the frame and spelled as written;
- no text lies on other text or runs out of its card;
- the logo is whole, sharp and the brand's own, on a ground it reads on;
- the screens are the product's and not a cookie banner or a login page;
- nothing is blank where something should show.

Fix what you find in film.json and render again. Then give the user the MP4's path, its length and look, and one line on each clip.

## Without a plan step

`npx -y launch-film@latest <url>` does all of the above in one go with the first plan, and saves the frames. Use it when the user wants a film quickly and has no wishes about the words.

## Options

- `--look <name>`, `--seconds <20-40>`, `--aspect 9:16` on `plan` or the one-go command.
- `--brand <folder>` uses an easybrandkit folder you already have; `--words <file>` a words.json you already have.
- `--no-music`, `--no-sfx` on the one-go command; or set `"music": false` and `"sfx": false` in film.json.
- `--jobs 1` renders one clip at a time on a slow machine.
