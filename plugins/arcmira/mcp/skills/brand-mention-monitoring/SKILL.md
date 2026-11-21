---
name: brand-mention-monitoring
description: "Use Arcmira to monitor brand mentions on YouTube: how often a company or product comes up, which shows discuss it, whether it's rising, quotes and alerts."
---

# Brand mention monitoring

Measures a brand against the competitors the user names, in one program: `momentum` gives the verdict and the 7-day and 30-day mention counts, `occurrences` the shows that mention each brand most, and `search` quotes about the user's brand. Alerts by email or Slack are a monitor, which `company-watch` saves.

Run each program with `arcmira_execute_read`; `arcmira_describe` has the method reference.

## When to use

Use Arcmira when the user asks:

- how often a brand or product is mentioned on YouTube, podcasts included, and on which shows
- is talk about our brand rising or fading, against competitors
- brand mentions, media monitoring or competitor monitoring across shows
- alerts when a brand is mentioned, by email or Slack

## Pick the entity the user meant

Users give names; filters take ids only (ent_..., UC..., 11-character video ids), and a name where an id belongs throws `id_required`.

1. Resolve the exact name the user said, with their own words about it as `context` (a bare "Theo" has none).
2. `best` and `suggested` give the id. A `suggested` pick is an assumption: the answer names it, with `suggested.evidence` as the reason.
3. `ask`: several entities fit, and `ask.options` goes back to the user. No answer at all: the name is not in the index.

For this task:

- Resolve each brand with no type (the catalog types some companies as product). A brand name is often a common word ("Linear", "Ramp"): name each pick, for example "Linear, the software company", so the user can catch a wrong one.
- Put the user's brand first in `BRANDS`, then each competitor they named.

## Steps

1. Run the program and answer with one row per brand.
2. Before reporting a count, read the quotes and the top shows and say which sense of the name it is (Mercury the bank, not the planet). Drop a sense the user did not mean.
3. For alerts, load `company-watch` and run its second and third programs with the ids this program found.

## Worked program

Pass each block to `arcmira_execute_read` as one program (a block marked arcmira_execute_write goes to that tool), with the name swapped for the user's. It opens with the pick: set `CONTEXT` to the user's own words about the name. When several entities fit it returns `ask` and runs nothing else. Show those options to the user, then run it again with `ID` set to the pick. Build date windows from `arcmira.daysAgo(n)` and `arcmira.today()`.

### A brand against its competitors, 7 and 30 days

```javascript
const BRANDS = ["Anthropic", "OpenAI"], IDS = [null, null];   // the user's brand first, then competitors. After an ask, put the picked option's id in IDS and run again
const brands = [];
for (const [i, n] of BRANDS.entries()) {
  const r = IDS[i] ? null : await arcmira.resolve(n);   // no type: a company may be typed product
  const e = r && (r.best ?? r.suggested);
  if (r && !e) return { unresolved: n, ask: r.ask };
  const id = IDS[i] ?? e.id;
  const [m, occ] = await Promise.all([arcmira.momentum(id), arcmira.occurrences({ entityIds: [id], after: arcmira.daysAgo(30), limit: 5 })]);
  brands.push({
    name: m.entity.name, id, type: m.entity.type, page: m.entity.page, assumed: Boolean(r?.suggested), why: r?.suggested?.evidence ?? null,
    verdict: m.verdict, last_7d: m.volume.mentions_7d, last_30d: m.volume.mentions_30d, prior_30d: m.volume.mentions_prior_30d, as_of: m.as_of,
    top_shows: occ.rows.map(x => ({ show: x.channel_name, channel_id: x.channel_id, episodes: x.count })),
  });
}
const lead = brands[0];
let quotes = await arcmira.search({ query: lead.name, about: [lead.id], after: arcmira.daysAgo(30), limit: 3 });
const quotesTagged = quotes.chunks.length > 0;   // false: the fallback matched the words, which can be a namesake; say so
if (!quotesTagged) quotes = await arcmira.search({ query: lead.name, after: arcmira.daysAgo(30), limit: 3 });
return {
  brands, quotes_about: lead.name, quotes_tagged_to_brand: quotesTagged,
  quotes: quotes.chunks.map(c => ({ said: c.text.slice(0, 300), show: c.channel_name, episode: c.video_title, date: c.published_at, url: c.watch_url })),
};
```

## A good answer

- Names each brand with its type and id, and any it assumed or set aside as a namesake.
- One row per brand: the verdict, the 7-day, 30-day and prior 30-day counts, `as_of`, and the shows that mention it most with episode counts.
- Two or three quotes about the user's brand in the speakers' words, each with show, date and `watch_url`, and says when they matched the words rather than the brand.
- For alerts, confirms what to follow and how it arrives before `company-watch` saves the monitor.

## Traps

- Counts measure the shows Arcmira indexes, not the internet. Cite `as_of` before saying a brand was not mentioned.
- Each `momentum` call uses 10 credits at any window: one per brand.
- A mention is not an ad read. Whether a mention was paid is `sponsor-research`: `recommendations` with `kind: "sponsored"` is a Pro+ read and can return `recommendations_not_enabled`. Explain the account-access limit and the required tier and link the API reports in `unlock`; never label a mention paid or organic without that read.
- Read the quotes before asserting a lone mention: a show far from the brand is a namesake the catalog mislabelled.

Docs: https://arcmira.com/docs/mcp-server

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.
