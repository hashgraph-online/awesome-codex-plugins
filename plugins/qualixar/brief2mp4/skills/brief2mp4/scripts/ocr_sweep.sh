#!/usr/bin/env bash
# ocr_sweep.sh: read the frames of a FINISHED video and fail on placeholder text or leaked file paths.
#
#   ocr_sweep.sh final.mp4
#   ocr_sweep.sh final.mp4 --fps 2 --extra 'Acme|v[0-9]+\.[0-9]+\.[0-9]+'
#   ocr_sweep.sh --scan-text notes.txt        # check a text file with the same patterns (no video, no OCR)
#
# It reads one frame per second (--fps) plus every scene change, runs OCR on each, and looks for:
#   TODO, TBD, FIXME, "placeholder", "lorem ipsum", "not recorded", {{ }} template tokens, [INSERT ...] style
#   tokens, and file paths (/Users/..., /home/..., C:\ or C:/Users).
# --extra adds your own pattern (an extended regular expression, case-insensitive): names, version
# strings, anything that must never be on screen.
#
# Needs tesseract. Without it the script prints the install command and a SKIP line and exits 3 (not
# measured: never read as a pass, and never a FAIL either):
#   macOS: brew install tesseract    Debian/Ubuntu: sudo apt-get install tesseract-ocr
#   Windows: winget install -e --id UB-Mannheim.TesseractOCR
#
# OCR misreads thin, wide-spaced display type, so a hit is a reason to LOOK at the frame (it is kept next
# to the list with --keep DIR), not proof. A miss is not proof either: view the frames yourself.
# Exit 0 = every frame read and nothing found; 1 = a pattern hit, or the frames or the OCR could not be read
# (a broken tesseract, a file ffmpeg cannot decode, no frames at all); 2 = bad arguments; 3 = SKIP or INCOMPLETE
# (no tesseract, or --max-frames stopped the 1 fps sweep before the end of the video).
set -uo pipefail

FPS=1 EXTRA="" KEEP="" MAX_FRAMES=600 VIDEO="" SCAN_TEXT=""
TESS="${TESSERACT:-tesseract}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fps) FPS="$2"; shift 2 ;;
    --extra) EXTRA="$2"; shift 2 ;;
    --keep) KEEP="$2"; shift 2 ;;
    --max-frames) MAX_FRAMES="$2"; shift 2 ;;
    --scan-text) SCAN_TEXT="$2"; shift 2 ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    -*) echo "ocr_sweep.sh: unknown option $1" >&2; exit 2 ;;
    *) VIDEO="$1"; shift ;;
  esac
done

# A word boundary that grep -E understands on macOS, Linux and Git Bash alike.
B='(^|[^A-Za-z0-9_])'
E='([^A-Za-z0-9_]|$)'
PATTERN="${B}(TODO|TBD|FIXME)${E}|lorem ipsum|${B}lorem${E}|placeholder|not recorded"
PATTERN+='|\{\{|\}\}|\[(INSERT|TODO|TBD|PLACEHOLDER)[^]]*\]'
# OCR often reads a thin slash as | I l 1 J or \\, so a home path is matched with any of those around "users".
PATTERN+="|${B}[/|\\\\Il1J]users[/|\\\\Il1J]"
PATTERN+='|/home/[a-z]|[A-Za-z]:\\|[A-Za-z]:/Users'
[[ -n "$EXTRA" ]] && PATTERN+="|$EXTRA"

HITS=0
# scan_text LABEL FILE: print one FAIL line per matching string, count them.
scan_text() {
  local label="$1" file="$2" m
  while IFS= read -r m; do
    [[ -z "$m" ]] && continue
    echo "FAIL  placeholder or leak at $label: \"$m\""
    HITS=$((HITS + 1))
  done < <(grep -o -i -E "$PATTERN" "$file" 2>/dev/null | sed 's#^[[:space:].,;:!?"()]*##;s#[[:space:].,;:!?"()]*$##' | sort -u)
}

if [[ -n "$SCAN_TEXT" ]]; then
  [[ -f "$SCAN_TEXT" ]] || { echo "ocr_sweep.sh: no such file: $SCAN_TEXT" >&2; exit 2; }
  scan_text "$SCAN_TEXT" "$SCAN_TEXT"
  [[ "$HITS" == 0 ]] && echo "PASS  no placeholder text or leaked paths in $SCAN_TEXT"
  [[ "$HITS" == 0 ]]; exit $?
fi

