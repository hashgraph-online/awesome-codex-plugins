# Word-Count Norms

**English-language market only.** Do not apply these ranges to a book in
another language (`language` in `story.md`): the same story runs to a
different word count in each language, Chinese and Japanese publishing
count characters rather than words (Japanese manuscripts are often
measured in 400-character manuscript pages), and each market has its own
expectations. For those books, ask the user for the norms of the market
and the publishers they are targeting, and report the count without a
verdict.

These ranges are rough industry conventions for debut novels in the
English-language trade market. They vary by agent, publisher, country, and
year. Always tell the user the manuscript's count and the range, and ask
them to confirm current norms for their market and the agents they are
querying. Never pad or cut a manuscript to fit a range without the user's
direction.

| Category | Typical range (words) |
|----------|-----------------------|
| Adult literary fiction | 70,000-100,000 |
| Adult commercial or upmarket fiction | 80,000-100,000 |
| Mystery | 70,000-90,000 |
| Cozy mystery | 60,000-80,000 |
| Thriller or suspense | 80,000-100,000 |
| Romance (single title) | 70,000-90,000 |
| Romance (category lines) | 50,000-75,000, set by each line |
| Science fiction or fantasy (adult) | 90,000-120,000 |
| Epic fantasy (adult) | 100,000-130,000 |
| Horror | 70,000-90,000 |
| Historical fiction | 90,000-110,000 |
| Young adult (contemporary) | 60,000-80,000 |
| Young adult (fantasy or SF) | 70,000-95,000 |
| Middle grade | 30,000-55,000 |
| Middle grade fantasy | 45,000-65,000 |
| Novella | 17,500-40,000 |
| Novelette | 7,500-17,500 |
| Short story | Under 7,500 |

The novella, novelette, and short-story bands follow the SFWA award
categories, a common reference for short-fiction markets. Magazines and
anthologies publish their own limits; follow those.

## How to report

- Take the count from `story wordcount .` and round it to the nearest
  thousand in submission copy.
- When the count is well outside the range (roughly 15% or more), tell the
  user, name the likely objection (printing cost for long books, thinness
  for short ones), and let them decide. If they choose to cut or expand,
  run `revision-continuity`'s
  [length pass](../../revision-continuity/references/pass-checklists.md#length-pass),
  which sets a budget per chapter and arc before touching the prose.
- Sequels and established authors are judged differently; these ranges are
  for a first submission.
- If `story.md` has `target-words`, also report the count against that
  target.
