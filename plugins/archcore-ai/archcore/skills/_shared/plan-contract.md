# Plan Content Contract — Proof-Tracked Tasks

Plugin runtime asset. Loaded by the `plan` skill at `sdd.decompose` and on
resume, by the implementing agent after **Implement now**, and by the `review`
skill at `closeout.verify`. Companion to `skills/_shared/prd-contract.md`, which
owns the section assignment, and `skills/_shared/precision-rules.md`.

## Purpose

A proof-tracked plan shows from the document alone what is done, what is next,
and what waits on someone outside the repository. A task is done only when it
is **proven**: it is checked and carries a proof line in the form of
"Checking a task", step 4.

## Recognition

1. A plan is **proof-tracked** WHEN a numbered task in its `## Tasks` section
   starts with a checkbox and a task identifier: `1. [ ] T1 …` or `1. [x] T1 …`.
2. Every other plan is a **legacy plan**. A checkbox task without `T<n>` keeps
   a plan legacy.
3. Every skill MUST read a legacy plan as before this contract existed: no
   progress count, no proof check, no format advisory.
4. A skill MUST NOT convert a legacy plan to the proof-tracked form unless the
   user asks for it.
5. A checkbox outside `## Tasks`, for example in `## Acceptance Criteria`, is
   not a task.

## Sections

The mandatory sections stay as `skills/_shared/prd-contract.md` assigns them:
Goal, Tasks, Acceptance Criteria, Dependencies, and `## Declared Delta`.

- **Tasks** holds one `### Phase <n>: <name>` subsection per phase.
- **Waiting on** (optional, after Tasks) lists each condition that no one in
  this repository can satisfy, one bullet each, with `(owner: <who>)`.

A plan records no decision section. A settled choice routes through the
decision instrument per sequencing rule 8 of `skills/_shared/delta-routing.md`.

## The frontier

1. The **frontier** is the first phase that has a task that is not proven, or
   the first phase that has no task.
2. The frontier phase MUST hold between 1 and 6 numbered tasks.
3. A phase after the frontier MUST hold no numbered task.
4. A phase after the frontier holds one line:
   `Covers: <clause references>; expand when Phase <n-1> is proven.`
5. Every Normative Behavior and Failure Behavior clause of every `spec` the plan
   implements MUST appear in a task's `covers` line or in a `Covers:` line.
6. WHEN every task of the frontier is proven, the agent that proved the last
   task MUST expand the next phase.
7. The expanding agent MUST compose the new tasks from the code at the
   current commit.

## Task form

```markdown
1. [ ] T3 Evict the cache entries past the cap in key order

   - files: @src/cache.js @test/cache.test.js
   - covers: acme-cache#6, acme-cache#7
   - done when: `npx mocha test/cache.test.js` passes "evicts entries past the cap"
   - proof: —
```

1. The task line is one imperative action of at most 17 words after `T<n>`.
2. A blank line MUST separate the task line from its detail list.
3. `T<n>` is the task identifier. The composing skill MUST NOT renumber or
   reuse an identifier. A removed task leaves a gap.
4. `files` names each file the task changes or creates, with `@path`.
5. `covers` names spec clauses as `<spec slug>#<n>` for Normative Behavior
   clause n and `<spec slug>#F<n>` for Failure Behavior clause n. A task that no
   clause owns, such as wiring or a migration, has `covers: none`.
6. A range is `<spec slug>#<a>-<b>` or `<spec slug>#F<a>-F<b>`. A bare `#<n>`
   and a range written with "to" MUST NOT appear.
7. `done when` names one check: a test name or a command, with its expected
   result. The check MUST fail before the change and pass after it.
8. The check MUST use a test runner or command that the repository already
   defines.
9. IF the composing skill cannot name the files or the check of a task, THEN
   the skill reports the task as not atomic and writes no `files` guess.
10. A condition outside the repository, such as an approval, a host, or another
    team's release, MUST NOT be a task. It goes to **Waiting on**.

## Checking a task

1. Before the change, the implementing agent shows the check to the user and
   runs it. Expected result: the check fails.
2. After the change, the agent runs the check again. Expected result: the check
   passes.
3. IF the change is not committed, THEN the agent leaves the task as `[ ]` and
   reports it as done but unproven.
4. The agent replaces `[ ]` with `[x]` and `proof: —` with
   `proof: <check> @ <commit sha>`, in one `update_document` call with `edits`.
5. `<check>` is the check from `done when`.
6. `<commit sha>` is 7 to 40 hexadecimal characters and ends the line.
7. `<commit sha>` MUST name the first commit at which the check passes, so that
   the revert probe undoes only this task's change.
8. A checked task whose proof line has another form is a **claim**. Every skill
   MUST report a claim as unproven.
9. The agent MUST NOT delete, move, or collapse a checked task.

## Proof verification

`closeout.verify` judges a checked task **fulfilled** only when all of these
hold. These checks read git and files and run nothing:

1. The commit sha exists on the branch.
2. The commit or an earlier branch commit changes a file the task names.
3. The check exists at that commit as a test name or a command.

The **revert probe** is optional:

1. The reviewing skill MUST ask the user before the probe. Without a user to
   ask, the skill skips the probe.
2. IF the user declines, THEN checks 1–3 decide the verdict.
3. The probe runs in a new temporary copy of the repository: a `git clone` or a
   `git worktree`. The user's working tree MUST NOT host the probe.
4. In the temporary copy, the skill restores the task's non-test files to
   the parent of the proof commit and runs the check.
5. IF the check still passes, THEN the task is unfulfilled.

## Compatibility

- The form keeps the mandatory plan headings, so every CLI version runs the
  same precision checks on a proof-tracked plan.
- The precision scan counts `[`, `]`, and `T<n>` as words. A task line of 17
  words after `T<n>` stays within the 20-word step limit on every CLI version.
- A CLI that does not read task checkboxes shows no progress line at session
  start. The rules of this contract still hold through the skills.
