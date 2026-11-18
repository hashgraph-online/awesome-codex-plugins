---
name: amq-remote
version: 0.153.2 # x-release-please-version
description: Let the owner reach this running agent from the Buzz app, on the phone or a computer. Use when the user types /amq-remote (Claude Code) or $amq-remote (Codex), /amq-remote --native, /amq-remote off, or /amq-remote status, or asks to control this session from Buzz. Not for AMQ messaging between agents (use amq-cli).
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

In Codex the skill is invoked as `$amq-remote` (Codex does not register `/`
commands for skills); the commands below are the same. Codex runs sandboxed:
attach writes `~/.amq/remote`, so the first attach may be refused until the
user reruns it with approval — ask for that one approval, do not work around
it.

- **Default (AMQ mailbox).** Each message the owner writes in the channel
  arrives as an AMQ message from `buzz` in this agent's inbox. This
  agent answers with `amq reply --id <id>`, and that reply is shown there. A reply with `--kind status` shows as progress;
  any other reply is the final answer. No Stop hook and no wake are needed.
  Noticing the message is this agent's own business (a wake, a built-in
  consumer, monitor, or the next drain).
- **`--native`.** For a session that is not on AMQ: each message is typed
  into this exact conversation, and the harness's own final answer goes back.
  On Claude Code it needs the AMQ Stop hook.

Run the steps in order. When a step says to stop, show the user the
command's own message. Do not work around a refusal.

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
3. **Tell the owner only what is still needed.** The JSON has `name`,
   `label`, `reused`, `machine` (`running`, `offline` or `missing`),
   `machine_name` when there is a machine agent, `machine_refusal` while
   `amq-remote serve` refuses it, `machine_line` while it does not serve,
   `unproven` when the session is not proven live and has no channel,
   `channel` and `channel_name`, `channel_error` and `channel_retry` when the
   channel is uncertain, failed or suspended, and `approval_reviewer` when a
   Codex thread runs Codex's automatic approvals reviewer. Attach already
   waited up to 15 s for the channel.
   Say "Connected: <label>." and then exactly one of, the first that applies:
   - `channel` is `suspended`: "This session's channel **<channel_name>** is
     suspended: <channel_error>. Nothing is sent there until that changes in
     Buzz; for a new channel run `amq-remote channel reset <name>`."
   - The JSON has `machine_line`: show it as it is (it says the machine agent
     runs inside amq-remote serve and is not running, with the next step).
   - `machine` is `running` and `channel` is `active`: "Open the
     **<channel_name>** channel in Buzz." Nothing else is needed.
   - `machine` is `running` and `channel` is `creating`: "AMQ Remote is making
     the channel; it appears in Buzz within a minute."
   - `machine` is not `missing` and the JSON has `unproven`: "<machine_name>
     makes a channel only for a session proven live, and this session is not
     (<unproven>)."
   - `channel` is `uncertain`: "Buzz did not confirm the channel
     (<channel_error>). AMQ keeps looking for it and will not make a second
     one. If it never appears, run `amq-remote channel reset <name>`."
   - `channel` is `failed`: show `channel_error`, then "AMQ tries again in 10
     minutes" when `channel_retry` is true, else "Run
     `amq-remote channel reset <name>`."
   - Otherwise (`machine` is `missing`, no enrolled machine key): this
     machine's one-time setup:
       1. Run `amq-remote machine request > request.txt`.
       2. The owner runs `amq-owner-sign --machine request.txt --out grant.json
          --relay <wss-url>` in their own terminal. Only the owner runs this
          signing step; never run it for them.
       3. Run `amq-remote machine enroll --grant grant.json`.
       4. Run `amq-remote service install`; it starts the agent now and at each login.
     Every later session then gets its channel by itself.
   If the JSON has `warning`, show it too. If it has `approval_reviewer`,
   say: "Buzz gets no Codex approvals: Codex's automatic reviewer answers
   them (approvals_reviewer = <approval_reviewer>)." It is the owner's
   setting; do not change it.
4. **Claude Code only: the approval hook** (default and `--native`, after
   a successful attach). Read `approval_hook` from the attach JSON: `ok`,
   `missing`, `stale`, `disabled` or `unreadable`. An older amq-remote
   gives no `approval_hook`: then run `amq-remote doctor --json` and use its
   `hooks` row for this session's settings file (`approval`: `installed`
   is `ok`, `missing` is `missing`; `approval_form` `stale` is `stale`), or
   with an even older doctor treat a `native_capability` failure that names
   the PermissionRequest hook as `missing` and anything else as `ok`.
   - `ok`: nothing to do.
   - `disabled`: say that this session's Claude settings set
     `disableAllHooks`, so approvals stay in the terminal unless a project
     or managed setting turns hooks on.
   - `unreadable`: say that the Claude settings file cannot be read, and that
     `amq-remote doctor` names it and the reason.
   - `stale`: say the installed hook is an older form, then run
     `amq-remote claude install-approval-hook`, which replaces only that
     entry. You may offer `amq-remote doctor --fix` as a question (it also
     installs the other hooks and the login service); never run it without a yes.
   - `missing`: tell the user: "This adds one approval hook. The first
     approval dialog of each Claude Code session on this machine connects
     that session to its own Buzz channel, even one that never ran
     /amq-remote: an AMQ session gets its own binding (the mailbox one
     /amq-remote writes), any other session a native binding, where chat
     needs /amq-remote --native. Every dialog of the session then shows
     there; ✅ allows, ❌ denies, first answer wins. /amq-remote off stops it
     for that session, and `amq-remote claude uninstall-approval-hook`
     removes the hook." Ask once, then run
     `amq-remote claude install-approval-hook`.

   Codex needs no hook: its approvals reach Buzz only for a session on the
   Codex app-server (the `--native` Codex path below); a plain `codex` TUI
   session answers approvals in the terminal.
5. Add one line for the carrier:
   - Default: "Buzz messages arrive in this agent's AMQ inbox."
   - Claude in mailbox mode: "In Buzz, a line starting with / is typed into
     the session like Remote Control; it waits while a dialog is open."
   - `--native`: "A message sent while this session is busy waits."
   - Claude with the hook installed: "Every approval dialog of this session
     shows in its Buzz channel with its options. ✅ or ❌, or a reply with the option
     number, answers it. A question with one single-select question shows
     its choices; reply with the number or your own text. The first answer,
     in Buzz or in the terminal, wins."
   - Claude in a machine agent channel: "The channel also shows each turn this
     session finishes; type `mirror off` there, or run `/amq-remote mirror
     off`, to stop it."
   - Codex on the app-server: the same line, unless the JSON has
     `approval_reviewer` (then the reviewer line above replaces it). A plain
     `codex` TUI session: "Approvals stay in the terminal."

Codex with `--native`: attach needs `CODEX_THREAD_ID` and a thread loaded in
the Codex app-server daemon. A session started with plain `codex` is not in
the daemon; start it with `codex app-server daemon start`, then
`codex --remote unix://`. Run `amq-remote` outside Codex's sandbox (request
escalation): the sandbox blocks the daemon socket.

## Answering a Buzz message (default mailbox)

A message from `buzz` with subject "Buzz DM" is the owner writing from Buzz,
in this session's channel.
Do the work, then answer with `amq reply --id <that message id>`. Use
`--kind status` for an interim update. Keep the final answer short; it is
read in a chat.

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
prunes the sessions proven ended.

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
