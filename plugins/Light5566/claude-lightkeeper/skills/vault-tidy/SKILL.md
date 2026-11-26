---
name: vault-tidy
description: Work the knowledge vault's attention signals — notes that grew too long or collected too many Gotchas, notes that went stale while their code kept moving, stubs whose files keep changing, Where-it-lives paths and link reasons that no longer match the code. Use whenever the user says "tidy the vault", "the notes need attention", "consolidate the gotchas", "summarise this note", "clean up the vault", when `_meta/Attention.md` lists something, when `vault status` or the session primer says notes need attention, or as the periodic pass after a vault-sync.
---

# Vault tidy: working the attention list

A vault that is written to on every change grows the way code grows: Gotchas pile up, History gets long, a note goes quiet while its files keep moving. `vault check --write` regenerates `_meta/Attention.md` with the signals; this skill is what you do about them. A tidy never changes what a note means. It makes the same facts shorter, truer and easier to find.

## Start

```bash
vault status                     # attention list, coverage and stale counts in one screen
cat <vault>/_meta/Attention.md   # the full list with the reason for each item
```

Work the top items, or the note the user named. The thresholds come from `tidy` in `_meta/vault.json`: `max_words` (default 4000), `max_gotchas` (20), `stale_days` (60), `churn_commits` (5).

Before touching a note, read it in full, and run `vault find <note>` to see who links to it and why. Record its word count and its number of *Gotchas* bullets; you will report both afterwards.

## Per signal

### Consolidate: too long, or too many Gotchas

- **Regroup and dedupe the Gotchas.** Cluster bullets about the same mechanism under one bullet with sub-points. Merge duplicates. Keep **every specific fact**: the class and method, the value, the symptom. Never drop a trap. If the code no longer does what a Gotcha warns about, verify that against the current code, then move the bullet to *History* as one line naming the release that fixed it, so the fact survives.
- **A Gotcha that is really a why moves to `6 Decisions`.** If a bullet explains a deliberate choice rather than a trap, write a Decision note from `_templates/Decision.md`, link it from the module's *Connects to* with a reason, and replace the bullet with a one-line pointer.
- **Fold old History.** Keep the entries for the last five releases. Replace everything older with one line: `- Earlier history: see [[Vault Changelog]] — this note's changes before vX.Y.Z`.
- **Tighten *How it works*** only by removing repetition and dead detours. If a paragraph describes a code path that no longer exists, that is a re-verify, not a trim.

### Re-verify: stale while its code moved

The note's `updated` is older than `stale_days` and its files have changed since. Do not bump `updated` on a hunch.

1. `git -C <repo> log -p --since=<updated> -- <the Where-it-lives paths>` and read the diffs.
2. Fix what changed: *How it works*, *Gotchas*, *Config & flags*, the *Where it lives* rows, the link reasons.
3. If nothing in the note is wrong, say so in the commit message ("re-verified against `<sha>`, no change") and bump `updated`. Bump it **only after reading**.

### Promote: a stub whose files keep changing

The module is clearly active and nobody has written it up. Write it from the code, not from memory: fill *How it works* in the order the code runs, add at least two reasoned links, list the real Gotchas you can see in the code and its tests, set `depth: full`, bump `updated`. If you can't learn enough to fill it honestly, leave it a stub and say what you did learn.

### Path rot: a Where-it-lives path no longer exists

Find where the code went (`git log --follow`, or grep for the class name). Fix the row to the real file, or delete the row if that surface is gone. If the whole module is gone, set `status: deprecated` and say so in *What it is*. Never delete the note.

### Link rot: a reason names a `Class::method` that no longer exists

Read the current code. Either the method was renamed (fix the reason) or the relationship is gone (remove the link on **both** notes and say why in the commit). A link whose reason is false is worse than no link.

## Finish

```bash
vault check --write        # must exit 0; Attention.md shrinks accordingly
git -C <vault> add -A && git commit -m "tidy: Payment (Gotchas 31→14, 5100→3300 words); re-verified Order"
```

Show the user a before/after line per note: word count and Gotcha count. Name every note in the commit message; `vault log <note>` and `Vault Changelog.md` are built from it.

A tidy never changes meaning. If you find yourself deciding how something works, stop: that is a re-verify, and the code decides.

If `_meta/local.md` exists in this vault, read it now and follow it. It holds this vault's own rules, and where they conflict with the generic ones above, local.md wins.
