# Codex Design

Turn Codex into your creative design workspace. Create and arrange UI mockups and images on a persistent local canvas.

![Codex Design running inside Codex, with four PACE running app screens arranged on the canvas](https://raw.githubusercontent.com/ummydev/codexdesign/main/docs/images/codex-design-pace-canvas.png)

[Website](https://codexdesign.io/) · [Installation instructions](https://codexdesign.io/install.md)

## Install

Paste this into a new Codex conversation:

```text
/goal Read https://codexdesign.io/install.md to install Codex Design for Codex.
```

Or use the Codex CLI:

```sh
codex plugin marketplace add ummydev/codexdesign --ref main
codex plugin add codexdesign@codexdesign-github
codex plugin list
```

Confirm the plugin is installed and enabled. Completely quit and restart Codex, then open a new conversation and try:

> Use Codex Design to create a canvas for a plant care app.

## Requirements

- Codex with plugin support and the `codex plugin` CLI commands.
- Git, access to GitHub, and Node.js **22.12 or later** in the MCP process PATH.
- macOS or Linux for the default launcher. A PowerShell launcher is included, but native Windows installation has not been verified.

This is a public Git marketplace; installing does not require a GitHub account or access to a private repository. Availability of Git marketplace plugins depends on the Codex client and organization policy.

The MCP server, daemon, frontend, and skills are prebuilt and included. **Do not run npm install, npm ci, or build commands** in your project, plugin cache, or marketplace snapshot. No separate React Flow installation is needed.

## Update

If the old canvas daemon is running, have Codex locate the installed plugin and run `node scripts/start.cjs stop` from that plugin directory. Then:

```sh
codex plugin marketplace upgrade codexdesign-github
codex plugin add codexdesign@codexdesign-github
codex plugin list
```

Restart Codex and open a new conversation. If an older marketplace points to a different repository, follow the migration instructions in the [installation guide](https://codexdesign.io/install.md).

## Local data and cost

Canvas projects are stored outside the plugin cache, by default in `~/.codex-design-plugin/projects`. Updates do not require deleting them.

There is no separate plugin API key or token wallet. Codex plan limits and applicable model usage charges still apply.

## Distribution contents

This repository contains the prebuilt plugin and its Git marketplace catalog on `main`. It is the installation source, not a development checkout. Third-party license notices are included in `plugins/codexdesign/THIRD_PARTY_NOTICES.txt`.

## License

Codex Design is licensed under the GNU General Public License v3.0 only (GPL-3.0-only); see [LICENSE](LICENSE). To report a security problem, see [SECURITY.md](SECURITY.md).

Codex Design is an independent plugin and is not affiliated with or endorsed by OpenAI.
