# Interpret the attachment

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
   - Mailbox mode: "A question, a ruling or a task that this agent sends to
     `user` shows in the channel with its default time; the owner answers with
     a reply in that thread, and no turn waits for it."
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
`codex --remote unix://`. If attach reports a socket-access denial, show the refusal and use the host's permission workflow when available and authorized.