[[ -f "$VIDEO" ]] || { echo "usage: ocr_sweep.sh FILE.mp4 [--fps N] [--extra REGEX] [--keep DIR]  |  --scan-text FILE" >&2; exit 2; }
if ! command -v "$TESS" >/dev/null 2>&1; then
  echo "SKIP  ocr_sweep: tesseract is not installed, so the final file was not read for placeholder text."
  echo "      Install it: macOS: brew install tesseract | Debian/Ubuntu: sudo apt-get install tesseract-ocr | Windows: winget install -e --id UB-Mannheim.TesseractOCR"
  echo "      Then rerun. Until then, look at the frames yourself (contact_sheet.sh)."
  exit 3
fi
[[ "$FPS" =~ ^[0-9]+([.][0-9]+)?$ && "$MAX_FRAMES" =~ ^[0-9]+$ ]] || { echo "ocr_sweep.sh: --fps and --max-frames must be numbers" >&2; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
# One frame per second, then every scene change (a frame just after a cut shows the new scene's text).
if ! ffmpeg -nostats -v error -i "$VIDEO" -an -vf "fps=$FPS" -frames:v "$MAX_FRAMES" "$WORK/t_%05d.png" 2> "$WORK/extract.log"; then
  echo "FAIL  ocr_sweep: ffmpeg could not read frames from $VIDEO: $(tr '\n' ' ' < "$WORK/extract.log" | cut -c1-200)"
  exit 1
fi
ffmpeg -nostats -v info -i "$VIDEO" -an -vf "select=gt(scene\,0.3),showinfo" -fps_mode vfr -frames:v 200 "$WORK/s_%05d.png" 2> "$WORK/scene.log" \
  || ffmpeg -nostats -v error -i "$VIDEO" -an -vf "select=gt(scene\,0.3)" -vsync vfr -frames:v 200 "$WORK/s_%05d.png"
grep -o 'pts_time:[0-9.]*' "$WORK/scene.log" 2>/dev/null | cut -d: -f2 > "$WORK/scene_times.txt" || true

COUNT=0 UNREAD=0 FIRST_ERR=""
for img in "$WORK"/t_*.png "$WORK"/s_*.png; do
  [[ -f "$img" ]] || continue
  base="$(basename "$img" .png)"; n=$((10#${base#*_}))
  if [[ "$base" == t_* ]]; then
    label="$(awk -v n="$n" -v f="$FPS" 'BEGIN{printf "%.1fs", (n-1)/f}')"
  else
    label="$(sed -n "${n}p" "$WORK/scene_times.txt" | awk '{printf "%.1fs (scene change)", $1}')"
  fi
  COUNT=$((COUNT + 1))
  rm -f "$WORK/ocr.txt"
  if ! "$TESS" "$img" "$WORK/ocr" --psm 11 >/dev/null 2> "$WORK/tess.log" || [[ ! -f "$WORK/ocr.txt" ]]; then
    UNREAD=$((UNREAD + 1))
    [[ -z "$FIRST_ERR" ]] && FIRST_ERR="$(tr '\n' ' ' < "$WORK/tess.log" | cut -c1-200)"
    continue
  fi
  before=$HITS
  scan_text "$label" "$WORK/ocr.txt"
  if [[ -n "$KEEP" && "$HITS" -gt "$before" ]]; then mkdir -p "$KEEP"; cp "$img" "$KEEP/$base.png"; fi
done

DUR="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$VIDEO" 2>/dev/null | head -1)"
READ_S="$(awk -v n="$MAX_FRAMES" -v f="$FPS" 'BEGIN{printf "%.0f", n/f}')"
CAPPED="$(awk -v d="${DUR:-0}" -v n="$MAX_FRAMES" -v f="$FPS" 'BEGIN{print (d*f > n+1)?1:0}')"
echo "----"
if [[ "$HITS" != 0 ]]; then
  echo "FAIL  $HITS hit(s) in $COUNT frame(s) of $VIDEO: open each frame and confirm${KEEP:+ (kept in $KEEP)}"
  exit 1
fi
if [[ "$COUNT" == 0 ]]; then
  echo "FAIL  ocr_sweep: no frames came out of $VIDEO, so nothing was read"
  exit 1
fi
if [[ "$UNREAD" != 0 ]]; then
  echo "FAIL  ocr_sweep: tesseract read nothing from $UNREAD of $COUNT frame(s) (is its language data installed? set TESSDATA_PREFIX): ${FIRST_ERR:-no output file}"
  exit 1
fi
if [[ "$CAPPED" == 1 ]]; then
  echo "WARN  ocr_sweep: read only the first ${READ_S} s of ${DUR%.*} s at $FPS fps (--max-frames $MAX_FRAMES); the rest was not read"
  echo "INCOMPLETE  no placeholder text or leaked paths in the $COUNT frame(s) read; raise --max-frames to read the whole video"
  exit 3
fi
echo "PASS  no placeholder text or leaked paths in $COUNT frame(s) of $VIDEO"
