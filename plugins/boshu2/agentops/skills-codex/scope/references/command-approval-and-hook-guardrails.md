# Command Approval And Hook Guardrails

Use this reference when path-scope protection is not enough and a session needs command approval, hook parity, or high-risk operation review.

## Guardrail Layers

| Layer | Blocks | Evidence |
|---|---|---|
| Path scope | Edits outside declared directories | `.agents/scope.lock` and hook stderr. |
| Command risk | Destructive or irreversible commands | Approval record or explicit denial. |
| Hook parity | Runtime-specific hook behavior drift | Hook fixture and schema tests. |
| Peer approval | High-risk command execution | Reviewer identity, command, and expiry. |

## Approval Rules

- Approval is per command shape, not a blanket session waiver.
- Expire approvals quickly.
- Record the exact command, working directory, and reason.
- Prefer a safer equivalent command when one exists.
- Refuse approval when rollback is unclear.

## Hook Review Checklist

- The hook fails open only for malformed hook input, not for known risky input.
- Output uses the portable subset accepted by all supported runtimes.
- Kill switches are documented and tested.
- Regex matchers have positive and negative examples.
- The hook has a timeout and no shell injection path.

---

**Source:** Adapted from an external skill corpus / `dcg`, `cc-hooks`, and `slb`. Pattern-only, no verbatim text.
