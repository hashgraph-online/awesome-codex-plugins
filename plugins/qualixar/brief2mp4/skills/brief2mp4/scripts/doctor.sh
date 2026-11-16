#!/usr/bin/env bash
# doctor.sh: check every tool brief2mp4 can use and print the install command for anything missing.
#   bash doctor.sh          # human-readable
#   bash doctor.sh --json   # one JSON object
# Exit 0 when every REQUIRED tool is present, 1 otherwise. Optional tools never fail the check.
set -uo pipefail

JSON=0; [[ "${1:-}" == "--json" ]] && JSON=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$(uname -s)" in
  Darwin) OS=macos ;;
  Linux) OS=linux; grep -qi microsoft /proc/version 2>/dev/null && OS=wsl ;;
  MINGW*|MSYS*|CYGWIN*) OS=windows ;;
  *) OS=unknown ;;
esac

PKG="sudo apt install -y"
command -v dnf >/dev/null 2>&1 && PKG="sudo dnf install -y"
command -v pacman >/dev/null 2>&1 && PKG="sudo pacman -S --needed"
command -v zypper >/dev/null 2>&1 && PKG="sudo zypper install -y"

fix() {  # fix <tool> -> install command for this OS
  case "$OS:$1" in
    macos:node) echo "brew install node" ;;
    macos:ffmpeg) echo "brew install ffmpeg" ;;
    macos:git) echo "xcode-select --install" ;;
    macos:blender) echo "brew install --cask blender" ;;
    macos:python) echo "brew install python@3.12" ;;
    windows:node) echo "winget install -e --id OpenJS.NodeJS.LTS" ;;
    windows:ffmpeg) echo "winget install -e --id Gyan.FFmpeg" ;;
    windows:git) echo "winget install -e --id Git.Git" ;;
    windows:blender) echo "winget install -e --id BlenderFoundation.Blender" ;;
    windows:python) echo "winget install -e --id Python.Python.3.12" ;;
    *:node) echo "install Node.js 22+ from https://nodejs.org (or nodesource setup_22.x)" ;;
    *:ffmpeg) echo "$PKG ffmpeg" ;;
    *:git) echo "$PKG git" ;;
    *:blender) echo "download from https://www.blender.org/download" ;;
    *:python) echo "$PKG python3 (3.12 or 3.13; Debian 12 ships 3.11: uv python install 3.12)" ;;
  esac
}

find_blender() {
  command -v blender 2>/dev/null && return
  local c
  for c in /Applications/Blender.app/Contents/MacOS/Blender "/c/Program Files/Blender Foundation"/Blender*/blender.exe; do
    [[ -x "$c" ]] && { echo "$c"; return; }
  done
}

find_python() {
  local p v
  for p in python3.13 python3.12 python3 python py; do
    command -v "$p" >/dev/null 2>&1 || continue
    v="$("$p" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)" || continue
    case "$v" in 3.12|3.13) echo "$p $v"; return ;; esac
  done
}

ROWS=(); FAIL=0
row() {  # row <name> <required:1|0> <status> <detail>
  ROWS+=("$1|$2|$3|$4")
  [[ "$2" == 1 && "$3" != ok ]] && FAIL=1
}

if command -v node >/dev/null 2>&1; then
  major="$(node -v | sed 's/^v//; s/\..*//')"
  if [[ "$major" -ge 22 ]] 2>/dev/null; then row node 1 ok "$(node -v)"
  else row node 1 old "$(node -v) is older than 22. $(fix node)"; fi
else row node 1 missing "$(fix node)"; fi

for t in ffmpeg ffprobe; do
  if command -v "$t" >/dev/null 2>&1; then row "$t" 1 ok "$("$t" -version 2>/dev/null | head -1 | cut -c1-60)"
  else row "$t" 1 missing "$(fix ffmpeg)"; fi
done

if command -v git >/dev/null 2>&1; then row git 1 ok "$(git --version)"; else row git 1 missing "$(fix git)"; fi

b="$(find_blender)"
if [[ -n "$b" ]]; then row blender 0 ok "$("$b" --version 2>/dev/null | head -1) ($b)"
else row blender 0 missing "only for Blender briefs. $(fix blender)"; fi

py="$(find_python)"
if [[ -n "$py" ]]; then row python 0 ok "$py"
else row python 0 missing "only for the 3D pack (3.12 or 3.13). $(fix python)"; fi

d3="$(bash "$HERE/detect_3d.sh" 2>/dev/null || echo '3d: not installed')"
if [[ "$d3" == *ready* ]]; then row 3d-pack 0 ok "${d3#3d: }"
else row 3d-pack 0 missing "optional. Install: bash \"$(cd "$HERE/.." && pwd)/3d/install_3d.sh\" --components core (Windows: install_3d.ps1 -Components core in the same folder)"; fi

de="$(bash "$HERE/detect_edit.sh" 2>/dev/null || echo 'edit: not installed')"
if [[ "$de" == *ready* ]]; then row edit-pack 0 ok "${de#edit: }"
else row edit-pack 0 missing "optional (ArtCraft editors). Install: bash \"$(cd "$HERE/.." && pwd)/edit/install_edit.sh\" --components film,sound (Windows: install_edit.ps1 -Components film,sound in the same folder)"; fi

if [[ "$JSON" == 1 ]]; then
  printf '{"os":"%s","ok":%s,"tools":[' "$OS" "$([[ $FAIL == 0 ]] && echo true || echo false)"
  sep=""
  for r in "${ROWS[@]}"; do
    IFS='|' read -r n req st det <<<"$r"
    det="${det//\\/\\\\}"; det="${det//\"/\\\"}"
    printf '%s{"name":"%s","required":%s,"status":"%s","detail":"%s"}' "$sep" "$n" "$([[ $req == 1 ]] && echo true || echo false)" "$st" "$det"
    sep=","
  done
  printf ']}\n'
else
  echo "brief2mp4 doctor ($OS)"
  for r in "${ROWS[@]}"; do
    IFS='|' read -r n req st det <<<"$r"
    printf '  %-8s %-9s %s%s\n' "$st" "$n" "$det" "$([[ $req == 0 ]] && echo '  [optional]')"
  done
  [[ $FAIL == 0 ]] && echo "RESULT: ready" || echo "RESULT: missing required tools (see above)"
fi
exit "$FAIL"
