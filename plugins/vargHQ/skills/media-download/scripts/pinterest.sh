#!/usr/bin/env bash
# Download Pinterest images with gallery-dl: a search query, pin, board, user, section or pin.it link.
# Prints the path of every downloaded image on stdout.
# Usage: pinterest.sh [-n 20] [-o dir] [-k cookies.txt] [-v] "<query or url>" ["<query or url>"...]
set -euo pipefail

limit=20 out="downloads" cookies=() videos=""
while getopts "n:o:k:vh" opt; do
  case $opt in
    n) limit=$OPTARG ;;
    o) out=$OPTARG ;;
    k) cookies=(--cookies "$OPTARG") ;;
    v) videos=1 ;;
    *) sed -n '2,4p' "$0"; exit 0 ;;
  esac
done
shift $((OPTIND - 1))
[ $# -gt 0 ] || { echo 'usage: pinterest.sh [-n 20] [-o dir] [-k cookies.txt] [-v] "<query or url>"' >&2; exit 2; }

# gallery-dl: PATH → uvx → pipx (both run it without a global install).
if command -v gallery-dl >/dev/null; then gdl=(gallery-dl)
elif command -v uvx >/dev/null; then gdl=(uvx gallery-dl)
elif command -v pipx >/dev/null; then gdl=(pipx run gallery-dl)
else
  echo "gallery-dl not found: brew install gallery-dl  (or: pip install gallery-dl)" >&2
  exit 1
fi

# Images only unless -v (videos/m3u8 on pins are better handled by video.sh).
filter=()
[ -n "$videos" ] || filter=(--filter "extension in ('jpg', 'jpeg', 'png', 'webp', 'gif')")

status=0
for q in "$@"; do
  if [[ $q =~ ^(https?://)?([a-z0-9-]+\.)?(pinterest\.[a-z.]+|pin\.it)/ ]]; then
    url=$q
  else
    url="https://www.pinterest.com/search/pins/?q=$(printf %s "$q" | jq -sRr @uri 2>/dev/null || python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$q")"
  fi
  echo "↓ $url" >&2
  "${gdl[@]}" --range "1-$limit" ${filter[@]+"${filter[@]}"} ${cookies[@]+"${cookies[@]}"} \
    -d "$out" -o "filename={id}.{extension}" --http-timeout 20 --retries 2 -- "$url" \
    | sed 's/^# //' || { status=1; echo "✗ failed: $q" >&2; }
done
exit $status
