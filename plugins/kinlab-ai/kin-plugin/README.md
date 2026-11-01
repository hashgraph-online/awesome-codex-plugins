# Kin

Kin lets your AI apps use your accounts, even two of one service, each with its own rules. Connect a work GitHub and a personal GitHub, a work Notion and a personal one. For each account and action, choose Allow, Ask me or Block. Kin checks the rule on its server when the action runs, in every AI app you connect.

This repository holds no server code. Kin runs as a hosted MCP server at `https://app.kinlab.ai/mcp`. What's here is the setup that points each AI app at that address, two skills that teach the app how to use Kin's tools, and an optional Claude Code hook. You need a Kin account, free at [kinlab.ai](https://kinlab.ai), and an account at each service you connect.

## Install

Claude Code:

```sh
claude plugin marketplace add kinlab-ai/kin-plugin
claude plugin install kin@kin
```

Then run `/mcp`, choose `kin` and sign in. To send Claude Code's permission prompts to Kin as well, add `claude plugin install kin-approvals@kin` (see below).

Codex:

```sh
codex plugin marketplace add kinlab-ai/kin-plugin
codex plugin add kin@kin
```

Gemini CLI:

```sh
gemini extensions install https://github.com/kinlab-ai/kin-plugin
```

Cursor, VS Code, LM Studio and Kiro: open the link for your app, then sign in.

[Add to Cursor](https://cursor.com/en/install-mcp?name=kin&config=eyJ1cmwiOiJodHRwczovL2FwcC5raW5sYWIuYWkvbWNwIn0%3D) · [Add to VS Code](https://insiders.vscode.dev/redirect/mcp/install?name=kin&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fapp.kinlab.ai%2Fmcp%22%7D) · [Add to LM Studio](https://lmstudio.ai/install-mcp?name=kin&config=eyJ1cmwiOiJodHRwczovL2FwcC5raW5sYWIuYWkvbWNwIn0%3D) · [Add to Kiro](https://kiro.dev/launch/mcp/add?name=kin&config=%7B%22url%22%3A%22https%3A%2F%2Fapp.kinlab.ai%2Fmcp%22%7D)

Claude, ChatGPT, Zed, Raycast, Warp and other AI apps: add `https://app.kinlab.ai/mcp` as a remote MCP server and sign in. The [setup guide for each app](https://kinlab.ai/docs/ai-apps) has the steps.

## What's in it

| File | What it does |
|---|---|
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | The Claude Code plugin `kin` and this repository's plugin list |
| `.mcp.json` | Kin's address for Claude Code: `https://app.kinlab.ai/mcp`, signed in with OAuth |
| `plugin.json`, `mcp.json`, `.agents/plugins/marketplace.json` | The same plugin and address for Codex |
| `gemini-extension.json`, `GEMINI.md` | The same address and a short note for Gemini CLI |
| `server.json` | Kin's entry for the MCP Registry |
| `skills/kin` | How to call Kin's tools (search, describe, read, execute, feedback) and read their answers |
| `skills/kin-accounts` | How to work with several accounts of one service |
| `approvals/` | The optional `kin-approvals` plugin for Claude Code, below |
| `assets/` | Kin's icon |

None of these files hold a key or a password. Each app signs you in to Kin through Kin's own sign-in page.

## The optional approvals hook

`kin-approvals` adds one Claude Code hook. When Claude Code is about to ask your permission for a tool, the hook runs `approvals/scripts/kin-permission.sh`, which hands the request to Kin's own permission hook on this computer. That hook comes with the Kin app on a Mac or with kin-bridge on Windows and Linux. It sends the request to your Kin account, so you can answer it on your phone or in Kin, and passes your answer back to Claude Code.

The script does nothing, and Claude Code asks you as usual, when the Kin app and kin-bridge aren't installed, or when Kin's hook is already in your Claude Code settings. It downloads and installs nothing, reads no credentials, and sends nothing on its own. Claude Code's deny and ask rules still apply.

## What Kin receives

When an AI app uses Kin, Kin receives the calls it makes: the action, its arguments and the reason the app gives. With the approvals hook, Kin also receives the permission request Claude Code would have shown you. Kin keeps these in your activity log. See Kin's [privacy policy](https://kinlab.ai/privacy).

## Help

Docs: [kinlab.ai/docs](https://kinlab.ai/docs). Support: [support@kinlab.ai](mailto:support@kinlab.ai). Security reports: [security@kinlab.ai](mailto:security@kinlab.ai).
