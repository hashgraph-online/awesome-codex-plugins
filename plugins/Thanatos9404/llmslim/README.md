# LLMSlim plugin for Claude Code

This plugin gives Claude Code long-term memory that persists across sessions, with no LLM in the loop. It runs the
LLMSlim MCP server, which stores messages word for word in a local SQLite file and, when asked, returns the stored
messages that answer a question within a token budget. Nothing is summarized or rewritten on the way in or out.

It also adds two commands for `llmslim wrap claude`, which runs Claude Code through a local proxy that shortens long
shell, search and web tool output in the requests it sends to Anthropic's API.

## What it adds

**The `llmslim` MCP server**, started with:

```bash
uvx --from "llmslim[mcp]==0.12.0" llmslim mcp
```

| Tool | What it does | Changes data |
|---|---|---|
| `remember` | Stores a message word for word and returns its id. | Adds |
| `recall` | Returns the stored messages that answer a question, under their dates and whole where they fit, within a token budget. | No |
| `list_memories` | Lists recent messages with their ids, newest first. | No |
| `forget` | Deletes one message. It can't be undone. | Deletes |
| `fit_context` | Shrinks a long text to a token budget, keeping what answers a query, in order. | No |

**Two commands** for the proxy. Neither one starts it.
- `/llmslim:wrap-claude` checks whether the proxy is installed (`llmslim proxy --help`) and explains how to restart
  Claude Code through it with `llmslim wrap claude`.
- `/llmslim:savings` runs `llmslim proxy stats` and reports how many input tokens the proxy kept out of Claude Code's
  requests. It is an estimate counted before prompt-cache discounts, not dollars saved.

## Install

```text
/plugin marketplace add Thanatos9404/llmslim
/plugin install llmslim@llmslim
```

On Claude Code 2.1.275 or later, `/plugin install llmslim --marketplace Thanatos9404/llmslim` does both in one step.

## Requirements

- [uv](https://docs.astral.sh/uv/), which provides `uvx`. The plugin starts the memory server with it.
- Python 3.10 or newer for the memory server. If you don't have one, `uv python install` adds one.
- For the two proxy commands, the proxy installed once with `uv tool install "llmslim[proxy]"` or
  `pip install "llmslim[proxy]"` (Python 3.10 or newer).

## Data and network

- **Memory stays on your machine.** It is a SQLite file at `~/.llmslim/memory.db`. Set `LLMSLIM_MEMORY_DB` to use
  another file.
- **No model call.** Storing and recalling are plain code: no LLM, no embedding API and no API key.
- **The memory server makes no network calls of its own.** Three things do reach the network:
  - `uvx` downloads `llmslim` and its dependencies from PyPI the first time it runs a version.
  - The `tiktoken` library downloads its tokenizer file (`cl100k_base`) from `openaipublic.blob.core.windows.net` the
    first time it counts tokens, and caches it. No memory content is sent. Without network access, LLMSlim falls back
    to an approximate count.
  - The proxy, if you choose to run it with `llmslim wrap claude`, listens on 127.0.0.1 and forwards Claude Code's
    requests, with your credentials, to Anthropic's API (or to `$ANTHROPIC_BASE_URL`). It stores tool output in
    `~/.llmslim/proxy.db`. The plugin's commands don't start it.
- **The scope is fixed when the server starts**, not chosen by the model, so injected text can't make it read or
  delete another user's memory. Recalled text is labelled as data, not instructions.

## More

- MCP server options, client setup and security: [docs/MCP.md](https://github.com/Thanatos9404/llmslim/blob/main/docs/MCP.md)
- The proxy: [docs/PROXY.md](https://github.com/Thanatos9404/llmslim/blob/main/docs/PROXY.md)
- Source and issues: [github.com/Thanatos9404/llmslim](https://github.com/Thanatos9404/llmslim)

## License

MIT. See [LICENSE](https://github.com/Thanatos9404/llmslim/blob/main/LICENSE).
