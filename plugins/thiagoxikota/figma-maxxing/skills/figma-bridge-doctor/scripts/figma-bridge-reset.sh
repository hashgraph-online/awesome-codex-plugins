#!/usr/bin/env bash
# figma-bridge-reset.sh
# One-command recovery for the figma-console "Figma Desktop Bridge".
#
#   bash figma-bridge-reset.sh                        # uses $FIGMA_BRIDGE_DEFAULT_URL or the last-used URL
#   bash figma-bridge-reset.sh myapp                  # resolves the alias from <state-dir>/figma-files.json
#   bash figma-bridge-reset.sh "https://figma.com/..." # literal URL
#   FIGMA_FULL_RESET=1 bash figma-bridge-reset.sh     # quit and relaunch Figma: ONLY after the user said yes
#   FIGMA_NO_PLUGIN=1 bash figma-bridge-reset.sh      # skip the osascript plugin re-launch
#   FIGMA_KILL_OTHER_SESSIONS=1 bash figma-bridge-reset.sh   # also kill the MCP servers of OTHER sessions (only when solo)
#   FIGMA_AGENT_PROCESS=<name> bash figma-bridge-reset.sh    # process name of the agent (default: claude), see step 1
#
# <state-dir> is ${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}.
#
# Why the canonical sequence is QUIT + relaunch (not just focus + keystroke):
# field note, 2026-05-23 (validated session): the Bridge plugin's launch handler
# will not re-initialize on an already-running Figma. Clicking the menu item
# only SELECTS it, and Cmd+Opt+P on a stale Figma also fails to re-establish
# the WebSocket. The only proven flow is:
#   kill stale MCP servers > graceful quit Figma > relaunch on URL > Cmd+Opt+P
# Fresh Figma state is what unblocks the plugin launch handler.
# (Step 5 below documents the trigger this script actually sends: a menu click.)
#
# Graceful quit (`osascript -e 'tell application "Figma" to quit'`) preserves the
# tabs that were open and lets Figma's shutdown handler run. NEVER `killall Figma`:
# that leaves Figma in a 0-window state where no plugin can attach.
#
# By default the script is GENTLE: it never quits Figma. It only kills stale MCP
# servers and clicks the plugin menu. Per the field note above that is the less
# reliable path, but the user may be working in Figma right now. Set
# FIGMA_FULL_RESET=1 (the full quit + relaunch) only after the user said yes to a
# Figma restart. FIGMA_GENTLE=1 is still accepted and always wins.
#
# macOS only (osascript, open, launchctl, lsof, pgrep). The menu click needs the
# Accessibility permission on the app that runs this script and assumes the
# English Figma UI.

set -u

# macOS guard.
if [ "$(uname -s)" != "Darwin" ]; then
  cat >&2 <<'CHECKLIST'
figma-bridge-reset.sh is macOS only (osascript, open, lsof, pgrep).
On this OS, recover by hand:
  1. Close the agent sessions you are not using (each one holds a
     figma-console-mcp server on a port in 9223-9232).
  2. Quit Figma DESKTOP normally (do not force-kill it) and reopen the file.
  3. Plugins > Development > "Figma Desktop Bridge" > Run.
     If it is not listed, import it once from
     ~/.figma-console-mcp/plugin/manifest.json.
  4. Leave the plugin window OPEN.
  5. Call figma_get_status: it is the only proof of a live connection.
CHECKLIST
  exit 1
fi

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"

URL_ARG="${1:-}"
# State files live under the state dir and are created empty on first run.
STATE_DIR="${FIGMA_MAXXING_STATE_DIR:-${HOME}/.config/figma-maxxing}"
URL_CACHE="${STATE_DIR}/figma-bridge-last-url"
REGISTRY="${STATE_DIR}/figma-files.json"
SIGNAL_FILE="${STATE_DIR}/figma-reconnect-signal"
WATCHDOG_LABEL="com.figma-maxxing.bridge-watchdog"
mkdir -p "$STATE_DIR"
[ -f "$REGISTRY" ] || echo '{}' > "$REGISTRY"
[ -f "$URL_CACHE" ] || : > "$URL_CACHE"

# Resolve the URL.
# Arg can be a literal URL OR an alias from <state-dir>/figma-files.json.
# Falls back to env var, then last-used cache.
resolve_alias() {
  [ -f "$REGISTRY" ] || return 1
  python3 -c "
import json, sys
try:
    print(json.load(open(sys.argv[1])).get('files', {})[sys.argv[2]]['url'])
except KeyError:
    sys.exit(1)
" "$REGISTRY" "$1" 2>/dev/null
}

if [ -n "$URL_ARG" ]; then
  if echo "$URL_ARG" | grep -qE '^https?://'; then
    FIGMA_URL="$URL_ARG"
  else
    FIGMA_URL=$(resolve_alias "$URL_ARG") || {
      echo "ERROR: '$URL_ARG' is not a URL and not a known alias. List: bash $SELF_DIR/figma-open.sh list" >&2
      exit 1
    }
  fi
