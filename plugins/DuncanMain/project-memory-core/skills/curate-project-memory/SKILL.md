---
name: curate-project-memory
description: Give Codex lasting project context in a local Obsidian-compatible Markdown vault. Use when a user asks PMC to set up or connect the project's Obsidian vault, scan or explain a codebase, create a Project Home, remember a decision, constraint, discovery, procedure, debugging lesson, or current state, recall what Codex already knows, prepare a handoff, check whether notes are stale or contradictory, relate code to knowledge, keep something session-only, export or share reviewed context, or resume work from existing project notes.
---

# Curate Project Memory

Use conversation as the interface. Do not ask the user to run commands or edit configuration manually. Use Codex's normal file tools and request narrowly scoped filesystem permission when needed.

## First-run experience

When the user invokes PMC and no project registration exists for the current repository, lead with a concise guided setup instead of describing the architecture:

1. Explain in one sentence: "PMC gives Codex lasting project context in an Obsidian vault you control."
2. Ask whether to create a new vault or connect an existing Obsidian vault. Ask only this one question first.
3. After that choice, ask for or confirm the vault path, infer the current repository, and propose a readable project name.
4. Complete the vault setup and project registration conversationally. Do not require the user to know commands, markers, folder layouts, or configuration formats.
5. Create useful initial notes rather than empty shells whenever the repository can be inspected safely.
6. At completion, state where the vault and project notes live, explain how to open the vault in Obsidian, and offer to scan the repository now.
7. End with these examples: "@PMC remember this", "@PMC what do we already know about authentication?", and "@PMC wrap up this task".

Do not overwhelm a first-time user with advanced features. Introduce context packs, health checks, exports, team review, and the companion only when relevant.

Read `references/project-profiles.md` when choosing registration defaults.

Read `references/local-similarity.md` before building or querying the optional machine-local similarity index.

Read `references/storage-and-portability.md` for setup or project registration. Read `references/automatic-orientation.md` when the user wants the vault added as a project source or wants future chats to load project notes without a prompt. Read `references/durable-note-policy.md` before promoting, changing, or removing knowledge. Read `references/note-structure.md` when creating notes. Read `references/context-packs.md` when orienting or resuming work. Read `references/knowledge-health.md` before auditing a vault. Read `references/code-traceability.md` when relating notes to source files. Read `references/branch-awareness.md` before promoting knowledge discovered on a branch or worktree. Read `references/drift-detection.md` before creating or running verification checks. Read `references/coverage.md` before assessing documentation coverage. Read `references/team-collaboration.md` before configuring shared-vault ownership or reviews. Read `references/exports.md` before creating a portable brief or audit artifact. Read `references/obsidian-companion.md` when installing, configuring, or responding to review actions from the optional Obsidian companion.

## Boundaries

- Operate only on local paths that the user selects or places in scope.
- Do not upload, transmit, or add telemetry.
- Do not request or capture complete raw chat transcripts.
- Store an optional concise session summary only when the user asks to wrap up or enables summaries.
- Exclude secrets, credentials, private keys, authentication cookies, and unnecessarily sensitive data.
- Treat the vault as curated knowledge, not a chat archive.
- Never contradict, delete, or supersede durable knowledge silently.
- Do not require Obsidian community plugins.
- If local filesystem access is unavailable, explain that setup requires a local Codex environment; do not pretend files were created.

## Set up a vault

Determine whether the user clearly requested a new vault or an existing vault. If ambiguous, ask one short question.

### New vault

1. Confirm the path and request permission if necessary.
2. Refuse to repurpose a populated non-Obsidian folder without explicit confirmation.
3. Create the selected folder and an empty `.obsidian` directory.
4. Create only the minimal shared structure from `references/note-structure.md`.
5. Create the machine-local configuration described in `references/storage-and-portability.md`.
6. Report the created paths and explain that the folder can now be opened in Obsidian.

### Existing vault

1. Confirm that the folder exists.
2. Treat `.obsidian` as evidence that it is an Obsidian vault.
3. If `.obsidian` is absent, explain that it appears to be a Markdown folder and ask before using it.
4. Preserve the existing organisation. Do not move or rename existing content unless asked.
5. Add project-memory notes incrementally and only where useful.

## Register a project

1. Infer the repository root from the current workspace when possible.
2. Ask for a project name and vault folder only when they cannot be inferred safely.
3. Create a stable lower-case project ID that does not depend on drive letters.
4. Store the absolute repository path only in machine-local configuration.
5. Store repository-relative code references in durable notes.
6. Create `Project Home.md`, `Project.md`, and `Current State.md` from the bundled templates when missing. `Project Home.md` is the attractive human-facing front door; `Project.md` remains the compact compatibility index used by existing workflows. Do not create empty directory forests.
7. Create `Inbox/Promotion Inbox.md`, `Handoff.md`, `Coverage.md`, and the useful Bases dashboards described in `references/note-structure.md` unless the user opts out.
8. Offer automatic project orientation as an opt-in. If accepted, follow `references/automatic-orientation.md` and preserve existing repository instructions.
9. Infer or ask for an optional project profile only when it improves initial coverage areas. Do not create empty folders from a profile.

