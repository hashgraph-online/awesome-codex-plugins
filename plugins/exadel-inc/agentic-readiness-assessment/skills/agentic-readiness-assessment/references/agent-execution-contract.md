# Agent execution contract

`agentic-readiness-assessment` is a **coding-agent workflow**: agentic repository investigation determines the relevant change and validation surfaces; deterministic tooling classifies commands, executes safe checks, and validates the finished report; a human controls scope and any irreversible action.

Before an assessment starts, the host runtime must provide or explicitly withhold the following evidence:

| Evidence | Record | If unavailable |
|---|---|---|
| Model identity | Provider, model identifier, and version or alias | `unavailable`; do not claim a pinned model. |
| Effective permission profile | The host's tool and path restrictions | `unavailable`; do not claim a tool allowlist. |
| Command boundary | Which command classes the host can run or refuse | `unavailable`; classify the resulting limitation. |
| Run stop condition | The host's turn, time, or cancellation limit | `unavailable`; retain the assessment's five-attempt discipline. |
| Context telemetry | Whether token usage, truncation, or context-limit signals are exposed | `unavailable`; do not infer context safety. |

Record the five fields or `unavailable` under the explicit constraints in **Run and Scope**. Missing host evidence is an `agent-environment` limitation on the assessment's confidence, not a repository finding. A portable prompt can request and record this evidence; it cannot enforce host permissions, pin a model, or add context telemetry.
