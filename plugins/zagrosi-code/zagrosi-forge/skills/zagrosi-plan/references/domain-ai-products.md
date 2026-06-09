# Domain Pack: AI Product Features

Use this when a plan touches LLM workflows, prompt chains, retrieval, agents,
tool use, evaluations, model selection, safety filters, or generated content.

## Evidence To Gather

- Existing prompt templates, model calls, tools, and retrieval stores.
- Evaluation datasets, golden outputs, and quality metrics.
- Latency, cost, and rate-limit constraints.
- Safety, privacy, logging, and retention policy.
- Human review or escalation workflows.
- Current failure modes and fallback behavior.

## Plan Must Decide

- Model and tool boundary.
- Input/output schemas and validation.
- Evaluation criteria and regression suite.
- Fallback behavior for model errors, bad outputs, and blocked content.
- Prompt/version management.
- Observability for quality, cost, latency, and safety.

## Tests First

- Schema validation for model inputs and outputs.
- Deterministic unit tests for prompt assembly and tool selection.
- Golden evals for representative tasks.
- Safety and privacy redaction tests.
- Fallback tests for provider failure, malformed output, and low confidence.
