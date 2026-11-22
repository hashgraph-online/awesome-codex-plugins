---
name: amq-remote
version: 0.160.0 # x-release-please-version
description: "Connect the current session to its owner channel, inspect or disconnect its binding, or change session mirroring. Use for /amq-remote or $amq-remote and their native, off, status and mirror operations."
metadata:
  short-description: Reach this agent from Buzz
  compatibility: claude-code, codex-cli
---

# AMQ Remote

`/amq-remote` gives this session its own private Buzz channel. One machine
agent per machine runs inside `amq-remote serve`; an owner-signed grant
configures it once. The owner reads and writes in the Buzz app. Several
sessions can be connected at once; each has its own channel. The same session connecting again gets
its own channel back. A resumed session gets its channel back by itself
unless the owner turned it off: a pi session within about 35 s; on macOS, a
Claude mailbox seat started directly by `amq coop exec claude` within about
35 s; any other Claude session at its first approval dialog. A Codex session
needs `$amq-remote` again. A different session never gets another
session's channel.

Use `$amq-remote` in a harness that invokes skills with `$`. Attach needs write
access to the binding directory. Try the requested attach under the session's
current policy. If it reports a permission refusal, show the specific failure and
follow the host's available approval workflow.

- **Default (AMQ mailbox).** Each message the owner writes in the channel
  arrives as an AMQ message from `buzz` in this agent's inbox. This
  agent answers with `amq reply --id <id>`, and that reply is shown there. A reply with `--kind status` shows as progress;
  any other reply is the final answer. No Stop hook and no wake are needed.
  Noticing the message is this agent's own business (a wake, a built-in
  consumer, monitor, or the next drain).
- **`--native`.** For a session that is not on AMQ: each message is typed
  into this exact conversation, and the harness's own final answer goes back.
  On Claude Code it needs the AMQ Stop hook.

Select the section matching the requested operation. For a connection request, run
the connect steps in order and report the command's refusal when one occurs.

## `/amq-remote` (connect)

1. **Tools.** Run `command -v amq-remote`. If it is missing, tell
   the user to run `brew install avivsinai/tap/amq`, then stop.
2. **Connect.**
   - Default: run `amq-remote attach --self --json`. It uses `AM_ROOT` and
     `AM_ME`. If it says this session is not an AMQ participant, offer
     `--native`.
   - `--native`: use `$AM_ROOT` when set, else `$HOME/.amq/remote/root`
     (create it private with `(umask 077 && mkdir -p "$HOME/.amq/remote/root")`). Run
     `amq-remote attach --self --native --root "$ROOT" --json`.
   - If it exits 6 and names `amq-remote claude install-stop-hook` (Claude
     Code with `--native`), tell the user this adds one Stop hook to
     `~/.claude/settings.json` (`$CLAUDE_CONFIG_DIR/settings.json` when set);
     it always exits 0, and
     `amq-remote claude uninstall-stop-hook` removes it. Ask once, run it,
     then run the attach again.
   - Any other failure: show its message and stop.
3. After attach returns JSON, use
   [interpret the attachment](references/attach-result.md) to report the channel,
   any remaining setup and the approval carrier for this session.

## Answering a Buzz message (default mailbox)

A message from `buzz` with subject "Buzz DM" is the owner writing from Buzz,
in this session's channel.
Do the work, then answer with `amq reply --id <that message id>`. Use
`--kind status` for an interim update. Keep the final answer short; it is
read in a chat.

A reply from `user` that references your own request is the owner's answer to it.

An image the owner sent is not downloaded: the message has a line
`[image not attached: <name>: <reason>]` for it. Say so in the answer, and ask
the owner to describe the image if it matters.

## `/amq-remote off`

Run `amq-remote detach --self` and show its output. The session keeps
running. Its channel stops taking messages now, and the machine agent then
archives it. When this session connects again, the same channel comes back.

## `/amq-remote mirror on|off|status`

Run `amq-remote mirror <on|off|status> --self` and show its output. It is
the same switch as typing `mirror on` or `mirror off` in the session's
channel: while it is off, the machine agent posts no turn of this session,
and turns that end while it is off are not posted later. Only a Claude,
Codex or pi session the machine agent serves has a mirror.

## `/amq-remote status`

Run `amq-remote bindings` and show its output. It lists the machine agent
(running in amq-remote serve, or not running with the next step) and each
connected session as `live` or `unknown` with its name and its channel, and
prunes the sessions proven ended. A session with a permission dialog not yet
resolved shows it at the end of its line, for example `dialog open 13m (Bash)`:
the phase, the time since it opened and the tool.

## Status line

`amq-remote statusline` prints `📡 buzz` while this session is connected,
`📡 buzz (mirror off)` while its mirror is off, and nothing otherwise. It
always exits 0, reads only the binding files, and `--plain` drops the emoji.
AMQ never edits the user's `statusLine` setting; if the user asks for it,
show them the line to add to their own Claude Code status-line script, where
`$input` holds the JSON the script read from stdin:

```bash
seg=$(amq-remote statusline <<<"$input" 2>/dev/null); [ -n "$seg" ] && out+=" | $seg"
```

Any other harness that runs a command in its status line passes the session
id: `amq-remote statusline --session <id>`.

## Trust limits

The machine agent's key is in `~/.amq/remote/machine/`. The owner's
grant lets that key act as the owner's Buzz agent for every event kind
until its signed end date. A copied key and grant stay valid until that date; only
removing the agent's access on the relay ends them earlier.
See the
[Machine agent](https://github.com/avivsinai/agent-message-queue/blob/main/cmd/amq-remote/README.md#machine-agent).
