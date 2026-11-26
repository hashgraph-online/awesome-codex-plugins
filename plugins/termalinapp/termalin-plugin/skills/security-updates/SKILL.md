---
name: security-updates
description: Find and install pending updates and fix known vulnerabilities (CVEs) on the user's servers through Termalin. Use when the user asks what needs updating, whether servers are patched, about a specific CVE, about a pending reboot, or wants to update packages on one or many servers.
---

Termalin checks every server hourly for pending updates and daily for known vulnerabilities in what is installed. Read that first; install only after the user agrees to a plan.

## Look

Call `updates_list`: no arguments for all servers, `host` for one, `tag` for a group (e.g. "prod", "distro:ubuntu"), or `cve` to answer "which servers have CVE-…".

It returns per server: number of updates and security updates, security packages with target versions, whether a reboot is requested, a newer kernel installed but not running, how old the package lists are, and CVEs with severity, the fixed version and whether the flaw is known to be exploited (CISA KEV). It covers Linux (apt, dnf, zypper, apk), Windows, macOS, running containers and application dependencies.

Report the most urgent first: known-exploited CVEs, then critical and high severity, then pending reboots and stale package lists. Name the package and the fixed version. Keep the rest to counts.

## Plan

Before installing, write a short plan per server and get a yes:

- what will be updated (security only, or everything);
- whether a service restarts or the server needs a reboot, and roughly when;
- for production, one server first, then the rest.

Offer a backup first on servers with data (the `backups` skill, `backup_create` with a label). A CVE in a container image or an app dependency is fixed by rebuilding or upgrading that app, not by the OS package manager: say so.

## Install

Updates take minutes, so use `job_start`, never a single `ssh_exec`, and follow with `job_status`:

- Debian/Ubuntu: `sudo apt-get update && sudo DEBIAN_FRONTEND=noninteractive apt-get -y upgrade` (security only: `sudo unattended-upgrade -v` when it is installed).
- RHEL/Alma/Rocky/Fedora: `sudo dnf -y upgrade --security` (or `upgrade`).
- openSUSE: `sudo zypper -n patch`. Alpine: `sudo apk upgrade`.
- Windows: `Install-WindowsUpdate` only when the PSWindowsUpdate module is present; otherwise tell the user to run Windows Update.

Keep `-y` and non-interactive flags; a prompt would hang the job.

## Reboot

Never reboot without an explicit yes for that server. After a reboot, wait for the server to come back in `hosts_list`, then check services (`systemctl --failed`) or use the `deploy-check` skill.

## Finish

Call `updates_list` again for the same servers and report what is left. The hourly check may lag, so mention when package lists were last read.
