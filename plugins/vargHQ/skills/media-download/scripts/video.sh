#!/usr/bin/env bash
# Download videos by URL with yt-dlp. Prints the final file path of every download on stdout.
# Usage: download.sh [-o dir] [-q 720] [-a] [-p] [-c browser] [-k cookies.txt] <url...>
set -euo pipefail

out="downloads" height="" audio="" playlist="--no-playlist"
cookies=()
while getopts "o:q:apc:k:h" opt; do
  case $opt in
    o) out=$OPTARG ;;
    q) height=$OPTARG ;;
    a) audio=1 ;;
    p) playlist="--yes-playlist" ;;
    c) cookies=(--cookies-from-browser "$OPTARG") ;;
    k) cookies=(--cookies "$OPTARG") ;;
    *) sed -n '2,3p' "$0"; exit 0 ;;
  esac
done
shift $((OPTIND - 1))
[ $# -gt 0 ] || { echo "usage: download.sh [-o dir] [-q 720] [-a] [-p] [-c browser] <url...>" >&2; exit 2; }

# yt-dlp: PATH → cached standalone build (installed on first use).
ytdlp=$(command -v yt-dlp || true)
if [ -z "$ytdlp" ]; then
  cache="${XDG_CACHE_HOME:-$HOME/.cache}/video-download"
  ytdlp="$cache/yt-dlp"
  if [ ! -x "$ytdlp" ]; then
    case "$(uname -s)-$(uname -m)" in
      Darwin-*) asset=yt-dlp_macos ;;
      Linux-aarch64 | Linux-arm64) asset=yt-dlp_linux_aarch64 ;;
      Linux-*) asset=yt-dlp_linux ;;
      *) echo "Install yt-dlp manually: https://github.com/yt-dlp/yt-dlp#installation" >&2; exit 1 ;;
    esac
    echo "Installing yt-dlp into ${cache}..." >&2
    mkdir -p "$cache"
    curl -fsSL "https://github.com/yt-dlp/yt-dlp/releases/latest/download/$asset" -o "$ytdlp.part"
    chmod +x "$ytdlp.part" && mv "$ytdlp.part" "$ytdlp"
  fi
fi

command -v ffmpeg >/dev/null || echo "warning: ffmpeg not found — YouTube HD can't be merged (brew install ffmpeg)" >&2

if [ -n "$audio" ]; then
  fmt=(-f "ba/b" -x --audio-format mp3)
else
  # res = smaller side, so -q 720 also means 720p for vertical videos.
  fmt=(-f "bv*+ba/b" -S "${height:+res:$height,}vcodec:h264,acodec:m4a,ext:mp4:m4a" --merge-output-format mp4)
fi

status=0
for url in "$@"; do
  echo "↓ $url" >&2
  "$ytdlp" "$playlist" "${fmt[@]}" ${cookies[@]+"${cookies[@]}"} \
    --no-simulate --no-mtime \
    -P "$out" -o "%(extractor_key)s/%(title).80B [%(id)s].%(ext)s" \
    --print "after_move:filepath" -- "$url" || { status=1; echo "✗ failed: $url" >&2; }
done
exit $status
