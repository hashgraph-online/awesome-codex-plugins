# WaveSpeed plugin for Codex

Generate and edit AI media — image, video, audio, 3D — on [WaveSpeed](https://wavespeed.ai) from Codex.

- **Hosted MCP server** at `https://api.wavespeed.ai/mcp`: generate, edit and extend images and videos, run any model, inspect schemas, and check prices and balance. Approve the connection once in the browser. Use public URLs; the hosted server cannot read local files.
- **Skill** `wavespeed-cli`: the find → inspect → run workflow on the open-source CLI, including `@path` local-file upload, batches and price quotes before spending credits.

For CLI use, install `@wavespeed/cli` and run `wavespeed login`. CLI authentication is separate from the hosted MCP connection. See the repository root README for installation.
