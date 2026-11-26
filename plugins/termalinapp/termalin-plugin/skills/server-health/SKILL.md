---
name: server-health
description: Answer "how are my servers doing", "is everything up", "anything wrong with prod" from Termalin's monitoring data. Use when the user asks about server status, load, disk, memory, uptime or alerts, before running any command on a server.
---

Answer health questions from the data Termalin already collects, not by running commands.

1. Call `alerts_list` first. Open alerts are the headline: say what is wrong, on which server, since when.
2. Call `server_metrics` (no `host` for all servers, default 6 hours; set `hours` when the user names a period). It returns per-server CPU, load, memory, disk per mount, failed systemd units, listening ports, certificate expiry and offline state.
3. If the user asks about one server, give its name or id from `hosts_list`.

How to report:

- Lead with problems: offline servers, disks over 85 %, memory under 10 % free, load above the core count, failed units, certificates expiring within 14 days. If there are none, say so in one line and give the numbers in a compact table (server, CPU, load, memory, worst disk).
- Compare with the previous window when the data has it: "disk / grew 3 GB in 6 h" matters more than the current percentage.
- Metrics come from the Connector on each server; a server that reports nothing is either offline or has monitoring switched off in Termalin. Say which, do not guess.
- Only after reporting, offer the next step. If the user wants to dig in, use the `incident-triage` skill or a read-only `ssh_exec` (for example `df -h`, `free -m`, `systemctl --failed`, `journalctl -p err -n 50`) — never a command that changes state.

If `server_metrics` says monitoring is off or there is no data, tell the user to enable monitoring for that server in their Termalin account (Account → Monitoring) and that alerts only work when monitoring is on.
