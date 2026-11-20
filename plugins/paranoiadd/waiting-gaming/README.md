# Waiting Gaming

An offline 2048 game for Windows Codex, with a Chinese game interface.

After a local turn has run for four seconds, a modeless invitation appears in
the Codex window captured when the turn started. Click **开始游戏** to play or
**本次不玩** to skip that turn. An invitation expires when its turn stops or is
interrupted. The game remembers the board, scores, and last closed position.

## Requirements and setup

Use a signed-in Windows desktop session and Codex with local lifecycle hooks.
Install this package through a repo marketplace, review its three hooks in
Codex Settings → Hooks, then start a new local chat.

For a first check, send an ordinary task that takes more than four seconds.
Keep its Codex window in the foreground, accept the invitation, and use the
arrow keys. Closing an invitation skips it. Closing the game saves its location.

## Local execution and data

The `UserPromptSubmit`, `Stop`, and `Interrupt` hooks run
`bin/WaitingGaming.Hook.exe`. That helper records native window and process
identity plus hashed session/turn identifiers, and may launch
`bin/WaitingGaming.exe`. The game also stores its board, scores, and window
position in the writable plugin data directory.

The game runs offline and needs no extra account, API key, or downloaded
runtime. Prompt and reply text are excluded from saved game data. Hook failures
are best effort and allow the Codex task to continue.

Window binding uses the foreground Codex window at hook execution. With
multiple Codex windows, it may differ from the actual originating chat. An
invitation hides when its captured window is backgrounded or minimized and
returns while that turn remains active. An unavailable window skips the offer.

Disable or uninstall the plugin in Codex to stop future invitations.

## Source, verification, and security reports

[Source and build instructions](https://github.com/paranoiadd/waiting-gaming)
include the C# code and a `build.ps1 -Test` command using the built-in .NET
Framework compiler. The published native programs are built from that source.
The manifest's `scripts` path includes the runtime programs when a community
marketplace mirrors the package.

[Report a vulnerability privately](https://github.com/paranoiadd/waiting-gaming/security/advisories/new).
The project is licensed under the MIT License.