## Create the initial project orientation

Trigger on requests such as "create an overview of this codebase", "scan this project", or acceptance of the setup offer.

1. Inspect the repository's primary README, package or build metadata, repository instructions, top-level structure, Git status, and a small number of entry points relevant to understanding the project.
2. Summarize what the project does, how it is organised, how to run or test it, its current state, important constraints, and likely next actions. Distinguish verified facts from inference.
3. Populate `Project Home.md`, `Project.md`, and `Current State.md`; create focused decision, constraint, discovery, procedure, or debugging-lesson notes only when evidence supports them.
4. Link useful notes from `Project Home.md` and keep it concise enough to scan quickly in Obsidian.
5. Report the evidence inspected and the exact vault files created or updated.

## Use the vault as a project source

For a Codex local project, guide the user through the one-time UI action: open **Edit project**, select **Add folder**, add the vault, and keep the code repository as the primary folder. Do not claim to have attached a folder through the UI.

Treat the vault as a secondary source folder. Read and edit only relevant notes. Secondary folders do not automatically contribute their own `AGENTS.md`, skills, or project configuration, so put automatic-orientation guidance in the primary code repository after explicit opt-in.

## Enable automatic project orientation

1. Confirm that the user wants relevant durable notes read at the beginning of future tasks for this repository.
2. Copy the managed block from `assets/agents-project-memory.md` into the primary repository's `AGENTS.md`; create that file only when necessary.
3. Replace the project ID token and preserve all unrelated instructions.
4. Do not include an absolute vault or repository path in `AGENTS.md`.
5. On future tasks, load `Project.md` and `Current State.md` first, then follow only relevant links.
6. If the vault is unavailable or permission is missing, continue safely and state that project-memory context was not loaded.

## Recognize markers

Interpret natural equivalents, not only exact prefixes:

- `Remember:` -> confirmed durable candidate.
- `Decision:` -> decision candidate with rationale and consequences.
- `Constraint:` -> requirement or constraint candidate.
- `Reference:` -> durable reference candidate.
- `Session only:` -> do not promote to durable notes.
- `Forget:` -> propose correction, removal, or supersession and require confirmation.

Treat these natural requests as first-class equivalents:

- `@PMC remember this` -> summarize the immediately preceding durable point and ask for confirmation when its scope is ambiguous.
- `@PMC remember the decision we just made` -> create or update a decision after conflict and evidence checks.
- `@PMC update the project status` -> propose a concise `Current State.md` update.
- `@PMC what do we already know about X?` -> build a focused context pack and answer with note links.
- `@PMC wrap up this task` -> follow the wrap-up workflow.

Markers never bypass secret filtering or conflict checks.

## Prompt for knowledge worth keeping

Do not rely on the user to remember a special marker. During ordinary project work, notice information that is likely to matter in a future task, especially:

- an accepted architectural or product decision and its rationale;
- a durable constraint, invariant, convention, or non-obvious requirement;
- a verified discovery that changes how the project should be understood;
- a reusable procedure, workaround, or operational lesson;
- a change that makes an existing durable note stale or incorrect.

At a natural checkpoint, ask one concise question: "This will matter in future tasks. Add it to the project's Obsidian vault?" Include a one-line summary of exactly what would be recorded. Do not interrupt for routine edits, speculative ideas, transient debugging output, or facts already captured. Batch multiple related candidates into one review prompt when practical.

If the user says yes, treat that response as an explicit durable marker and follow the normal conflict, branch, evidence, and secret checks before writing. If the user says no, keep it session-only and do not repeatedly ask about the same candidate. When wrapping up, always include a short separate list titled `Worth adding to the project's Obsidian vault` or state that no durable candidates were found.

## Promote durable knowledge

1. Extract only information likely to help future project work.
2. Read relevant existing notes before proposing a change.
3. Classify each candidate as create, update, duplicate, conflict, supersede, or session-only.
4. Add unmarked candidates to `Inbox/Promotion Inbox.md` using `assets/promotion-inbox.md`. Record the proposed operation, target, evidence, confidence, and conflict status without treating the candidate as durable truth. For a conflict, quote concise existing and proposed claims with separate evidence so the reviewer can compare both sides.
5. For an explicit marker, write after checking for conflicts unless the user requested review-only mode.
6. Ask before resolving a conflict, deletion, or supersession.
7. When reviewing the inbox, let the user approve, edit, reject, or defer each candidate independently. Follow the guarded lifecycle in `references/obsidian-companion.md` when applying an approved candidate, record the outcome, and keep rejected candidates out of durable notes.
8. Report the exact durable files changed.

Before promotion, inspect the repository branch and revision when Git is available. Treat branch-only discoveries according to `references/branch-awareness.md`; never present unmerged implementation as canonical released state.

## Build a context pack

