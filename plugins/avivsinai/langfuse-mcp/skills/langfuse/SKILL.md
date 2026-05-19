---
name: langfuse
version: 0.9.1
description: Debug AI agents and LLM applications via Langfuse MCP. Use when investigating traces, exceptions, slow generations, sessions, prompt versions, datasets, or evaluation sets. Triggers on "langfuse", "traces", "debug AI", "find exceptions", "what went wrong", "why is it slow", "datasets", "evaluation sets".
metadata:
  short-description: Langfuse observability via MCP
  compatibility: claude-code, codex-cli
---

# Langfuse Skill

Debug AI agents and LLM applications through Langfuse observability.

This skill is the agent-facing companion to `langfuse-mcp`. It tells Claude Code and Codex when to use Langfuse, which MCP tool to call first, and how to move from broad trace discovery to a concrete root-cause hypothesis.

**Triggers:** langfuse, traces, debug AI, find exceptions, set up langfuse, what went wrong, why is it slow, datasets, evaluation sets

## What This Skill Provides

- Setup steps for connecting `langfuse-mcp` to Claude Code or Codex.
- Playbooks for exception triage, trace inspection, latency analysis, sessions, prompts, and datasets.
- A quick reference for the highest-value MCP tools.
- Links to full setup and tool references for deeper troubleshooting.

Use the playbooks before guessing at individual tools. Start broad, identify the relevant trace/session/observation, then drill into the exact failure or slow path.

## Setup

**Step 1:** Get credentials from https://cloud.langfuse.com → Settings → API Keys

If self-hosted, use your instance URL for `LANGFUSE_HOST` and create keys there.

**Step 2:** Install MCP (pick one):

Requires Python 3.10 or newer. CI verifies Python 3.10 through 3.14.

```bash
# Claude Code (project-scoped, shared via .mcp.json)
claude mcp add \
  --scope project \
  --env LANGFUSE_PUBLIC_KEY=pk-... \
  --env LANGFUSE_SECRET_KEY=sk-... \
  --env LANGFUSE_HOST=https://cloud.langfuse.com \
  langfuse -- uvx langfuse-mcp

# Codex CLI (user-scoped, stored in ~/.codex/config.toml)
codex mcp add langfuse \
  --env LANGFUSE_PUBLIC_KEY=pk-... \
  --env LANGFUSE_SECRET_KEY=sk-... \
  --env LANGFUSE_HOST=https://cloud.langfuse.com \
  -- uvx langfuse-mcp
```

Add `--python 3.14` before `langfuse-mcp` if you want to pin a CI-verified interpreter explicitly.

**Step 3:** Restart CLI, verify with `/mcp` (Claude) or `codex mcp list` (Codex)

**Step 4:** Test: `fetch_traces(age=60)`

### Read-Only Mode

For safer observability without risk of modifying prompts or datasets, enable read-only mode:

```bash
# CLI flag
langfuse-mcp --read-only

# Or environment variable
LANGFUSE_MCP_READ_ONLY=true
```

This disables write tools: `create_text_prompt`, `create_chat_prompt`, `update_prompt_labels`, `create_dataset`, `create_dataset_item`, `delete_dataset_item`.

### Default Output Mode

If you want MCP clients to default to writing full payloads to files when they omit `output_mode`, configure:

```bash
langfuse-mcp --default-output-mode full_json_file

# Or via environment variable
LANGFUSE_MCP_DEFAULT_OUTPUT_MODE=full_json_file
```

For manual `.mcp.json` setup or troubleshooting, see `references/setup.md`.

---

## Playbooks

### "Where are the errors?"

```
find_exceptions(age=1440, group_by="file")
```
→ Shows error counts by file. Pick the worst offender.

```
find_exceptions_in_file(filepath="src/ai/chat.py", age=1440)
```
→ Lists specific exceptions. Grab a trace_id.

```
get_exception_details(trace_id="...")
```
→ Full stacktrace and context.

