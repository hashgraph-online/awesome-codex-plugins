# Capability Cookbook

This file holds concrete examples so `SKILL.md` can stay focused on routing and operating policy.

## Exact-path read

```bash
obsidian vault="My Vault" read path="Projects/Kestrel.md"
```

Target mode:
- `exact-path`

## Broad note lookup before mutation

Use a read-only resolution step first:

```bash
obsidian vault="My Vault" search query="Kestrel"
```

Then switch to an exact path for the mutation:

```bash
obsidian vault="My Vault" append path="Projects/Kestrel.md" content="\n- [ ] Follow up"
```

If multiple candidates exist, keep resolving before the mutation rather than picking one silently.

## Create with missing parent folder

Try the CLI path first:

```bash
obsidian vault="My Vault" create path="Projects/Brief.md" content="# Brief\n\nInitial notes"
```

If it fails specifically because `Projects/` is missing, inspect actual state first. Set `RESOLVED_VAULT_ROOT` from the verified canonical target vault mapping, never CWD; validate containment including symlinks. Only then create the folder locally when permitted, recheck collision state, and retry once:

```bash
mkdir -p "${RESOLVED_VAULT_ROOT:?resolve the target vault root first}/Projects"
obsidian vault="My Vault" create path="Projects/Brief.md" content="# Brief\n\nInitial notes"
```

Keep the note-content creation itself on the official CLI path.

## Structured backlinks

```bash
obsidian vault="My Vault" backlinks path="Projects/Kestrel.md" format=json
```

Use structured output whenever the command supports it.

## Structured tasks

```bash
obsidian vault="My Vault" tasks verbose format=json
```

## Exact-path property update

```bash
obsidian vault="My Vault" property:set path="Projects/Kestrel.md" name=status value="draft" type=text
```

## Daily-note append

```bash
obsidian vault="My Vault" daily:append content="- [ ] Follow up with design team"
```

Target mode:
- `daily-note`

## Vault structure support before CLI move

Try the CLI path first:

```bash
obsidian vault="My Vault" move path="Projects/Kestrel.md" to="Archive/Projects/Kestrel.md"
```

If it fails specifically because `Archive/Projects` is missing, resolve `RESOLVED_VAULT_ROOT` from the verified target vault mapping and validate containment including symlinks. Inspect state, create the parent when permitted, recheck, and retry once:

```bash
mkdir -p "${RESOLVED_VAULT_ROOT:?resolve the target vault root first}/Archive/Projects"
obsidian vault="My Vault" move path="Projects/Kestrel.md" to="Archive/Projects/Kestrel.md"
```

Use this kind of support step for safe vault structure work, while keeping note operations on the CLI path.

## History inspection before diff

```bash
obsidian vault="My Vault" history path="Projects/Kestrel.md"
obsidian vault="My Vault" history:read path="Projects/Kestrel.md" version=1
obsidian vault="My Vault" diff path="Projects/Kestrel.md" from=2 to=1
```

Only run `diff` after `history` shows the versions you plan to compare.

## Reviewed section revision

Request: “Update Risks in Projects/Atlas.md in Work using these findings.”

Resolve Work's stable identity/root, read Atlas, inspect outline and exact Risks span, and show the minimal diff. Duplicate Risks headings require context/selection. Use `scripts/revision.py` relative to the loaded core skill to build the candidate from the snapshot and unique exact span. This helper writes nothing. Follow [authoring-and-revision.md](authoring-and-revision.md) for approval, capability/lossless transport checks, whole-file overwrite disclosure, stale-state recheck, and complete post-write verification. If overwrite/transport is unavailable, return the diff and specific limitation; do not silently append a second Risks section.

## Safe create/append retry

Keep before and expected state. After a lost response, reread the pinned vault/path: expected content means skip the duplicate effect; unchanged before means retry only the same approved action after rechecks and proof that the original operation is no longer in flight; partial/unexpected content means stop and reconcile. A failed read is not proof that a destination is absent. See the shared authoring contract for step statuses and recovery.
