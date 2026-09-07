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

**Adding an entry:** see [`catalog-recipe.md`](catalog-recipe.md) in this directory. An entry that
does not declare its ending, its definition of done, and what it will never do is not reviewable,
and will not be merged.
