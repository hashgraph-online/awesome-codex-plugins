---
name: find-movie-clips
description: >-
  Finds the video clip of a movie or TV scene and turns it into one clean reference take for an
  AI remake, a parody, an edit or a motion-control run. Covers which clip database fits a quote,
  a film and scene, a look or a character; which of them an agent may fetch and which only a
  person opens; a tested yt-dlp search and download; cutting straight from a public-domain film
  on the Internet Archive; a script that splits a scene into uncut takes with a contact sheet;
  the rules for a take a video model can follow; and a rights check. Use when someone asks
  where to find movie clips, film scene references, a scene by its quote, scene packs, a
  reference video for Seedance, Kling Motion Control, MiniMax Recast or Higgsfield Genjutsu, or
  says the source has cuts, watermarks or black bars. For still frames use find-references; for
  the remake itself use scene-recast-video.
license: MIT
metadata:
  author: vargHQ
  version: "1.4.0"
  openclaw:
    requires:
      anyBins:
        - yt-dlp
        - ffmpeg
    homepage: https://varg.ai/how-to
compatibility: >-
  No key. Needs yt-dlp, ffmpeg, ffprobe, curl, jq and bc on the machine. The clip databases
  marked "person" are opened by the person in a browser, not by the agent.
allowed-tools: Bash(yt-dlp:*) Bash(ffmpeg:*) Bash(ffprobe:*) Bash(curl:*) Bash(jq:*) Bash(bash:*) Read Write
---

# Find movie clips: the scene, the clean take, the rights

A remake is only as good as its reference clip. Still-frame libraries (ShotDeck, Film-Grab, Shot Cafe) give you a look, not motion; for a video reference you need a clip database, a download and a cut down to one usable take. Everything marked "tested" below was run on 2026-11-13.

## Setup

```bash
brew install yt-dlp ffmpeg jq        # macOS; bc and curl ship with the system
# Debian or Ubuntu: sudo apt install ffmpeg jq bc curl && pipx install yt-dlp
yt-dlp --version && ffmpeg -version | head -1 && jq --version      # all three must answer
```

## Best practices, in one screen

1. **Start from what is known** (a line, a film and moment, a look, a character) and open the one database built for it. Do not browse.
2. **Respect access.** Fetch only what allows it (YouTube through yt-dlp, the Internet Archive). For the rest, name the site and the search words and let the person open it.
3. **Read the result list before downloading.** One download per scene, at 720p, from the upload that holds the scene in the film's own cut.
4. **Never hand over a scene. Hand over a take:** one uncut shot, one person, real movement, 5 to 30 s, no logo, no subtitles, no black bars.
5. **Look at the frames.** Cut detection finds the takes; only the contact sheet shows an end card, a second person or a logo.
6. **Check the resolution column, not the file name,** and prefer the original file over a derivative.
7. **Settle rights before the work:** own footage, licensed stock, public domain, then a short clip of a known scene for parody. A refusal from a model is an answer, not an obstacle.
8. **Write the source down:** film, year, link, film time, licence. The next step and the caption both need it.
9. **No take passes? Change the scene,** not the rules.

## 1. Ask, then go

- **What do they know about the scene?** A line of dialogue, the film and the moment, only a look or a move, or one character across a whole show. This picks the database (section 2).
- **What is it for?** A video reference for a model (needs one uncut take, 5 to 30 s), a quote for an edit, or a mood reference.
- **Where will the result be posted?** Decides how much the rights section (7) matters.

## 2. Pick the database by what you know

