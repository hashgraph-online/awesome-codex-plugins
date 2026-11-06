#!/bin/sh

# Resolve a user-managed Node.js 22.12+ without pinning launchd to one
# Homebrew Cellar version.
goal_progress_node_is_supported() {
  candidate=${1:-}
  [ -n "$candidate" ] && [ -x "$candidate" ] || return 1
  "$candidate" -e '
    const [major = 0, minor = 0, patch = 0] = process.versions.node.split(".").map(Number);
    const supported = major > 22 || (major === 22 && (minor > 12 || (minor === 12 && patch >= 0)));
    process.exit(supported ? 0 : 1);
  ' >/dev/null 2>&1
}

goal_progress_resolve_node() {
  seen='|'

  goal_progress_try_node() {
    candidate=${1:-}
    [ -n "$candidate" ] || return 1
    case "$seen" in
      *"|$candidate|"*) return 1 ;;
    esac
    seen="${seen}${candidate}|"
    if goal_progress_node_is_supported "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
    return 1
  }

  explicit=${GOAL_PROGRESS_NODE_BINARY:-}
  if [ -n "$explicit" ] && goal_progress_try_node "$explicit"; then
    return 0
  fi

  for candidate in \
    /opt/homebrew/bin/node \
    /usr/local/bin/node \
    "$HOME/.local/bin/node" \
    "$HOME/.volta/bin/node"
  do
    if goal_progress_try_node "$candidate"; then
      return 0
    fi
  done

  path_node=$(command -v node 2>/dev/null || true)
  if [ -n "$path_node" ] && goal_progress_try_node "$path_node"; then
    return 0
  fi

  if [ -x /bin/zsh ]; then
    login_node=$(/bin/zsh -lc 'command -v node 2>/dev/null || true' 2>/dev/null || true)
    if [ -n "$login_node" ] && goal_progress_try_node "$login_node"; then
      return 0
    fi
  fi

  echo "GOAL_PROGRESS_NODE_VERSION_UNSUPPORTED: install Node.js 22.12 or newer" >&2
  return 1
}
