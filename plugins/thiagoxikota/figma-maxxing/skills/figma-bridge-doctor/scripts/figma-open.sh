#!/usr/bin/env bash
# figma-open.sh: resolve a Figma file alias (or URL), open it in Figma Desktop,
# then trigger the Figma Desktop Bridge plugin so the figma-console MCP server
# is ready to use.
#
#   bash figma-open.sh myapp              # opens the file registered as "myapp" + triggers plugin
#   bash figma-open.sh "https://..."      # opens a literal URL + triggers
#   bash figma-open.sh list               # lists known aliases
#   FIGMA_NO_PLUGIN=1 bash figma-open.sh myapp   # open without plugin trigger
#
# Aliases live in <state-dir>/figma-files.json, where <state-dir> is
# ${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}. Register one with
# figma-add.sh. The script ALSO updates the URL cache
# (<state-dir>/figma-bridge-last-url) so a subsequent `figma-bridge-reset.sh`
# with no arg will target the same file.
#
# Difference vs figma-bridge-reset.sh: this one does NOT kill stale MCP servers and
# does NOT quit Figma. Use this for opening a fresh file; use figma-bridge-reset.sh
# when the bridge is misbehaving and needs surgical recovery.
#
# macOS only (open, osascript, launchctl). The menu click needs the Accessibility
# permission on the app that runs this script and assumes the English Figma UI.

set -u

# macOS guard.
if [ "$(uname -s)" != "Darwin" ]; then
  cat >&2 <<'CHECKLIST'
figma-open.sh is macOS only (open, osascript). On this OS, do it by hand:
  1. Open the file in Figma DESKTOP (not the browser).
  2. Plugins > Development > "Figma Desktop Bridge" > Run.
     If it is not listed, import it once from
     ~/.figma-console-mcp/plugin/manifest.json.
  3. Leave the plugin window OPEN.
  4. Call figma_get_status: it is the only proof of a live connection.
CHECKLIST
  exit 1
fi

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"

# State files live under the state dir and are created empty on first run.
STATE_DIR="${FIGMA_MAXXING_STATE_DIR:-${HOME}/.config/figma-maxxing}"
REGISTRY="${STATE_DIR}/figma-files.json"
CACHE="${STATE_DIR}/figma-bridge-last-url"
SIGNAL_FILE="${STATE_DIR}/figma-reconnect-signal"
WATCHDOG_LABEL="com.figma-maxxing.bridge-watchdog"
mkdir -p "$STATE_DIR"
[ -f "$REGISTRY" ] || echo '{}' > "$REGISTRY"
[ -f "$CACHE" ] || : > "$CACHE"

ARG="${1:-list}"

# list mode
if [ "$ARG" = "list" ] || [ "$ARG" = "--list" ] || [ "$ARG" = "-l" ]; then
  echo "Known Figma aliases (from $REGISTRY):"
  echo "  Status: [V] validated open  [?] unverified: first open is the test"
  echo
  python3 -c "
import json, sys
files = json.load(open(sys.argv[1])).get('files', {})
if not files:
    print('  (none yet; register one with: bash figma-add.sh <figma-url> [alias])')
for alias, meta in files.items():
    status = '[V]' if meta.get('validated') else '[?]'
    print(f'  {status} {alias:20s} {meta[\"label\"]}')
    print(f'      {\"\":20s} {meta[\"url\"]}')
" "$REGISTRY" 2>/dev/null || jq -r '(.files // {}) | to_entries[] | "  [?] \(.key)  \(.value.label)\n      \(.value.url)"' "$REGISTRY"
  exit 0
fi

# URL passed literally: just open it
if echo "$ARG" | grep -qE '^https?://'; then
  URL="$ARG"
else
  # Resolve alias via registry
  URL=$(python3 -c "
import json, sys
try:
    files = json.load(open(sys.argv[1])).get('files', {})
    print(files[sys.argv[2]]['url'])
except KeyError:
    sys.exit(1)
" "$REGISTRY" "$ARG" 2>/dev/null)

  if [ -z "$URL" ]; then
    echo "ERROR: unknown alias '$ARG'. Try: bash $SELF_DIR/figma-open.sh list" >&2
    echo "       Register a new one: bash $SELF_DIR/figma-add.sh <figma-url> [alias]" >&2
    exit 1
  fi
fi

# `open -a "Figma" <url>` is explicit: it forces macOS to use the Figma Desktop app
# as the URL handler, even if Chrome or Safari is the default for figma.com URLs.
# NEVER use just `open <url>` here: that can fall back to the browser.
echo "-> opening Figma DESKTOP (not browser) on: $URL"
open -a "Figma" "$URL"

# Warn if this alias is unverified
if ! echo "$ARG" | grep -qE '^https?://'; then
  validated=$(python3 -c "
import json, sys
try:
    files = json.load(open(sys.argv[1])).get('files', {})
    print(files.get(sys.argv[2], {}).get('validated') or 'null')
except Exception:
    print('null')
" "$REGISTRY" "$ARG" 2>/dev/null)
  if [ "$validated" = "null" ]; then
    echo "   WARN: alias '$ARG' is unverified. Confirm the right file opened."
    echo "   To mark as validated, edit $REGISTRY and set validated: \"$(date +%Y-%m-%d)\""
  fi
fi

# Cache for the next no-arg figma-bridge-reset.sh call.
mkdir -p "$(dirname "$CACHE")"
echo "$URL" > "$CACHE"
echo "   (cached as last-used target; figma-bridge-reset.sh will re-use it)"

# Trigger the Figma Desktop Bridge plugin via System Events menu click.
# Same recipe as figma-bridge-reset.sh step 5: keep them in sync.
# Field note, 2026-05-23: validated. Requires Accessibility permission on the parent
# terminal app. Idempotent: clicking a running plugin is a no-op.
# The watchdog LaunchAgent is optional: when it is not loaded, the click runs
# directly from this script.
if [ "${FIGMA_NO_PLUGIN:-0}" != "1" ]; then
  echo "   waiting 7s for Figma to load before triggering the Bridge plugin..."
  sleep 7
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
  echo "   Bridge plugin trigger step complete. Verify with: bash $SELF_DIR/figma-status.sh, then call figma_get_status"
fi
