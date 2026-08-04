# Multi-module workspace (experimental)

Use this protocol only when one change spans multiple modules. Keep it small: Praxis coordinates the current change; it does not become a project-management system.

## Mode marker

Multi-module mode is **declared, not remembered**. Two carriers hold it:

1. The per-turn triage announcement: `topology=multi-module`.
2. The declaration block at the top of the coordinator spec (created at `design`) and the workspace plan (created at `plan`):
   ```
   topology: multi-module
   change-set: <topic-id>
   coordinator: <repo path>
   repos: <repo paths>
   ```
   The workspace plan adds module plan paths and the integration task.

This declaration is the on-disk source of truth. A freshly loaded skill reads it to re-establish mode - never rely on session memory. If neither the announcement nor a declared coordinator spec/plan says `multi-module`, you are in single-module mode.

## Minimal model

- **Coordinator** — an existing repository chosen by the user. It owns the cross-module spec/plan and the change manifest.
- **Module** — a code unit with its own local spec, plan, tests, and implementation.
- **Change set** — a stable topic ID shared by the current change's artifacts and commits.
- **Revision set** — the exact repository commits tested together.

The coordinator spec and workspace plan each open with the declaration block above, which serves as the change manifest - listing this change's repositories, modules, relative paths, shared contract (if any), and integration check. Resolve paths at runtime. Define shared contracts once in the coordinator; module specs reference them.

In a monorepo, the coordinator is the root and module docs stay with modules. In a multi-repo change, docs stay in their owning repos and each repo gets its own commit. No project registry or global status database.

## Minimal lifecycle

`prepare → implement → sync docs → test modules → integrate → record revisions → archive`

The only completion checks are:

1. Code changes have matching module-document updates.
2. Every participating repository has a known commit.
3. The recorded revision set passes the coordinator's integration acceptance.

No percentages or global state machine. Use only `blocked` and `partial-commit` when needed.

## Safety

- Inspect each repo before editing. A missing repo, red baseline, or unrelated dirty change blocks the change. Do not clone, reset, rebase, discard, or absorb changes automatically.
- IDE visibility does not grant write authority. Edit or commit only registered repositories.
- Do not add repos after implementation starts; update the manifest and plans first.
- Put the change-set ID in branch names and linked commit subjects, e.g. `[praxis:checkout-v2]`.

## Integration and commits

1. Finish module tests and sync module docs.
2. Run integration acceptance against the current repository combination.
3. For multiple repositories, commit in dependency order and record each SHA in the coordinator manifest; commit the coordinator last.
4. If a commit fails, stop, report committed/uncommitted repos, and preserve all work. Repair or roll back only with explicit authority.

Cross-repo commits are not atomic. The revision set is the reproducibility boundary.

## Concurrent changes

Multiple change sets may share a repo. Give each its own branch/worktree. Stop only for an overlapping edit or shared-contract conflict; record and resolve it in the affected plan.

Use branches for implementation. Fixed-SHA detached checkouts are valid for read-only integration, not commits.

## Tool scope

Harnesses launch from a single working directory. Semantic indexing (code graph, symbol search) only covers the coordinator repo — sibling modules at `../` paths are not indexed. File tools (`read`, `grep`, `glob`) still work across repos with relative paths.

When dispatching a subagent to a module repo, note the repo path and that semantic tools may need an explicit project parameter. If the harness has no cross-repo tooling, fall back to file-level search.

This is a harness limitation, not a Praxis defect.
