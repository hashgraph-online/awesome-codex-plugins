#!/usr/bin/env bash
# figma-watchdog.sh
# Watches for <state-dir>/figma-reconnect-signal and launches the Figma Desktop
# Bridge plugin. <state-dir> is ${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}.
#
# OPTIONAL. Meant to run as a persistent LaunchAgent under the user session
# context (template: com.figma-maxxing.bridge-watchdog.plist.template, next to
# this file). figma-open.sh and figma-bridge-reset.sh keep working without it:
# when the agent is not loaded they click the menu directly.
#
# macOS only (osascript). The menu click needs the Accessibility permission for
# the process that runs it and assumes the English Figma UI.

# macOS guard.
if [ "$(uname -s)" != "Darwin" ]; then
  cat >&2 <<'CHECKLIST'
figma-watchdog.sh is macOS only (osascript). On this OS there is no watchdog:
  1. Open the file in Figma DESKTOP (not the browser).
  2. Plugins > Development > "Figma Desktop Bridge" > Run.
  3. Leave the plugin window OPEN.
  4. Call figma_get_status: it is the only proof of a live connection.
CHECKLIST
  exit 1
fi

STATE_DIR="${FIGMA_MAXXING_STATE_DIR:-${HOME}/.config/figma-maxxing}"
SIGNAL_FILE="${STATE_DIR}/figma-reconnect-signal"
mkdir -p "$STATE_DIR"

echo "Figma watchdog: Starting watcher on ${SIGNAL_FILE}..."

while true; do
  if [ -f "$SIGNAL_FILE" ]; then
    echo "Figma watchdog: Signal detected at $(date), triggering Figma Desktop Bridge..."
    # Perform the AppleScript click
    osascript -e 'tell application "Figma" to activate' \
              -e 'delay 0.5' \
              -e 'tell application "System Events" to tell process "Figma" to click menu item "Figma Desktop Bridge" of menu 1 of menu item "Development" of menu 1 of menu bar item "Plugins" of menu bar 1' 2>/dev/null
    rm -f "$SIGNAL_FILE"
    echo "Figma watchdog: Bridge triggered, signal cleared."
  fi
  sleep 2
done
