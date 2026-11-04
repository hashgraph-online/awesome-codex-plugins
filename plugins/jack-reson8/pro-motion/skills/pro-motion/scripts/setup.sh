#!/usr/bin/env bash
# setup.sh [project_dir] [--yes] — prepare a project folder for an MG film.
# Copies the template (film.html, film.js, motion-lib.js, fonts) and tools into the folder.
# Installing packages needs the user's yes: it lists what would be installed and stops unless --yes is passed
# (Claude: show this list to the user and rerun with --yes only after they agree).
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
YES=0; ARGS=(); for a in "$@"; do [ "$a" = "--yes" ] && YES=1 || ARGS+=("$a"); done
DIR="${ARGS[0]:-.}"; mkdir -p "$DIR"; cd "$DIR"
[ -f film.js ] && echo "film.js exists — template not copied (delete it to start fresh)" || cp -R "$SKILL/assets/template/"* .
mkdir -p tools music out stills && cp "$SKILL/scripts/"* tools/ && rm -f tools/setup.sh
PUPPETEER_VERSION=24.10.2; FFMPEG_STATIC_VERSION=5.2.0
if [ ! -d tools/node_modules/puppeteer ]; then
  if [ "$YES" -ne 1 ]; then
    echo "Needs npm packages in $DIR/tools (no bundled browser download):"
    echo "  puppeteer@$PUPPETEER_VERSION  ffmpeg-static@$FFMPEG_STATIC_VERSION"
    echo "Rerun with --yes to install them."; exit 2
  fi
  (cd tools && npm init -y >/dev/null && PUPPETEER_SKIP_DOWNLOAD=1 npm i --silent --save-exact "puppeteer@$PUPPETEER_VERSION" "ffmpeg-static@$FFMPEG_STATIC_VERSION")
fi
chmod +x tools/node_modules/ffmpeg-static/ffmpeg 2>/dev/null || true
python3 -c "import numpy, scipy, matplotlib" 2>/dev/null || echo "⚠︎ python deps missing (ask the user before installing): pip3 install numpy scipy matplotlib"
B=$(node tools/render-fast.js --find-chrome 2>/dev/null) && echo "browser: $B" || echo "⚠︎ no Chrome/Chromium found — install one or set CHROME=/path/to/chrome"
echo "ready: put your track at music/track.mp3, then run tools/analyze_music.py (see SKILL.md §2)"
