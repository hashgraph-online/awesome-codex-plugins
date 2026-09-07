# Feishu to Codex

Community packaging of the Skills from the official [Lark CLI](https://github.com/larksuite/cli) project, plus a Codex setup Skill.

The bundled Skills are synced from [`larksuite/cli@6675e3c`](https://github.com/larksuite/cli/commit/6675e3c2472f773035524d57651a081f81c7fd06), CLI version `1.0.73`.

Codex does not execute arbitrary commands inside the Marketplace install transaction. After installing the plugin, review and trust its `SessionStart` hook, then start a new task and ask:

> Set up and connect Feishu/Lark to Codex.

The hook installs the matching official runtime when needed and requires setup before Lark workflows are treated as ready. The `lark-setup` Skill then follows the browser/device OAuth flow. Manual fallback:

```bash
npm install --global --no-audit --no-fund @larksuite/cli@1.0.73
```

Then configure and authorize it locally:

```bash
lark-cli config init --new
lark-cli auth login --recommend
lark-cli auth status --json --verify
```

The plugin does not contain application secrets, OAuth tokens, or local configuration. `lark-cli` keeps credentials in its local configuration and OS credential storage. See the repository [README](../../README.md#connect-feishulark) for complete installation instructions.