| You know | Open | What you get | Who opens it |
|---|---|---|---|
| The line | [PlayPhrase.me](https://www.playphrase.me) | Every place in films and series where the phrase is said, played back to back. Free. | person |
| The line, and you need a file | [Clip.cafe](https://clip.cafe) | Search by quote or film; longer scenes than Yarn, with a download. | person |
| The line, as a short reaction | [Yarn](https://getyarn.io) | A few seconds around the quote. Too short for a remake, right for a meme. | person |
| The film and the moment | YouTube: Movieclips and channels like it | Two to four minute scenes, 720p or 1080p. | agent (section 3) |
| A look, a move, a kind of shot | [Flim](https://flim.ai) | Search in plain words across stills and video clips from films, ads and music videos. | person |
| The name of a technique | Eyecannndy | Short excerpts sorted by visual technique. | person |
| One character, every scene | Scene packs | Fan editors cut all scenes of a character in 4K and share them from Instagram accounts (a MEGA link in the caption), Google Drive folders and YouTube. Search `<character> scene pack 4k`. | person |
| An old film, with no rights question | [Internet Archive](https://archive.org/details/feature_films) | Whole public-domain films, cut by time code without downloading the file. | agent (section 4) |

Who says so: Clip.cafe as "longer scenes" against Yarn's "super short" clips ([@graceea29887132](https://x.com/graceea29887132/status/2105729889030574170)); PlayPhrase ([@malummiivt](https://x.com/malummiivt/status/2027822155426103388), 1,577 bookmarks); Flim's "1.5M stills and 400K video clips" ([@xpg0970](https://x.com/xpg0970/status/2074264672887595432)); scene packs ([@kawaiidinof](https://x.com/kawaiidinof/status/2121220961944948980), [@xaurorasxo](https://x.com/xaurorasxo/status/1979304680116064346)). Counts are the posters' claims.

**Why "person":** tested with a plain request. Clip.cafe's `robots.txt` disallows AI crawlers by name (`anthropic-ai`, `cohere-ai`, `CCBot`, `Bytespider`). Yarn and Eyecannndy answer automation with HTTP 403. PlayPhrase and Flim are browser apps with accounts. For these the agent names the site and the words to search, the person opens it and hands back a file or a YouTube link. Do not fetch them with a changed user agent.

## 3. The agent route: search YouTube, read the list, download once

```bash
# 1. search with metadata, no download
yt-dlp "ytsearch8:<film> <year> <the line or the moment> scene" --flat-playlist \
  --print "%(id)s | %(duration)s | %(view_count)s | %(channel)s | %(title)s"

# 2. download the one you picked at 720p with sound
yt-dlp -f "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]" --merge-output-format mp4 \
  -o "scene.%(ext)s" "https://www.youtube.com/watch?v=<id>"

# 3. find where the line is said: captions with time codes, no download
yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs "en.*" --sub-format vtt \
  -o "subs.%(ext)s" "https://www.youtube.com/watch?v=<id>"
grep -i -B3 "<three words of the line>" subs.en.vtt | grep -E "^[0-9]{2}:"      # 00:00:13.360 --> 00:00:16.080
```

The take you want is the one whose start and end (section 6) contain that time. A download that answers `HTTP Error 403` usually passes on a second try.

How to read the list (tested on one scene, eight results):

- **Take the 2 to 4 minute upload from a clip channel** (Movieclips, Binge Society): it holds the whole scene in the film's own cut. The 8 s and 27 s results are memes of one line, often re-cropped.
- **Be wary of uploads much longer than the scene** (one result ran 7 minutes for a 3 minute scene): they add commentary or other scenes.
- **720p is enough.** Video models take 720p plates; a 480p plate was refused as invalid input in our run (`scene-recast-video`).
- One download per scene. Links from X, TikTok, Instagram and 1,800 other sites: `media-download`.

## 4. Public-domain films: cut straight from the Internet Archive

```bash
# 1. find items; ask for 30, because the most downloaded ones are old 480p uploads
curl -s "https://archive.org/advancedsearch.php?q=title%3A%28<title>%29+AND+mediatype%3Amovies&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=licenseurl&sort%5B%5D=downloads+desc&rows=30&output=json"

# 2. list an item's video files: name | resolution | seconds | bytes | original or derivative
curl -s "https://archive.org/metadata/<identifier>" | jq -r '.files[] | select(.name|test("(mp4|mkv|mpeg|avi)$")) | "\(.name) | \(.width)x\(.height) | \(.length) | \(.size) | \(.source)"'

# 3. find the moment: one frame every 2 minutes from the small mp4, tiled
for t in $(seq 0 120 5400); do ffmpeg -v error -ss $t -i "$SMALL_URL" -frames:v 1 -vf scale=320:-2 "scout_$(printf %04d $t).jpg"; done
ffmpeg -v error -pattern_type glob -i "scout_*.jpg" -vf tile=8x6 scout.jpg     # read it, pick the minutes

# 4. cut up to 3 minutes around it from the best file, without downloading the film
ffmpeg -ss 1770 -t 180 -i "$BEST_URL" -map 0:v:0 -map "0:a:0?" -map_chapters -1 \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac cut.mp4
```

The file URL is `https://archive.org/download/<identifier>/<file name>`, with the name URL-encoded (spaces as `%20`, brackets as `%5B` `%5D`).

Tested twice (once by a fresh agent following this page): ten seconds at 1920x1080 out of a 1.8 GB file arrived in 6 s; a 3 minute cut took 46 s; 31 scout frames took 8 s. What the runs taught:

- **The `.mp4` is usually the Archive's own downscaled copy** (`derivative`, 480p). The HD file is the `original`, often an `.mkv`. Read the resolution column, not the file name: a file named `1080p` was 640x480.
- **The best item is rarely on top.** The 720p item was result 26 of 30 by downloads.
- **Licence:** `licenseurl` is set by the uploader. Pass: a public-domain mark or CC0 (`publicdomain/mark`, `publicdomain/zero`, `licenses/publicdomain`) on a film that is itself known to be public domain. Not a pass: no field, or a `by-nc` or `by-nd` licence. A public-domain mark on a recent film is an uploader's mistake.
- **Confirm the film itself on a second source** before trusting the mark or the person's word: the film's Wikipedia article or "List of films in the public domain in the United States". Read the sentence, not just the yes: for one 1963 film it says the picture is public domain "immediately upon its release" but "the original music remains under copyright". Put that in `source.txt`, and mute the track if the music matters.
- **A public-domain film goes here first, even when all you know is the line.** Many items carry a subtitle file (`.srt`, `.asr.srt`) in the same file list: download it and `grep` the line to get the film time.
- **A 4K original is slow and more than a model takes.** A 90 s cut from a 38 GB file took 3 minutes. Add `-vf scale=-2:1080` to the cut.
- **Write down film time.** The time code that matters for the source note is the `-ss` offset plus the take's start inside the cut.

## 5. What a model can follow

| Rule | Why | Source |
|---|---|---|
| One continuous take, no cuts | Cuts make the model lose who is who, or it truncates the clip | Kling guide; [@everestchris6](https://x.com/everestchris6/status/2107135574469746896) |
| One person on screen most of the time, face and upper body visible | With two people only the larger or nearer one is followed | Kling guide; Higgsfield blog |
| Real movement | "If the camera sits still and the person barely moves, you get the same flat shot in a new costume" | Calixte LeBlanc, YouTube |
| 5 to 30 s, and no longer than you need | Tools cap at 30 s and the price follows the length | tool limits |
| Empty hands, nobody crossing in front | A held prop is read as part of the body. If the scene is about the prop (a phone call), keep it and name the prop in the remake prompt | Higgsfield blog |
| A clean copy | Burned-in subtitles and logos are copied into the remake; find the clean original instead of erasing them | [@everestchris6](https://x.com/everestchris6/status/2107135574469746896) |

## 6. Split the scene into takes, then choose

```bash
bash scripts/takes.sh scene.mp4 8 30 takes     # min seconds, max seconds, out dir
```

Run it by its path inside this skill's folder; the output folder can be anywhere. It finds every cut, prints the uncut takes, and for each one of at least the minimum length writes `take_NN.mp4` and `take_NN.jpg` (a frame every 1.5 s, ten at most). A take longer than the maximum is kept as its first seconds and marked `(first 30 s kept)`. Look at the sheets, or give them to a vision model, and choose by section 5. Each file is 0.3 s shorter than the listed length, because 0.15 s is shaved off both ends; ask for a minimum half a second above what you need. After any further trim, make the sheet again: a second person can enter in the last two seconds.

How a cut is found: ffmpeg's scene score with a threshold of 0.17, set by looking at the frames around every candidate in a 3 minute handheld scene. All real cuts scored 0.177 or more; pans, runs and blows without a cut scored 0.168 or less. The usual advice of 0.3 found 33 cuts where there were about 49, and one of the cuts it missed sat in the middle of the "longest take". The margin is thin, so the script errs toward splitting, and a dissolve or a cut between two dark, similar shots can still pass. The contact sheet is the final check, not the table.

Tested on a 3 min 24 s scene from a clip channel: 49 cuts in the film part, 4 takes of 8 s or more, the longest 14.1 s. What the sheets showed, and what to do about each:

- **The last two "takes" were the channel's end card** (subscribe panel, 31 s in two parts). Drop whatever follows the film's last frame in a clip-channel upload.
- **A channel logo is burned into a corner.** It sits inside the picture, so cropping the bars does not remove it. Crop tighter only if the subject survives; otherwise find another upload or the film itself (section 4). Left in, it is redrawn in the remake.
- **Black bars at the sides** (a 4:3 film in a 16:9 file). Find and remove them (`cropdetect=24:2:0`: pixels darker than 24 of 255 count as black, sizes rounded to even numbers; take the crop printed most often, measured on a bright moment: in a dark shot the detector counts shadows as bars):

```bash
ffmpeg -ss 2 -t 4 -i take_01.mp4 -vf cropdetect=24:2:0 -f null - 2>&1 | grep -o "crop=[0-9:]*" | sort | uniq -c | sort -rn | head -1
ffmpeg -i take_01.mp4 -vf "crop=1060:720:60:0" -c:v libx264 -crf 18 -c:a copy take_01_clean.mp4
```

- **A take can start with two people and end with one.** Trim to the part with one: `ffmpeg -ss 7 -t 6 -i take_01.mp4 ...`.
- **Fights and handheld chaos fail rule 2** even when uncut: bodies overlap and faces leave the frame.

**Verify the take before handing it over.** Run the script on the chosen take itself and read its numbers:

```bash
bash scripts/takes.sh take.mp4 1 30 verify       # must print exactly one row: no cut inside
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 take.mp4   # short side 720 or more
```

Two rows mean a cut is still inside: trim and run it again. Then read `verify/take_01.jpg` once more for a logo, a subtitle or a second person. Only a take that passes goes to section 8.

A dialogue scene rarely has one take over 10 s. When the take that was asked for cannot pass, do not hand over a different take in silence and do not hand over nothing. Say which rule fails and by how much, and offer the choices:

1. the asked-for moment trimmed to the seconds that do pass ("he is alone for 7.1 s of the 8 asked");
2. the nearest take that passes, named as a different moment;
3. the asked-for take as it is, with `rules not met` filled in, for a tool that can take it (MiniMax Recast replaces people left to right);
4. another scene.

"One person" means one person a model could follow: a still shoulder or a hat at the frame edge passes, a second face or a moving body does not.

## 7. Rights and filters: check before the work, not after

- **A film clip is someone's copyright.** Parody that changes the meaning has a fair-use argument in the US; it is an argument, not a licence, and other countries are stricter. Client work and ads need a licensed or public-domain source.
- **Platforms act on the soundtrack and on known footage.** Creators report film and TV sources "get claimed and muted" more than phone footage ([@everestchris6](https://x.com/everestchris6/status/2107135574469746896)).
- **Video models refuse known footage and real faces.** A refused job means the provider said no to this input. Change the scene (a public-domain film, your own footage, an original scene in the same style); do not look for a setting that slips it through.
- **Real actors are real people.** Their face and voice are theirs: recast with invented characters, and do not clone an actor's voice. Putting a real person (a founder, a client) into a known scene needs that person's consent and a source you may use; for an ad, the parody argument does not apply.
- **Label the result** as AI-made and as parody where you post it.
- **Scene packs and full-film downloads** are other people's copies of copyrighted films. This skill names them because editors use them; it does not fetch them.

Safest order of sources: your own footage, licensed stock, a public-domain film (section 4), then a short clip of a known scene for commentary or parody.

## 8. Hand over

Give the next step one folder: `take.mp4` (one take, 720p or more, clean), `sheet.jpg` (made from the final trim) and `source.txt`:

```
film: <title> (<year>)
source: <link to the item or video>
file: <file name>
film time: 00:31:03 to 00:31:15
licence: <the licence field, or "copyrighted, used for parody">
in the take: <who, doing what>; rules not met: <none, or which>
```

Then:

- `scene-recast-video`: recast the take with your own characters.
- `ai-parody-video`: the joke and the format around it.
- `find-references`: still frames for the look, from the libraries this skill does not cover.

## Evaluations

`evals/evals.json` holds three test requests with what a correct run does: a scene found by its quote, a take from a public-domain film, and a request that must not be fetched. Run them after any change to this skill.

## Sources

Posts and guides read on 2026-11-12 and 2026-11-13: [@everestchris6](https://x.com/everestchris6/status/2107135574469746896) (how remake sources are chosen and checked), [@malummiivt](https://x.com/malummiivt/status/2027822155426103388), [@graceea29887132](https://x.com/graceea29887132/status/2105729889030574170), [@xpg0970](https://x.com/xpg0970/status/2074264672887595432), [@tgprovod](https://x.com/tgprovod/status/1969851511476736000), [@kawaiidinof](https://x.com/kawaiidinof/status/2121220961944948980), the [Kling Motion Control guide](https://kling.ai/quickstart/motion-control-user-guide), the [Higgsfield character swap guide](https://higgsfield.ai/blog/AI-Face-Character-Swap-in-Video-Photo-PRO-Guide). The commands and `scripts/takes.sh` were run on a public-domain scene; the databases marked "person" were not searched by the agent. Access rules change: read a site's `robots.txt` again before relying on the "agent" or "person" column.
