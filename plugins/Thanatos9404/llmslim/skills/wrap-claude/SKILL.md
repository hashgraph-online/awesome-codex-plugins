---
name: wrap-claude
description: Set up llmslim wrap claude, which runs Claude Code through a local proxy that shortens long test logs, build output and search results the first time the model sees them and resends the same bytes on every later turn.
disable-model-invocation: true
allowed-tools: Bash(llmslim proxy --help), Bash(uvx --from llmslim[proxy]==0.12.0 llmslim proxy --help)
---

Help the user start Claude Code through the LLMSlim proxy. Work through these steps and keep the explanation short.

1. Check whether the proxy is installed by running `llmslim proxy --help`. If that fails, try
   `uvx --from "llmslim[proxy]==0.12.0" llmslim proxy --help`.
2. If neither works, tell the user to install it once, with either command (Python 3.10 or newer):

   ```bash
   uv tool install "llmslim[proxy]"
   pip install "llmslim[proxy]"
   ```

   Don't install it yourself unless the user asks you to.
3. Explain that the proxy can't attach to the session that is already running. The user exits this session and starts
   Claude Code with:

   ```bash
   llmslim wrap claude
   ```

   Anything after `--` goes to Claude Code, for example `llmslim wrap claude -- --continue` or
   `llmslim wrap claude -- -p "Run the tests and fix what fails"`. Without a permanent install,
   `uvx --from "llmslim[proxy]==0.12.0" llmslim wrap claude` works the same way.
4. Tell them what it changes, in one or two sentences:
   - Output from Bash, PowerShell, Grep, Glob, WebFetch, WebSearch and Monitor that is longer than 1,500 tokens is
     shortened once. Errors, failures and the lines related to the command are kept, and repeated lines collapse into
     one line with a count.
   - Read, Edit and Write output is never changed, and neither is anything the model saw before the proxy started.
   - Each shortened output is replayed byte for byte on later turns, so prompt caching and thinking keep working.
   - MCP tools are left alone unless the user adds them with `--tool mcp__server__tool` or `--mcp`.
5. Mention that Remote Control is off while Claude Code uses a custom base URL. `llmslim wrap claude` keeps tool search
   on (`ENABLE_TOOL_SEARCH=true`); if the user runs `llmslim proxy` on its own instead, they should set it themselves.
6. After a session through the proxy, `/llmslim:savings` shows what it kept out of the requests.

Full guide: https://github.com/Thanatos9404/llmslim/blob/main/docs/PROXY.md
