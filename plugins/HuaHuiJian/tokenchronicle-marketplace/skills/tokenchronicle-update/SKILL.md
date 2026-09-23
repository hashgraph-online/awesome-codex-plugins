---
name: tokenchronicle-update
description: Upgrade TokenChronicle code without overwriting user archives, configuration, feedback drafts, or local analysis data.
---

# TokenChronicle Update

Resolve the plugin root and use only the matching signed executable under
`bin/<platform>/tokenchronicle/`. If an
installed plugin has no matching executable, report that the platform client has not been published
and stop. Never download, replace, or trust an unverified executable.

Run the read-only `readiness` command before and after the update. Preserve the exact pre-update state;
an update must not silently mark onboarding complete, enable scheduling, or turn an operational
installation into manual-only mode.

1. Run `tokenchronicle doctor` and record the current version and application data directory.
2. Verify the release checksum before unpacking or installing it.
3. Replace only the program or plugin directory. Never copy the existing application data into a release bundle.
4. Keep the previous program version available until the new version passes `tokenchronicle doctor`.
5. Configuration schema migration may add defaults, but must preserve feedback and automation opt-in states.
6. Do not run archive or memory analysis merely to validate a code upgrade.