---

### "What happened in this interaction?"

```
fetch_traces(age=60, user_id="...")
```
→ Find the trace. Note the trace_id.

If you don't know the user_id, start with:
```
fetch_traces(age=60)
```

```
fetch_trace(trace_id="...", include_observations=true)
```
→ See all LLM calls in the trace.

```
fetch_observation(observation_id="...")
```
→ Inspect a specific generation's input/output.

---

### "Why is it slow?"

```
fetch_observations(age=60, type="GENERATION")
```
→ Find recent LLM calls. Look for high latency.

```
fetch_observation(observation_id="...")
```
→ Check token counts, model, timing.

---

### "What's this user experiencing?"

```
get_user_sessions(user_id="...", age=1440)
```
→ List their sessions.

```
get_session_details(session_id="...")
```
→ See all traces in the session.

---

### "Manage datasets"

```
list_datasets()
```
→ See all datasets.

```
get_dataset(name="evaluation-set-v1")
```
→ Get dataset details.

```
list_dataset_items(dataset_name="evaluation-set-v1", page=1, limit=10)
```
→ Browse items in the dataset.

```
create_dataset(name="qa-test-cases", description="QA evaluation set")
```
→ Create a new dataset.

```
create_dataset_item(
  dataset_name="qa-test-cases",
  input={"question": "What is 2+2?"},
  expected_output={"answer": "4"}
)
```
→ Add test cases.

```
create_dataset_item(
  dataset_name="qa-test-cases",
  item_id="item_123",
  input={"question": "What is 3+3?"},
  expected_output={"answer": "6"}
)
```
→ Upsert: updates existing item by id or creates if missing.

---

### "Manage prompts"

```
list_prompts()
```
→ See all prompts with labels.

```
get_prompt(name="...", label="production")
```
→ Fetch current production version.

```
create_text_prompt(name="...", prompt="...", labels=["staging"])
```
→ Create new version in staging.

```
update_prompt_labels(name="...", version=N, labels=["production"])
```
→ Promote to production. (Rollback = re-apply label to older version)

---

## Quick Reference

| Task | Tool |
|------|------|
| List traces | `fetch_traces(age=N)` |
| Get trace details | `fetch_trace(trace_id="...", include_observations=true)` |
| List LLM calls | `fetch_observations(age=N, type="GENERATION")` |
| Get observation | `fetch_observation(observation_id="...")` |
| Error count | `get_error_count(age=N)` |
| Find exceptions | `find_exceptions(age=N, group_by="file")` |
| List sessions | `fetch_sessions(age=N)` |
| User sessions | `get_user_sessions(user_id="...", age=N)` |
| List prompts | `list_prompts()` |
| Get prompt | `get_prompt(name="...", label="production")` |
| List datasets | `list_datasets()` |
| Get dataset | `get_dataset(name="...")` |
| List dataset items | `list_dataset_items(dataset_name="...", limit=N)` |
| Create/update dataset item | `create_dataset_item(dataset_name="...", item_id="...")` |

`age` = minutes to look back (max 10080 = 7 days)

---

## Troubleshooting

### MCP connection fails
- Verify credentials: check `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
- Restart CLI after adding/updating MCP config
- Test MCP independently: `fetch_traces(age=60)` — if this fails, the issue is MCP, not the skill
- See `references/setup.md` for detailed troubleshooting

### No traces found
- Increase the `age` parameter (default lookback may be too short)
- Verify your application is sending traces to the correct Langfuse project
- Check `LANGFUSE_HOST` points to the right instance (cloud vs self-hosted)

### Permission denied
- Regenerate API keys from Langfuse dashboard
- Ensure keys have the required scopes for the operation
- Write operations require read-write keys (not read-only mode)

---

## References

- `references/tool-reference.md` — Full parameter docs, filter semantics, response schemas
- `references/setup.md` — Manual setup, troubleshooting, advanced configuration
