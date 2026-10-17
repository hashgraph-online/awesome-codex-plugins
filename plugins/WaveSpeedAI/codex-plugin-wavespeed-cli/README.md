# WaveSpeed plugin for Codex

Generate and edit AI media — image, video, audio, 3D — on the [WaveSpeed](https://wavespeed.ai) platform from inside Codex.

- **MCP server** `@wavespeed/mcp`, started on demand with `npx`. Tools: `search_models`, `get_model_schema`, `get_price`, `upload_file`, `run_model`, `get_prediction`, `get_balance`.
- **Skill** `wavespeed-cli`: the find → inspect → run workflow on the open-source `wavespeed` CLI, with `@path` local-file upload and price quotes before spending credits.

Auth: `wavespeed login` once, or set `WAVESPEED_API_KEY`. One login covers the MCP server and the CLI. See the repository root README for installation.
