# Extending the skill to a new agent

Today the skill supports `claude` (Claude Code) and `codex` (OpenAI Codex) fully, plus an
`opencode` stub. Adding a new agent (OpenCode, Aider, Cursor-CLI, a future model) takes four
touch-points.

## 1. Add a transcript parser in `scripts/parse_transcript.py`

Signature: `def parse_<agent>(path: Path) -> dict`. Return the same shape as `parse_claude_session`
so downstream aggregation and the report template work unchanged:

```python
{
    "agent": "<name>",
    "model": "<model id or None>",
    "session_id": "<or None>",
    "raw_event_count": <int>,
    "tokens": {"input", "output", "cache_read", "cache_creation", ... , "total"},
    "thinking": {"blocks", "chars", "approx_tokens"},
    "cost_usd": <float or None>,
    "duration_ms_self_reported": <int or None>,
    "num_turns": <int or None>,
    "messages": {"assistant", "user", ...},
    "tool_calls": {"total", "by_tool", "parallel_distribution", "avg_parallel_calls_per_message"},
    "skills_used": {},
    "subagents_used": {},
    "trajectory": {"files_read_total", "files_read_unique", "files_read_by_extension",
                   "files_read_before_first_edit", "n_edits", "n_subagents", "gate_invocations"},
}
```

Fields you can't populate: leave them at `0`, `{}`, or `None`. The report template tolerates
missing keys and renders `<MISSING:...>` for them.

## 2. Register in the `PARSERS` dict

```python
PARSERS = {
    "claude": parse_claude_session,
    "codex": parse_codex_session,
    "opencode": parse_opencode_stub,  # replace with real parser
}
```

## 3. Add the CLI invocation in `scripts/run_trial.py`

Extend `build_agent_command()` with a new branch that returns the argv list for the new agent.
The command must:
- emit newline-delimited JSON event stream to stdout (for the parser)
- run with the worktree as CWD or via an agent-native flag (like `--cd` or `--add-dir`)
- run non-interactively without approval prompts (e.g. Claude Code's
  `--dangerously-skip-permissions`, Codex's `exec` subcommand which is non-interactive by
  design, or the equivalent for the new agent). Always verify the current CLI help before
  hardcoding a flag — agent CLIs change their flag contracts frequently.

## 4. Add pricing to `scripts/pricing.json`

USD per 1M tokens:

```json
{
  "<model-id>": {
    "input": <float>,
    "output": <float>,
    "cache_read": <float>,
    "cache_creation_5m": <float>,
    "cache_creation_1h": <float or 0 if the provider has no TTL split>
  }
}
```

The cost estimator (`estimate_cost_usd` in parse_transcript.py) uses exact key match first, then
prefix match (`model.startswith(k)`) — so registering a family root like `"gpt-5"` covers its
variants.

---

## Testing the new agent

```bash
# Real trial
python scripts/run_trial.py --repo /path/to/repo --config .agent-bench.toml \
    --agent <new> --run 1

# Parse existing transcript
python scripts/parse_transcript.py --agent <new> --session session.jsonl
```

Sanity checks:
- `tokens.total > 0` (the stream produced usage info)
- `tool_calls.total > 0` (the agent did something)
- `cost_usd` or `cost_usd_estimated` is present
- `trajectory.files_read_before_first_edit` is non-trivial (agent didn't blind-edit)
