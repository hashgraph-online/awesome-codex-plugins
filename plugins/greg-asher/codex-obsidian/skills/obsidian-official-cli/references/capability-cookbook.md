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

If it fails specifically because `Projects/` is missing, then create the folder locally and retry:

```bash
mkdir -p "Projects"
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

If it fails because `Archive/Projects` is missing, then create that folder locally and retry:

```bash
mkdir -p "Archive/Projects"
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
