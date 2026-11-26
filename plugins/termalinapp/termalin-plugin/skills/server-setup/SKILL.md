---
name: server-setup
description: Set up a fresh Linux server or VPS through Termalin — updates, a sudo user, SSH settings, firewall, swap, time zone, Docker, a web server with HTTPS. Use when the user just got a new server and asks to prepare it, harden it, or install a typical stack on it.
---

Set up a new server in small, checked steps. The server is reached through its Termalin Connector, so firewall or SSH changes can't cut you off from it, but they can lock out the user's own SSH clients: be careful with those.

## First look

Check what you are working with before changing anything (one `ssh_exec`):

`cat /etc/os-release; uname -m; nproc; free -h; df -h /; swapon --show; timedatectl | head -5; ss -ltn`

Then show the user a short plan with the steps below that apply and get a yes. Skip what is already done.

## Steps

1. **Updates.** `job_start` with the package manager's full upgrade (`apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y upgrade`, or `dnf -y upgrade`), then `job_status`. See the `security-updates` skill for a reboot.
2. **A sudo user** instead of working as root. Ask for the user name. Create it (`adduser --disabled-password --gecos ""` + `usermod -aG sudo`, or `useradd -m -G wheel` on RHEL). It signs in with an SSH key; if the user also wants a password on it, they set it themselves in their own terminal.
3. **SSH.** Before turning off password logins or root login, make sure the user has a working key for the new user (ask them to add their public key, or confirm one is in `~/.ssh/authorized_keys`). Then write a drop-in (`/etc/ssh/sshd_config.d/50-hardening.conf`), check it with `sshd -t`, and reload. Do not change the port unless asked, and don't touch the Connector's own SSH settings.
4. **Firewall.** `ufw` (Debian/Ubuntu) or `firewalld` (RHEL). Allow SSH and the ports the user names (80, 443) first, then enable. Show the rule list.
5. **Swap** on small servers without one: a 1–2 GB swap file, added to `/etc/fstab`.
6. **Time zone and time sync** if the user cares: `timedatectl set-timezone`, `timedatectl set-ntp true`.
7. **Automatic security updates**: `unattended-upgrades` or `dnf-automatic`, when the user wants them.
8. **Stack on request**: Docker from the official repository (`job_start`), nginx or Caddy, Certbot for HTTPS when a domain already points to the server (check with `dig +short`).

Run long steps with `job_start`. Before each config change, keep a copy of the file, and after it check the config (`sshd -t`, `nginx -t`) before reloading.

## Then

- Suggest turning on Termalin monitoring for the server (alerts on disk, memory, failed services) and a backup job (the `backups` skill).
- Finish with a short summary: what was done, the user name created, open ports, what is left for the user (adding a key, DNS records).
