# Parking Lot

> Decisions for the owner. During a shift the agent parks here instead of asking — one short,
> plain-language entry per decision, written for a human.
> Known tasks do not belong here: the owner stages later work in `drafting-table.md`, and a bug a
> shift finds is fixed on that shift and recorded in `snag-log.md`. A fix that would change
> behaviour users rely on does belong here, with the default chosen and applied. Active approved
> work belongs in `punch-list.md`; timed Hunt orders belong in `work-orders.md`.

**Each entry** is one `- ` bullet below the rule: a sentence or two of context · the
production-grade default chosen so work could continue · why it was chosen. Wrapped and indented
lines belong to the bullet, and so do `Default:` and `Rollback:` lines under it. Archive files only
bullets: text written as a paragraph stays here for good, and Doctor names it.

**Dispositions:** `fixed`, `ignored`, `answered`, `rejected-because`, `accepted-tradeoff`.
An entry with no disposition is open and waits for the owner; Nightshift Start surfaces open entries
at the top of the next shift. The owner answers by appending ` · answered: <decision>` to the entry,
and Archive files it. A runtime `[notice]` closes the same way, with ` · ignored` once read. Never
delete an answered entry: the answer is the record Archive keeps.

A `Filed:` line points at answered history — follow it and search that file by topic or identifier.
Historical decisions are evidence, not fresh authorization. A broken pointer is reported in
`snag-log.md`; never guess or delete history.

---

(empty)
