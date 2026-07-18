---
name: oc-codex-setup
description: Install or refresh oc-codex-multi-auth in OpenCode, choose the right config mode, and verify Codex OAuth with ChatGPT Plus or Pro access.
---

# oc-codex-setup

Use this skill when the user wants to install, reinstall, upgrade, or troubleshoot `oc-codex-multi-auth` in OpenCode.

## Default install (compact modern)

```bash
npx -y oc-codex-multi-auth@latest
```

This is the default. It installs the compact modern catalog: 12 base OAuth model families with OpenCode variant presets (53 total variants). The TUI model picker shows bases such as `gpt-5.5` and `gpt-5.6-sol`; reasoning depth is selected with `--variant`.

## Full install (explicit selector IDs)

```bash
npx -y oc-codex-multi-auth@latest --full
```

Use this when the user needs direct selector IDs such as `openai/gpt-5.5-medium` or `openai/gpt-5.6-sol-high` in addition to the compact bases.

## Legacy install (older OpenCode)

```bash
npx -y oc-codex-multi-auth@latest --legacy
```

Use this on older OpenCode versions that do not support variant-based model entries. Installs 53 explicit model IDs only.

## Other installer flags

- `--dry-run` — show planned actions without writing files
- `--no-cache-clear` — skip clearing the OpenCode plugin cache
- `--modern` — same compact modern catalog as the default

## Standalone CLI (no agent cost)

```bash
oc-codex-multi-auth status
oc-codex-multi-auth list
oc-codex-multi-auth warm
oc-codex-multi-auth doctor
```

Also available: `limits`, `dashboard`, `health`, `diag`.

## Login and verification

1. Run `opencode auth login`.
2. Run a quick verification request with **compact modern** selectors (default install):

```bash
opencode run "Explain this repository" --model=openai/gpt-5.5 --variant=medium
```

Do **not** use `openai/gpt-5.5-medium` unless the user installed with `--full` or `--legacy`.

3. Optional GPT-5.6 smoke:

```bash
opencode run "Explain this repository" --model=openai/gpt-5.6-sol --variant=medium
```

4. For a Codex-focused workflow, try:

```bash
opencode run "Refactor the retry logic and update the tests" --model=openai/gpt-5-codex --variant=high
```

5. After `--full`, explicit IDs are valid:

```bash
opencode run "Explain this repository" --model=openai/gpt-5.5-medium
```

## Troubleshooting

- Confirm `"plugin": ["oc-codex-multi-auth"]` is present in the OpenCode config.
- Re-run `opencode auth login` if tokens expired or the wrong workspace was selected.
- Inspect `~/.opencode/logs/codex-plugin/` after a failed request.
- Set `ENABLE_PLUGIN_REQUEST_LOGGING=1` for deeper request logging.
- For full docs, see `docs/getting-started.md`, `docs/configuration.md`, `docs/troubleshooting.md`, and `docs/faq.md`.

## Usage boundaries

This project is for personal development use with your own ChatGPT Plus or Pro subscription. For production or shared services, prefer the OpenAI Platform API.