elif [ -n "${FIGMA_BRIDGE_DEFAULT_URL:-}" ]; then
  FIGMA_URL="$FIGMA_BRIDGE_DEFAULT_URL"
elif [ -s "$URL_CACHE" ]; then
  FIGMA_URL=$(cat "$URL_CACHE")
else
  FIGMA_URL=""
fi

echo "-- figma-console Bridge reset --"
[ -n "$FIGMA_URL" ] && echo "target:    $FIGMA_URL" || echo "target:    (no URL)"
FULL_RESET=0; [ "${FIGMA_FULL_RESET:-0}" = "1" ] && [ "${FIGMA_GENTLE:-0}" != "1" ] && FULL_RESET=1
[ "$FULL_RESET" = "0" ] && echo "mode:      gentle (no Figma quit)" || echo "mode:      full (will quit + relaunch Figma)"

# -- 1. Kill stale MCP servers LISTENing on 9223-9232 --------------------------
# Use `lsof -t -i tcp:PORT -s TCP:LISTEN` (not `-ti tcp:PORT`: that returns every
# PID with ANY connection to the port, including Figma helpers with an established
# WS connection. Killing those harms Figma without killing the actual server).
echo
# MULTI-SESSION SAFETY: by default, only kill this session's MCP server. Set
# FIGMA_KILL_OTHER_SESSIONS=1 to kill all servers on 9223-9232 (the original
# behavior, dangerous when other Claude Code sessions are running because it
# kills their MCP servers too).
#
# How "this session's" is decided. In Claude Code (checked on macOS), each
# session's MCP server is a descendant of that session's `claude` process, and
# so is the shell that runs this script. A server is this session's when its
# nearest ancestor named $FIGMA_AGENT_PROCESS (default: claude) is the same
# process as this script's nearest one. Do NOT compare full ancestor chains:
# every session started from the same terminal app shares the terminal and
# `login` ancestors, so a full-chain match counts other sessions' servers as
# this session's and kills them. If no such ancestor is found, nothing counts
# as this session's and the default mode kills nothing.
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
is_my_session() {
  [ -n "$my_agent" ] || return 1
  [ "$(agent_of "$1" || true)" = "$my_agent" ]
}

echo "servers before:"
killed_any=0
any_seen=0
if [ -z "$my_agent" ] && [ "${FIGMA_KILL_OTHER_SESSIONS:-0}" != "1" ]; then
  echo "  WARN: no ancestor process named '$AGENT_PROC', so this session's server cannot be told apart."
  echo "        Nothing will be killed. Set FIGMA_AGENT_PROCESS to your agent's process name,"
  echo "        or FIGMA_KILL_OTHER_SESSIONS=1 when no other session uses Figma."
fi

for p in $(seq 9223 9232); do
  pids=$(lsof -t -i tcp:"$p" -s TCP:LISTEN 2>/dev/null || true)
  for pid in $pids; do
    any_seen=1
    name=$(ps -p "$pid" -o comm= 2>/dev/null | sed 's|.*/||' | tr -d ' ')
    if ! echo "$name" | grep -qiE 'node|figma-console'; then
      echo "  :$p pid=$pid ($name) -> SKIP (not a node MCP server)"
      continue
    fi
    if [ "${FIGMA_KILL_OTHER_SESSIONS:-0}" = "1" ]; then
      echo "  :$p pid=$pid ($name) -> KILL (FIGMA_KILL_OTHER_SESSIONS=1)"
      kill "$pid" 2>/dev/null && killed_any=1
    elif is_my_session "$pid"; then
      echo "  :$p pid=$pid ($name) -> KILL (this session's)"
      kill "$pid" 2>/dev/null && killed_any=1
    else
      echo "  :$p pid=$pid ($name) -> SKIP (other session; set FIGMA_KILL_OTHER_SESSIONS=1 to override)"
    fi
  done
done
[ "$any_seen" -eq 0 ] && echo "  (no LISTEN on 9223-9232)"
[ "$killed_any" -eq 1 ] && sleep 1

# Cache URL for next no-arg call.
[ -n "$FIGMA_URL" ] && echo "$FIGMA_URL" > "$URL_CACHE"

# -- 2. Graceful quit of Figma (only with FIGMA_FULL_RESET=1) ------------------
if [ "$FULL_RESET" = "1" ]; then
  if pgrep -x Figma >/dev/null 2>&1; then
    echo
    echo "-> graceful quit of Figma Desktop (preserves tabs, no killall)"
    osascript -e 'tell application "Figma" to quit' 2>/dev/null || true
    # Wait for Figma to actually exit (poll up to 8s).
    for i in 1 2 3 4 5 6 7 8; do
      pgrep -x Figma >/dev/null 2>&1 || break
      sleep 1
    done
    if pgrep -x Figma >/dev/null 2>&1; then
      echo "   (Figma still running after 8s, proceeding anyway)"
    else
      echo "   Figma exited cleanly"
    fi
  else
    echo
    echo "-> Figma not running, will launch fresh"
  fi
