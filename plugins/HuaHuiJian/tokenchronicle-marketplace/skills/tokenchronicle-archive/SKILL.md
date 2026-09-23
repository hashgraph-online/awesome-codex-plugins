---
name: tokenchronicle-archive
description: Archive local Codex activity into the user's private TokenChronicle data directory and verify the generated usage reports.
---

# TokenChronicle Archive

Resolve the plugin root first. If a signed bundled executable exists under
`bin/<platform>/tokenchronicle/`, use `tokenchronicle` on macOS or `tokenchronicle.exe` on Windows. Use the
exact executable matching macOS arm64, macOS x86_64, or Windows x86_64; never execute a binary for a
different platform and never download a replacement. If an installed plugin has no executable for the
current platform, report that the platform client has not been published and stop. For an unpacked development bundle only,
resolve the plugin root relative to this skill and use its bundled Python package: on macOS/Linux use
`PYTHONPATH=<plugin-root>/src python3 -m tokenchronicle.cli <command>`; on Windows use an equivalent
PowerShell environment assignment followed by `py -3 -m tokenchronicle.cli <command>`. Never assume
the Unix command form works on Windows.

Run the read-only `readiness` command before anything else. If its state is `not_initialized`, switch
to the guided setup skill and do not archive. After a successful archive, run `readiness` again. If it
reports `schedule_choice_required`, continue the activation flow and ask the user to choose the
recommended zero-model-token OS schedule or explicit manual-only mode; do not imply that a manual
archive enabled daily protection.

1. Run `doctor` and stop if the Codex home is unavailable.
2. Run `archive` and wait for its final completion line and exit code.
3. Never add `--copy-raw`.
4. Verify that the daily token and session usage reports exist under the configured exports directory.
5. Report paths and counts without exposing conversation content.
6. Do not write Codex automation memory, hooks, configuration, or core memory.
