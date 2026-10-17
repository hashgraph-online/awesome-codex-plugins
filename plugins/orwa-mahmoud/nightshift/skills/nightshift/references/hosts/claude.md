# Start on Claude Code

The owner configures permissions directly in Claude Code. Nightshift never writes permission
modes or allowlists and never adds bypass flags during recovery. Set `recovery.launchScope` to
`host-default` to recover using that independent host configuration; this does not promise the
original session's permission mode. The shipped recorded-scope choice refuses when it cannot
restore a supported restricted scope. A prompt or denial can require the owner's attention.
A live conversation is handed back with `claude --resume <id>` for a
terminal, or `vscode://anthropic.claude-code/open?session=<id>` for the IDE; `claude agents --json`
lists ids. Claude Code records clean session ends and Esc, and its watchman stands down for either
rather than resuming.

The plan room closes on the owner's typed `/nightshift:plan-exit` or `/nightshift:start`. Claude Code
fires `UserPromptExpansion` for a command the owner types, with `command_name` (`nightshift:plan-exit`),
`command_source` (`plugin`) and the typed line in `prompt`; the hook removes the marker before the
command expands. A typed command does not fire `UserPromptSubmit`, and a skill Claude invokes through
the Skill tool fires neither event, so the model cannot close the room. `ns plan-exit` in a terminal
is the other exit.
