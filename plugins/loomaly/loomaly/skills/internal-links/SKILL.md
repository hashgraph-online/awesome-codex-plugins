---
name: internal-links
description: "Add the internal links Loomaly suggests: review each suggestion with the user, add the approved ones to the source content in this repository, and record each decision."
---

# Internal links worth adding

Use this when the user wants to improve internal linking or asks about Loomaly's link suggestions.

## Tools (Loomaly MCP)

- `link_suggestions` (`siteId`, `limit`): each has `id`, `fromUrl`, `toUrl`, `sentence`, `anchor` and `role` (`definition`, `comparison`, `next_step` or `tangential`). An empty list includes `lastPassAt`, `status` and `nextStep`: still running, nothing worth adding, or it will run after the next scan.
- `decide_link` (`suggestionId`, `decision`: `accepted` or `dismissed`).
- `sites_list` or `get_started` for the site ID. If the result has `needsSite`, the account has no site yet: find the domain in the repository (or use one the user already gave you) and call `add_site`, then wait until a scan finishes. Link suggestions appear only after a scan. Don't ask for the domain when you can see it. A free plan shows a fixed 3 suggestions (the strongest, including ones already dismissed). Dismissing one does not reveal the next; `lockedCount` is the rest. Suggestions stay in one language.

## Steps

1. `link_suggestions` with `limit: 10`. If `suggestions` is empty, follow `nextStep` and stop. Do not treat "still running" and "nothing worth adding" as the same result.
2. Show them as a short list: on which page, which words become a link, to which page, and why (`role`). Suggest skipping `tangential` ones unless the user wants them.
3. For each one the user approves, find the source of `fromUrl` in this repository (Markdown, MDX, CMS export or template), and turn `anchor` inside `sentence` into a link to `toUrl`. If the sentence isn't there any more, skip it and dismiss it.
4. Commit on a branch and open a PR.
5. `decide_link` with `accepted` for each link you added and `dismissed` for each one the user rejected.

Don't add links the user didn't approve, and don't change the sentence around the anchor.
