# Start on Cursor

Arm the Cursor watchman, never the Claude or Codex one. Record the Cursor conversation id in
`.shift-session` (host line `cursor`); that id is the origin IDE tab. Revival mints or resumes a
CLI worker in `.shift-worker` and never passes the IDE id to `agent --resume`.

The plan room closes on the owner's typed `/nightshift:plan-exit` or `/nightshift:start` as the first
word of a message: `beforeSubmitPrompt` carries the typed text in `prompt` and removes the marker.
`ns plan-exit` in a terminal is the other exit.
