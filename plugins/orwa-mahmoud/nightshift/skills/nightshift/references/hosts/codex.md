# Start on Codex

Approvals are per launch, and unattended execution and sandbox scope are two separate choices. A
shift runs unattended under `-a never`; a contract that does not commit needs only
`-s workspace-write`, because ticks alone finish a night. Under Codex's `workspace-write` sandbox
`.git` is protected, so a contract that commits cannot run under it and is started
`codex -a never -s danger-full-access`. The guards remain the fence either way. For a scheduled
start the same grant travels in the generator's agent string: `--agent 'codex exec -s danger-full-access'`
on POSIX, `-Agent 'codex exec -s danger-full-access'` on native Windows.

A live conversation is handed back with `codex resume <id>`. Codex SessionEnd (reason `other`) is
pause-recovery: closing, archiving, or an idle unload stands the watchman down and Start re-arms;
the punch list stays. A crash that never fires SessionEnd still revives, but only when
`$NS/run/.shift-session` holds a resumable session id — a UUID or a long hex token. ChatGPT
thread/conversation handles, rollout paths and other non-resumable identities are refused: the
watchman stands down rather than starting an unrelated conversation. A missing id still falls back
to a fresh session whose handover is the punch list.

The plan room closes on the owner's typed `$nightshift:plan-exit` or `$nightshift:start` (the `/`
spelling works too) as the first word of a message. Codex's `UserPromptSubmit` carries the prompt
about to be sent in `prompt`, and Codex keeps a `$` skill mention as the text typed; a skill the
model invokes is not a prompt and never reaches the hook. Codex runs a plugin hook only once it has
been reviewed and trusted, so until this one is, and on any surface that does not deliver the event,
`ns plan-exit` in a terminal is the exit.
