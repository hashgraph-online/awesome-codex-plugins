# Security And Privacy

This plugin is a local bridge between OpenAI Codex and a user's own Google Antigravity / Antigravity 2.0 desktop app.

## Public Repo Rules

Do not commit:

- Antigravity logs, screenshots, or user data.
- Project names, chat contents, emails, or personal identifiers.
- Runtime ports as fixed assumptions.
- CSRF tokens, OAuth tokens, cookies, API keys, or credentials.
- Machine-specific absolute paths except documented environment-variable based examples.

## Local Runtime Rules

- Read model quota state through the local language server only.
- Use DevTools for live UI verification before submitting chat messages.
- Treat the live UI as the source of truth for selected project, selected chat, composer state, and model.
- Do not bypass Antigravity authentication, quota, billing, or safety controls.
- Do not repeatedly resubmit after quota or rate-limit errors.

## Before Publishing

Run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\antigravity.ps1" privacy
git diff --check
```

Also run a targeted local scan for any personal names, emails, project names, or task names mentioned during development. Keep those terms out of commits and public documentation.
