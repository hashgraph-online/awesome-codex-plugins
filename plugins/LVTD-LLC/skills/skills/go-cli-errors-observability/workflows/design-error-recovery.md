# Design Error Recovery Workflow

## Steps

1. [ ] Inventory invalid input, dependency, conflict, cancellation, and defect cases.
2. [ ] Assign programmatic types or causes without coupling to prose.
3. [ ] Write one concise message and one recovery action per recoverable class.
4. [ ] Define exit or structured error mapping at the process boundary.
5. [ ] Assign one terminal owner; remove intermediate log-and-return duplication.
6. [ ] Define cleanup-failure policy and preserve material secondary failures.
7. [ ] Define panic and recovery boundaries for violated invariants only.
8. [ ] Decide what context is safe in normal and debug modes.
9. [ ] Test cause trees, mapping, messages, cleanup, and stream placement.

## Exit Criteria

- [ ] Callers can distinguish actionable classes without parsing prose.
- [ ] Users receive enough context to recover without exposing sensitive detail.
- [ ] Each failure is rendered or logged once and retains inspectable causes.
