---
name: waggle-recall
description: Recall project-scoped Waggle history about a topic, component, decision, bug, experiment, or implementation attempt.
---

# Recall project history

1. Extract the requested topic from the user's prompt. Ask only if no topic can reasonably be inferred.
2. Determine the stable project scope: prefer the credential-free Git remote identity, otherwise the canonical absolute Git root or workspace path.
3. Call `query_graph` with the topic, that project scope, `agent_id: "codex"`, `retrieval_mode: "hybrid"`, `max_nodes: 10`, and `max_depth: 1`.
4. If a useful node needs more context, call `get_related` with its node ID and `max_depth: 1`.
5. Answer with a concise synthesis. Identify contradictions, updates, provenance, or uncertainty when returned. Never treat an empty result as evidence that something did not happen.

This is the Codex skill equivalent of `/waggle-recall <topic>`; invoke it as `$waggle-recall` followed by the topic.
