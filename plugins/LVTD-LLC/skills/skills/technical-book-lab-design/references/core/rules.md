# Technical Book Lab Design Rules

Use these rules when designing technical labs, tutorials, and worked examples for nonfiction.

## Core Rules

### 1. Start From A Reader Outcome

Every lab should produce a useful result.

- Prefer "deploy a private file-sync service behind HTTPS" over "learn reverse proxies."
- Prefer "restore a backup to a fresh machine" over "backup theory."
- Put the outcome near the beginning so readers know why the lab matters.

### 2. Make Starting State Explicit

List assumptions before the lab begins.

- Operating system and architecture.
- Tool versions or acceptable ranges.
- Accounts, domains, hardware, network access, permissions, and costs.
- Prior concepts the book assumes and what to read if missing.

### 3. Use Small Verified Checkpoints

Do not let readers perform many steps before seeing success.

- Explain the purpose of each checkpoint.
- Show expected output or state.
- Include a command, UI check, request, or file inspection to verify.
- Stop the reader from continuing when a checkpoint fails.

### 4. Separate Action From Explanation

Keep the lab moving while preserving understanding.

- Explain why a step exists before the action.
- Put deeper theory after a successful checkpoint.
- Move optional context, variants, and historical background into notes or companion resources.

### 5. Design For Real Failure

Add failure handling for common reader environments.

- Include likely errors, symptoms, causes, and next checks.
- Add cleanup for temporary resources.
- Add rollback for risky changes.
- Mark destructive, public, paid, privileged, or security-sensitive operations.

### 6. Finish With Transfer

Close by helping the reader reuse the skill.

- Summarize what now exists.
- Name what the reader should understand.
- Show the next safe variation or extension.
- Tell the reader what to monitor or maintain.

## Guidelines

- Keep one lab focused on one outcome.
- Use real filenames, ports, hostnames, and placeholders consistently.
- Avoid unexplained magic commands.
- Prefer copyable commands only when they are safe and context-bound.
- Avoid hiding important caveats in footnotes.
- Use diagrams or tables when a mental model is blocking progress.

## Exceptions

- **Reference chapters**: May be browsable rather than linear, but each recipe still needs outcome and starting state.
- **Advanced books**: Can assume more, but must say what is being assumed.
- **Dangerous domains**: Security, data loss, payments, or public exposure require stronger warnings and rollback.

## Quick Reference

| Rule | Summary |
|------|---------|
| Outcome first | Design around visible reader progress. |
| Starting state | State environment and knowledge assumptions. |
| Checkpoints | Verify before the next complex step. |
| Action plus why | Keep pace without losing understanding. |
| Failure paths | Include common errors and recovery. |
| Transfer | End with reusable understanding. |
