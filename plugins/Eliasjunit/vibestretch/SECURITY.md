# Security

## Reporting a vulnerability

Please report security problems privately, through GitHub's private
vulnerability reporting: open the repository's **Security** tab and choose
**Report a vulnerability**.

If that option isn't available, open an issue on
[Eliasjunit/vibestretch](https://github.com/Eliasjunit/vibestretch/issues)
that says you have a security report, without the details, and a private
channel will be set up with you there.

Expect a first reply within a week. Fixes ship as a new release, and the
report is credited in the release notes unless you'd rather stay unnamed.

## Supported versions

Only the latest release gets fixes.

## What the plugin touches

Useful for judging what counts as a vulnerability here:

- It runs one POSIX shell script from the agent's hooks, as your user.
- It reads the hook payload on stdin, and only for the session id.
- It writes small state files under `~/.cache/vibestretch/`.
- It reads your exercise list from `~/.config/vibestretch/exercises.txt`, if
  you made one.
- It plays a bundled sound with the system player, and on macOS reads the
  keyboard/mouse idle time.
- It makes no network calls, sends no telemetry, and adds nothing to the
  model's context.

The optional `/vibestretch:statusline` skill for Claude Code edits your Claude
Code `settings.json`, after backing it up, and only when you run it.
