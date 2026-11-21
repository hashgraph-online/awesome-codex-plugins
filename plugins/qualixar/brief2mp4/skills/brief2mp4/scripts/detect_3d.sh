#!/usr/bin/env bash
# detect_3d.sh: say whether the optional 3D pack is installed. Always exits 0, so a caller can branch on the text.
#
#   3d: ready (components: core,cad,blender)
#   3d: not installed
#
# "ready" needs the core component. cad and blender are listed when present.
# B2M3D_HOME overrides the install folder (default ~/.brief2mp4/3d).
set -u

HOME_DIR="${B2M3D_HOME:-$HOME/.brief2mp4/3d}"
found=()

PY="$HOME_DIR/venv/bin/python"
[[ -x "$PY" ]] || PY="$HOME_DIR/venv/Scripts/python.exe"   # Windows venv layout (Git Bash)
# "ready" means the pack actually imports and its node packages are present, not just that files exist.
if [[ -x "$PY" && -d "$HOME_DIR/node_modules/three" && -d "$HOME_DIR/node_modules/jolt-physics" ]] \
   && "$PY" -c "import b2m3d.cli" >/dev/null 2>&1; then
  found+=(core)
  "$PY" -c "import cadquery" >/dev/null 2>&1 && found+=(cad)
fi

blender_found=0
if [[ -n "${B2M3D_BLENDER:-}" && -x "${B2M3D_BLENDER}" ]]; then blender_found=1
elif command -v blender >/dev/null 2>&1; then blender_found=1
else
  for c in /Applications/Blender.app/Contents/MacOS/Blender /usr/bin/blender /usr/local/bin/blender /snap/bin/blender "/c/Program Files/Blender Foundation"/Blender*/blender.exe; do
    [[ -x "$c" ]] && { blender_found=1; break; }
  done
fi

if [[ " ${found[*]-} " == *" core "* ]]; then
  [[ $blender_found -eq 1 ]] && found+=(blender)
  (IFS=,; echo "3d: ready (components: ${found[*]})")
else
  echo "3d: not installed"
fi
exit 0
