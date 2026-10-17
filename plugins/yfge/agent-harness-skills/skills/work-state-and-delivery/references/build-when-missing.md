# Build When Missing

Use this when intent, work state, or delivery evidence lives only in conversation and the repository profile requires a durable governance surface.

## Equivalent Artifacts

- GitHub Issues, Jira, Linear, internal boards, pull request descriptions, release notes, and handoff records may already satisfy work-state or delivery roles.
- Record mapped artifacts under `Detected Mapping` before creating repo-local defaults.
- Use `templates/task-state.md` and `templates/delivery-record.md` only for roles with no reliable equivalent.

## Minimum Files

- A mapped external tracker or `tasks.md` / `docs/tasks.md` for current work state.
- A design-doc location only when decisions need durable explanation.
- An execution-plan location only for complex multi-step or multi-day work.
- A mapped review, release, or handoff surface; create a ledger directory only when durable delivery records are required.
- Commit and task-coupling rules in `AGENTS.md`, `CONTRIBUTING.md`, or another mapped policy surface.

## Bootstrap Steps

1. Map existing planning, tracking, review, release, handoff, and commit-policy surfaces.
2. Create only missing roles required by the repository profile.
3. Define responsibilities and update order for design, work state, execution plans, and delivery evidence.
4. Define task-to-change coupling and exact-path staging rules in the mapped policy surface.
5. Define required delivery evidence, artifact references, redaction, and explicit skip conditions.
6. Link the mapped surfaces from the agent entrypoint or contributor documentation.

## Validation

- Confirm active tracked work has status and executable acceptance criteria.
- Confirm design, work state, and delivery records do not duplicate the same truth.
- Inspect one logical change and verify task updates, validation, and artifact references agree.
- Confirm optional governance surfaces are absent when the repository profile does not justify them.

## Do Not Include

- Raw private chat transcripts, secrets, sensitive logs, or large temporary artifacts.
- A second task board or ledger format when an existing surface is reliable.
- A rule that every commit needs a task or ledger entry unless the repository explicitly requires it.
- Heavy execution-plan machinery for small changes.
