# Langfuse MCP Tool Reference

Reference documentation for all Langfuse MCP tools. The top-level README also lists the current tool inventory.

## Tools by Category

| Category | Tools |
|----------|-------|
| Traces | fetch_traces, fetch_trace |
| Observations | fetch_observations, fetch_observation |
| Routing | find_route_decisions, get_route_decision, summarize_route_decisions, find_low_confidence_route_decisions |
| Sessions | fetch_sessions, get_session_details, get_user_sessions |
| Exceptions | find_exceptions, find_exceptions_in_file, get_exception_details, get_error_count |
| Prompts | list_prompts, get_prompt, get_prompt_unresolved, create_text_prompt*, create_chat_prompt*, update_prompt_labels* |
| Datasets | list_datasets, get_dataset, list_dataset_items, get_dataset_item, create_dataset*, create_dataset_item*, delete_dataset_item*, list_dataset_runs, get_dataset_run, list_dataset_run_items, create_dataset_run_item*, delete_dataset_run* |
| Annotation Queues | list_annotation_queues, create_annotation_queue*, get_annotation_queue, list_annotation_queue_items, get_annotation_queue_item, create_annotation_queue_item*, update_annotation_queue_item*, delete_annotation_queue_item*, create_annotation_queue_assignment*, delete_annotation_queue_assignment* |
| Scores | list_scores_v2, get_score_v2 |
| Metrics | query_metrics, get_metrics_schema |
| Schema | get_data_schema |

*\*Tools marked with \* are disabled in read-only mode (`--read-only` or `LANGFUSE_MCP_READ_ONLY=true`).*

## Output Modes

Some tools support output modes via the `output_mode` parameter:

| Mode | Description |
|------|-------------|
| `compact` | Summary with large values truncated (default) |
| `full_json_string` | Complete data as JSON string (returns string, not object) |
| `full_json_file` | Save to file, return summary with path |

**Tools with output_mode:** `fetch_traces`, `fetch_trace`, `fetch_observations`, `fetch_observation`, `find_route_decisions`, `get_route_decision`, `find_low_confidence_route_decisions`, `fetch_sessions`, `get_session_details`, `get_user_sessions`, `find_exceptions_in_file`, `get_exception_details`, `list_dataset_items`, `get_dataset_item`, `get_dataset_run`, `list_dataset_run_items`, `query_metrics`

Other tools do not accept `output_mode`.

## Filter Semantics

Filter behavior depends on the Langfuse API:

| Filter | Matching Rule |
|--------|---------------|
| `name` | Passed to Langfuse API (behavior varies by endpoint) |
| `tags` | Comma-separated, passed to Langfuse API |
| `metadata` | Exact key/value match, top-level keys only |
| `user_id`, `session_id`, `trace_id` | Exact match |

**Note:** `list_prompts` uses exact name matching. Other tools pass filters to the Langfuse API.

## Sort Order

Sort order depends on the Langfuse API. Traces and observations are typically sorted by timestamp descending (newest first).

## Pagination

Some tools support pagination via `page` and `limit` parameters. Check individual tool docs.

**Tools with pagination:** `fetch_traces`, `fetch_observations`, `find_route_decisions`, `summarize_route_decisions`, `find_low_confidence_route_decisions`, `fetch_sessions`, `list_prompts`, `list_datasets`, `list_dataset_items`, `list_dataset_runs`, `list_dataset_run_items`, `list_annotation_queues`, `list_annotation_queue_items`, `list_scores_v2`

Other tools do not accept `page` and `limit`.

**Tip:** For large results, use `output_mode="full_json_file"` to avoid context overflow.

---

## Traces

### fetch_traces

Search and filter traces with pagination.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `age` | int | Yes | - | Look back window in minutes from now (e.g., 1440 for 24h). Max 10080 (7 days). |
| `name` | string | No | null | Name filter (passed to API) |
| `user_id` | string | No | null | User ID to filter traces by (exact match) |
| `session_id` | string | No | null | Session ID to filter traces by (exact match) |
| `metadata` | object | No | null | Metadata fields to filter by (exact key/value match) |
| `tags` | string | No | null | Tag or comma-separated list of tags |
| `page` | int | No | 1 | Page number for pagination (starts at 1) |
| `limit` | int | No | 50 | Maximum traces per page |
| `include_observations` | bool | No | false | Add the full observation objects (omitted entirely when false) |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** List of trace objects with metadata including pagination info.

**Example:**
```
fetch_traces(age=1440, user_id="user_123", include_observations=true)
```

---

### fetch_trace

