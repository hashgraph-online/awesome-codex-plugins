#!/usr/bin/env bash
# cut_points.sh: list the cut points (scene changes) of a recording or finished video as JSON.
#
#   cut_points.sh recording.mp4                       # JSON to stdout
#   cut_points.sh recording.mp4 --out cuts.json --threshold 20 --min-scene 1.0
#   cut_points.sh recording.mp4 --detector adaptive   # better on footage with camera or screen movement
#
# Uses PySceneDetect (BSD-3-Clause), which you install yourself. Without it the script prints the install
# command and a SKIP line and exits 3 (no cut list was made: never read as success, never a failure either):
#   python3 -m pip install --user scenedetect opencv-python-headless
#
# Options
#   --detector content|adaptive|threshold   content (default) reacts to colour and brightness change;
#                                           adaptive divides by the change around it (steadier on motion);
#                                           threshold finds fades to and from black
#   --threshold N    detector sensitivity (content default 27: lower finds more cuts)
#   --min-scene S    shortest scene in seconds (default 0.6); a closer cut is ignored
#   --out FILE       write the JSON there as well as printing it
#
# Output: {"file", "detector", "threshold", "cuts": [seconds...], "scenes": [{"start", "end"}...]}.
# Use it on a screen recording to find where the takes and edits are, before choosing holds and zooms; or on
# your own render to confirm that the cuts fall where the beat sheet says. For a cut-versus-pan call on a
# finished film, check_seams.py classifies each change with two signals.
set -uo pipefail

FILE="" DETECTOR=content THRESHOLD="" MIN_SCENE=0.6 OUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --detector) DETECTOR="$2"; shift 2 ;;
    --threshold) THRESHOLD="$2"; shift 2 ;;
    --min-scene) MIN_SCENE="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    -*) echo "cut_points.sh: unknown option $1" >&2; exit 2 ;;
    *) FILE="$1"; shift ;;
  esac
done
[[ -f "$FILE" ]] || { echo "usage: cut_points.sh FILE [--detector content|adaptive|threshold] [--threshold N] [--min-scene S] [--out FILE]" >&2; exit 2; }
case "$DETECTOR" in content|adaptive|threshold) ;; *) echo "cut_points.sh: --detector must be content, adaptive or threshold" >&2; exit 2 ;; esac

PY="$(command -v python3 || command -v python || true)"
SD=()
if [[ -n "${SCENEDETECT:-}" ]]; then      # point at a specific install (or at nothing, to see the SKIP message)
  command -v "$SCENEDETECT" >/dev/null 2>&1 && SD=("$SCENEDETECT")
elif command -v scenedetect >/dev/null 2>&1; then
  SD=(scenedetect)
elif [[ -n "$PY" ]] && "$PY" -c "import scenedetect" >/dev/null 2>&1; then
  SD=("$PY" -m scenedetect)
fi
if [[ ${#SD[@]} -eq 0 ]]; then
  echo "SKIP  cut_points: PySceneDetect is not installed, so no cut list was made."
  echo "      Install it: python3 -m pip install --user scenedetect opencv-python-headless"
  exit 3
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
args=(-i "$FILE" -q detect-"$DETECTOR" -m "${MIN_SCENE}s")
[[ -n "$THRESHOLD" ]] && args=(-i "$FILE" -q detect-"$DETECTOR" -t "$THRESHOLD" -m "${MIN_SCENE}s")
if ! "${SD[@]}" "${args[@]}" list-scenes -f scenes.csv -o "$WORK" >"$WORK/log.txt" 2>&1 || [[ ! -f "$WORK/scenes.csv" ]]; then
  echo "FAIL  cut_points: PySceneDetect could not read $FILE:" >&2
  tail -5 "$WORK/log.txt" >&2
  exit 1
fi

# CSV rows: scene number, start frame, start timecode, start seconds, end frame, end timecode, end seconds, ...
safe_name="$(printf '%s' "$FILE" | tr '\\' '/' | sed 's/"/\\"/g')"
json="$(awk -F, -v file="$safe_name" -v det="$DETECTOR" -v thr="${THRESHOLD:-default}" '
  $1 ~ /^[0-9]+$/ { n++; start[n] = $4; end[n] = $7 }
  END {
    printf "{\"file\": \"%s\", \"detector\": \"%s\", \"threshold\": %s, \"cuts\": [", file, det, (thr == "default" ? "null" : thr)
    for (i = 2; i <= n; i++) printf "%s%s", (i > 2 ? ", " : ""), start[i]
    printf "], \"scenes\": ["
    for (i = 1; i <= n; i++) printf "%s{\"start\": %s, \"end\": %s}", (i > 1 ? ", " : ""), start[i], end[i]
    printf "]}\n"
  }' "$WORK/scenes.csv")"
echo "$json"
[[ -n "$OUT" ]] && echo "$json" > "$OUT"
exit 0
