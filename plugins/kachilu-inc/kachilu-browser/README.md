# Kachilu Browser

`kachilu-browser` is an anti-bot-aware browser automation CLI for AI agents such
as Codex and Claude.

<p align="center">
  <img src="docs/reCAPTCHA.gif" alt="Kachilu Browser detecting a reCAPTCHA challenge" width="100%">
</p>

> CAPTCHA in the way? The LLM detects it through the SKILL and hands off
> completion automatically. Nothing complicated.

Human-like interaction is the default. When reCAPTCHA v2/v3 or Cloudflare
Turnstile appears, `kachilu-browser` detects the challenge and routes completion
through the local CLI/browser flow.

WSL2 is first-class: agents running in Linux can control the Windows-side
browser profile you actually use, instead of a separate WSL-only browser.

Free to use. Local by design. No hosted relay, no telemetry, no external control
plane between the agent and your browser.

## Install

```bash
npm install -g kachilu-browser
kachilu-browser onboard
```

When this page appears, tick the checkbox so the agent can connect to your browser:

![Remote debugging permission checkbox](docs/remote-debugging.png)

## OpenClaw

```bash
openclaw plugins install kachilu-browser
openclaw gateway restart
```

OpenClaw uses the same npm package bundle, so no separate package name or extra
install script is needed.

## Onboarding targets

- If `--target` is omitted in an interactive terminal, `kachilu-browser onboard` prompts for the host target
- In non-interactive runs, pass `--target codex`, `--target claudecode`, or `--target claudedesktop`
- Use `--skill-only` or `--no-mcp` for desktop hosts that already provide a browser session and only need the Codex or Claude Code skill
- For Codex and Claude Code on WSL2, full MCP onboarding persists `KACHILU_BROWSER_AUTO_CONNECT_TARGET=windows` and auto-detected `KACHILU_BROWSER_WINDOWS_LOCALAPPDATA` unless you override them
- When targeting Windows browsers from WSL2 through MCP, `onboard` also ensures `%USERPROFILE%\.wslconfig` has `[wsl2] networkingMode=mirrored` and reports when `wsl --shutdown` is required
- `codex`: writes `~/.codex/config.toml` and links `~/.codex/skills/kachilu-browser`
- `claudecode`: writes `~/.claude.json` and links `~/.claude/skills/kachilu-browser`
- `claudedesktop`: writes the Claude Desktop local MCP config. Use `claude-desktop` as an equivalent alias.
- Claude Desktop Skills are distributed as `kachilu-browser-skill.zip` on GitHub Releases and must be uploaded through Claude Desktop's Skills UI.

```bash
kachilu-browser onboard --target codex --codex-home <desktop-codex-home> --skill-only
```

## MCP control plane

Agents should keep using a host-provided browser session when one is explicit. Otherwise, they should keep using the MCP prepare/exec workflow whenever the tools are available, including after context compaction or resume. For MCP-managed sessions, this preserves the session, profile, and WSL2 Windows-browser target from the MCP env block.

Raw `kachilu-browser` shell commands are a fallback for environments without MCP, explicit CLI requests, or intentional local WSL/Linux browser work. On WSL2, a raw shell command can miss `KACHILU_BROWSER_AUTO_CONNECT_TARGET=windows` and launch or control a WSL2-local browser instead of the intended Windows browser.

Successful prepare and exec responses include `controlPlane: "mcp"` and `followUpTool: "kachilu_browser_exec"` so agents can preserve the MCP route across context compaction and long-running resumes.

## Release model

- Native binaries are built from the private source repo.
- The npm package bundles available native binaries so `npm install -g kachilu-browser` works without exposing the private source tree.
- The source repo must provide `KACHILU_BROWSER_RELEASE_TOKEN` so it can create this repo's GitHub Release and push synced tags.
- This public repo publishes the npm package via npm Trusted Publishing after the package already exists on npm.
- The very first npm publish for `kachilu-browser` must be done manually with `npm publish --access public`.
- If the package was unpublished, npm blocks republishing the same package name for 24 hours.
- This repo's publish workflow also refuses to publish if the package does not yet exist on npm.
- The npm package downloads matching native binaries from GitHub Releases only when the current platform binary was not bundled in the package.

## Commands

```bash
kachilu-browser --help
kachilu-browser onboard --help
node scripts/mcp-server.mjs
```
