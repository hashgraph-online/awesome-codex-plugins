# Langfuse MCP Setup Reference

Detailed setup instructions, troubleshooting, and configuration options.

## Manual .mcp.json Setup

If you prefer manual configuration over `claude mcp add`:

```json
{
  "mcpServers": {
    "langfuse": {
      "command": "uvx",
      "args": ["langfuse-mcp"],
      "env": {
        "LANGFUSE_PUBLIC_KEY": "pk-...",
        "LANGFUSE_SECRET_KEY": "sk-...",
        "LANGFUSE_HOST": "https://cloud.langfuse.com"
      }
    }
  }
}
```

**Important:** If `.mcp.json` already exists, merge the `langfuse` entry into the existing `mcpServers` object. Don't overwrite the file.

### Add to .gitignore

```bash
grep -q '.mcp.json' .gitignore 2>/dev/null || echo '.mcp.json' >> .gitignore
```

Never commit credentials to version control.

---

## Troubleshooting

### Authentication Errors

- Public key must start with `pk-`
- Secret key must start with `sk-`
- Host must match your Langfuse instance (cloud vs self-hosted)

### Python Version Errors

If MCP fails to connect, check your Python version. Langfuse MCP requires Python 3.10 or newer and CI currently verifies Python 3.10 through 3.14.

If your default interpreter is older than Python 3.10, pin a CI-verified Python in the uvx command:
```bash
uvx --python 3.14 langfuse-mcp
```

Or verify manually:
```bash
uvx --python 3.14 langfuse-mcp --help
```

### Timeout Errors

Increase the timeout:

```bash
# Claude Code with timeout
claude mcp add \
  --scope project \
  --env LANGFUSE_PUBLIC_KEY=pk-... \
  --env LANGFUSE_SECRET_KEY=sk-... \
  --env LANGFUSE_HOST=https://cloud.langfuse.com \
  langfuse -- uvx langfuse-mcp --timeout 60

# Or in .mcp.json
"args": ["langfuse-mcp", "--timeout", "60"]
```

### Empty Results

- Check `age` parameter (minutes, not hours/days)
- Verify filters match your data
- Try `fetch_traces(age=1440)` with no filters to confirm data exists
- Data older than 7 days (10080 minutes) cannot be retrieved

### MCP Not Found

- Restart Claude Code / Codex CLI after adding MCP
- Run `/mcp` (Claude) or `codex mcp list` (Codex) to verify
- Check `.mcp.json` syntax (valid JSON, correct paths)
- Codex CLI uses `~/.codex/config.toml` for config; verify that file instead of `.mcp.json`

---

## Date-to-Minutes Conversion

| Time Range | Minutes |
|------------|---------|
| 1 hour | 60 |
| 6 hours | 360 |
| 12 hours | 720 |
| 1 day | 1440 |
| 2 days | 2880 |
| 3 days | 4320 |
| 7 days | 10080 (max) |

---

## Glossary

| Term | Definition |
|------|------------|
| **Trace** | Top-level container for a user interaction/request |
| **Observation** | Span, generation, or event inside a trace |
| **Generation** | LLM API call with input/output/tokens/latency |
| **Span** | Timed operation (function call, API request) |
| **Event** | Discrete log entry or exception |
| **Session** | Group of traces from the same user session |

---

## Tool Groups

Load specific tool groups to reduce token overhead:

```bash
langfuse-mcp --tools traces,prompts
```

| Group | Tools |
|-------|-------|
| `traces` | fetch_traces, fetch_trace |
| `observations` | fetch_observations, fetch_observation |
| `sessions` | fetch_sessions, get_session_details, get_user_sessions |
| `exceptions` | find_exceptions, find_exceptions_in_file, get_exception_details, get_error_count |
| `prompts` | list_prompts, get_prompt, get_prompt_unresolved, create_text_prompt, create_chat_prompt, update_prompt_labels |
| `datasets` | list_datasets, get_dataset, list_dataset_items, get_dataset_item, create_dataset, create_dataset_item, delete_dataset_item |
| `annotation_queues` | list_annotation_queues, create_annotation_queue, get_annotation_queue, list_annotation_queue_items, get_annotation_queue_item, create_annotation_queue_item, update_annotation_queue_item, delete_annotation_queue_item, create_annotation_queue_assignment, delete_annotation_queue_assignment |
| `scores` | list_scores_v2, get_score_v2 |
| `schema` | get_data_schema |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LANGFUSE_PUBLIC_KEY` | API public key (starts with `pk-`) |
| `LANGFUSE_SECRET_KEY` | API secret key (starts with `sk-`) |
| `LANGFUSE_HOST` | Langfuse instance URL |
| `LANGFUSE_TIMEOUT` | API timeout in seconds (default: 30) |
| `LANGFUSE_MCP_TOOLS` | Comma-separated tool groups to load |
| `LANGFUSE_MCP_LOG_FILE` | Log file path (default: `/tmp/langfuse_mcp.log`) |
| `LANGFUSE_MCP_READ_ONLY` | Set to `true` to disable write tools (safer observability mode) |
| `LANGFUSE_MCP_DEFAULT_OUTPUT_MODE` | Default MCP tool `output_mode` (`compact`, `full_json_string`, `full_json_file`) |

---

## Skill Installation Scopes

| Scope | Claude Code | Codex CLI |
|-------|-------------|-----------|
| Project | `.claude/skills/langfuse/` | `.codex/skills/langfuse/` |
| User/Global | `~/.claude/skills/langfuse/` | `~/.codex/skills/langfuse/` |

Install globally:
```bash
cp -r skills/langfuse ~/.claude/skills/   # Claude Code
cp -r skills/langfuse ~/.codex/skills/    # Codex CLI
```

---

## Security Notes

- Never commit `.mcp.json` with real credentials
- Rotate keys if leaked
- `full_json_file` exports may contain sensitive user data
- Use environment variable injection in CI/CD rather than hardcoded values