Fetch a specific trace by ID.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `trace_id` | string | Yes | - | The ID of the trace to fetch |
| `include_observations` | bool | No | false | Include full observation objects |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** Single trace object with all details.

**Example:**
```
fetch_trace(trace_id="abc-123", include_observations=true, output_mode="full_json_file")
```

---

## Observations

### fetch_observations

Search and filter observations (spans, generations, events, tool calls, agent steps, and more).

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `age` | int | Yes | - | Look back window in minutes from now. Max 10080 (7 days). |
| `type` | string | No | null | Filter by type: `SPAN`, `GENERATION`, `EVENT`, `AGENT`, `TOOL`, `CHAIN`, `RETRIEVER`, `EVALUATOR`, `EMBEDDING`, or `GUARDRAIL` |
| `name` | string | No | null | Name filter (passed to API) |
| `user_id` | string | No | null | User ID filter (exact match) |
| `trace_id` | string | No | null | Trace ID filter (exact match) |
| `parent_observation_id` | string | No | null | Parent observation ID filter (exact match) |
| `page` | int | No | 1 | Page number |
| `limit` | int | No | 50 | Max items per page |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** List of observation objects.

**Example:**
```
fetch_observations(age=60, type="GENERATION", name="chat-completion")
```

---

### fetch_observation

Fetch a specific observation by ID.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `observation_id` | string | Yes | - | The ID of the observation to fetch |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** Single observation object with full details.

---

## Routing

These tools read SPAN observations whose metadata has `schema_version="mcp.route_decision.v1"`. The optional `trace_id`, `session_id`, `router_name`, `provider`, and `capability_id` filters narrow route decisions; `age` defaults to 10080 minutes.

| Tool | Use and key parameters |
|------|------------------------|
| `find_route_decisions` | List decisions; also accepts `decision_id`, `page=1`, `limit=50`, and `output_mode="compact"`. |
| `get_route_decision` | Fetch one decision by required `decision_id`; accepts `age` and `output_mode`. |
| `summarize_route_decisions` | Count decisions by router, provider, capability, and callable state; report confidence. Accepts `max_confidence=0.5`, `page=1`, and `limit=200`. |
| `find_low_confidence_route_decisions` | Find decisions at or below `max_confidence=0.5`; `include_uncallable=True` also includes uncallable decisions. Accepts `page=1`, `limit=50`, and `output_mode`. |

---

## Sessions

### fetch_sessions

List recent sessions with pagination.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `age` | int | Yes | - | Look back window in minutes from now. Max 10080 (7 days). |
| `page` | int | No | 1 | Page number |
| `limit` | int | No | 50 | Max items per page |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** List of session summaries.

---

### get_session_details

Get detailed session info by ID.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `session_id` | string | Yes | - | The session ID to fetch |
| `include_observations` | bool | No | false | Add the full observation objects (omitted entirely when false) |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** Session object with all traces.

---

### get_user_sessions

Get all sessions for a user.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `user_id` | string | Yes | - | The user ID to look up |
| `age` | int | Yes | - | Look back window in minutes from now. Max 10080 (7 days). |
| `include_observations` | bool | No | false | Add the full observation objects (omitted entirely when false) |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** List of sessions for the user.

---

## Exceptions

### find_exceptions

Find error-level observations grouped by file, function, type, observation name, or observation type.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `age` | int | Yes | - | Look back window in minutes from now. Max 10080 (7 days). |
| `group_by` | string | No | "file" | How to group: "file", "function", "type", "name", or "observation_type" |

**Returns:** List of `{group: string, count: int, observation_id: string|null, trace_id: string|null}` objects, sorted by count descending (top 50). Each group carries a representative observation/trace ID.

**Note:** Does not support `output_mode` parameter. Counts describe error-level observations (`level=ERROR`), NOT individual exception events — the standard observation listing does not expose events. Missing recorded metadata groups as `"unknown"`.

**Example:**
```
find_exceptions(age=1440, group_by="type")
```

---

### find_exceptions_in_file

Find error-level observations recorded against a specific file.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `filepath` | string | Yes | - | Path to the file as recorded in Langfuse metadata (typically relative to project root, e.g., `src/utils/ai.ts`) |
| `age` | int | Yes | - | Look back window in minutes from now. Max 10080 (7 days). |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** List of error records (top 10, newest first):
- `observation_id`, `trace_id`, `timestamp`
- `exception_type`, `exception_message`, `exception_stacktrace` (null when not recorded)
- `function`, `line_number`
- `level`, `observation_type`, `status_message`
- `event_id`, `event_name` (always null — events are not retrievable via the API)

