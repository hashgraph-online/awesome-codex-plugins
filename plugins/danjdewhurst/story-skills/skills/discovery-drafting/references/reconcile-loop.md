# The Reconcile Loop

The reconcile loop is the core discipline of discovery drafting: after each
discovered chapter, extract what the chapter invented, reverse-outline it,
diff it against the bible, and reconcile. This is what makes pantsing
compatible with a markdown-first story bible — the bible is maintained
*after* the prose, not before.

## The loop (run after every chapter, before the next)

### 1. Extract new entities and promises

Treat the finished chapter like `story import` treats a manuscript:

1. Read the chapter prose and list every new **entity candidate**: characters,
   locations, factions, artifacts, systems/rules the chapter introduced or
   implied. Present candidates to the user for approval, exactly as the
   import workflow does — do not auto-create bible files.
2. List every new **promise** (setup needing payoff) and **question**
   (mystery raised). Check each against `continuity/promises/` and
   `continuity/questions/` for duplicates before creating new records.

### 2. Reverse-outline the chapter

Write the outline the chapter *would* have had if it had been planned —
after the fact:

- One line per scene: what the scene accomplishes, POV, location.
- State changes the scene made (feeding the scene record in `scenes/`).
- Promises planted, questions raised, foreshadowing laid.

Store the reverse outline in the chapter file above the prose (same
convention as chapter-writing's approved outlines) and create/update the
`scenes/` records.

### 3. Diff against the bible

Compare the reverse outline and entity candidates against the existing
bible:

- **New** — genuinely new elements: create the files (after user approval).
- **Contradiction** — the chapter says X, the bible says Y: one of them is
  wrong. Decide with the user which one, then fix the loser.
- **Enrichment** — the chapter deepens something the bible sketched: update
  the bible file (character voice detail, location texture, system rule).
- **Dangling** — a promise or question with no plausible payoff yet: keep
  it open in the ledger, but flag it in the chapter notes so the next
  reconcile loop checks it again.

### 4. Reconcile

Apply the diff: update bible files, `continuity/state.md`,
`plot/timeline.md`, and the chapter/scene records. Then run `story reindex .`,
`story wordcount . --write`, and `story check .` to rebuild the registries and
check the result. The two legal outcomes
are **update the bible** (the chapter discovered something true) or
**revise the chapter** (the chapter broke something true). "Leave both"
is not an outcome — unresolved diffs become continuity bugs.

## Post-hoc chapter notes

After the loop, add a `## Chapter Notes (post-hoc)` section above
`## Chapter Text`. `story wordcount` and `story export` count everything
after `## Chapter Text` as prose, so notes and TODOs below that heading
ship in the manuscript. Record:

- What was discovered (new entities, rules, relationships).
- What was cut or left dangling.
- Any open questions for future chapters.

These notes are the project's memory of *why* the bible looks the way it
does. Future agents read them before drafting the next chapter.

## The `mode: discovered` flag

Every chapter drafted in discovery mode carries this frontmatter:

```yaml
mode: discovered
```

The flag tells the CLI and later audits that the reconcile loop is a
**required step** for this chapter: a discovered chapter without post-hoc
notes and a completed diff is unfinished work, not a stylistic choice.
`story next` and `story doctor` flag any `mode: discovered` chapter with no
`## Chapter Notes (post-hoc)` heading as `[P1] Reconcile discovered
chapters: ... for <ids>`; the action clears once the heading is present.
When `story.md` uses `draft-mode: discovered`, treat missing post-hoc notes on
any chapter as a maintenance finding. Chapters written outline-first in a mixed
project use `mode: outlined` (or omit the field).

## Reconcile checklist (per chapter)

- [ ] Entity candidates extracted and user-approved; new files created
- [ ] New promises/questions checked for duplicates, then recorded
- [ ] Reverse outline written into the chapter file
- [ ] Scene records created/updated with state changes
- [ ] Diff run: every contradiction resolved (bible updated OR chapter revised)
- [ ] `continuity/state.md` and `plot/timeline.md` updated
- [ ] Post-hoc notes appended; `mode: discovered` in frontmatter
- [ ] `story reindex .`, `story wordcount . --write`, and `story check .`
