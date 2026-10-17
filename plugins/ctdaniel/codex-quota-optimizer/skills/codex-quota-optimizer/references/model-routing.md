# Model routing

The exact model lineup can change. Route by role first, model name second.

| Task shape | Preferred role | Current example | Reasoning | Escalate when |
|---|---|---|---|---|
| Mechanical edit, extraction, rename, repetitive change | cheapest/fastest | GPT-5.6 Luna | low | behavior is ambiguous |
| Normal feature/fix, repo exploration, code review | balanced daily model | GPT-5.6 Terra | low/medium | cross-cutting reasoning is unresolved |
| Complex design, hard debugging, open-ended implementation | deep model | GPT-5.6 Sol | medium/high | strongest end-to-end orchestration is needed |
| Very hard multi-step/tool workflow | strongest available | GPT-6 Astra | only as needed | n/a |

Rules:

1. Start with the lowest adequate reasoning effort.
2. Escalate one dimension at a time: reasoning OR model, not both automatically.
3. For scanning/reading, prefer cheaper models than for final architectural judgment.
4. Avoid Ultra unless parallel decomposition is genuinely useful; parallel agents multiply work/context.
5. Treat model availability as dynamic. If the client does not expose a model, use its closest role equivalent.
