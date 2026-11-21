#!/usr/bin/env bash
# install_3d.sh: install components of the optional brief2mp4 3D pack. No sudo, ever.
#
#   bash install_3d.sh                          # core only
#   bash install_3d.sh --components core,cad    # pick what the brief needs
#   bash install_3d.sh --components core,dev    # core + pytest, to run the test suite
#   bash install_3d.sh --uninstall              # remove $B2M3D_HOME (only if this script created it)
#
# Components
#   core     node: three, GSAP, glTF Transform, meshoptimizer, Jolt, fonts
#            python: numpy, scipy, trimesh, manifold3d (in a venv, Python 3.12 or 3.13)
#   cad      CadQuery (large: ships the OpenCascade kernel). Needs core.
#   blender  checks for a system Blender and prints how to install it. Installs nothing.
#   dev      pytest, for tests/run_tests.sh. Needs core.
#
# Installs into $B2M3D_HOME (default ~/.brief2mp4/3d), including its own copy of the pack, so moving
# or deleting the folder you ran this from does not break it. Safe to run again.
set -euo pipefail

PACK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${B2M3D_HOME:-$HOME/.brief2mp4/3d}"
COMPONENTS="core"
UNINSTALL=0
MARKER=".installed-by-brief2mp4-3d"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --components) [[ -n "${2:-}" ]] || { echo "install_3d.sh: --components needs a value, e.g. core,cad" >&2; exit 2; }; COMPONENTS="$2"; shift 2 ;;
    --uninstall) UNINSTALL=1; shift ;;
    --components=*) COMPONENTS="${1#*=}"; shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "install_3d.sh: unknown option $1" >&2; exit 2 ;;
  esac
done

# Only these entries are ever created in $HOME_DIR. Uninstall removes exactly these, then the folder
# itself only if nothing else is left in it, so a folder you also use for other things keeps them.
OWNED="venv node_modules pack js package.json package-lock.json .node-stamp .components .components.tmp $MARKER"

if [[ "$UNINSTALL" == 1 ]]; then
  if [[ ! -e "$HOME_DIR" ]]; then echo "nothing to remove at $HOME_DIR"; exit 0; fi
  [[ -f "$HOME_DIR/$MARKER" ]] || { echo "install_3d.sh: $HOME_DIR was not created by this script; left it alone" >&2; exit 1; }
  for e in $OWNED; do [[ -e "$HOME_DIR/$e" ]] && rm -rf "${HOME_DIR:?}/$e"; done
  if rmdir "$HOME_DIR" 2>/dev/null; then echo "removed $HOME_DIR"
  else echo "removed the 3D pack from $HOME_DIR; other files in it were left alone"; fi
  exit 0
fi

# Never adopt a folder that already holds someone else's files: the marker would let uninstall touch it.
if [[ -d "$HOME_DIR" && ! -f "$HOME_DIR/$MARKER" && -n "$(ls -A "$HOME_DIR" 2>/dev/null)" ]]; then
  echo "install_3d.sh: $HOME_DIR already exists and was not created by this installer. Set B2M3D_HOME to a new or empty folder." >&2
  exit 1
fi

want() { [[ ",$COMPONENTS," == *",$1,"* ]]; }
for c in ${COMPONENTS//,/ }; do
  case "$c" in core|cad|blender|dev) ;; *) echo "install_3d.sh: unknown component '$c' (core, cad, blender, dev)" >&2; exit 2 ;; esac
done
if { want cad || want dev; } && ! want core; then COMPONENTS="core,$COMPONENTS"; fi

VENV="$HOME_DIR/venv"
VBIN="$VENV/bin"; VPY="$VBIN/python"
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) VBIN="$VENV/Scripts"; VPY="$VBIN/python.exe" ;; esac
size_mb() { [[ -d "$1" ]] && du -sk "$1" | awk '{printf "%d", $1/1024}' || echo 0; }
say() { printf '%s\n' "$*"; }

find_python() {
  local cand v
  if [[ -n "${B2M3D_PYTHON:-}" ]]; then   # explicit interpreter, e.g. B2M3D_PYTHON="$(uv python find 3.12)"
    v="$("$B2M3D_PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
    case "$v" in 3.12|3.13) echo "$B2M3D_PYTHON"; return 0 ;; esac
    say "B2M3D_PYTHON=$B2M3D_PYTHON is Python ${v:-unknown}; 3.12 or 3.13 is needed." >&2; return 1
  fi
  for cand in python3.13 python3.12 python3 python py; do
    command -v "$cand" >/dev/null 2>&1 || continue
    v="$("$cand" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
    case "$v" in 3.12|3.13) command -v "$cand"; return 0 ;; esac
  done
  return 1
}

