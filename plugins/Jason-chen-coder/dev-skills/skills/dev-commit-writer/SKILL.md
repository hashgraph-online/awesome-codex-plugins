---
name: dev-commit-writer
description: Write a commit message from a requested Git diff when the user asks for message generation. Does not review, stage, or commit. Requests such as 帮我 commit require the commit workflow, including review when required; asking for a message does not require an explicit skip-review declaration.
---

# Dev Commit Writer

Produce an accurate, concise commit message in the repository's style. This is a read-only writing task, not a quality verdict or authorization to run `git commit`.

## Load baseline

Read [references/dev-baseline.md](references/dev-baseline.md) before execution. Resolve paths relative to this skill directory.

## Read the intended change

- Identify the actual repository root and inspect status, staged diff, unstaged diff, and recent commit subjects/bodies.
- Honor explicit `--staged` / `--cached`, `--path=<glob>`, named files, and exclusions. Without an explicit scope, use the staged diff when present; otherwise use changes attributable to the task. State the chosen scope briefly if mixed changes could cause confusion.
- Include untracked files only when they belong to the requested change and their content has been inspected. Never silently fold unrelated unstaged work into a message for the index.
- If there is no change to describe, say so. A user-provided diff is also a valid source, but do not pretend to have inspected a local repository when only that text is available.

## Write the message

Follow repository instructions and dominant recent history for language, prefixes, scope, and body style. If no convention can be established, use a short descriptive subject; Conventional Commits is an acceptable fallback when appropriate. Aim for a subject within 72 characters unless repository rules specify otherwise.

Describe the concrete behavior or reason for the change. Add a body only to explain a non-obvious motivation, compatibility impact, or related change that the subject cannot cover. Do not invent issue IDs, verification results, breaking-change labels, or review approval.

When the diff contains independent changes, provide suggested separate messages or one accurate combined message if that grouping was requested. Do not force a question just because two wordings are possible. Ask only if a material factual ambiguity prevents an accurate message, and provide the supported portion first.

Use artifact references only when task context or inspected content establishes the association and repository convention supports the footer. If `.claude/artifacts/{designs,plans,fixes}/` exists, it is optional context; omit unrelated or uncertain references without blocking message generation. The presence of one artifact or a similar slug is not sufficient evidence.

## Output and boundaries

Return the paste-ready message in a code block, with a short scope note only when needed. Do not add a review checklist or claim the code is ready. Preserve the working tree and index: no file edits, `git add`, `git commit`, or `git stash`.

If the user's request is to perform a commit, continue through the authorized commit workflow rather than misrouting it into message-only mode. Use `dev-code-review` when available and required, or equivalent review; message generation itself does not require asking the user to waive review.

## Multi-Agent Note

Message generation normally needs no separate agent. The main agent can use inspected diff and history directly; in a larger task, preserve the reviewed commit scope. See `docs/multi-agent-policy.md` when this repository is available; standalone use needs no external skill or policy file.
