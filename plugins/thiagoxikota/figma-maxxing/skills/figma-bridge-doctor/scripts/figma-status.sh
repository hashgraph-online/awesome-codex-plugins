#!/usr/bin/env bash
# figma-status.sh: one-shot snapshot of bridge state, for the skill to read.
# Outputs structured key=value lines; meant to be parsed by the agent.
#
#   bash figma-status.sh
#
# Read-only against Figma: it never opens, quits or clicks anything.
# macOS only (pgrep, lsof, ps).

set -u

# macOS guard.
if [ "$(uname -s)" != "Darwin" ]; then
  cat >&2 <<'CHECKLIST'
figma-status.sh is macOS only (pgrep, lsof, ps). On this OS, check by hand:
  1. Figma DESKTOP (not the browser) is running with a file open.
  2. A figma-console-mcp server is listening on a port in 9223-9232.
  3. The "Figma Desktop Bridge" plugin window is open in that file
     (Plugins > Development > Figma Desktop Bridge).
  4. Call figma_get_status: it is the only proof of a live connection.
CHECKLIST
  exit 1
fi

# State files live under the state dir and are created empty on first run.
STATE_DIR="${FIGMA_MAXXING_STATE_DIR:-${HOME}/.config/figma-maxxing}"
REGISTRY="${STATE_DIR}/figma-files.json"
CACHE="${STATE_DIR}/figma-bridge-last-url"
mkdir -p "$STATE_DIR"
[ -f "$REGISTRY" ] || echo '{}' > "$REGISTRY"
[ -f "$CACHE" ] || : > "$CACHE"

echo "-- figma-status --"

# Is Figma running?
if pgrep -x Figma >/dev/null 2>&1; then
  figma_pid=$(pgrep -x Figma)
  echo "figma_running=true"
  echo "figma_pid=$figma_pid"
else
  echo "figma_running=false"
fi

# This session's MCP server.
# In Claude Code (checked on macOS), each session's MCP server is a descendant of
# that session's `claude` process, and so is the shell that runs this script. A
# listener is this session's when its nearest ancestor named $FIGMA_AGENT_PROCESS
# (default: claude) is the same process as this script's nearest one. Do NOT
# compare full ancestor chains: every session started from the same terminal app
# shares the terminal and `login` ancestors, so a full-chain match counts other
# sessions' servers as this session's (other_sessions_count drops to 0 and the
# consent gates never fire). If no such ancestor is found, every listener counts
# as another session's.
AGENT_PROC="${FIGMA_AGENT_PROCESS:-claude}"
proc_name() { ps -p "$1" -o comm= 2>/dev/null | sed 's|.*/||' | tr -d ' '; }
agent_of() {
  local p="$1"
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    if [ -z "$p" ] || [ "$p" = "0" ] || [ "$p" = "1" ]; then
      return 1
    fi
    if [ "$(proc_name "$p")" = "$AGENT_PROC" ]; then
      echo "$p"
      return 0
    fi
  done
  return 1
}
my_agent=$(agent_of $$ || true)
echo "my_agent_pid=${my_agent:-none}"
[ -n "$my_agent" ] || echo "my_agent_note=no ancestor process named '$AGENT_PROC'; no listener counts as this session's (set FIGMA_AGENT_PROCESS)"

# Orphans: listeners nothing alive owns. A listener is an orphan when it has no
# agent ancestor and every process from it up to launchd (pid 1) is the server or
# its own npx wrapper (the command line mentions figma-console-mcp), so the session
# that started it is gone. In Claude Code the chain is node (server) > npm exec
# figma-console-mcp > claude; an orphan is that chain with the agent missing.
# A listener under any other live process (another agent, a terminal, an
# mcp-direct daemon) is NOT an orphan: something may still be using it, so it
# goes to other_sessions and killing it needs the user's consent.
is_orphan() {
  local p="$1" parent
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    ps -o args= -p "$p" 2>/dev/null | grep -q 'figma-console-mcp' || return 1
    parent=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    [ "$parent" = "1" ] && return 0
    if [ -z "$parent" ] || [ "$parent" = "0" ]; then
      return 1
    fi
    p="$parent"
  done
  return 1
}

mine_port=""
mine_pid=""
others=""
orphans=""
for p in $(seq 9223 9232); do
  pids=$(lsof -t -i tcp:"$p" -s TCP:LISTEN 2>/dev/null || true)
  for pid in $pids; do
    owner=$(agent_of "$pid" || true)
    if [ -n "$my_agent" ] && [ "$owner" = "$my_agent" ]; then
      mine_port="$p"
      mine_pid="$pid"
    elif [ -z "$owner" ] && is_orphan "$pid"; then
      orphans="$orphans ${p}:${pid}"
    else
      others="$others ${p}:${pid}"
    fi
  done
done

