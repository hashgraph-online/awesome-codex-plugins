# Security

## Reporting a vulnerability

Email li@minicut.ai with the details. Please do not open a public issue for a security problem.

## What these skills do

- `miniapi-video` reads your key from the `MINIAPI_KEY` environment variable and sends it only to https://api.minicut.ai. It never writes the key to disk or prints it.
- Every paid job is quoted first. The script submits a job only after the user says yes (`--yes`).
- `minicut-film-studio` installs the MiniCut CLI from https://minicut.ai/install.sh and signs in through the browser. It stores no keys of its own.
- These skills send no telemetry themselves. `minicut-film-studio`, `GEMINI.md` and the MCP server set
  `MINICUT_FROM` to the agent's name (for example `claude` or `mcp`), and the MiniCut CLI records that
  name once, on its first run, so MiniCut can count installs by agent.