**Note:** Only matches observations whose recorded `code.filepath` equals the argument; an empty result means no matching ERROR observations were found, not that the file is error-free.

**Example:**
```
find_exceptions_in_file(filepath="src/ai/chat.py", age=1440)
```

---

### get_exception_details

Get detailed error info for a trace/span.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `trace_id` | string | Yes | - | The trace ID to analyze |
| `span_id` | string | No | null | Optional observation ID to filter by (across all observation types) |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** List of error records with full context including observation details. Fields as in `find_exceptions_in_file` plus `filepath` and `observation_name`.

---

### get_error_count

Get counts of error-level observations in the lookback window.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `age` | int | Yes | - | Look back window in minutes from now. Max 10080 (7 days). |

**Returns:**
```json
{
  "data": {
    "age_minutes": 60,
    "from_timestamp": "2024-01-15T09:30:00Z",
    "to_timestamp": "2024-01-15T10:30:00Z",
    "trace_count": 5,
    "observation_count": 12,
    "exception_count": null
  },
  "metadata": {"count_basis": "error_level_observations", "note": "..."}
}
```

**Note:** Does not support `output_mode` parameter. `exception_count` is always null — individual exception events are not retrievable from the standard observation listing; `observation_count` counts error-level observations.

---

## Prompts

### list_prompts

List and filter prompts in the project.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | No | null | Filter by exact prompt name |
| `label` | string | No | null | Filter by label (e.g., "production") |
| `tag` | string | No | null | Filter by tag |
| `page` | int | No | 1 | Page number |
| `limit` | int | No | 50 | Max items per page (max 100) |

**Returns:** List of prompt metadata:
- `name`, `type` ("text" or "chat")
- `versions`, `labels`, `tags`
- `lastUpdatedAt`, `lastConfig`

---

### get_prompt

Fetch a specific prompt with resolved dependencies.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | The prompt name |
| `label` | string | No | null | Label to fetch (e.g., "production"). Mutually exclusive with version. |
| `version` | int | No | null | Specific version number. Mutually exclusive with label. |

**Returns:** Prompt object:
- `id`, `name`, `version`, `type`
- `prompt` (string for text, list for chat)
- `labels`, `tags`, `config`

**Example:**
```
get_prompt(name="chat-system", label="production")
```

---

### get_prompt_unresolved

Fetch a prompt WITHOUT resolving dependencies.

Returns raw prompt content with dependency tags intact (e.g., `@@@langfusePrompt:name=xxx@@@`) when the SDK supports `resolve=false`. If the SDK doesn't support this parameter, returns the resolved prompt and sets `metadata.resolved=true` to indicate fallback behavior.

**Parameters:** Same as `get_prompt`.

**Returns:** Same structure but with dependency tags preserved in prompt content. Check `metadata.resolved` to verify if unresolved content was returned.

---

### create_text_prompt

Create a new text prompt version.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | The prompt name |
| `prompt` | string | Yes | - | Prompt text content (supports `{{variables}}`) |
| `labels` | list[string] | No | null | Labels to assign (e.g., ["staging"]) |
| `config` | object | No | null | Model config (see example below) |
| `tags` | list[string] | No | null | Tags for organization |
| `commit_message` | string | No | null | Commit message describing changes |

**Config Example:**
```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1.0
}
```

**Returns:** Created prompt object.

**Note:** Prompts are immutable. Creating a new version is the only way to update content. Labels are unique across versions - assigning a label here removes it from other versions.

**Example:**
```
create_text_prompt(
  name="greeting",
  prompt="Hello {{name}}, welcome to {{app}}!",
  labels=["staging"],
  config={"model": "gpt-4", "temperature": 0.7},
  commit_message="feat: add personalized greeting"
)
```

---

### create_chat_prompt

Create a new chat prompt version.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | The prompt name |
| `prompt` | list[object] | Yes | - | Chat messages (see format below) |
| `labels` | list[string] | No | null | Labels to assign |
| `config` | object | No | null | Model config (same as create_text_prompt) |
| `tags` | list[string] | No | null | Tags for organization |
| `commit_message` | string | No | null | Commit message |

**Prompt Format:**
```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "{{user_input}}"}
]
```

**Returns:** Created prompt object.

**Example:**
```
create_chat_prompt(
  name="assistant",
  prompt=[
    {"role": "system", "content": "You are a helpful coding assistant."},
    {"role": "user", "content": "{{question}}"}
  ],
  labels=["staging"],
  config={"model": "gpt-4", "temperature": 0.3}
)
```

---

