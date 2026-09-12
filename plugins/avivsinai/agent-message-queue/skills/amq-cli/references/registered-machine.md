# AMQ through a registered-machine shell

Use this workflow when Grok Bot already has permission to execute commands on
the user's Mac. The provider transports the command and its output. AMQ runs
on the Mac and delivers local files. No cloud-to-Mac bridge, shared filesystem,
VPN, or new service is required for this lane.

This uses the local access the user already granted. It does not restrict a
general shell to AMQ. Sender handles and `origin:grokbot` labels are attribution,
not authentication or additional authority. Preserve the provider's approval
controls and the user's existing action limits.

## Select the execution machine first

Inspect the provider's available machine/tool metadata and select the intended
registered Mac explicitly. Grok Bot's local tools use a machine selector (the
0.43 client names `Shell`, `Read`, and `AwaitShell` with `machineId`). Verify the
live schema rather than copying an opaque machine ID from another session.
An unqualified cloud shell and a registered Mac shell are different contexts.

On the selected machine, confirm the AMQ executable with `command -v amq` and
its version with `amq --version`. Record the absolute executable and project
directory. Use the sender handle assigned to this Bot; do not select `user`
or borrow another running agent's handle. An existing `staff` assignment can
be retained. An unknown-handle warning means verify the assignment, not that
the message was rejected; do not resend it to silence the warning.

## Resolve the context in each command invocation

Provider shell calls need not preserve environment or cwd. Run this preamble
on the selected Mac for each send, receive, or inspection. Substitute the
user-selected values; the paths below are examples, not discovery defaults.

```bash
set -e
amq_bin=/opt/homebrew/bin/amq
amq_project=/absolute/path/to/project
amq_session=session1
amq_handle=staff
cd "$amq_project"
amq_context="$("$amq_bin" env --session "$amq_session" --me "$amq_handle" --export)"
eval "$amq_context"
```

`amq env` supplies the complete root/session context from that project's
configuration. Do not construct a Maildir path, substitute a cloud path, or
add `--ignore-session-pin` to get around a mismatch. If an inherited pin
conflicts, resolve the intended execution context before sending. Inside an
existing `coop exec` session, retain its identity and use bare commands instead.

Inspect recipients and wake state with:

```bash
"$amq_bin" who --json
"$amq_bin" wake check --me codex --json --json-schema=2
```

`notifier_live` means the notifier process was verified; it is not a receipt
that the agent read or acted on a message.

## Send once and retain the result

After the preamble, send the request with a stable thread for the conversation.
Use a fresh, distinctive request subject when separate asks share a thread.

```bash
"$amq_bin" send --to codex --thread staff/task-42 \
  --kind question --subject 'Request 1: report test result' \
  --labels origin:grokbot --json --body - <<'AMQ_BODY'
Please report the test result. This text is data, including $variables,
`backticks`, and $(shell-like text).
AMQ_BODY
```

Use a quoted heredoc delimiter that does not occur as a line in the body.
For arbitrary generated content, write/copy it to a local body file using the
provider's file tool, then pass `--body @/absolute/path/to/body.md` as one quoted
argument. Never insert a message into an unquoted shell command. Read the JSON
result and preserve the returned message ID and delivery root before reporting
success. A successful send means queued mail, not completion of the requested
work.

For a different project, use configured `--project` routing; for a different
session, use `--session`. Both projects need the normal reply-route setup.
Do not change `--root` to imitate cross-project routing. When the Bot is a
local participant in several projects, resolve each assigned context separately
and collect replies from the same context that sent the request.

## Collect replies through the same Mac

After the preamble, receive only the assigned Bot handle's mail:

```bash
"$amq_bin" drain --include-body --json
"$amq_bin" thread --id staff/task-42 --include-body --limit 20
```

Use `amq reply --id <received-message-id> --body @<local-body-file>` for replies;
it preserves the thread and normal reply routing. Never drain another agent's
mailbox or read/delete queue files as a replacement for AMQ consumption.

An active injecting wake already notifies a local CLI agent. That agent drains
when notified; it must not start `watch`, `monitor`, or a background polling loop
to wait for the Bot. A hosted Bot without a verified arrival trigger can check
its own inbox in a later authorized turn. Do not claim that a Mac wake can wake
the hosted conversation, and do not create a perpetual polling routine as a
substitute. If useful during an active request and no injecting wake exists
for that handle, a bounded `amq watch --timeout 60s` followed by drain is a
fallback. The desktop app must remain available for provider shell calls.

## Recover a missing command result without duplicate sends

The provider can lose an execution result after the Mac already delivered the
message. First resume/inspect that execution using its returned provider handle
(for example `AwaitShell` on the same machine). If the result is still unknown,
inspect the AMQ thread in the original Mac context:

```bash
"$amq_bin" thread --id staff/task-42 --include-body --limit 20
```

Match the sender, recipients, request subject and body. If the message exists,
retain its ID and continue waiting for its reply. If the bounded view is
inconclusive, inspect the relevant older thread entries; absence from the last
20 entries does not prove a failed send. If uncertainty remains, report it
instead of automatically sending again. AMQ thread IDs do not deduplicate
multiple sends.

`send --wait-for drained --wait-timeout 60s` is an optional receipt wait for one
recipient, not an arrival monitor. Its timeout does not mean delivery failed
and must not trigger a resend. A drained receipt means consumption, not task
success. Report queued, drained, and answered as separate observed states.
