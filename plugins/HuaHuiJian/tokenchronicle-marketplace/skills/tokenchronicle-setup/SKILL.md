---
name: tokenchronicle-setup
description: Initialize, diagnose, or open the local TokenChronicle Codex activity archive without importing any packaged user data.
---

# TokenChronicle Setup

Resolve the plugin root first. If a signed bundled executable exists under
`bin/<platform>/tokenchronicle/`, use `tokenchronicle` on macOS or `tokenchronicle.exe` on Windows. Use the
exact executable matching macOS arm64, macOS x86_64, or Windows x86_64; never execute a binary for a
different platform and never download a replacement. A public plugin release may support only a subset
of platforms. If this installed plugin has no executable for the current platform, report that the
platform client has not been published and stop; do not download or substitute an unrelated launcher.
For an unpacked development bundle only,
resolve the plugin root relative to this skill and use its bundled Python package. Use `python3` plus
`PYTHONPATH` on macOS/Linux and `py -3` plus PowerShell environment syntax on Windows. Never copy a
Unix environment-assignment command unchanged into Windows.

## Guided entry

Start every setup request by running the read-only `readiness` command. Installation alone is never
proof that TokenChronicle is initialized or protecting activity. Continue from the returned `state`
instead of restarting completed steps. Do not describe onboarding as complete while the state is
`not_initialized`, `first_archive_required`, `schedule_choice_required`,
`first_scheduled_run_pending`, `daily_protection_off`, or `attention_required`.

Treat the Marketplace default prompt, "initialize TokenChronicle", "set up TokenChronicle", and their
clear Chinese equivalents as requests to start the guided initialization flow. Before explicit privacy
acceptance, only explain the product and run read-only commands such as `guide` and `preflight`; do not
create directories, write configuration, start an archive, enable background work, or send network
requests.

After presenting the available choices, summarize the selected Codex source, archive directory,
language, viewer port, and whether to run the first full archive. Ask the user to confirm that summary
in natural language. Do not require a memorized or verbatim consent sentence. The confirmation must
unambiguously accept the current privacy notice and the listed initialization choices. Consent to setup
or the first archive never implies consent to scheduling, Codex Automation, feedback transmission,
cloud backup, or historical migration.

## Initialize

1. Run `guide`, then explain that TokenChronicle privately preserves searchable Codex inputs, replies,
   process evidence, and usage trends for review, audit, idea recovery, and future personal insights.
2. Explain that no dedicated project or working directory is required. TokenChronicle reads the chosen
   Codex home read-only and writes only to its separate user-owned application data directory.
   Distinguish the installed plugin/runtime, operational application state, and durable archive library.
   Use host-provided `PLUGIN_DATA` for plugin operational state when available.
3. Run the read-only `preflight` command. Report Python support, Codex state availability, selected data
   path, current archive size, free disk space, viewer port status, and every failing check.
4. Give the user a real choice before setup:
   - accept the operating-system defaults;
   - choose a different Codex home with `--codex-home`;
   - choose an exact durable archive library with `--archive-dir`;
   - choose a different local port with `--port`.
   - follow the system language with `--language auto`, or select Simplified Chinese with `zh-CN`
     or English with `en`.
   Do not ask the user to create these directories manually.
   Explain that Documents is visible and portable but may be processed by iCloud, enterprise sync,
   search indexing, or backup software. The default application-data location is less visible.
   If the selected data directory is outside the current sandbox, show the exact path and request the
   required filesystem approval. If the user declines, do not work around the decision; offer another
   user-selected writable location and rerun `preflight`.
5. Explain that all scheduling is disabled by default, so the default model-token use is `0/day`.
   Recommend the bundled local OS scheduler after a successful manual archive; it runs deterministic
   commands with zero model tokens and requires `--confirm-background-schedule`. If the user instead
   asks to create a daily Codex Automation, disclose the planning estimate: `0.7M-2.0M`
   total tokens per run, commonly `1.0M-1.5M`, or about `21M-60M` over 30 daily runs. State that
   cached input is included, the estimate is not a billing quote, and first or broad scans can reach
   approximately `1.5M-4.0M`.
6. Explain that archives can grow to multiple GB and recommend at least 5 GB of free space before the
   first archive. A low-space warning informs the user but does not silently delete data.
7. Ask for explicit privacy acceptance before initialization. Ask separately before enabling the local
   OS scheduler, creating Codex Automation, or enabling feedback transmission; one consent never implies another.
8. After the user selects paths and accepts privacy, run `setup --accept-privacy` with the selected flags.
   Do not enable optional features.
9. Run `doctor` and `usage-notice`, report every failing check, then run the consented first-use
   sequence: `archive`, `serve`, and optionally `memory-daily`. After the first archive passes, do not
   end the guided task until the user makes one explicit choice:
   - recommended: run `run-daily`, then explicitly consent to `schedule enable`; or
   - run `schedule manual --confirm-manual-only` after the user accepts that no automatic daily archive
     will occur.
   Keep any legacy Codex Automation active until the new schedule has a verified run, then avoid
   running both schedulers long term.
   Treat an unavailable viewer port as either an already-running viewer or a conflict; check before
   recommending a different port.
10. Finish by running `readiness`. `operational` means verified automatic daily protection.
    `manual_only` means onboarding is complete but automatic daily protection is off. Report this
    distinction prominently. Any other state means onboarding is incomplete and its `next_action`
    must be handled or clearly reported as blocked.
11. Explain that the Web language can be switched at any time. Translate only product UI and guidance;
    preserve user inputs, session titles, Codex responses, process evidence, and archived files verbatim.

## Safety boundaries

- Do not copy packaged sample conversations because the plugin contains none.
- Do not modify Codex hooks, configuration, memories, or automation state.
- Do not enable network feedback or synchronization without explicit consent.
- Keep all generated data in the configured TokenChronicle application data directory.