### update_prompt_labels

Update labels for a specific prompt version.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | The prompt name |
| `version` | int | Yes | - | The version to update |
| `labels` | list[string] | Yes | - | Labels to add (existing labels preserved) |

**Returns:** Updated prompt object.

**Note:** This is the only supported mutation for existing prompts. Labels are unique across versions - adding a label here removes it from other versions.

**Example (promote to production):**
```
update_prompt_labels(name="greeting", version=3, labels=["production"])
```

**Example (rollback):**
```
update_prompt_labels(name="greeting", version=2, labels=["production"])
```

---

## Datasets

### list_datasets

List all datasets with pagination.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `page` | int | No | 1 | Page number |
| `limit` | int | No | 50 | Max items per page |

**Returns:** List of dataset objects with metadata.

**Example:**
```
list_datasets(page=1, limit=20)
```

---

### get_dataset

Get a dataset by name.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | The name of the dataset to fetch |

**Returns:** Dataset object with full details.

**Example:**
```
get_dataset(name="evaluation-set-v1")
```

---

### list_dataset_items

List items in a dataset with optional filters.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `dataset_name` | string | Yes | - | The name of the dataset |
| `source_trace_id` | string | No | null | Filter by source trace ID |
| `source_observation_id` | string | No | null | Filter by source observation ID |
| `page` | int | No | 1 | Page number |
| `limit` | int | No | 50 | Max items per page |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** List of dataset items.

**Example:**
```
list_dataset_items(dataset_name="evaluation-set-v1", page=1, limit=10)
```

---

### get_dataset_item

Get a specific dataset item by ID.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `item_id` | string | Yes | - | The ID of the dataset item to fetch |
| `output_mode` | string | No | "compact" | Output format |

**Returns:** Dataset item object with full details.

**Example:**
```
get_dataset_item(item_id="item-abc-123")
```

---

### create_dataset

Create a new dataset.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | The name for the new dataset |
| `description` | string | No | null | Description of the dataset |
| `metadata` | object | No | null | Additional metadata |

**Returns:** Created dataset object.

**Example:**
```
create_dataset(name="qa-evaluation-set", description="QA test cases for v2.0")
```

---

### create_dataset_item

Create or upsert a dataset item.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `dataset_name` | string | Yes | - | The name of the dataset |
| `input` | any | No | null | Input data for the item |
| `expected_output` | any | No | null | Expected output for evaluation |
| `metadata` | object | No | null | Additional metadata |
| `source_trace_id` | string | No | null | Link to source trace |
| `source_observation_id` | string | No | null | Link to source observation |
| `item_id` | string | No | null | Item ID (for upsert; if exists, updates the item) |
| `status` | string | No | null | Item status (e.g., "ACTIVE", "ARCHIVED") |

**Returns:** Created or updated dataset item object.

**Example:**
```
create_dataset_item(
  dataset_name="qa-evaluation-set",
  input={"question": "What is the capital of France?"},
  expected_output={"answer": "Paris"},
  metadata={"category": "geography"}
)
```

---

### delete_dataset_item

Delete a dataset item.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `item_id` | string | Yes | - | The ID of the dataset item to delete |

**Returns:** Confirmation of deletion.

**Example:**
```
delete_dataset_item(item_id="item-abc-123")
```

---

### Dataset runs and experiments

Dataset-run reads use the experiments API with `langfuse>=4.13.1`; older servers can use the legacy read routes. An older SDK whose legacy read route is gone raises `ERR_LANGFUSE_EXPERIMENTS_SDK_UPGRADE`.

| Tool | Use and key parameters |
|------|------------------------|
| `list_dataset_runs` | List a required `dataset_name`; accepts `page=1` and `limit=50`. |
| `get_dataset_run` | Fetch `dataset_name` and `run_name`, including items; accepts `output_mode="compact"`. |
| `list_dataset_run_items` | List items by required `dataset_id` and `run_name`; accepts `page=1`, `limit=50`, and `output_mode="compact"`. |
| `create_dataset_run_item` | Link an existing `dataset_item_id` to `run_name`; optional `run_description`, `metadata`, `observation_id`, and `trace_id`. |
| `delete_dataset_run` | Delete by `dataset_name` and `run_name`; `delete_traces=False` by default. |

`create_dataset_run_item` uses a legacy link route. After Langfuse Cloud removes it on 2026-11-16, the tool raises `ERR_LANGFUSE_RUN_ITEM_CREATE_REMOVED`; use the SDK experiment runner or OTel ingestion to create new experiment data.

