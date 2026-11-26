---
name: deploy-check
description: Verify a server after a deployment, update or restart — services up, ports listening, logs clean, site answering, certificates valid, metrics stable. Use when the user says they just deployed, updated, restarted or migrated something and wants to know it is fine.
---

A deployment is good when the service is up, nothing new is in the error logs, the site answers and the numbers look like before. Check all four, read-only, and report in that order.

1. Services and ports (`ssh_exec`):
   - `systemctl --failed --no-pager` — must be empty.
   - `systemctl status <unit> --no-pager | head -5` for the deployed unit(s); for Docker: `docker compose ps` or `docker ps --format '{{.Names}} {{.Status}}'` — look for "Restarting" and recent restarts.
   - `ss -tlnp | grep -E ':(80|443|<app port>)'` — the expected ports are listening.
2. Logs since the deploy:
   - `journalctl -u <unit> --since '-15 min' -p warning --no-pager | tail -50`, or `docker logs --since 15m <container> 2>&1 | grep -i -E 'error|fatal|panic|exception' | tail -30`.
   - Web server: `tail -50 /var/log/nginx/error.log` (or the equivalent).
3. From the outside: `curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' https://<domain>/` and one real endpoint (`/health`, `/api/...`). A 200 with the previous latency is the goal; a 502/503 means step 1 lied — go back.
4. Certificate and monitoring:
   - `echo | openssl s_client -connect <domain>:443 -servername <domain> 2>/dev/null | openssl x509 -noout -enddate`.
   - `server_metrics` for the host with `hours: 2`: CPU, memory and load should settle within minutes; a climbing memory line after a deploy is a leak or a missing cache limit, say so.
   - `alerts_list`: nothing new for this host.

Report as a short checklist with ✓ / ✗ per item and the evidence (one line each). If anything failed, give the most likely cause and the first rollback or fix step, but do not perform it without the user's yes. If a migration or build is still running, follow it with `job_status` instead of re-running it.
