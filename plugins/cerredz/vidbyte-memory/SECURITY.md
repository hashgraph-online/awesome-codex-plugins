# Security policy

## Supported versions

Fixes go into `main` and the next release. Task repos made from the template do not update themselves; the release notes say when a fix needs to be copied into existing task repos.

## Reporting a vulnerability

Report it privately through [GitHub private vulnerability reporting](https://github.com/cerredz/vidbyte-memory/security/advisories/new). Please do not open a public issue. Include what an attacker could do, the files involved, and the steps to reproduce. You will get an acknowledgement within 7 days and a plan or a fix within 30.

## What counts

The template runs code on the machine of whoever uses it, so these are in scope:

- `scripts/guard.py`, which Claude Code runs as a Stop hook and which runs `pytest` and `git` in the repo.
- `scripts/footprint.py`, which stages every change with `git add -A`, commits and pushes.
- Anything in the skills, prompts or verifiers that could lead an agent to write secrets into memory, run untrusted commands, or follow instructions planted in a memory file (memory poisoning).
- The integrity test's secret scan (`test_no_secrets_in_memory`) missing a common credential format.

## What the template never does

It has no telemetry and makes no network calls of its own. The only data that leaves the machine is what `git push` sends to the `origin` remote you configured. Footprint commits carry a `Memory-Template: vidbyte-memory` trailer, which is visible only where the repo itself is public.