`delete_dataset_run` uses the legacy delete route while it works. After removal, `delete_traces=True` is required; it deletes the run's traces, observations, and related scores. Without opt-in, no traces are deleted.

---

## Annotation Queues

Queue writes are disabled in read-only mode.

| Tool | Use and key parameters |
|------|------------------------|
| `list_annotation_queues` | List queues with `page=1` and `limit=50`. |
| `create_annotation_queue` | Create a queue with required `name`; optional `description` and `score_config_ids`. |
| `get_annotation_queue` | Fetch a queue by `queue_id`. |
| `list_annotation_queue_items` | List items by `queue_id`, `page=1`, and `limit=50`. |
| `get_annotation_queue_item` | Fetch an item by `queue_id` and `item_id`. |
| `create_annotation_queue_item` | Add `object_id` and `object_type` to `queue_id`; optional `status`. |
| `update_annotation_queue_item` | Set an item's `status` by `queue_id` and `item_id`. |
| `delete_annotation_queue_item` | Remove an item by `queue_id` and `item_id`. |
| `create_annotation_queue_assignment` | Assign `user_id` to `queue_id`. |
| `delete_annotation_queue_assignment` | Unassign `user_id` from `queue_id`. |

---

## Scores

Score reads use Scores API v3 with `langfuse>=4.8.1`; if an older SDK cannot use v3 and the old route is gone, they raise `ERR_LANGFUSE_SCORES_V2_REMOVED`.

| Tool | Use and key parameters |
|------|------------------------|
| `list_scores_v2` | List scores with `page=1`, `limit=50`, and optional `name`, `from_timestamp`, `to_timestamp`, `environment`, `source`, `score_ids`, `config_id`, `session_id`, `trace_id`, `queue_id`, `user_id`, `trace_tags`, `operator`, `value`, and `data_type` filters. |
| `get_score_v2` | Fetch a score by required `score_id`. |

With `operator="="` and `value`, an omitted `data_type` defaults to `NUMERIC`; pass `data_type="BOOLEAN"` for boolean scores. The response metadata includes `data_type_hint` when this default applies. `user_id` and `trace_tags` need the old v2 route, which Langfuse Cloud removes on 2026-11-16.

---

## Metrics

| Tool | Use and key parameters |
|------|------------------------|
| `query_metrics` | Aggregate a required `view` (`observations`, `scores-numeric`, or `scores-categorical`) and required `metrics` list. Optional `dimensions`, `filters`, `age`, `from_timestamp`, `to_timestamp`, `time_granularity`, `order_by`, and `output_mode="compact"`. |
| `get_metrics_schema` | Read the supported views, measures, dimensions, filter operators, and query shape. |

Use `get_metrics_schema` before building a new query. `query_metrics` defaults to a 24-hour window when no time range is given. The v2 metrics endpoint is Cloud-only; a server that returns 404 can use the legacy metrics route.

---

## Schema

### get_data_schema

Get schema information for response structures.

**Parameters:** None (dummy parameter for compatibility).

**Returns:** Documentation of response schemas for all tools.

---

## Response Format

Tools return responses in one of two formats depending on `output_mode`:

### For `compact` and `full_json_file` modes:

```json
{
  "data": [...] | {...},
  "metadata": {
    "item_count": 10,
    "page": 1,
    "total": 100,
    "next_page": 2,
    "file_path": "/tmp/langfuse_mcp/traces_2024...json",
    "file_info": {...}
  }
}
```

### For `full_json_string` mode:

Returns a **string** containing serialized JSON (not an object). Parse it if you need structured access.

---

## Example Response (compact)

```json
{
  "data": [
    {
      "id": "trace-abc-123",
      "name": "chat-completion",
      "user_id": "user-456",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "metadata": {
    "item_count": 1,
    "next_page": 2,
    "file_path": null,
    "file_info": null
  }
}
```

On Observations API v2, `fetch_traces` no longer returns `total_cost`, `scores`, or an
`observations` field by default — pass `include_observations=true` to add an `observations`
field with the full observation objects (not just IDs), and use `query_metrics` for cost and
score aggregates. Pagination is cursor-based, so `metadata` carries `next_page` but no `total`
or `page` count.

## Example Response (full_json_file)

```json
{
  "data": [{"id": "trace-abc-123", "...": "truncated"}],
  "metadata": {
    "item_count": 1,
    "page": 1,
    "total": 47,
    "file_path": "/tmp/langfuse_mcp/traces_20240115_103000.json",
    "file_info": {
      "size_bytes": 15234,
      "created_at": "2024-01-15T10:30:05Z"
    }
  }
}
```
