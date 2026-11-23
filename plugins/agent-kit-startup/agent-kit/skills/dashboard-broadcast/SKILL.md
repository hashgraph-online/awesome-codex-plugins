---
name: dashboard-broadcast
description: /dashboard-broadcast notes and troubleshooting table (port allocation, log path, detach lessons, common failure symptoms). Invoke via the command's own link; do not auto-load.
version: 0.1.0
category: core
disable-model-invocation: true
---

# /dashboard-broadcast notes and troubleshooting

Off-default-path detail for `.cursor/commands/dashboard-broadcast.md`, only needed after the happy path or on failure.

## Notes

- Port: `PORT` env overrides; default is the per-workspace hash allocation (range `3333-3588`), walking to the next candidate when one is held. Derive the preferred port with the snippet in the command's step 0, or read the printed `Bind:` line / `system.port`. Explicit `PORT` refuses instead of walking, so a pinned port never silently moves.
- Log default: `/tmp/mission-control-broadcast-<rootId>.log` (per workspace; `MISSION_CONTROL_LOG` overrides)
- Loopback UX remains `/dashboard` / `npm run dashboard` / `agent-kit dashboard`
- Detach lessons match `/dashboard` (error `2026-07-25_dashboard-server-reaped-agent-shell`)

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Serve exits: non-loopback requires token | `HOST` set without `MISSION_CONTROL_TOKEN` | Use `dashboard:broadcast` or set a ≥16 char token |
| Port busy / token rejected | Existing instance on the allocated port | Nothing to do: the starter skips it and binds the next per-workspace candidate. Want that exact port? Kill the LISTEN pid **only** after verifying `repoRoot` is yours |
| Explicit `PORT` refused | You pinned a `PORT` that another instance holds | Unset `PORT` (auto-pick a free per-workspace port), or free that port yourself if it is this workspace's |
| A second broadcast appears each run | `MISSION_CONTROL_TOKEN` is regenerated per run, so the running one cannot be identified | Export a stable `MISSION_CONTROL_TOKEN` to reuse the existing broadcast |
| Phone cannot connect | Firewall or wrong IP | Confirm printed LAN IPv4; allow inbound TCP |
| Config save 403 from phone | Expected | Config writes are loopback-only |
