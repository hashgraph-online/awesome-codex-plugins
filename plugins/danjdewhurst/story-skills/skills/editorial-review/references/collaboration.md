# Collaboration and Backups

The markdown model suits collaboration through version control: every
change is a diff, every contribution is attributable, and conflicts are
visible. It does not support real-time co-editing (two people typing in
the same file at the same moment); that is out of scope. Recommend
taking turns per file through branches, and a shared document tool
outside the project for live brainstorming.

## Multi-author books

List every author in `story.md`:

```yaml
authors:
  - Jane Doe
  - Sam Rivera
```

Use `authors` for multi-author books; `author` still works for a single
author. `story build . --format metadata` lists the authors on the
retailer sheet. Agree the credit order with the authors, and
never add a name the users have not confirmed.

Agree and record in `story.md`'s `## Notes`:

- **Who owns what.** POV characters, chapters, or arcs per author.
- **Who decides canon.** One author, both by agreement, or per domain
  (one owns the magic system, the other the politics).
- **One voice or several.** Alternating POV books can keep distinct
  voices; a single-voice book needs one final line-editing pass by one
  person against `style-sheet.md`.

## Git workflow

1. One repository per book (or per shared world plus one per book, linked
   with the series fields).
2. `main` holds the agreed manuscript. Each author works on a branch:
   `jane/chapter-07`, `sam/magic-system`. One chapter or one entity
   change per branch keeps reviews small.
3. Merge through pull requests. The other author reviews story changes;
   the `story-checks.yml` template from `templates/github/` runs
   `story check` (validate, links, and continuity) on every pull request.
4. Update branches by rebasing onto `main` before merging, and push a
   rebased branch with `--force-with-lease`, never plain `--force`.
5. Registries (`_index.md` files) and word counts are generated: when two
   branches conflict there, take either side and run `story reindex .`,
   `story wordcount . --write`, and `story check .` rather than
   hand-merging.
6. Conflicts in chapter prose or entity files are creative decisions;
   show both versions to the users and let them choose.

The agent never commits, pushes, rebases, or changes branches without the
user's approval.

## Shared worlds

For a world several authors write in, protect canon with a
`CODEOWNERS` file (in `.github/`, `docs/`, or the repository root on
GitHub) so changes to shared entities require review by their owner:

```text
# Canon owners for the shared world
/worldbuilding/systems/   @jane-doe
/worldbuilding/factions/  @sam-rivera
/glossary/                @jane-doe @sam-rivera
/characters/              @jane-doe @sam-rivera
/style-sheet.md           @jane-doe
```

CODEOWNERS only enforces review when branch protection on `main`
requires code-owner review; tell the user to enable it in the repository
settings. Use `story names '<candidate>' --path .` before adding a name,
so authors do not create clashing characters or places (it exits 1 on an
exact clash and warns about look-alikes; pass each word of a multi-word
name separately to check it for look-alikes too), and run
`story series .` across linked books.

## Backups

A local folder is not a backup. Set one up the day the project starts:

1. A git remote (a private repository on GitHub, GitLab, or similar).
   Ask the user to create it and confirm visibility is private.
2. Commit and push after every writing or editing session, with the
   user's approval. A session's work that exists only on one laptop is
   one spilled coffee from gone.
3. Tag milestones (`draft-1`, `sent-to-editor-1`) and push the tags.
4. Optionally, a second copy outside git (a cloud-synced folder or
   external drive) of the whole project, refreshed weekly. Do not place
   copies inside the project, where `story` commands would scan them.
5. Built files in `dist/` are disposable and are not a backup of the
   manuscript; the markdown is.

Remind the user at the end of a session if there are uncommitted or
unpushed changes (`git status`), and ask before committing or pushing.
