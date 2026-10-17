# Session Mining

Use this when asked to turn prior AI work, chat history, or project lessons into a reusable skill or durable workflow.

## Principles

- Mine repeated patterns, not raw chat.
- Keep private code, screenshots, stack dumps, and proprietary details out of reusable public artifacts.
- Separate collaboration preferences from architecture rules.
- Put each durable rule in the artifact that owns it.
- Treat memory as a lead; verify live files when the fact can drift.

## Structural Parsing

For Codex-style JSONL sessions:

- `session_meta.payload.id` identifies the session.
- `session_meta.payload.cwd` and `turn_context.payload.cwd` identify repo-scoped turns.
- `response_item.payload.type == "message"` and `role == "user"` contains user prompts.
- Filter out injected `AGENTS.md`, environment blocks, plugin lists, base64 images, and tool metadata.

Use native tools if shell wrappers distort counts:

```bash
/usr/bin/find /path/to/sessions -name '*.jsonl' | /usr/bin/wc -l
```

## Classification Buckets

- Collaboration/status/tone -> collaboration skill or repo instructions.
- Screenshot/UI/repeated visual failure -> runtime-owner proof and UI workflow.
- Visual source asset rules -> visual asset workflow.
- Structural C#/refactor rules -> modular architecture workflow.
- Validation/runtime doubts -> validation workflow.
- Cleanup/deletion -> cleanup workflow.
- Gameplay balance/content -> content/system workflow.
- Git/publish -> git workflow.

## Rule Update Workflow

1. Count and describe scan scope.
2. Filter to relevant repo/project turns unless user asks cross-project.
3. Group repeated failures and successful fixes.
4. Convert each lesson into a short reusable rule.
5. Patch only the owning artifact.
6. Validate docs/skill frontmatter and `git diff --check`.
7. Report scan scope, changed artifacts, and what was intentionally excluded.

## Do Not Include

- raw private prompts
- proprietary source code
- base64 images
- secrets, tokens, email, account IDs
- one-off user frustration as a permanent rule without repeated evidence
- stale runtime maps that should live in current architecture docs
