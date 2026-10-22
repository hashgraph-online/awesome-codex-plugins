# Security

The collector reads local Claude Code and Codex session logs, writes one export file to `~/.nueton-receipts/`, and opens no network connections. It never reads prompt bodies or file contents into the export: claim sentences are masked, key-shaped strings are replaced with `<secret>`, and ids are hashed with a salt that stays on your machine. `verify/receipts_verify.py` refuses an export that still contains path-, URL-, email- or key-shaped text.

## Reporting a vulnerability

Email receipts@nueton.ai with "SECURITY" in the subject, or open a private security advisory on this repository. Please include the collector version (`VERSION` in `collector/receipts_collect.py`), the command you ran, and a synthetic example that reproduces the problem. Never send real logs or real credentials. We aim to reply within three working days.

## Supported versions

Only the latest commit on `main` is supported.
