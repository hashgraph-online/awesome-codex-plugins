# README Validation

**Purpose**: Quality gates before declaring the README done.

## Evidence checks

- [ ] Every install command appears in the repo's manifest, lockfile, or existing docs.
- [ ] Every script invocation (`npm run build`, `cargo test`, `pnpm dev`, etc.) exists in the actual scripts/tasks file.
- [ ] Every command in the CLI section maps to an actual command handler in source.
- [ ] Every API or exported symbol in the usage section is exported from the entry point.
- [ ] Every file path mentioned exists in the repo.
- [ ] Every linked URL points to a real local file or a documented external resource.

## Shape checks

- [ ] Project type is recorded in the discovery profile.
- [ ] Section selection matches the type policy in `rules/readme/section-design.md`.
- [ ] Order follows the default unless the project explicitly uses another.
- [ ] Quickstart is reachable within the first screen on a typical viewport.
- [ ] Project structure section is included only when non-trivial.

## Language checks

- [ ] README prose is Korean by default, or uses another language only because the user requested it or an existing target README required preservation.
- [ ] Terminology matches the codebase (folder, command, and config names are exact).
- [ ] No marketing fluff; capability is stated, not exaggerated.
- [ ] Sentence-case or Title-case headings are used consistently.

## Anti-fabrication checks

- [ ] No invented commands, scripts, env vars, or APIs.
- [ ] No badges without a real source.
- [ ] No screenshots referenced without a real file.
- [ ] Unknowns are marked with `<!-- TODO -->` or an explicit "verify with maintainer" note.

## Refactor-mode checks

- [ ] Existing accurate sections are preserved.
- [ ] Stale commands and dead links are removed or replaced.
- [ ] Diff against the prior README is small enough to review.

## Update-mode checks

- [ ] Only the requested or implied sections were touched.
- [ ] Surrounding sections were left intact.
- [ ] If a change-history section already exists, a dated entry was appended.

## Completion summary

Report the following at the end:

```text
Mode: [create | refactor | update]
Project type: [cli | library | web-app | monorepo | plugin | framework | docs-site | service]
Files inspected: [list of paths actually read]
Sections changed: [list of headings created or rewritten]
Unknowns flagged: [count + locations of <!-- TODO --> markers]
```

If any check fails, fix the README rather than relaxing the check.

## Sources

> No external sources; content checked 2026-09-21.

This rule states the repository-local validation gates for README authoring. It makes no external claim, so no external source is cited.
