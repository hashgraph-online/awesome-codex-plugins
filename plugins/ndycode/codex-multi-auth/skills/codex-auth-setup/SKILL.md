---
name: codex-auth-setup
description: Install or refresh codex-multi-auth for the official Codex CLI, run first login, and verify account health and routing.
---

# codex-auth-setup

Use this skill when the user wants to install, reinstall, upgrade, or troubleshoot `codex-multi-auth` for the official `@openai/codex` CLI.

## Install

```bash
npm i -g @openai/codex
npm i -g codex-multi-auth
```

If the old scoped prerelease package is still installed:

```bash
npm uninstall -g @ndycode/codex-multi-auth
npm i -g codex-multi-auth
```

## First login

```bash
codex-multi-auth login
```

Default flow:

1. Open the account menu.
2. Choose the browser-first OAuth path.
3. Complete the official OAuth flow.
4. Return to the terminal and confirm the account was saved.

## Verify health and routing

```bash
codex-multi-auth status
codex-multi-auth list
codex-multi-auth check
codex-multi-auth forecast --live
```

Use these next when managing multiple accounts:

```bash
codex-multi-auth switch 2
codex-multi-auth verify-flagged
codex-multi-auth doctor --fix
```

## Alternate login paths

Use these when browser launch is blocked or the shell is headless:

```bash
codex-multi-auth login --manual
CODEX_AUTH_NO_BROWSER=1 codex-multi-auth login
```

## Troubleshooting

- Run `where codex-multi-auth` if `codex-multi-auth` is not recognized.
- Free port `1455` and retry if the OAuth callback server cannot bind.
- Re-run `codex-multi-auth login` if the active account is stale or the wrong account was selected.
- Use `codex-multi-auth doctor --fix` followed by `codex-multi-auth check` for a fast recovery loop.
- See `docs/getting-started.md`, `docs/configuration.md`, `docs/troubleshooting.md`, and `docs/reference/commands.md` for the full command and config docs.

## Usage boundaries

This project is for personal development use. For production or commercial workloads, use the OpenAI Platform API.
