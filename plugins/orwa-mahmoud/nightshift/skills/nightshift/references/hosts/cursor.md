# Start on Cursor

Arm the Cursor watchman, never the Claude or Codex one. Record the Cursor conversation id in
`.shift-session` (host line `cursor`); that id is the origin IDE tab. Revival mints or resumes a
CLI worker in `.shift-worker` and never passes the IDE id to `agent --resume`.

The CLI runs the installed plugin's hooks, including in print mode (`agent -p`). A finished shift whose session is gone or idle is clocked out by the watchman, which runs the same ending as the stop hook. A project
`.cursor/hooks.json` is not required. One that points at Nightshift's hook scripts runs each
of those hooks twice; remove that file. Setup does not write it.

The plan room closes on the owner's typed `/nightshift:plan-exit` or `/nightshift:start` as the first
word of a message: `beforeSubmitPrompt` carries the typed text in `prompt` and removes the marker.
`ns plan-exit` in a terminal is the other exit.
