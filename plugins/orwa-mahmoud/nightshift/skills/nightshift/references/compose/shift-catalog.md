# Shift catalog

The ready shifts Hunt offers. Each entry is a punch-list item, complete with its own contract and
Verify line — paste one into `## Items` by hand, or let Hunt assemble it for you.

**Entries live one per file in [`shifts/`](shifts/).** Read that directory; this page never lists
them. A catalog that enumerated its own contents would put every contributor in the same diff, and
the point of a file per shift is that two people can add one the same week without meeting.

Two endings exist, and every entry declares which it has in its title line:

- **Open-ended** — no natural end but the clock. It stays a single open box while its loop runs and
  closes at the whistle (or at convergence, where the entry says so). Hunt requires hours for
  these; a walkthrough may not start without a deadline.
- **Finite** — the work is a known list. It ends when the list is clear. Hours are optional: a cap,
  not a requirement.

Open-ended entries share the loop — scan → verify → fix behind the item gate → re-scan — and log one
line per cycle to `shift-log.md` (`cycle N · <scanned> · <found> · <fixed>`). They differ in the scan
and in the ending.

## Maintainer night

A preset, not an entry: for an open-source maintainer, compose
[`developer-onboarding.md`](shifts/developer-onboarding.md) then
[`documentation-drift.md`](shifts/documentation-drift.md) then
[`ci-warning-cleanup.md`](shifts/ci-warning-cleanup.md) then
[`release-readiness.md`](shifts/release-readiness.md), in that order, under one time budget. The
order carries the work: a stranger's clone is followed end to end, the documented claims that
walkthrough disproves are corrected, the build warnings still standing are cleared, and what
remains is measured against the release bar. Every entry keeps its own contract, discovery rules
and definition of done, and the composed shift ends when the four are clear or the budget does.
All four are finite, so hours here are a cap rather than a requirement: six is a workable budget
for the set, and the owner names the number. Guided may offer it as a preset line; it is
not a card, and Automatic still composes from the entries themselves.

**Adding an entry:** see [`catalog-recipe.md`](catalog-recipe.md) in this directory. An entry that
does not declare its ending, its definition of done, and what it will never do is not reviewable,
and will not be merged.
