# figma-bridge-doctor: optional watchdog LaunchAgent

Optional. macOS only. Nothing in this skill requires it: when the agent is not loaded,
`figma-open.sh` and `figma-bridge-reset.sh` click the Figma menu directly with `osascript`.

## What it is

`scripts/figma-watchdog.sh` is an endless loop that checks every 2 seconds for a signal file,
`<state-dir>/figma-reconnect-signal`. When the file exists, it activates Figma, clicks
`Plugins > Development > Figma Desktop Bridge`, and deletes the file. `<state-dir>` is
`${FIGMA_MAXXING_STATE_DIR:-$HOME/.config/figma-maxxing}`.

It is meant to run as a persistent LaunchAgent in the user session, so the menu click comes from
one long-lived process instead of from whichever terminal the agent happens to run in.

How the other scripts use it:

- `figma-open.sh` and `figma-bridge-reset.sh` run `launchctl list` and look for the label
  `com.figma-maxxing.bridge-watchdog`.
- Label found: they `touch` the signal file and let the watchdog click.
- Label not found: they click directly with `osascript`. This is the default path.

## Rules for the agent

- Installing it is a USER decision. It is a background process that starts again at every login.
  Never install, load or unload it on your own initiative. Mention it as an option, nothing more.
- Never treat "signal sent" as success. The watchdog deletes the signal file even when the click
  failed. `figma_get_status` is the only proof.

## Install (the user runs this)

The template is `scripts/com.figma-maxxing.bridge-watchdog.plist.template`. launchd does not expand
`~` or `$HOME`, so the two placeholders must become absolute paths.

```bash
# from this skill's scripts/ directory
SCRIPTS_DIR="$(pwd)"
PLIST="$HOME/Library/LaunchAgents/com.figma-maxxing.bridge-watchdog.plist"
sed -e "s|__SCRIPTS_DIR__|$SCRIPTS_DIR|g" -e "s|__HOME__|$HOME|g" \
  com.figma-maxxing.bridge-watchdog.plist.template > "$PLIST"
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl list | grep com.figma-maxxing.bridge-watchdog   # one line = loaded
```

Keep the label unchanged: the scripts look for it by that exact name. If you set
`FIGMA_MAXXING_STATE_DIR` in your shell, repeat it in the plist (`EnvironmentVariables`, see the
commented block in the template). launchd does not inherit your shell environment, so without it
the watchdog watches the default state dir while the scripts write the signal somewhere else.

## Permissions

The click goes through System Events, so the process that launchd starts needs the Accessibility
permission (System Settings > Privacy & Security > Accessibility). The click also assumes the
English Figma UI, like every other menu click in this skill.

Logs go to `~/Library/Logs/figma-watchdog.out.log` and `~/Library/Logs/figma-watchdog.err.log`.

## Remove

```bash
launchctl bootout "gui/$(id -u)/com.figma-maxxing.bridge-watchdog"
rm "$HOME/Library/LaunchAgents/com.figma-maxxing.bridge-watchdog.plist"
```

After removal the scripts fall back to the direct click on their own.
