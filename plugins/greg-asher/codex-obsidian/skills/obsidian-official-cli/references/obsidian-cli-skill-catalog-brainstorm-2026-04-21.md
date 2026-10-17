# Skill Catalog Brainstorm (2026-04-21)

Goal: represent the full official Obsidian CLI surface in this plugin while keeping skills narrow, explicit, and safe.

Status update (implemented):
- dedicated `obsidian-cli-workspace-and-navigation` was added
- explicit invocation remains default across all shipped skills
- Publish remains available only through the dedicated `obsidian-cli-sync-and-publish` skill with explicit guardrails and capability probing

## Design constraints

- Keep the plugin focused on local official desktop `obsidian` CLI workflows.
- Keep skills narrow and easy to reason about.
- Preserve exact-path mutation safety for note content operations.
- Add stronger safety for high-impact surfaces (Sync, Publish, plugin/theme changes, developer eval).

## Approach options

## Option 1: One expanded mega-skill

Description:
- Keep a single `obsidian-official-cli` skill and broaden command coverage to all command families.

Pros:
- Lowest file count.
- Easy discoverability for users who always invoke one skill name.

Cons:
- Routing gets noisy and less predictable.
- Safety policy must juggle low-risk note edits and high-risk admin/dev actions in one place.
- Harder to maintain and test.

## Option 2: Strict domain split (many small skills)

Description:
- Split by command family into many sibling skills.

Pros:
- Very clear boundaries.
- Easier targeted evals and maintenance.

Cons:
- More coordination overhead.
- Higher risk of missed cross-skill workflows unless chain guidance is first-class.

## Option 3 (recommended): Layered split with orchestration recipes

Description:
- Keep one core note-ops skill.
- Add a limited set of sibling advanced skills grouped by operational risk.
- Publish explicit pipeline recipes that chain skills safely.

Pros:
- Preserves simple entry point for common note workflows.
- Separates risky admin/dev surfaces with dedicated safeguards.
- Keeps catalog manageable while covering full CLI functionality.

Cons:
- Requires up-front command ownership mapping.
- Needs disciplined references so recipes do not drift.

## Recommended skill catalog

## 1) `obsidian-official-cli` (keep, core note and knowledge ops)

Owns:
- files/note CRUD and targeting safety
- daily workflows
- search/search:context
- outline
- links graph checks
- tasks
- properties/aliases/tags
- templates
- history/diff

Primary safety model:
- exact `path=` for mutations
- read-only resolution before ambiguous mutations
- explicit target-mode reporting

## 2) `obsidian-cli-bases-and-bookmarks`

Owns:
- `bases`, `base:*`
- `bookmarks`, `bookmark`

Reason to split:
- Bases semantics and bookmark workflows are distinct from basic note editing and often used for structured/query-driven automation.

## 3) `obsidian-cli-runtime-admin`

Owns:
- plugins and restricted mode (`plugins*`, `plugin:*`, `plugins:restrict`)
- themes/snippets (`themes`, `theme:*`, `snippets*`, `snippet:*`)
- command palette introspection (`commands`, `command`, `hotkeys`, `hotkey`)

Reason to split:
- Runtime and customization actions are higher impact and need explicit confirmation policy.

## 4) `obsidian-cli-sync-and-publish`

Owns:
- Sync family (`sync*`)
- Publish family (`publish:*`)

Reason to split:
- Remote side effects and distribution steps require stronger guardrails and explicit intent checks.

## 5) `obsidian-cli-workspace-and-navigation`

Owns:
- vault/workspace/tab/navigation surfaces (`vault*`, `workspace*`, `tabs`, `tab:open`, `recents`, `open`, `random*`, `unique`, `web`, `wordcount`)

Reason to split:
- Session and UI-state navigation tasks differ from note content mutation and are useful for operator-centric automation.

## 6) `obsidian-cli-devtools`

Owns:
- developer command family (`devtools`, `dev:*`, `eval`)

Reason to split:
- Devtools/eval can introspect or modify runtime behavior and should be isolated with explicit dev-mode policies.

## Pipeline and chaining patterns (high-value)

## Pipeline A: Knowledge capture and triage

Intent:
- Capture idea -> enrich metadata -> add follow-up task -> validate graph links.

Chain:
1. `create` or `unique`
2. `property:set` and `tags`
3. `append` or `daily:append` with task
4. `backlinks` and `unresolved`

## Pipeline B: Research to structured extraction

Intent:
- Search corpus -> contextual read -> structured query output for downstream summarization.

Chain:
1. `search` or `search:context`
2. `read` and `outline`
3. `base:query` (format=json/csv/tsv)
4. optional `bookmarks` / `bookmark`

## Pipeline C: Plugin/theme development feedback loop

Intent:
- Reload plugin -> inspect runtime errors -> capture UI evidence.

Chain:
1. `plugin:reload`
2. `dev:errors` and `dev:console`
3. `dev:dom` / `dev:css`
4. `dev:screenshot`

## Pipeline D: Sync and publish release gate

Intent:
- Verify state before publishing and avoid accidental remote drift.

Chain:
1. `sync:status`
2. publish capability probe, then `publish:status` if supported
3. `diff`/`history` on changed files
4. `publish:add changed` if supported
5. `publish:list` and optional `publish:open` if supported

## Pipeline E: Vault hygiene sweep

Intent:
- Reduce graph entropy and stale task carryover.

Chain:
1. `orphans`, `deadends`, `unresolved`
2. `tasks` (todo + verbose)
3. `search:context` on unresolved terms
4. `move`/`rename`/`property:set` fixes

## Proposed implementation order (if approved)

1. Expand inventory references and command ownership docs. (done)
2. Split risky surfaces first: create `obsidian-cli-devtools` and `obsidian-cli-sync-and-publish`. (done)
3. Add `obsidian-cli-runtime-admin`. (done)
4. Add `obsidian-cli-bases-and-bookmarks`. (done)
5. Add `obsidian-cli-workspace-and-navigation`. (done)
6. Tighten plugin manifest descriptions and eval prompts for the multi-skill catalog. (done)

## Resolved decisions

- Publish is handled only by the dedicated `obsidian-cli-sync-and-publish` skill and only when publish commands are supported in the local CLI.
- `eval` remains devtools-only with explicit risk framing.
- `open`, `random`, and `web` live in `obsidian-cli-workspace-and-navigation`.