1. Read `references/context-packs.md`.
2. Run `scripts/build_context_pack.py <project-folder> --query <task>` yourself to produce a deterministic candidate ranking; pass each relevant repository-relative path with `--code-path`.
3. Always inspect the project's `Project.md` and `Current State.md` when available, then inspect only the highest-value ranked candidates required for safe work.
4. Exclude rejected, deprecated, and superseded knowledge except when historical context is necessary.
5. State briefly which additional notes were loaded and why. Never load the entire vault by default.
6. If terminology mismatch leaves important knowledge undiscovered, offer the optional local similarity index from `references/local-similarity.md`; keep its generated index outside the vault and inspect every returned note.

## Trace code and knowledge

Use the schema in `references/code-traceability.md`. Store stable repository IDs and repository-relative paths, never drive-specific paths. When code changes implement or invalidate durable knowledge, propose reciprocal links or status updates through the Promotion Inbox. Answer "which decisions affect this file?" by running the context-pack builder with `--code-path` and verifying the returned notes.

## Review staleness and contradictions

Use the health checker for objective structural signals, then compare potentially affected claims with current code, configuration, tests, and accepted notes. Record suspected contradictions in the Promotion Inbox using `Existing claim`, `Existing evidence`, `Proposed change`, and `Evidence`. Do not choose a winner or rewrite canonical notes silently. Distinguish `stale`, `conflicting`, and `unverified`; a recent timestamp is not proof of correctness.

## Detect evidence drift

Read `references/drift-detection.md`. Add verification checks only for important claims that have stable, non-sensitive machine-verifiable evidence. Run `scripts/check_drift.py <project-folder> <repository-root>` yourself. Inspect failed checks, distinguish a changed implementation from a bad check, and place proposed corrections in the Promotion Inbox. Never auto-rewrite canonical knowledge from a failed check.

## Assess knowledge coverage

Read `references/coverage.md`. Run `scripts/knowledge_coverage.py <project-folder>` yourself, passing expected workstreams from Project metadata when needed. Update `Coverage.md` from `assets/coverage.md` with the results and links. Treat coverage as a navigation and review signal, not a performance score.

## Collaborate in a team vault

Read `references/team-collaboration.md`. Use one durable decision per file, stable `knowledge_id` values, explicit owners and reviewers, and contributor-specific inboxes when several people work concurrently. Never infer approval merely from a Git merge. Resolve semantic conflicts through reviewed supersession or correction, not by keeping both claims active.

## Export project knowledge

Read `references/exports.md`. Run the health checker first and stop if possible-secret findings remain. Run `scripts/export_project.py <project-folder> <output-file> --mode <onboarding|decision-log|audit|context>` yourself. For context mode, pass only paths already selected and inspected for the current task. Do not overwrite an existing export without the user's approval. Explain that exports are snapshots and do not update automatically.

## Interoperate with the Obsidian companion

Read `references/obsidian-companion.md`. Treat companion review actions as workflow state, not proof that a proposed semantic change has been applied. When asked to apply approved candidates, run `scripts/candidate_lifecycle.py` to verify the approval fingerprint and perform guarded state transitions, rerun current conflict and evidence checks, update canonical notes, and record `applied`, `conflict`, or `failed` with outcome metadata. Never assume approval resolved a conflict automatically.

## Check knowledge health

Run `scripts/check_vault_health.py <project-folder>` yourself when the user asks to audit, review, or check the vault. Do not ask the user to use a terminal. Interpret its JSON report using `references/knowledge-health.md`; inspect reported notes before proposing repairs. When the user wants portable or companion-visible results, run `scripts/generate_health_report.py <project-folder> <project-folder>/Health Report.md --project-id <id>` and include `--repository-root` when available. Never make destructive repairs automatically.

For "@PMC check this project's memory" or "check whether these notes are out of date", combine structural health with a focused evidence review:

1. Run the health checker.
2. Inspect `Project Home.md`, `Project.md`, `Current State.md`, active decisions, and unresolved Promotion Inbox items.
3. Compare claimed commands, paths, status, dependencies, and completed work with current repository evidence where safe.
4. Report stale information, contradictions, missing setup knowledge, broken links, completed actions still shown as active, and important repository changes not reflected in the vault.
5. Separate safe mechanical repairs from semantic changes. Ask before changing meaning, resolving conflicts, deleting, or superseding knowledge.

## Create a handoff brief

On wrap-up, project restart, or explicit handoff request, update `Handoff.md` from `assets/handoff.md`. Keep it one-page in spirit: objective, current position, recent work, accepted decisions, blockers, open questions, next actions, and relevant links. Treat it as a generated navigation aid, not a replacement for canonical notes.

## Wrap up

Trigger on requests such as "wrap up", "finish for today", or "summarize this session".

1. Summarize the objective, work completed, decisions, discoveries, changed files, open questions, and next actions.
2. Omit transient tool output, secrets, and unnecessary conversation detail.
3. If session summaries are enabled or requested, save the concise summary outside the Obsidian vault using the configured session-summary location.
4. Propose durable updates separately from the summary.
5. Apply only approved durable changes.
6. Update `Handoff.md` after approved durable changes when it would materially help the next session.
7. Never imply that a complete transcript was archived.

## Resume work

Read `Project Home.md`, `Project.md`, `Current State.md`, and only the relevant linked notes. Summarize current status, known constraints, unresolved questions, and likely next steps. Flag stale or contradictory notes instead of guessing which is correct.
