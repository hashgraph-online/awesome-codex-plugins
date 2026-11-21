#!/bin/sh
set -eu

base=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
node_binary=${GOAL_PROGRESS_NODE_BINARY:-}

node_is_supported() {
  candidate=$1
  [ -x "$candidate" ] || return 1
  "$candidate" -e '
    const [major, minor] = process.versions.node.split(".").map(Number);
    process.exit(major > 22 || (major === 22 && minor >= 12) ? 0 : 1);
  ' >/dev/null 2>&1
}

if [ -n "$node_binary" ] && ! node_is_supported "$node_binary"; then
  node_binary=
fi

if [ -z "$node_binary" ]; then
  for candidate in \
    /opt/homebrew/bin/node \
    /usr/local/bin/node \
    "$HOME/.local/bin/node" \
    "$HOME/.volta/bin/node"
  do
    if node_is_supported "$candidate"; then
      node_binary=$candidate
      break
    fi
  done
fi

if [ -z "$node_binary" ]; then
  candidate=$(command -v node 2>/dev/null || true)
  if [ -n "$candidate" ] && node_is_supported "$candidate"; then
    node_binary=$candidate
  fi
fi

if [ -z "$node_binary" ] && [ -x /bin/zsh ]; then
  candidate=$(/bin/zsh -lc 'command -v node 2>/dev/null || true' 2>/dev/null || true)
  if [ -n "$candidate" ] && node_is_supported "$candidate"; then
    node_binary=$candidate
  fi
fi

if [ -z "$node_binary" ]; then
  echo "GOAL_PROGRESS_NODE_NOT_FOUND: install Node.js 22.12 or newer" >&2
  exit 1
fi

export GOAL_PROGRESS_NODE_BINARY="$node_binary"
exec "$node_binary" "$base/bootstrap.mjs" "$@"
