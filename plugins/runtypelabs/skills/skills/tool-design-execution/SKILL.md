---
name: tool-design-execution
description: 'Design how an agent tool runs: sync or async job, idempotency, timeouts, transactions, and compensation. Use when a tool is slow, has side effects that a retry could duplicate, or spans several systems.'
user-invocable: true
argument-hint: '[tool whose execution semantics to design]'
---

# Tool Execution Design

Agents retry. They retry on timeouts, on ambiguous errors, and sometimes on nothing at
all. Execution design makes that safe: bounded time, safe repetition, and consistent
state when a multi-step operation fails halfway.

## Procedure

1. **Measure or estimate the wall-clock time** of the operation: typical (p50) and
   worst case (p99).
2. **Pick the access pattern**: synchronous for bounded seconds, async job for minutes,
   streaming when partial output is useful as it arrives, event-driven when the tool
   notifies rather than answers.
3. **For every command tool, decide the retry story**: natural idempotency, an
   idempotency key, or a documented "not safe to retry" with a confirmation gate.
4. **For every multi-step command, decide the consistency story**: a real transaction
   where one system owns all steps, or compensation where several systems do.
5. **Set the timeout** and decide what a timeout returns.
6. **Verify**: call the tool with a slow or failing input. Confirm that the timeout
   error names the limit and the async alternative, and that a second identical call
   changes nothing.

## Rules with examples

### Default to synchronous, and bound it (Synchronous Execution)

Most tools return in the same call within seconds. Set an explicit timeout in the tool
definition, keep the description honest ("returns immediately"), and use the async
pattern only when the operation takes minutes.

### Long work returns a job handle (Async Job)

One tool starts the job and returns immediately. Sibling tools poll and fetch:

```json
{
  "jobId": "job_42",
  "status": "queued",
  "estimatedMinutes": 5,
  "nextAction": { "tool": "check_job_status", "args": { "jobId": "job_42" }, "afterSeconds": 30 }
}
```

- `start_*` returns the id, an estimate, and the names of the status and result tools.
- `check_job_status(jobId)` returns `queued | running | succeeded | failed` plus
  progress when available.
- `get_job_result(jobId)` returns the shaped result. Add `cancel_job(jobId)` when the
  work is cancellable.
- The start tool's description says the operation is long and names the polling tool,
  so the agent does not wait on the first call.

### Retries must be harmless (Idempotent Operation)

Query tools are idempotent by nature. Command tools need one of:

- **Natural key**: `create_order(orderId=...)` where the caller's id makes the second
  call a no-op that returns the first result.
- **Idempotency key**: an explicit `idempotencyKey` parameter. The tool stores the
  first result under that key for a documented window and returns it on repeat.
- **Deduplication**: detect an equivalent recent call and return its result.

