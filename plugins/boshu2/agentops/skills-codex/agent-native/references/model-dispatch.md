# Model Dispatch (controller-session)

Caller-elected multi-model judgment from the session you are already in.
No mailbox, no queue, no Agent Mail path for judgment. The working session
is the orchestrator: it starts workers, observes them, and collects artifacts.

This recipe is optional. Absent adapters, consumers stay single-model and
disclose that fact. Multi-model dispatch never starts unless the caller asks.

## Request shape

One request maps to exactly one worker and one artifact:

```text
{
  role,                 # judge | perspective | validator | ...
  model_profile,        # caller-named model/runtime identity string
  prompt_packet,        # exact bytes or path the worker receives
  workdir,              # absolute working directory
  sandbox,              # read-only | workspace-write | as declared
  output_path,          # where the worker must write its artifact
  context_id            # distinct from author and every peer worker
}
```

Return a factual receipt: exit status, `model_identity` (echo of
`model_profile` or adapter-reported identity), context ID, output path,
transcript reference when available. One request → one worker → one
artifact + receipt. Retry is the caller's decision, not this recipe's.

## Adapters (probe, never assume)

Probe at runtime; an absent adapter is a disclosed fact, never a silent
fallback.

| Adapter | Probe | Use when |
|---|---|---|
| `codex-exec` | `command -v codex` | Headless Codex workers (`codex exec` one-shot) |
| `ntm` | `command -v ntm` | Interactive / TUI-only runtimes hosted in panes |
| fake runner | always available in tests | Deterministic conformance without real models |

Order: use the adapter the caller named; if unset, prefer `codex` when the
profile is a Codex model, else `ntm` when interactive hosting is required.
If neither live adapter can satisfy the request, emit an explicit
`diversity_unsatisfied` disclosure on the consumer artifact and continue
single-model. Never invoke `claude -p` or `claude --print`.

## Guardrails (carry-overs)

- **kill-the-witness** — capture robot state / transcript before restarting a stuck pane.
- **prompt-send optimism** — a successful send is transport, not engagement; judge liveness by artifacts, then transcript growth, then robot state.
- **stdin hang** — non-TTY Codex runs must pipe the prompt or close stdin.

## Model identity

Model identity is a declared runtime fact, like context identity. Record it
per judge / perspective / validator. It strengthens diversity accounting; it
is not cryptographic proof of independence. Do not change `verdict.v2`
schema for it — put identities in evidence refs and freshness attestation
notes.

## Consumers

- `council` — per-judge model identity beside methodology; cross-model agreement is an extra diversity axis.
- `idea-genie` (duel) — per-perspective model identity; optional distinct-model pins.
- `validate` — optional cross-model fresh validator; author and validator model identities in evidence/attestation.
