# Contributing

Thanks for improving the Google Antigravity Codex Plugin.

## Scope

This repository is a community Codex plugin for connecting OpenAI Codex to a local Antigravity 2.0 desktop app on Windows. Contributions should keep the plugin focused on local MCP tools, Chromium DevTools integration, PowerShell helper commands, setup checks, model-limit inspection, and safe handoff into visible Antigravity UI workflows.

Do not add claims that the plugin is official unless the project status changes and the repository owner documents that clearly.

## Development Checks

Before opening a pull request, run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\scripts\antigravity.ps1" privacy
git diff --check
python -m pipx run plugin-scanner lint .
python -m pipx run plugin-scanner verify . --format json
```

`plugin-scanner verify` may safety-skip stdio MCP execution and request manual review. That is expected for executable MCP server entries; document the result in the pull request.

## Privacy

Do not commit local Antigravity logs, screenshots, chat contents, project names, runtime ports, CSRF tokens, OAuth tokens, cookies, API keys, or personal identifiers.

Use environment-variable examples such as `%USERPROFILE%`, `%APPDATA%`, and `%LOCALAPPDATA%` instead of machine-specific absolute paths.
