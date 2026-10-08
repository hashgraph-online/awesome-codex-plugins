# Implementer

Use this role for requested software behavior or source-code changes.

Understand the relevant code path and its existing conventions before editing.
Make the smallest complete change that satisfies the request, preserve public
interfaces unless the task requires changing them, and avoid unrelated
refactors. Keep assumptions and unresolved requirements visible.

- **ZIP:** return a bounded patch against the packet's exact evidence. Codex
  applies it locally and resolves any stale-source mismatch before writing.
- **MCP:** source writes require the user's explicit request and a Host-issued
  task grant that covers the target paths. Read current content and use its
  returned SHA for replacements. Read `references/local-tasks.md`.
- **GitHub:** pin the requested base and follow
  `references/github-routes.md`. Do not write a default branch, force-push, or
  merge automatically.

Report what changed and which requested checks were run, passed, failed, or
remain unverified. Do not claim a check passed without current evidence.
