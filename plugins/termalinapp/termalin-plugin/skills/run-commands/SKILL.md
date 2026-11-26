---
name: run-commands
description: Run shell commands and edit files on the user's servers through Termalin safely. Use whenever a task needs ssh_exec, ssh_exec_many, job_start, sftp_read or sftp_write — installing packages, editing configs, restarting services, tailing logs, running scripts on one or many servers.
---

Termalin runs each command on the user's own server through their Connector, authenticated with a short-lived certificate, and records it in their audit log. Treat every call as something the user will read later.

## Before running

- Start with `hosts_list` to get server ids and the connection policy (full access, allowlist or read-only) and the server note; follow the note, it is the owner's instruction for this machine.
- If there are no servers, do not improvise: tell the user to add one at https://termal.in/account (Add → Tunnel gives a one-line Connector install) and stop.
- Pick the login user: the Connector's default unless the user names another. Run root commands only when the policy and the user allow it.

## How to run

- One server, quick command: `ssh_exec`. Keep output bounded (`tail -n`, `head`, `--no-pager`, `-q`), a call waits 60 seconds by default (`timeout` raises it to at most 300, and some chat apps stop waiting sooner), so long work goes to `job_start`.
- Longer than a minute (builds, migrations, backups, `apt-get upgrade`, large `rsync`): `job_start`, then `job_status` with `lines` to follow it, `job_stop` only on request. Report the job id so the user can ask about it later.
- The same command on several servers: `ssh_exec_many` with the ids, at most 10 per call, and report per server.
- Files: `sftp_read` before `sftp_write`, never overwrite blind. Writing a config: keep a copy first (`cp file file.bak-$(date +%F)` via `ssh_exec`), write, then validate (`nginx -t`, `sshd -t`, `apachectl configtest`, `postgres --check` equivalents, `docker compose config`) and reload only if the user asked for the reload.

## What not to do without an explicit yes

- Anything destructive or hard to undo: `rm -rf`, `dd`, disk formatting, `DROP`, `git push --force`, `reboot`, `shutdown`, firewall changes that could lock the user out, `apt-get remove` of a running stack, changing `sshd_config` or the Connector's own service.
- Printing secrets into the chat: environment files, private keys, the shadow password file, password fields in configs, tokens in logs. If a task needs such a value, ask the user to provide it or to set it on the server themselves; never copy it into the conversation.
- Interactive commands (`vim`, `top` without `-bn1`, `less`, `apt` prompts): use non-interactive flags (`-y`, `DEBIAN_FRONTEND=noninteractive`, `--no-pager`).
- Guessing paths and unit names: look first (`ls`, `systemctl list-units | grep`), then act.

## After running

Say what ran, where, the exit code and the part of the output that matters. If a command failed, show the error and suggest the next step; do not retry blindly with `sudo` or `--force`.