# This session's server can be alive without a port, for example when it started
# while 9223-9232 were all taken: it then runs without the WebSocket transport.
# Report its pid so deep recovery can restart it.
if [ -z "$mine_pid" ] && [ -n "$my_agent" ]; then
  for pid in $(pgrep -f figma-console-mcp 2>/dev/null); do
    [ "$(proc_name "$pid")" = "node" ] || continue
    if [ "$(agent_of "$pid" || true)" = "$my_agent" ]; then
      mine_pid="$pid"
      echo "my_mcp_note=this session's server holds no port in 9223-9232"
      break
    fi
  done
fi

echo "my_mcp_port=${mine_port:-none}"
echo "my_mcp_pid=${mine_pid:-none}"
echo "other_sessions_count=$(echo "$others" | wc -w | tr -d ' ')"
[ -n "$others" ] && echo "other_sessions=$(echo $others | xargs)"
echo "orphans_count=$(echo "$orphans" | wc -w | tr -d ' ')"
[ -n "$orphans" ] && echo "orphans=$(echo $orphans | xargs)"

# Cached last-used URL
if [ -s "$CACHE" ]; then
  echo "last_url_cached=$(cat "$CACHE")"
fi

# Registry summary
if [ -f "$REGISTRY" ]; then
  alias_count=$(python3 -c "import json, sys; print(len(json.load(open(sys.argv[1])).get('files', {})))" "$REGISTRY" 2>/dev/null || echo "?")
  echo "registry_aliases=$alias_count"
fi

# Plugin version drift (field note, 2026-09): a server started from an OLD npx
# cache rewrites ~/.figma-console-mcp/plugin/ with its own bundle, and the plugin
# starts announcing "update available". The banner does NOT say the direction:
# it can be a downgrade. Measure it here.
PLUGIN_DIR="${HOME}/.figma-console-mcp/plugin"

# Read the version of a bundle directory: the .version file wins when it exists
# (it is what the installer writes); the grep over code.js is only a fallback,
# because it picks the highest version string in the whole bundle and lies when
# the code mentions another one. The fallback only runs when .version is missing,
# and its pattern assumes a 1.x bundle.
bundle_version() {
  local dir="$1"
  if [ -s "$dir/.version" ]; then
    tr -d ' \t\r\n' < "$dir/.version"
    return 0
  fi
  grep -oE '1\.[0-9]+\.[0-9]+' "$dir/code.js" 2>/dev/null | sort -t. -k1,1n -k2,2n -k3,3n | tail -1
}

if [ -f "$PLUGIN_DIR/code.js" ]; then
  disk_v=$(bundle_version "$PLUGIN_DIR")
  echo "plugin_disk_version=${disk_v:-unknown}"
  # The npx cache lives under the npm cache dir, which differs per machine:
  # resolve it at runtime instead of assuming a path.
  NPM_CACHE="$(npm config get cache 2>/dev/null || true)"
  [ -n "$NPM_CACHE" ] || NPM_CACHE="${HOME}/.npm"
  NPX_DIR="${NPM_CACHE}/_npx"
  best_pkg=""; best_bundle=""; best_dir=""; best_rank=-1; cache_count=0
  for d in "$NPX_DIR"/*/node_modules/figma-console-mcp; do
    [ -f "$d/package.json" ] || continue
    [ -f "$d/dist/local.js" ] || continue
    cache_count=$((cache_count+1))
    v=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1]))['version'])" "$d/package.json" 2>/dev/null) || continue
    rank=$(echo "$v" | awk -F. '{printf "%d", $1*1000000+$2*1000+$3}')
    if [ "${rank:-0}" -gt "$best_rank" ]; then
      best_rank=$rank; best_pkg=$v; best_dir=$d
      best_bundle=$(bundle_version "$d/figma-desktop-bridge")
    fi
  done
  echo "plugin_npx_dir=$NPX_DIR"
  echo "plugin_npx_caches=$cache_count"
  echo "plugin_pkg_newest=${best_pkg:-unknown}"
  echo "plugin_bundle_newest=${best_bundle:-unknown}"
  if [ -n "$disk_v" ] && [ -n "$best_bundle" ] && [ "$disk_v" != "$best_bundle" ]; then
    echo "plugin_drift=true"
    # The source package is the one with the HIGHEST VERSION, never the newest mtime.
    echo "plugin_drift_fix=cp \"$best_dir\"/figma-desktop-bridge/{code.js,ui.html,manifest.json} \"$PLUGIN_DIR\"/ && re-run the plugin (back up the plugin dir first and write .version: full recipe in SKILL.md)"
  else
    echo "plugin_drift=false"
  fi
fi

# What is my MCP server currently paired with? That needs an MCP call, which a
# script cannot make. The agent must call figma_get_status to get
# currentFileName + transport state.
# figma_get_status also returns connectedFiles[].pluginVersion and
# pluginUpdateAvailable: the version that is RUNNING in each file, which can
# differ from the one on disk until the plugin is re-run there.
echo "current_file_pairing=ask_figma_get_status"
echo "-- end --"