install_core() {
  command -v node >/dev/null 2>&1 || { say "node not found. Install Node.js 22 or newer (macOS: brew install node; Linux: your package manager or https://nodejs.org)." >&2; exit 1; }
  command -v npm >/dev/null 2>&1 || { say "npm not found. It ships with Node.js: https://nodejs.org" >&2; exit 1; }
  local major; major="$(node -p 'process.versions.node.split(".")[0]')"
  [[ "$major" -ge 22 ]] || { say "Node.js $major is too old: 22 or newer is needed." >&2; exit 1; }

  local py
  py="$(find_python)" || { say "Python 3.12 or 3.13 not found. macOS: brew install python@3.13. Debian/Ubuntu: python3.13 and python3.13-venv from your package manager. Then run this again." >&2; exit 1; }

  mkdir -p "$HOME_DIR"
  touch "$HOME_DIR/$MARKER"
  local before; before=$(( $(size_mb "$VENV") + $(size_mb "$HOME_DIR/node_modules") ))

  say "core: python venv ($py) at $VENV"
  [[ -x "$VPY" ]] || "$py" -m venv "$VENV"
  say "core: installing numpy, scipy, trimesh, manifold3d"
  "$VPY" -m pip install --disable-pip-version-check -q -r "$PACK/requirements-core.txt"

  install_node_packages
  link_pack
  say "core: done, $(( $(size_mb "$VENV") + $(size_mb "$HOME_DIR/node_modules") - before )) MB added (venv $(size_mb "$VENV") MB, node_modules $(size_mb "$HOME_DIR/node_modules") MB)"
}

node_stamp() {
  { cat "$HOME_DIR/package.json"; cat "$HOME_DIR/package-lock.json" 2>/dev/null || true; } | cksum
}

install_node_packages() {
  say "core: installing three, gsap, glTF Transform, meshoptimizer, jolt-physics, fonts"
  cp "$PACK/package.json" "$HOME_DIR/package.json"
  if [[ -f "$PACK/package-lock.json" ]]; then cp "$PACK/package-lock.json" "$HOME_DIR/package-lock.json"; fi
  local stamp; stamp="$(node_stamp)"
  if [[ -d "$HOME_DIR/node_modules/three" && "$(cat "$HOME_DIR/.node-stamp" 2>/dev/null || true)" == "$stamp" ]]; then
    say "core: node packages already up to date"
    return
  fi
  if [[ -f "$HOME_DIR/package-lock.json" ]]; then
    (cd "$HOME_DIR" && npm ci --omit=dev --no-audit --no-fund --loglevel=error)
  else
    (cd "$HOME_DIR" && npm install --omit=dev --no-audit --no-fund --loglevel=error)
  fi
  stamp="$(node_stamp)"
  printf '%s\n' "$stamp" > "$HOME_DIR/.node-stamp"
}

link_pack() {
  # Copy the pack into the install home, then point a .pth file at the copy, so `python -m b2m3d`
  # works from any folder and keeps working if the clone or plugin cache moves.
  local dest="$HOME_DIR/pack" site
  rm -rf "$dest.new"; mkdir -p "$dest.new"
  cp -R "$PACK/b2m3d" "$PACK/js" "$PACK/templates" "$PACK/presets" "$dest.new/"
  [[ -d "$PACK/examples" ]] && cp -R "$PACK/examples" "$dest.new/"
  find "$dest.new" -name __pycache__ -type d -prune -exec rm -rf {} +
  rm -rf "$dest"; mv "$dest.new" "$dest"
  site="$("$VPY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
  printf '%s\n' "$dest" > "$site/b2m3d-pack.pth"
  printf '#!/usr/bin/env bash\nexec "%s" -m b2m3d "$@"\n' "$VPY" > "$VBIN/brief2mp4-3d"
  chmod +x "$VBIN/brief2mp4-3d"
  "$VPY" -c "import b2m3d.cli" || { say "core: the pack copy in $dest does not import" >&2; exit 1; }
  say "core: command ready: $VBIN/brief2mp4-3d   (or: $VPY -m b2m3d)"
}

install_cad() {
  local before; before=$(size_mb "$VENV")
  say "cad: installing CadQuery (large download)"
  "$VPY" -m pip install --disable-pip-version-check -q -r "$PACK/requirements-cad.txt"
  say "cad: done, $(( $(size_mb "$VENV") - before )) MB added"
}

install_dev() {
  say "dev: installing pytest"
  "$VPY" -m pip install --disable-pip-version-check -q -r "$PACK/requirements-dev.txt"
}

check_blender() {
  local found=""
  if [[ -n "${B2M3D_BLENDER:-}" && -x "${B2M3D_BLENDER}" ]]; then found="$B2M3D_BLENDER"
  elif command -v blender >/dev/null 2>&1; then found="$(command -v blender)"
  else
    for c in /Applications/Blender.app/Contents/MacOS/Blender /usr/bin/blender /usr/local/bin/blender /snap/bin/blender; do
      [[ -x "$c" ]] && { found="$c"; break; }
    done
  fi
  if [[ -n "$found" ]]; then
    say "blender: found $found ($("$found" --version 2>/dev/null | head -1))"
  else
    say "blender: not found. Install it yourself (this script never uses sudo):"
    say "  macOS:  brew install --cask blender"
    say "  Linux:  your package manager (Blender 4.2 or newer), or https://www.blender.org/download/"
  fi
}

want core && install_core
want cad && install_cad
want dev && install_dev
want blender && check_blender
mkdir -p "$HOME_DIR"
touch "$HOME_DIR/.components"
{ cat "$HOME_DIR/.components"; printf '%s\n' ${COMPONENTS//,/ }; } | sort -u > "$HOME_DIR/.components.tmp"
mv "$HOME_DIR/.components.tmp" "$HOME_DIR/.components"
say "installed components: $(paste -sd, "$HOME_DIR/.components")   total on disk: $(size_mb "$HOME_DIR") MB in $HOME_DIR"
