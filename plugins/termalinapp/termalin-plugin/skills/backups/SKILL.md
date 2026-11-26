---
name: backups
description: Check, set up and run encrypted backups of the user's servers through Termalin — folders and Postgres/MySQL databases, on a schedule or right now. Use when the user asks whether a server is backed up, wants a backup before a risky change, wants to back up a site or database, or asks why last night's backup failed.
---

Termalin backs up a server through its Connector into encrypted archives. Only the owner holds the key, so you can check, propose and run backups, but restoring and confirming new jobs happen in the owner's cabinet.

## See what exists

Call `backup_list` with the server from `hosts_list`. It shows each job (folders, databases, schedule, copies kept, storage), its recent archives (time, size, success or error), drafts marked DRAFT with their confirmation link, and the storages the owner set up.

Report in a few lines: is there a working job, when was the last good archive, how big, anything failing. A job whose last run failed is the headline.

## Set up a job

1. Find what matters on the server before proposing (read-only `ssh_exec`): web roots (`/var/www`, `/srv`), app folders, `/etc` configs, `docker ps` for database containers, `systemctl list-units | grep -E 'postgres|mysql|mariadb'`.
2. Call `backup_job_create` with:
   - `paths`: absolute folders; `excludes` for `node_modules`, `*.log`, caches;
   - `databases`: `engine` postgres or mysql, `database` (or none for all), `container` when it runs in Docker;
   - `schedule` (daily by default, `hour` in UTC), `keep_last` (default 7), `destination` (one of the owner's storages, default Termalin storage).
3. It is saved as a draft; nothing runs yet. Give the user the confirmation link from the result and say plainly what the job will back up and how often. Confirming creates the encryption key, which only the owner can do. Drafts expire after 7 days.

Database dumps run on the server itself and sign in the way the database already allows there: the local socket, or the container's own settings. Never ask for a database password in the chat and never put one into the job.

## Back up now

- Before a migration, upgrade, config rewrite or bulk delete, call `backup_create` with a `label` saying why ("before upgrading postgres 15 → 16"). It waits about a minute; a longer one keeps running and appears in `backup_list`.
- It needs a confirmed job. If there is only a draft, the owner confirms first; if there is none, propose one.
- `keep_last` applies: when the limit is reached the oldest archive is removed. Say so if the user cares about an old copy.

## Restore

Archives are decrypted with the owner's key in the Termalin cabinet or desktop app (Backups → the archive → Decrypt & save). Point the user there; do not try to restore by extracting files on the server yourself.

## When a backup fails

Read the error in `backup_list`, then check the cause read-only: disk space (`df -h`), the database being up, the container name still matching, the storage quota. Suggest the fix; change the job only with the user's yes.
