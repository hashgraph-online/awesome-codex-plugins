#!/usr/bin/env bash
# Render local HTML frames; fail if any browser job fails or produces no image.
# usage: render.sh <template.html> <out_dir> <frame_id> [frame_id ...]
set -euo pipefail
if (( $# < 3 )); then echo "usage: render.sh <template.html> <out_dir> <frame_id> [...]" >&2; exit 2; fi
tpl="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
[[ -f "$tpl" ]] || { echo "missing template: $tpl" >&2; exit 2; }
mkdir -p "$2"; out="$(cd "$2" && pwd)"; shift 2
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
[[ -x "$CHROME" ]] || { echo "browser is not executable: $CHROME" >&2; exit 2; }
for id in "$@"; do [[ "$id" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo "invalid frame id: $id" >&2; exit 2; }; done
work="$(mktemp -d "${TMPDIR:-/tmp}/post-render.XXXXXX")"
pids=(); ids=()
cleanup() { for pid in "${pids[@]:-}"; do kill "$pid" 2>/dev/null || true; done; rm -rf "$work"; }
trap cleanup EXIT
for id in "$@"; do
  perl -e 'alarm 40; exec @ARGV' "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run --no-default-browser-check --password-store=basic --use-mock-keychain \
    --force-device-scale-factor=1 --window-size=1080,1440 --virtual-time-budget=4000 \
    --user-data-dir="$work/profile-$id" --screenshot="$work/$id.png" "file://$tpl?p=$id" >"$work/$id.log" 2>&1 &
  pids+=("$!"); ids+=("$id")
done
failed=0
for i in "${!pids[@]}"; do
  id="${ids[$i]}"
  if ! wait "${pids[$i]}" || [[ ! -s "$work/$id.png" ]]; then
    echo "render failed: $id" >&2; cat "$work/$id.log" >&2; failed=1
  fi
done
pids=()
(( failed == 0 )) || exit 1
for id in "$@"; do mv "$work/$id.png" "$out/$id.png"; done
ls "$out"