fi

# -- 3. Relaunch Figma DESKTOP (never the browser) -----------------------------
# `open -a "Figma" <url>` is explicit: it forces the Figma Desktop app as URL handler
# even if Chrome/Safari is the default for figma.com URLs. NEVER use bare `open <url>`.
if [ -n "$FIGMA_URL" ]; then
  echo "-> opening Figma DESKTOP on target URL"
  open -a "Figma" "$FIGMA_URL" 2>/dev/null
else
  echo "-> opening Figma DESKTOP (no URL: will restore last session)"
  open -a "Figma" 2>/dev/null
fi
# Fresh Figma needs ~6-8s to fully load + restore session before the plugin will
# accept a launch. Polling for window readiness is unreliable, so just wait.
echo "   waiting 7s for Figma to load..."
sleep 7

# -- 4. Wait for MCP server to respawn on 9223 BEFORE clicking plugin ----------
# Race we are avoiding: step 1 killed the MCP server(s). Claude Code respawns
# them lazily (next MCP call). If we click the plugin now, the plugin tries
# to WebSocket-connect on 9223 and gets ECONNREFUSED because no listener yet.
# Wait up to 15s for any listener to come back. If still none, surface the
# issue and skip the click (the user/agent needs to make an MCP call first).
if [ "${FIGMA_NO_PLUGIN:-0}" != "1" ]; then
  echo "-> waiting for MCP server to respawn on 9223-9232..."
  for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    if lsof -t -i tcp:9223-9232 -s TCP:LISTEN >/dev/null 2>&1; then
      echo "   MCP listener up after ${i}s"
      break
    fi
    sleep 1
  done
  if ! lsof -t -i tcp:9223-9232 -s TCP:LISTEN >/dev/null 2>&1; then
    echo "   WARN: no MCP listener on 9223-9232 after 15s. Plugin click will likely fail."
    echo "   Agent should call figma_get_status to respawn the server, then retry the plugin click."
    echo "   Skipping click to avoid plugin-side connect failure that requires manual re-click."
    exit 0
  fi
fi

# -- 5. Launch the Bridge plugin via System Events menu click ------------------
# CANON (field note, 2026-05-23: validated as a manual two-step run): click
# "Figma Desktop Bridge" in Plugins > Development. Unambiguous (targets by name)
# and works regardless of which plugin was last-run.
#
# The single-call form in this script was not validated separately; the
# inferred behavior is "same primitives in one process = same outcome".
#
# Requires macOS Accessibility permission on the parent terminal app, and the
# English Figma UI (the click targets the menu items by name).
# If two "Figma Desktop Bridge" entries appear (one with a warning icon), the
# click hits the FIRST match: remove the duplicate with the warning icon via
# Plugins > Manage plugins.
# The watchdog LaunchAgent is optional: when it is not loaded, the click runs
# directly from this script.
if [ "${FIGMA_NO_PLUGIN:-0}" != "1" ]; then
  if launchctl list 2>/dev/null | grep -q "$WATCHDOG_LABEL"; then
    echo "-> sending trigger signal to decoupled watchdog..."
    touch "$SIGNAL_FILE"
  else
    echo "-> watchdog launchd agent not running; falling back to direct osascript..."
    osascript <<'APPLESCRIPT' 2>/dev/null || echo "   (osascript click failed: check Accessibility permission for the parent terminal app, and that the Figma UI is in English)"
tell application "Figma" to activate
delay 0.5
tell application "System Events"
  tell process "Figma"
    set frontmost to true
    delay 0.5
    click menu item "Figma Desktop Bridge" of menu 1 of menu item "Development" of menu 1 of menu bar item "Plugins" of menu bar 1
  end tell
end tell
APPLESCRIPT
  fi
  sleep 4
fi


# -- 6. Final state -------------------------------------------------------------
echo
echo "ports 9223-9232 after:"
any_listener=0
for p in $(seq 9223 9232); do
  pids=$(lsof -t -i tcp:"$p" -s TCP:LISTEN 2>/dev/null || true)
  for pid in $pids; do
    name=$(ps -p "$pid" -o comm= 2>/dev/null | sed 's|.*/||' | tr -d ' ')
    echo "  :$p pid=$pid ($name)"
    any_listener=1
  done
done
[ "$any_listener" -eq 0 ] && echo "  (no listeners yet: the plugin may need a few more seconds; re-probe figma_get_status)"

cat <<'STEPS'

Now re-probe `figma_get_status`.

If STILL disconnected:
  - The Bridge plugin was not the last plugin you ran. In Figma:
    Plugins > Development > "Figma Desktop Bridge" (the one WITHOUT the
    warning icon) > Run
  - Or: another Claude Code session is racing for port 9223. Close the
    other windows you are not using.
  - Or: the plugin is not imported yet. Import it once from
    ~/.figma-console-mcp/plugin/manifest.json (in the Figma file picker
    press Cmd+Shift+G and paste the path).
-- done --
STEPS
