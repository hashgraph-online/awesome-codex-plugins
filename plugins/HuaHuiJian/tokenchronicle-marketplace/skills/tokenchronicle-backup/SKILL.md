---
name: tokenchronicle-backup
description: Explain, inspect, or create an explicit AES-256 encrypted TokenChronicle snapshot in the user's iCloud Drive without moving the live archive.
---

# TokenChronicle iCloud Backup

Resolve the plugin root and prefer its matching signed executable under
`bin/macos-arm64/tokenchronicle/` or `bin/macos-x86_64/tokenchronicle/`. If an installed plugin has neither matching executable, report that the macOS
client has not been published for this architecture and stop. Never download or substitute a binary.

Run the read-only `readiness` command first. If TokenChronicle is not initialized, switch to guided
setup before offering a snapshot. If daily protection is inactive, disclose that fact separately; a
backup snapshot does not activate daily archiving.

1. Run `tokenchronicle backup status` and report whether macOS `hdiutil` and iCloud Drive are available.
2. Explain before every first snapshot:
   - iCloud synchronization is not an independent backup;
   - the encrypted snapshot leaves the Mac through iCloud Drive;
   - the live archive, configuration, credentials, locks, and logs stay local;
   - Advanced Data Protection is recommended;
   - a full snapshot can require roughly the archive size in iCloud capacity and temporary local space.
3. Never request, receive, repeat, store, log, or place a backup password in chat or a command argument.
4. Ask the user to run `tokenchronicle backup create --confirm-cloud-backup` in their own interactive
   terminal. The CLI securely prompts twice for a password of at least 12 characters.
5. Report only the resulting snapshot path, receipt path, size, file count, SHA-256, and verification state.
6. Do not schedule backups, enable feedback, migrate history, move the live archive, or delete snapshots
   without a separate explicit request.
