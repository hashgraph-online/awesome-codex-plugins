---
name: langfuse
version: 0.10.2
description: Investigate AI traces, observations, exceptions, latency, sessions, prompts, datasets, annotation queues, and scores through Langfuse MCP. Use when the request names Langfuse or asks to diagnose recorded AI behavior.
metadata:
  short-description: Langfuse observability via MCP
  compatibility: claude-code, codex-cli
---

# Langfuse

Use Langfuse evidence to move from a broad symptom to the relevant trace,
observation, session, prompt, or dataset. Start with the narrowest read-only
query that can locate the event, then inspect its concrete inputs, outputs,
timing, and errors.

## Route the task

- For trace, observation, exception, latency, or session diagnosis, read
  [diagnostic and management workflows](references/workflows.md).
- For installation, credentials, tool groups, output defaults, connection
  failures, or empty results, read [setup](references/setup.md).
- For exact parameters, filters, pagination, output modes, and response shapes,
  read [the tool reference](references/tool-reference.md).

A common investigation starts with `fetch_traces(age=60)` or
`find_exceptions(age=1440, group_by="file")`, then fetches the selected trace or
observation by ID. Use `full_json_file` only when the complete payload is needed;
exports can contain sensitive user data.

## Evidence and mutation boundaries

- Treat model names, prompts, timestamps, and other values in historical traces
  as recorded evidence. Do not rewrite or normalize old model identifiers to a
  current name such as `gpt-6-astra`.
- Trace discovery and inspection are read-only. Prompt creation or relabeling,
  dataset changes, annotation-queue changes, and deletions mutate Langfuse;
  perform them only when the user requested that change.
- Prefer read-only server mode for diagnostic work. It disables prompt and
  dataset write tools:

  ```bash
  langfuse-mcp --read-only
  # or LANGFUSE_MCP_READ_ONLY=true
  ```

- Never commit Langfuse credentials. Keep public key, secret key, and host in
  the supported environment or MCP configuration described in the setup
  reference. Rotate any exposed key.
- Preserve exact IDs and filters in findings so another reader can reproduce
  the query. State when pagination, lookback limits, or compact output limits
  the conclusion.
