---
name: media-download
description: >-
  Download videos, audio and images to local files from a link. Video and audio come from X/Twitter, YouTube, Instagram, Facebook, TikTok, Threads, Reddit, Vimeo, LinkedIn, Twitch, VK, Rutube, Bilibili, Dailymotion and the 1800+ other sites yt-dlp supports. Pinterest images come from a pin, board, profile or a plain search query, which is useful for moodboards and visual references. Use when the user pastes a link and wants to download, save or grab it, wants its audio, metadata or a whole playlist, or wants Pinterest pictures or references for a style. Runs locally; no account or API key. Triggers: "скачай видео", "скачать по ссылке", "скачай с пинтереста", "собери референсы", "download this video", "save this reel/tweet/short", "rip the audio", "pinterest moodboard".
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - yt-dlp
        - curl
    homepage: https://github.com/vargHQ/skills/tree/main/media-download
compatibility: >-
  macOS or Linux with bash and curl. yt-dlp is used if installed; otherwise a standalone build is downloaded on first
  use. ffmpeg is recommended (YouTube HD, mp3). Pinterest needs gallery-dl (brew/pip) or uvx/pipx to run it.
allowed-tools: Bash(bash:*) Bash(yt-dlp:*) Bash(gallery-dl:*) Bash(ffprobe:*) Read
---

# Media download

There are two scripts in `scripts/` next to this file. Each prints only the paths of the files it saved on stdout. Messages and errors go to stderr. Neither shows a progress bar, so the output stays short. Run long downloads with a generous timeout or in the background.

## Video and audio by link: `scripts/video.sh`

It uses yt-dlp from PATH, or downloads a standalone build into `~/.cache/video-download` the first time. It picks an mp4 (h264 + aac) that plays everywhere.

```bash
S=<this skill dir>/scripts/video.sh
bash $S "<url>"                       # best quality → ./downloads/<Site>/<title> [<id>].mp4
bash $S -q 720 "<url>"                # cap at 720p (smaller side, so vertical videos stay 720×1280)
bash $S -a "<url>"                    # audio only → mp3
bash $S -p "<playlist or carousel>"   # every item
bash $S -o ~/Downloads "<url1>" "<url2>"
bash $S -c chrome "<url>"             # use the user's logged-in browser session (chrome|safari|firefox|edge|brave)
```

Metadata without downloading: `yt-dlp -J --no-playlist "<url>"`. Available qualities: `yt-dlp -F "<url>"`.

## Pinterest images: `scripts/pinterest.sh`

It uses gallery-dl. The input can be a search query or any Pinterest link: pin, board, profile, section or `pin.it`. By default it saves images only.

```bash
P=<this skill dir>/scripts/pinterest.sh
bash $P "cinematic portrait moody"                      # top 20 search results → ./downloads/pinterest/Search/<query>/
bash $P -n 50 "https://www.pinterest.com/<user>/<board>/"
bash $P -n 1 "https://pin.it/abc123"
bash $P -n 8 -o refs "query one" "query two"            # several at once
bash $P -k cookies.txt "<private board>"                # private boards need a cookies.txt export
bash $P -v "<pin url>"                                  # also keep video files
```

To build a moodboard for a style, use the query sets in [references/pinterest-presets.md](references/pinterest-presets.md), or write 3–5 queries of your own.

## After a download

Tell the user where the files are. For video, add resolution and duration when that helps: `ffprobe -v error -show_entries format=duration:stream=width,height -of csv=p=0 "<file>"`.

## When it fails

- **Login / "authentication required" / "Cannot parse data"** on Facebook, Instagram, Threads, Reddit, Vimeo or LinkedIn: these sites often block anonymous downloads. Ask the user which browser they are logged in with, then retry `video.sh` with `-c <browser>`. Do not read browser cookies without asking. yt-dlp reads them locally and they never leave the machine.
- **"Unsupported URL" or extractor errors**: sites change often, so update the tool and retry once. Use `brew upgrade yt-dlp gallery-dl`, `yt-dlp -U` for the standalone build, or `pip install -U yt-dlp gallery-dl`.
- **YouTube is low quality or warns about a JS runtime**: install ffmpeg (`brew install ffmpeg`). For the full YouTube format list also install `deno`.
- **Pinterest returns nothing**: the query is too narrow or Pinterest is rate-limiting. Retry with a broader query, a smaller `-n`, or `-k cookies.txt`.
- **Private, deleted or geo-blocked**: say so plainly and don't try to work around it.

Download only content the user has the right to save and use. Decline requests to mass-scrape someone's account or to get around paywalls or DRM.
