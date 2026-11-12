# Watch Mode

Once a teardown exists, rerun it monthly and report only what is new.

1. Re-run the stage 1 history checks, the stage 5 signals, the hiring boards, reviews, ad libraries, and paid promotion sweep, plus the industry section's checks, and pull the last month's posts and interviews. Append new dated moves to a fresh `moves.csv`.
2. Diff the new log against the last one:
   ```bash
   node <skill-dir>/scripts/timeline.mjs diff --old teardowns/<target>/moves-2026-10.csv --new teardowns/<target>/moves.csv --out teardowns/<target>/new-moves.csv
   ```
3. Report only meaningful new moves: a new ad network, page family, loop, pricing change, content format, hiring burst in one channel, or complaint theme. **Launch radar:** when two or more of these land within a few weeks (a new subdomain, a trademark filing, new job titles in one area, a sitemap jump, a new domain verification), flag a likely launch and say what it points to. Write "no new moves" when there are none, which is the usual result.
4. For each new move, say whether it changes a play and which skill takes it.

To schedule it, run it as the monthly watch loop in `suede-marketing-loops`, keeping the dated move logs as its state.
