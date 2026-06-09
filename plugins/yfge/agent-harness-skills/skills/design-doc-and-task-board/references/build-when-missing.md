# Build When Missing

Use this when product intent and execution state live only in conversation. Pattern sources include task boards, external task systems, design-doc directories, active/completed exec-plan directories, and docs indexes.

## Equivalent Artifacts

- External trackers, planning documents, issue templates, design indexes, or roadmap files may already satisfy the work-state, design, or exec-plan roles.
- Record the chosen artifacts under `Detected Mapping` before creating `tasks.md` or new planning directories.
- Use `templates/task-state.md` only when no reliable work-state surface exists.

## Minimum Files

- `tasks.md`, `docs/tasks.md`, or an explicitly mapped external tracker for current work state.
- `docs/design/`, `docs/design-docs/`, or an explicitly mapped equivalent for durable decisions.
- `docs/exec-plans/active/` and `docs/exec-plans/completed/` only for complex work that needs execution plans.
- `docs/exec-plans/template.md` or an equivalent plan template.

## Bootstrap Steps

1. Map existing issue trackers, planning docs, and design docs to their roles.
2. Create a default task-state file only when no reliable mapped work-state surface exists.
3. Create a design-doc directory and index only if decisions need longer-lived explanation.
4. Create exec-plan directories only when the repository has multi-step or multi-day work.
5. Define update order: design source first, task state second, exec-plan status third.
6. Define commit coupling: when a commit completes, changes, or invalidates a tracked task, stage the task-state update with that same logical commit.
7. Link planning files or external trackers from README or the entrypoint.

## Validation

- Confirm every active task has a status and acceptance criteria.
- Confirm design docs and task board do not duplicate the same decision as separate sources of truth.
- Confirm completed, changed, or invalidated tracked tasks are updated with the corresponding logical commit.
- Confirm completed exec plans are archived or clearly marked.

## Do Not Include

- Chat logs as task board content.
- Vague tasks such as "improve" without acceptance criteria.
- A rule that every commit must have a task, unless the repository explicitly wants that overhead.
- Large exec-plan machinery for small one-file fixes.
