---
name: book-init
description: "Phase 0: Onboarding. Define genre, reader, language, scope, and voice; capture the author's voice fingerprint; index source material; generate PRD.md and STYLE.md."
argument-hint: "[project-dir]"
---

# Phase 0: Onboarding

Goal: enough shared understanding that every later agent writes the same book the author imagines. The two documents produced here, `PRD.md` and `STYLE.md`, are read by every agent on every task. Vague answers here become vague chapters later.

Read `${CLAUDE_PLUGIN_ROOT}/skills/loom/quality-bar.md` first.

## Interview

At most 3 questions per round, at most 4 rounds. Ask only what cannot be inferred from what the author already said or from materials they pointed to. If the author gives a rich brief up front, skip straight to confirmation.

**Round 1 — What and for whom**
- Genre and subgenre (fiction/nonfiction/technical/screenplay/poetry/game/academic; for fiction, the shelf it sits on: 스릴러, 로맨스, literary, SF, etc.)
- The reader: one or two concrete people, not demographics. "A 34-year-old backend engineer who has shipped LLM features and been burned by them" beats "developers."
- Language, and if Korean or Japanese, register conventions (존댓말 narration? 문어체?).

**Round 2 — Scale and materials**
- Length. Offer the genre norm from quality-bar.md language notes; let the author adjust.
- Existing material: notes, outlines, prior drafts, research, code, an Obsidian or alcove vault. Where does it live?
- Timeline and any hard constraints (series continuity, publisher spec, trim size).

**Round 3 — Voice**
- Ask for a voice sample: 500-2,000 words of the author's own prose in the register they want, or 2-3 published authors whose voice is the target, or both. If neither exists, offer to write three 200-word openings in different voices during ideation and let them choose.
- Tone words the author would use and words they would reject.
- Anything the author never wants to see (patterns, words, tropes, structures).

**Round 4 — The promise** (can merge into Round 1 for experienced authors)
- What does the reader have at the end that they did not have at the start? One sentence. This becomes the north star for beta-reader.

## Voice fingerprint

From the voice sample or named authors, write a **Voice Fingerprint** section in `STYLE.md`. This is the single most important input to chapter-writer. Be specific and quantitative where possible:

- Sentence length: typical range, how short the shortest go, how often a long sentence appears, what a long sentence is for in this voice
- Paragraph shape: one-liners common or rare; longest paragraphs do what
- Diction register: plain/literary/technical; Latinate vs. Germanic (English); 한자어 vs 고유어 balance (Korean); slang, profanity, jargon policy
- Figurative density: metaphors per page; what domains they draw from; what the voice never compares things to
- Narrative distance (fiction): how close to the POV character's thoughts; free indirect style or not
- Humor: kind, frequency, targets
- Dialogue conventions: tags (said only? none?), beats, dialect, 존댓말 map for Korean
- Signature moves: two or three things this voice does that another would not
- Three short quoted examples from the sample (or reconstructed exemplars if the author named published writers; never quote living authors at length)

If the author supplied a sample, also store it verbatim under `## Voice Sample` in `STYLE.md`.

## Source indexing

If the author has materials, scan them now (`find`, alcove `search_project_docs`/`search_vault` if available, Obsidian tags). Write `sources/INDEX.md`:

```markdown
# Sources

| ID | Path or URL | Type | What it contains | Trust | Use for |
|----|-------------|------|------------------|-------|---------|
| S01 | sources/interview-kim.md | interview transcript | ... | primary | ch03, ch07 |
```

Trust levels: primary (author's own data, interviews, code they wrote), secondary (published, citable), tertiary (blogs, forums; use for leads only). Every factual claim in nonfiction drafts must cite an ID from this index or a verified URL. Copy or symlink materials into `sources/` when practical.

## Outputs

**`PRD.md`** — YAML frontmatter (`title`, `genre`, `subgenre`, `language`, `target_length`, `count_unit`, `chapters`) then sections: Identity, Reader (personas), Reader Promise, Scope, Constraints, Source Map (summary of INDEX), Success Criteria (measurable, including "readiness PASS from beta-reader"), Open Questions.

**`STYLE.md`** — Voice Fingerprint, Voice Sample (if any), Language Rules, Formatting Rules, Prohibited (author's list + quality-bar.md taxonomy reference), Dialogue Conventions, Genre Conventions (pointer to genre skill with any overrides). Leave a `## Voice Lock` heading with "pending" so the router knows the lock has not happened.

**Directories** — `drafts/ edits/ publish/ sources/ .velith/`. Offer `git init` if the directory is not a repository; the pipeline snapshots drafts before rewriting stages regardless.

## Gate

`PRD.md` and `STYLE.md` exist. STYLE.md has a Voice Fingerprint with at least five specific attributes. PRD.md has a one-sentence reader promise. Source index exists if the author has materials.

## Post-completion

```bash
node ${CLAUDE_PLUGIN_ROOT}/velith.mjs scan [project-dir]
```
