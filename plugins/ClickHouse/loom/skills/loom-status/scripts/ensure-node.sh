#!/bin/sh
# LF line endings only (.gitattributes): sh reads a CR as part of a command.
# Loom's coding-agent hooks run through bin/loom-node, which finds Node 18+
# on PATH, under a version manager or in the usual install directories.
#   ensure-node.sh --check   report only: exit 0 when ready, 1 when missing
#   ensure-node.sh           install Node when missing (root or sudo -n);
#                            exit 2 names what blocks the install
set -eu

LAUNCHER="$(dirname "$0")/../../../bin/loom-node"
CLAUDE_SETTINGS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"
SETUP_FILE=''
trap 'if [ -n "$SETUP_FILE" ]; then rm -f "$SETUP_FILE"; fi' EXIT HUP INT TERM

as_root() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo -n "$@"
  fi
}

require_privilege() {
  if [ "$(id -u)" -ne 0 ] && { ! command -v sudo >/dev/null 2>&1 || ! sudo -n true 2>/dev/null; }; then
    echo 'Node is required, but installation needs root or passwordless sudo. Run this helper from a privileged shell.' >&2
    exit 2
  fi
}

download_setup() {
  SETUP_FILE=$(mktemp "${TMPDIR:-/tmp}/loom-node-setup.XXXXXX")
  curl -fsSL --connect-timeout 10 --max-time 120 "$1" -o "$SETUP_FILE"
}

# The launcher as Claude Code started from the Dock runs it: no shell
# profile, only HOME, the system PATH and its settings.json `env`.
gui_check() {
  set -- HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin
  settings=$(sh "$LAUNCHER" -e '
    try {
      const env = require(process.argv[1]).env || {};
      for (const [k, v] of Object.entries(env))
        if (/^[A-Za-z_]\w*$/.test(k) && typeof v === "string" && !v.includes("\n"))
          console.log(`${k}=${v}`);
    } catch {}' "$CLAUDE_SETTINGS" 2>/dev/null)
  while IFS= read -r kv; do
    [ -n "$kv" ] && set -- "$@" "$kv"
  done <<SETTINGS
$settings
SETTINGS
  env -i "$@" sh "$LAUNCHER" --check >/dev/null 2>&1
}

claude_code() {
  [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && return 0
  case $0 in */.claude/plugins/*) return 0 ;; esac
  [ -n "${CLAUDE_CONFIG_DIR:-}" ] && case $0 in "$CLAUDE_CONFIG_DIR"/plugins/*) return 0 ;; esac
  return 1
}

# Codex runs its MCP header helper with HOME and PATH, and no LOOM_NODE.
# LOOM_NODE_SYSTEM_DIRS is kept when set, so a test can replace the fixed
# directories both runs search.
codex_helper_check() {
  set -- HOME="$HOME" PATH="$PATH"
  [ -n "${LOOM_NODE_SYSTEM_DIRS+x}" ] && set -- "$@" LOOM_NODE_SYSTEM_DIRS="$LOOM_NODE_SYSTEM_DIRS"
  env -i "$@" sh "$LAUNCHER" --check >/dev/null 2>&1
}

if [ "${1:-}" = '--check' ]; then
  sh "$LAUNCHER" --check || exit 1
  # On Windows a GUI app gets the user's PATH, and Codex runs no launcher.
  case "$(uname -s)" in Darwin | Linux) ;; *) exit 0 ;; esac
  if claude_code; then
    gui_check || echo 'Found only with this shell'"'"'s environment: Claude Code started from the Dock or a desktop launcher finds no Node. Set LOOM_NODE to the path above in the env block of '"$CLAUDE_SETTINGS."
  else
    codex_helper_check || echo 'The MCP header helper, which Codex runs without LOOM_NODE or a version manager'"'"'s variables, finds no Node. Put that Node'"'"'s directory on the PATH Codex starts with.'
  fi
  exit 0
fi

if sh "$LAUNCHER" --check 2>/dev/null; then
  exit 0
fi

if [ -n "${LOOM_NODE:-}" ]; then
  echo "LOOM_NODE=$LOOM_NODE is not Node.js 18+, and it wins over any install; fix or unset it." >&2
  exit 2
fi

case "$(uname -s)" in
  Linux)
    require_privilege
    if command -v apt-get >/dev/null 2>&1; then
      if ! command -v curl >/dev/null 2>&1; then
        as_root apt-get update
        as_root apt-get install -y curl
      fi
      download_setup 'https://deb.nodesource.com/setup_22.x'
      as_root bash "$SETUP_FILE"
      as_root apt-get install -y nodejs
    elif command -v dnf >/dev/null 2>&1 || command -v yum >/dev/null 2>&1; then
      pkg=dnf
      command -v dnf >/dev/null 2>&1 || pkg=yum
      if ! command -v curl >/dev/null 2>&1; then
        as_root "$pkg" install -y curl
      fi
      download_setup 'https://rpm.nodesource.com/setup_22.x'
      as_root bash "$SETUP_FILE"
      as_root "$pkg" install -y nodejs
    elif command -v apk >/dev/null 2>&1; then
      as_root apk add --no-cache nodejs
    else
      echo 'Unsupported Linux package manager; install Node.js 18+, or set LOOM_NODE=/path/to/node.' >&2
      exit 2
    fi
    ;;
  Darwin)
    if ! command -v brew >/dev/null 2>&1; then
      echo 'Homebrew is needed to install Node.js automatically on macOS.' >&2
      exit 2
    fi
    brew upgrade node || brew install node
    ;;
  *)
    echo 'No installer for this OS; install Node.js 18+, or set LOOM_NODE=/path/to/node.' >&2
    exit 2
    ;;
esac

sh "$LAUNCHER" --check
echo 'Restart the coding-agent session.'
