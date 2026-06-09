# Build When Missing

Use this when agent work has no durable delivery record. Pattern sources include delivery ledgers, review summaries, release notes, and handoff records with validation sections, linked tasks, and linked commits.

## Equivalent Artifacts

- Pull request descriptions, release notes, handoff notes, or an existing delivery log may already satisfy the ledger role.
- Record the chosen artifact under `Detected Mapping` before creating a default ledger directory.
- Use `templates/delivery-record.md` only when no equivalent delivery evidence format exists.

## Minimum Files

- `agent_chats/`, `agents_chat/`, or an explicitly mapped equivalent ledger surface.
- `.gitkeep` if the directory would otherwise be empty.
- `docs/agent-ledger-template.md` or a template section in `AGENTS.md`.
- Optional CI checker only after the policy is stable.

## Bootstrap Steps

1. Map any existing review, release, or handoff record to the ledger role.
2. If no equivalent exists, choose one ledger location and document that no parallel format should be created.
3. Define filename or record identity format appropriate to the mapped surface.
4. Define required sections: user prompt or goal, changes, validation, risks or next steps, linked tasks, and linked commits.
5. Define coupling: per commit, per review, per session, or per milestone.
6. Add skip policy for trivial or emergency changes, including how to record the skip reason.

## Validation

- Create or inspect one sample record and confirm all required sections exist.
- Confirm validation commands and artifact paths in the record match what actually ran.
- Confirm the ledger references task state without replacing the authoritative task surface.
- If CI exists, confirm code changes that require ledgers are detected.

## Do Not Include

- Raw private chat transcripts, secrets, credentials, or sensitive logs.
- Two competing ledger directory names unless one is explicitly deprecated.
- Task-status ownership that belongs in `tasks.md`, an issue tracker, or another work-state surface.
- Commit-splitting rules that belong in atomic commit discipline.
