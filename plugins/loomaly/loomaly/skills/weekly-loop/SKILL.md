---
name: weekly-loop
description: "Run the weekly SEO loop on one page that should make money: read how the focus page did, judge the last change by search and conversions, and propose one next change with evidence. Use when the user asks what to work on this week, whether a change worked, or wants a weekly SEO check-in."
---

# The weekly loop on the focus page

Rankings that don't convert are worth nothing, and a sitewide audit gives no idea which fix pays. So the loop works on **one page** (the focus page the owner picked in Loomaly) and makes **one change at a time**, then judges it on search *and* conversions.

## Tools (Loomaly MCP)

- `sites_list`: find the site id.
- `focus_page` (`siteId`): the owner's brief (what the site sells, to whom, what counts as a conversion), the focus page's Search Console numbers (last 28 days vs the 28 before), its open issues, a conversion checkup (the page read against the brief), and the change log, each change with a `verdict`. With no focus page it returns `candidates` instead.
- `fix_prompt` (`findingId`): instructions for one open issue on the page.
- `log_change` (`siteId`, `summary`, `shippedOn`, `ref`, optional `conversionsBefore` / `conversionsAfter`): record a change once it is live.
- `set_focus_page` (`siteId`, `page`) and `set_brief` (`siteId`, `offer`, `customer`, `conversion`): save the owner's choice of page and their brief.
- `mark_fixed` / `verify`: close an issue the change fixed.

## Steps

1. `sites_list`, then `focus_page`.
   - No focus page: suggest one of the `candidates` (pages already seen in search, ranking 3–20) that looks like it should convert; without Search Console there are none, so ask which page matters most (often pricing or the main product page). Once the owner picks, `set_focus_page`.
   - `checkup.state` is `needs_brief`: ask the owner what the site sells, to whom, and what counts as a conversion, and `set_brief` with their words.
2. Report the week, short:
   - Search numbers for the page, and whether they moved beyond normal noise. Say plainly when they did not.
   - Every change whose verdict arrived. Conversions decide: `miss` means the page climbed but did not convert better; `win` means more conversions, even with flat rankings. `too_little` (and `lowTraffic`) means the page gets too few clicks for search to show anything: say so, and judge the page by the checkup and its index status until traffic grows. `search_up` only says search improved, because no conversions were given — ask the owner for them (before and after windows are in `measure.windows`) and record them with `log_change`'s fields on a new entry or in the dashboard.
3. If `blockers` is not empty, those come first: pages that can't be found can't be improved by any change to the focus page. Recommend fixing the biggest one (`fix_prompt` with its `findingId`).
4. If any change is still `watching`, **recommend nothing new**. Changing the page now makes that change impossible to judge. Say how many days are left.
5. Otherwise recommend **one** change, with the evidence behind it:
   - First choice: a `fail` item in `checkup` (the page does not say what it offers, has no proof, no step towards the conversion…). These cost conversions directly.
   - Then the worst open issue on the page (`openFindings`), using `fix_prompt`.
   - Leave a page that is doing well alone unless there is a strong reason.
6. Wait for the owner's yes before drafting. When the change ships, `log_change` with the day it went live and the PR, and `mark_fixed` any issue it closed (the owner can also do this in the dashboard; a fix claimed on the focus page is logged automatically).

## Accuracy

- Only report what the tools return. Search Console numbers land 2–3 days late; a small site can have too few clicks for any change to clear the noise, so say so rather than read meaning into it.
- Don't promise AI citations, and don't recommend schema or llms.txt as a way to get cited: there is no good evidence they help. Recommend what makes the page answer its question plainly and convert.
- Never claim a change "worked" from rankings alone.
