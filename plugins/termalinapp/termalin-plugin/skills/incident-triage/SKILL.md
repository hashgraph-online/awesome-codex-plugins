---
name: incident-triage
description: Work through a server alert or outage step by step — disk full, high load, service down, OOM, certificate expiring, server offline. Use when the user pastes an alert, says something is down or slow, or asks why a server misbehaves.
---

Triage in a fixed order, read-only first, and stop to ask before any change.

## 1. Frame it

- Which server? Resolve the name with `hosts_list`. If the alert came from Termalin, `alerts_list` has the current state and when it started.
- Pull `server_metrics` for that host with `hours: 24` to see the trend: a disk that fills steadily and a disk that jumped are different problems.

## 2. Look, with read-only commands

Run these with `ssh_exec` as needed; they change nothing:

- Disk: `df -h`, then `du -xsh /var/log /var/lib/docker /home /tmp 2>/dev/null | sort -h`, `journalctl --disk-usage`, `docker system df` if Docker is there.
- Memory / OOM: `free -m`, `ps aux --sort=-%mem | head -15`, `dmesg -T | grep -i -E 'oom|killed process' | tail -20`.
- Load / CPU: `uptime`, `top -bn1 | head -25`, `ps aux --sort=-%cpu | head -15`, `iostat -x 1 3` or `vmstat 1 5` when I/O is suspected.
- Service down: `systemctl status <unit> --no-pager -l`, `journalctl -u <unit> -n 100 --no-pager`, `ss -tlnp` to see what is actually listening.
- Server offline per Termalin but the user says it is up: the Connector itself may be down; check `systemctl status termalin-agent` from another path or ask the user to look at the machine.
- Certificate: `openssl x509 -in <path> -noout -enddate`, and whether a renewal timer exists: `systemctl list-timers | grep -i -E 'certbot|acme'`.
- Website slow: `curl -s -o /dev/null -w '%{http_code} %{time_total}s' https://<domain>/`, then the web server and app logs.

Keep output short: use `tail`, `head`, `-n`. Anything that could run longer than a minute goes through `job_start` and `job_status`, not `ssh_exec`.

## 3. Explain

Give one paragraph: what is wrong, the evidence (numbers, log lines), the likely cause. Then a numbered plan, with the first step being the least destructive thing that stops the bleeding (rotate logs, clear a cache, restart one service) and the real fix after it.

## 4. Fix only with consent

Do not restart services, delete files, kill processes or change configs until the user says yes to the specific step. For deletion prefer the reversible form: `journalctl --vacuum-size=500M`, `apt-get clean`, `docker image prune -f` (not `-a` unless agreed). After each change, re-check the metric that triggered the alert and say whether it recovered.

Respect the connection's policy and the server note Termalin shows in the tool output; a read-only connection cannot perform fixes, say so instead of trying.
