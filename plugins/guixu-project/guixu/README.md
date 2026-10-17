<!--
Copyright (c) 2026 The State Key Laboratory of Blockchain and Data Security, Zhejiang University
SPDX-License-Identifier: Apache-2.0
-->

# Guixu

Guixu is the self-evolving AI agent for autonomous data discovery and trading. Guixu empowers AI agents with task-aware data discovery and decentralized data trading on Blockchain. AI agents can autonomously discover both free and paid data sources through a unified interface on Guixu.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/guixu-project/guixu/main/install.sh | bash
```

That's it. The installer downloads the binary, initializes a local node, auto-detects your AI clients (Codex, Cursor, Claude Code, OpenCode, OpenClaw), and registers the Guixu MCP server with each one.

## Development

After cloning the repository, run the bootstrap script to configure git hooks:

```bash
./bootstrap.sh
```

This configures `core.hooksPath` to use the project's `.githooks/` directory, enabling automatic pre-commit checks (SPDX headers, English comments, formatting, clippy) before each commit.


## AI Agent Integration (MCP)

Guixu exposes an MCP server so AI agents can discover, evaluate, and purchase datasets.

### Register / Unregister

```bash
guixu mcp install codex       # Codex
guixu mcp install cursor      # Cursor
guixu mcp install claude-code # Claude Code
guixu mcp install opencode    # OpenCode
guixu mcp install openclaw    # OpenClaw
```

To remove: `guixu mcp uninstall <client>`

`openclaw` uses `~/.openclaw/config.json` for MCP registration and installs a Guixu skill at `~/.openclaw/workspace/skills/guixu/`.

Current OpenClaw support is installation-layer integration: Guixu registers a standard MCP server entry and installs a skill that nudges dataset acquisition requests through the Guixu workflow. The MCP tools themselves are shared across all clients.

### Manual Configuration

Add to your client's MCP config:

```json
{
  "mcpServers": {
    "guixu": {
      "command": "guixu",
      "args": ["mcp"]
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `intent_parse` | Parse natural-language data requests |
| `dataset_search` | Search the Guixu network for datasets |
| `dataset_evaluate` | Evaluate dataset suitability and value |
| `dataset_purchase` | Purchase a dataset via smart contract |
| `dataset_feedback` | Record post-use feedback on-chain |

### HTTP Mode

```bash
guixu mcp --mode http   # MCP over HTTP on :3927/rpc
```

## Plugin Packaging

Guixu can be packaged as a plugin for Codex Desktop and Claude Cowork.

### Automated Packaging

Use the automated packaging script to create plugin packages:

```bash
# Package plugins for both Codex Desktop and Claude Cowork
make package

# Or use the script directly
./scripts/package-plugins.sh --output dist --clean

# Package only for Codex Desktop
make package-codex

# Package only for Claude Cowork
make package-claude
```

### Manual Installation

After packaging, install the plugins:

```bash
# Install Codex Desktop plugin
codex plugin install dist/guixu-codex-plugin

# Install Claude Cowork plugin
claude plugin install dist/guixu-claude-plugin
```

### Plugin Structure

The packaged plugins follow the standard structure:

- **Codex Desktop**: `.codex-plugin/plugin.json` + `skills/` + `.mcp.json`
- **Claude Cowork**: `.claude-plugin/plugin.json` + `skills/` + `.mcp.json`

For more details on plugin development, see [guixu-plugin.md](docs/guixu-plugin.md).

For packaging and installation instructions, see [plugin-packaging.md](docs/plugin-packaging.md).

## License

Guixu is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text and [NOTICE](NOTICE) for repository attribution notices.

Trademark use is governed separately. `Guixu`, the Guixu logo, and related marks are not licensed under Apache-2.0 except for reasonable and customary use in describing the origin of the software and reproducing the NOTICE file. See [TRADEMARKS.md](TRADEMARKS.md).

Contribution terms are described in [CONTRIBUTING.md](CONTRIBUTING.md) and [CLA.md](CLA.md). Unless you explicitly state otherwise in writing and the maintainers agree, any contribution intentionally submitted for inclusion in this project is submitted under Apache-2.0, subject to any separate signed contributor agreement that applies.
