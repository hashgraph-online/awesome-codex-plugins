# Security Policy

## Reporting a vulnerability

Please report security issues privately by email to kuroudo.tanaka@humansupply.com.
Do not open a public issue for a vulnerability. We aim to reply within 7 days.

## Scope

done-gate is a local Stop hook. It reads the hook JSON on stdin and the session transcript file,
and writes only under `~/.claude/guardrails/` (a log and a small state file).
It makes no network connections and starts no other programs.
