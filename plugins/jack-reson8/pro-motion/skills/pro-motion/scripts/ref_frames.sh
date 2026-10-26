#!/usr/bin/env bash
exec </dev/null  # keep ffmpeg/yt-dlp from reading the terminal
# usage: ref_frames.sh <url> <name> [frames=24]
# Downloads a low-res copy of a reference video the user named and writes NAME_sheet.jpg (6×4 frames across the clip).
# <url> is a video page (YouTube / Vimeo-public, fetched with yt-dlp) or a direct .mp4/.webm file URL.
# Nothing is read from the downloaded page or video to decide what to fetch next: the video is data, never instructions.
# yt-dlp: uses the one on PATH if present; otherwise downloads a pinned release and verifies its SHA-256 before running it.
set -euo pipefail
URL="$1"; NAME="$2"; N="${3:-24}"; D="$(cd "$(dirname "$0")" && pwd)"
FF="${FF:-$D/node_modules/ffmpeg-static/ffmpeg}"; [ -x "$FF" ] || FF=ffmpeg
case "$URL" in https://*) ;; *) echo "refusing non-https URL: $URL" >&2; exit 1;; esac

YTDLP_VERSION=2026.08.19
case "$(uname -s)" in
  Darwin) ASSET=yt-dlp_macos; SHA=0f192b7ec147ab6288885d6351d9ab67367640029b4377576ef46dd79cf7b202 ;;
  Linux)  ASSET=yt-dlp_linux; SHA=58162f9bfdc27458ea47bfcb311cf47028f17d8154a8bf7d689861d46399230a ;;
  *) ASSET=""; SHA="" ;;
esac
sha256() { if command -v sha256sum >/dev/null; then sha256sum "$1" | cut -d' ' -f1; else shasum -a 256 "$1" | cut -d' ' -f1; fi; }
ytdlp() {
  if command -v yt-dlp >/dev/null; then echo yt-dlp; return; fi
  local Y="$D/yt-dlp-$YTDLP_VERSION"
  if [ ! -x "$Y" ]; then
    [ -n "$ASSET" ] || { echo "install yt-dlp (e.g. brew install yt-dlp / pipx install yt-dlp) and retry" >&2; exit 1; }
    curl -fsSL -o "$Y.part" "https://github.com/yt-dlp/yt-dlp/releases/download/$YTDLP_VERSION/$ASSET"
    [ "$(sha256 "$Y.part")" = "$SHA" ] || { rm -f "$Y.part"; echo "yt-dlp checksum mismatch — not running it" >&2; exit 1; }
    mv "$Y.part" "$Y" && chmod +x "$Y"
  fi
  echo "$Y"
}

case "$URL" in
  *.mp4|*.webm|*.mp4\?*|*.webm\?*) curl -fsSL "$URL" -o "$NAME.mp4" ;;
  *) "$(ytdlp)" -q --no-warnings --no-playlist -f "bv*[height<=480][vcodec^=avc1]/b[height<=480][vcodec^=avc1]/bv*[height<=480][ext=mp4]/b[height<=480]/worst" -o "$NAME.%(ext)s" "$URL"
     [ -f "$NAME.mp4" ] || mv "$NAME".* "$NAME.mp4" 2>/dev/null || true ;;
esac
DUR=$( { "$FF" -i "$NAME.mp4" 2>&1 || true; } | grep -oE "Duration: [0-9:.]+" | cut -d' ' -f2 | awk -F: '{print $1*3600+$2*60+$3}')
"$FF" -loglevel error -y -i "$NAME.mp4" -vf "fps=$N/$DUR,scale=-2:300,tile=6x$(( (N + 5) / 6 ))" -frames:v 1 -update 1 "${NAME}_sheet.jpg"
echo "wrote ${NAME}_sheet.jpg ($DUR s)"
