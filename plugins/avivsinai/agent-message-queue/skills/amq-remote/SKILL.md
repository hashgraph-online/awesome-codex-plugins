---
name: amq-remote
version: 0.113.1 # x-release-please-version
description: Let the owner reach this running agent from Buzz, on the phone or in Buzz Desktop. Use when the user types /amq-remote (Claude Code) or $amq-remote (Codex), /amq-remote --native, /amq-remote off, or /amq-remote status, or asks to control this session from Buzz. Not for AMQ messaging between agents (use amq-cli).
metadata:
  short-description: Reach this agent from Buzz
  compatibility: claude-code, codex-cli
---

# AMQ Remote

`/amq-remote` gives this session its own Buzz agent, with its own DM. The
owner DMs that agent from the Buzz phone app or Buzz Desktop. Several
sessions can be connected at once; each has its own agent. The same session
connecting again gets its own agent back. A different session never gets
another session's agent.

In Codex the skill is invoked as `$amq-remote` (Codex does not register `/`
commands for skills); the commands below are the same. Codex runs sandboxed:
attach writes `~/.amq/remote`, so the first attach may be refused until the
user reruns it with approval — ask for that one approval, do not work around
it.

- **Default (AMQ mailbox).** Each DM arrives as an AMQ message from `buzz` in
  this agent's inbox. This agent answers with `amq reply --id <id>`, and that
  reply is shown in the DM. A reply with `--kind status` shows as progress;
  any other reply is the final answer. No Stop hook and no wake are needed.
  Noticing the message is this agent's own business (a wake, a built-in
  consumer, monitor, or the next drain).
- **`--native`.** For a session that is not on AMQ: each DM is typed into
  this exact conversation, and the harness's own final answer goes back.
  On Claude Code it needs the AMQ Stop hook.

Run the steps in order. When a step says to stop, show the user the
command's own message. Do not work around a refusal.

## `/amq-remote` (connect)

1. **Tools.** Run `command -v amq-remote amq-acp`. If either is missing, tell
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
     `~/.claude/settings.json`; it always exits 0, and
     `amq-remote claude uninstall-stop-hook` removes it. Ask once, run it,
     then run the attach again.
   - Any other failure: show its message and stop.
3. **Tell the owner only what is still needed.** The JSON has `name`,
   `label`, `agent`, `helper`, `draft`, `reused`, and `agent_name` when there
   is an agent. Say "Connected: <label>." and then exactly one of:
   - `agent` is `running`: "DM **<agent_name>** in Buzz." Nothing else is
     needed.
   - `agent` is `offline`: "Start **<agent_name>** in Buzz Desktop (Agents,
     the agent, Start), then DM it. If you deleted it, run
     `amq-acp setup --session <name>` and import the file."
   - `agent` is `missing` and `draft` is true: "Buzz Desktop opens Create
     agent for it: pick AMQ Remote, then Create and start."
   - `agent` is `missing` and `helper` is `missing`: this machine has no
     helper yet. Run
     `amq-acp setup --helper --out "$HOME/Downloads/AMQ Remote helper.agent.json"`
     once, and show its printed steps as they are (Buzz Desktop: Agents,
     then + then Import, pick that file, then Start, and turn on
     Auto-start). Later sessions then need only the Create agent dialog.
   - `agent` is `missing` otherwise: this session's one-time setup. Run
     `amq-acp setup --session <name> --out "$HOME/Downloads/AMQ <name>.agent.json"`
     and show its printed steps as they are.
   If the JSON has `warning`, show it too.
4. **`--native` on Claude Code only: the approval hook.** Run
   `amq-remote doctor --root "$ROOT" --json` and read its `failing` list; the
   exit code is not the signal. When a `native_capability` entry says the
   PermissionRequest hook is not installed:
   - **No relay share** (the usual `--native` case). Tell the user: "This adds
     one PermissionRequest hook. It exits at once in sessions that are not
     connected. It lets Buzz deny a tool call only: a cross-mark reaction (❌)
     in the DM denies, and allow stays in Claude's terminal.
     `amq-remote claude uninstall-approval-hook` removes it." Ask once, then run
     `amq-remote claude install-approval-hook`.
   - **A Claude target shared through a relay share.** Tell the user:
     - "This adds one PermissionRequest hook. It exits at once in sessions
       that are not shared."
     - "It pins your Buzz public key and this share's relay, body, DM channel
       and target. Only your signed check-mark reaction (✅), or your yes in
       the approval's thread, in this DM can allow a tool call."
     - "Do not allow Claude to edit .claude for a session, use
       bypassPermissions or auto permission mode (also when started with
       `--permission-mode`), or allow every Bash command: each lets the pin
       be changed."
     - "The relay is trusted to return the message's full edit and deletion
       history. Replacing the amq-remote binary, or a settings edit you
       approve, defeats the pin."
     - "Run the install again if the share's relay or channel changes.
       Another decision hook you have can answer first.
       `amq-remote claude uninstall-approval-hook` removes it."

     Ask once, then run
     `amq-remote claude install-approval-hook --root "$ROOT"`. If doctor
     reports `claude_approval_pin_warnings`, show them to the user.
5. Add one line for the carrier:
   - Default: "DMs arrive in this agent's AMQ inbox. Stop in Buzz stops
     waiting; a delivered message may still be acted on."
   - `--native`: "A DM sent while this session is busy waits. Buzz Stop cannot
     interrupt a Claude turn."
   - Approval hook installed in step 4 with a relay share: "When a Buzz
     request needs a tool approval, the DM shows it. A cross-mark reaction
     (❌) blocks that call. A check-mark reaction (✅), or yes replied in the
     approval's thread, allows it when the DM offers the check mark: a Bash
     command shown whole. Otherwise allow it in the terminal. The first
     answer wins."
   - Approval hook installed without a relay share: "When a Buzz request
     needs a tool approval, the DM shows it. A cross-mark reaction (❌)
     denies that call; allow it in Claude's terminal. The first answer wins."

Codex with `--native`: attach needs `CODEX_THREAD_ID` and a thread loaded in
the Codex app-server daemon. A session started with plain `codex` is not in
the daemon; start it with `codex app-server daemon start`, then
`codex --remote unix://`. Run `amq-remote` and `amq-acp` outside Codex's
sandbox (request escalation): the sandbox blocks the daemon socket, and
`amq-acp setup` writes files outside the workspace.

## Answering a Buzz DM (default mailbox)

A message from `buzz` with subject "Buzz DM" is the owner writing from Buzz.
Do the work, then answer with `amq reply --id <that message id>`. Use
`--kind status` for an interim update. Keep the final answer short; it is
read in a chat.

## `/amq-remote off`

Run `amq-remote detach --self`. The session keeps running; its Buzz agent
archives itself and its DM answers "Not connected". When this session
connects again, the same agent comes back.

## `/amq-remote status`

Run `amq-remote bindings` and show its output. It lists each connected
session as `live` or `unknown` with its agent (`running`, `offline` or
`missing`), prunes the sessions proven ended, and names, once, old agents
the owner should delete.

## Trust limits

The Buzz agent's identity belongs to Buzz Desktop. Its grant has no kind limit
and no expiry. Archiving the agent does not invalidate a copied key and
grant; only removing the agent's relay access does that. Buzz "owner only"
also admits the owner's other agents. See the
[amq-acp README](https://github.com/avivsinai/agent-message-queue/blob/main/cmd/amq-acp/README.md).
