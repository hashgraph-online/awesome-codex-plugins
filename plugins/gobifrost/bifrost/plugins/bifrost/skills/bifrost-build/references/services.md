# Supervised Services

Use `@service` for long-lived work that holds a connection, subscription, or
listener indefinitely and bridges an external system into Bifrost by emitting
events (Telegram long-polling, Discord gateway, MQTT subscriber). Services
run under supervision (desired state, fenced leases, restart policy) instead
of producing a terminal result like workflows. Service rows live in the
workflows table with `type='service'`. Decorator choice across all executable
types is covered in `references/workflows.md`.

```python
from bifrost import events, service


@service
async def telegram_bridge() -> None:
    """Bridge Telegram messages into Bifrost events."""
    await service.ready()
    while not service.is_stopping():
        for update in await poll_once():
            await events.emit("bridge.telegram.message", {"update": update})
```

Contract differences from `@workflow` (all enforced, all load-bearing):

- Must be `async def`: registration rejects sync service functions. A sync
  function would block its worker forever.
- Takes no meaningful inputs and returns no result: there is no caller to
  receive them. Keep the body a thin poll/emit loop; put reusable logic in
  modules under the same test-driven rule as workflows.
- Reports lifecycle through the supervision namespace on the `service`
  object: call `service.ready()` once startup is complete (marks the
  attempt running); leave the loop when `service.is_stopping()` is true or
  `await service.wait_until_stopping()`. Stops are cooperative (SIGTERM
  resolves a parked wait); the platform restarts the attempt per policy
  after exit.
- Accepts only identity metadata (`name`, `description`, `category`,
  `tags`) under the same backwards-compatible unknown-kwarg rule as
  `@workflow`. Lifecycle configuration (startup/restart policy, shutdown
  and startup grace, backoff, crash-loop limits) is operator state: manage
  it through the UI/API/CLI, never in code.
- Never handles credentials: a renewable service token is handed down at
  dispatch and rotated automatically. Do not read platform secrets, mint
  tokens, or persist auth in the body.

Operate a service through the generated CLI surface (`generated/cli-reference.md`
`services` section): `services list/get`, `services start/stop/restart`,
`services enable/disable`, `services update` for policy,
`services attempts` for run history, `services logs` for the trailing
persisted tail (live output streams over the `service:` WebSocket channel
while running).

Ownership and registration follow the workflow rules in
`references/workflows.md`: Solution-owned source under `functions/` with a
`.bifrost/workflows.yaml` entry plus `bifrost solution deploy`, or loose
files registered with `bifrost workflows register` (the platform detects
`@service` and ensures the supervised definition). Deleting or converting a
service row parks its definition (disabled + stopped) rather than dropping
history; a crash-looping service surfaces `blocked_reason: crash_loop` on
the definition — tune backoff/crash-loop policy with `services update`,
don't delete and re-register.

Before handoff, in addition to the workflow checklist: start the service on
a dev instance and confirm it reaches `running`; stop it and confirm the
attempt exits promptly (no hang past the graceful window); confirm
`services logs` shows the expected lines; kill/restart once and confirm a
new attempt appears rather than a stuck one.