Document the guarantee in the description ("Safe to retry: repeated calls with the same
`idempotencyKey` return the original payment"). Never let a retry create a second
payment, message, or ticket.

### All or nothing where one system owns the data (Transactional Boundary)

When every step touches one database, wrap them in a transaction. Keep the transaction
short, and state in the description what is inside it ("Either both accounts are
updated or neither is").

### Undo in reverse where systems are separate (Compensation Handler)

Cross-system operations cannot roll back atomically. Track each completed step, define
a compensating action for each, and run them in reverse order on failure:

```text
create_account   -> compensate: delete_account
setup_billing    -> compensate: cancel_billing
grant_access     -> compensate: revoke_access
```

Log every compensation. Say which steps may not be fully reversible (a sent email is
not un-sent) and surface that in the result. For slow undos, compensate asynchronously
and return a job handle.

### Time limits are explicit (Timeout Boundary)

Every tool that calls an external service has a maximum execution time. On timeout,
clean up, return partial results if any exist, and return a `retryable` error (see the
error classes in `tool-design-errors`) that names the limit and, when one exists, the
async alternative. Log timeouts. A rising timeout rate is the signal to convert the
tool to an async job.

### Streaming and events

Streaming suits tools whose partial output is useful before completion (search results
arriving, a document being generated). Event-driven tools push when something happens
and belong behind a subscription tool plus a webhook or queue, not a blocking call.
Both still need the timeout and idempotency decisions above.

## Anti-patterns

- A 45-second report generator exposed as a synchronous tool.
- A `create_*` command with no idempotency story and no confirmation gate.
- Multi-step provisioning that leaves the account created and billing missing with no
  compensation and no partial-success report.
- A timeout that surfaces as a generic failure with no partial result and no
  "try the async variant" hint.
- A polling tool with no `nextAction` and no interval, so the agent polls in a tight
  loop.

## On Runtype

- **Read the platform guides first.** `get_platform_documentation(topic="operational-design")`
  covers retries, idempotency, and choosing an execution mode.
  `topic="limits"` lists every time budget, and `topic="subagent-delegation"` covers
  detached subagents.
- **Tool time limits.** An external (HTTP) tool call is capped at 30 s. A custom tool
  defined inline in a dispatch request is rejected when its `config.timeout` is above
  30000 ms. The **Timeout (ms)** field on a saved custom tool accepts up to 300000 ms.
  An MCP server `timeout` can be up to 300000 ms, but a call that holds the original
  request open is clamped to 30 s.
- **Run budgets.** A flow step gets 5 minutes by default and a flow 15 minutes.
  `options.stepTimeoutMs` goes up to 10 minutes and `options.flowTimeoutMs` up to 15
  minutes. For a flow started with `async: true` (`Prefer: respond-async` over REST),
  both go up to 30 minutes. An `execute-agent` step gets only 30 s unless you raise
  its `config.timeout`, and that value is nested inside the step budget. One agent
  turn gets 5 minutes, or 30 minutes on durable execution, and
  `config.durability.maxBudgetMs` raises it up to 24 hours.
- **Async job shape inside an agent.** Use a `subagent` tool with
  `config.execution.mode: "detached"`. The call returns a `subagent_run` handle
  (`runId`, `status`). `notify` sets what happens on completion: `none` only stores the
  result, and `narrate` (the default) posts a completion status into the parent
  conversation. `narrate` needs a saved parent agent and a `conversationId`. `react`
  (start a new parent turn) is rejected today, so use `narrate` or `none`. Bound the
  run with `maxBudgetMs` (up to 24 hours) and `noProgressBudgetMs` (a silence timeout
  that resets on progress). Runtype adds `get_subagent_run`, `list_subagent_runs`, and
  `cancel_subagent_run` automatically, so you do not write status or cancel tools.
  With `narrate`, completion arrives in the conversation, so the agent must not poll
  `get_subagent_run` in a loop. The dynamic `spawn_subagent` tool can run detached when
  `config.tools.subagentConfig.executionModes` includes `"detached"`.
- **Async job shape from outside.** Start a flow or agent with `run_flow`, `dispatch`,
  or `execute_agent` with `async: true`, then poll `get_execution_status` with the
  returned execution id. After a timeout, poll instead of starting the run again. When a
  saved agent runs on durable execution, send an `Idempotency-Key` header on
  `POST /v1/agents/{id}/execute` or `dispatch` so a repeated request does not start a
  second run. The header is ignored on other runs.
- **A `flow` tool is not async.** The agent waits for the nested flow and gets its
  result, so the flow must finish inside the tool's budget.
- **Waiting on an external job inside a flow.** Use a `wait-until` step with
  `poll: { http, intervalMs, maxAttempts, success }`. The flow pauses without holding
  a connection. On durable execution Runtype caps the attempts at 1,000, so raise
  `intervalMs` for a longer wait. Keep the worst-case wait under 30 days, or the flow
  is rejected when you save it. Set
  `continueOnTimeout: true` when a timeout must not fail the flow.
- **Idempotent records.** Use `upsert-record` with `recordType` and a `recordName`
  built from a stable id that the caller supplies. A repeated call updates the same
  record instead of adding a duplicate.
- **Isolate side effects.** Put each side-effecting step (`send-email`,
  `upsert-record`, an `api-call` that changes data) in its own step, never in a step
  that can retry. A retry re-runs the failed step, and a resume after `wait-until`,
  `crawl`, or an approval pause re-enters the flow. For an external POST, pass the
  provider's idempotency key and check status after an ambiguous timeout before you
  retry.
- **Platform retries.** A `tool-call` step never retries a timeout, and it retries a
  tool that reports failure only when you set `onError: "retry"` or `maxRetries`
  (backoff up to 5 s between attempts). A step's `errorHandling.fallbacks` can also
  hold `{ "type": "retry", "delay": 2000 }`. Turn either on only for a tool that is
  safe to retry.
- **Compensation in flows.** Context steps take
  `errorHandling: { "onError": "fail" | "continue" | "fallback", "fallbacks": [...] }`.
  `fail` stops the flow, `continue` substitutes `defaultValue`, and `fallback` runs the
  `fallbacks` chain in order. A chain entry is a `retry`, a `step`, or a `flow`, so a
  compensating step or flow can be the undo path:

  ```json
  {
    "errorHandling": {
      "onError": "fallback",
      "fallbacks": [
        { "type": "flow", "flowId": "flow_refund_order", "inputs": { "orderId": "{{orderId}}" } }
      ]
    }
  }
  ```

  A `tool-call` step uses its own `config.onError` (default `fail`) instead. For the
  defaults when `errorHandling` is unset, see `tool-design-errors`. Flows have no
  cross-step transaction, so order the steps so the irreversible one runs last.

- **Confirmation gate.** List command tools that are not safe to retry in
  `config.tools.approval.require`. The approval `timeout` defaults to 300000 ms. An
  approval authorizes the action but does not make a retry safe. See
  `tool-design-security` for the full approval contract.
- **Timeout errors** from a tool reach the model as the tool's error. Name the async
  alternative in the tool description so the agent knows where to go.
