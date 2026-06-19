# Pronounce — Codex plugin

Pronounce developer jargon out loud. A community-maintained pronunciation
dictionary of **1,721 sourced entries** (kubectl, nginx, YAML, GIF, JSON, JWT, …)
— each with IPA, a plain-English respelling, audio, and a cited source.

This plugin ships:

- the **pronounce MCP server** — tools `lookup(word)` and `search(query)` returning
  IPA, respelling, `audio_url`, source, and confidence for any term;
- the **pronounce-word skill** — auto-answers "how do you pronounce X" with the
  sourced reading instead of a confabulated guess.

- Browse all entries: https://pronounce.renlab.ai
- Source / issues: https://github.com/anzy-renlab-ai/pronounce
- License: MIT

## Install

```
codex plugin marketplace add anzy-renlab-ai/pronounce
```

Or point any MCP client at the bundled `.mcp.json`.
