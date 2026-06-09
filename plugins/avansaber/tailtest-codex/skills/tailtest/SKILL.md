---
name: tailtest
description: Generate test scenarios, write the test file, and run it for a specific source file using the tailtest R1-R15 rule layer. When the agent needs to (1) cover a file the Stop hook skipped, (2) regenerate tests after refactoring, (3) test a legacy file Codex did not modify this session, or (4) explicitly run tailtest on a named file.
---

Generate or update tests for $ARGUMENTS.

Read the source file at `$ARGUMENTS`. Generate production-like test scenarios covering its public surface -- happy path, key edge cases, and failure modes at the configured depth. Write or update the test file following the tailtest Step 4 rules in AGENTS.md (correct location, correct name, style-matched to existing tests). Run the tests and report only failures; stay silent if all pass.

Treat the file as new-file regardless of its git status -- this skill explicitly requests generation even for legacy files or files the Stop hook would normally skip.

After completing, update `.tailtest/session.json`: add the file to `generated_tests` and clear it from `pending_files` if present.
