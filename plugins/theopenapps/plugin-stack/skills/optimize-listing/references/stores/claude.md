Checked: 2026-11-05 against https://claude.com/docs/connectors/building/managing-your-listing.md. Over 90 days old: fetch that URL, and where it disagrees follow the store's docs and say so in the report.

# Claude listings

Also read on that date: https://claude.com/docs/connectors/building/after-publishing.md, https://claude.com/docs/connectors/building/submission.md, https://claude.com/docs/plugins/submit.md and https://claude.com/docs/plugins/pre-submission-checklist.md.

One directory holds connectors, edited in the portal at claude.ai/directory/manage, and plugins, edited in their GitHub repo.

## Connector fields

Portal edits are saved, then submitted for review, and stay pending until a reviewer approves them. Submit a batch as one edit.

| Field | Limit | Where to edit | Cost of a change | What is shown |
|---|---|---|---|---|
| Display name | 100 | Portal | Re-review; it affects existing users | Name |
| One-liner (the portal's tagline) | 200 | Portal | Review | Card, which shows only the start |
| Description | 2,000 | Portal | Review | Detail card, in your words; Anthropic can't edit it |
| Categories | 1 to 5 | Portal | Review | Categories |
| Tool and prompt names | Tool name 64 | Portal | Review | Names on the listing |
| Slug | Locked after publication | Nowhere | Can't change | Listing URL |

Cards show two lines, so make the one-liner's opening stand alone.

## Plugin fields

Edit `plugin.json` and the README, push to the tracked branch or tag, and publish a new version. Each version runs validation and a security scan, and **Publish** is by default a request a reviewer acts on. A version that fails or is held leaves the live one up. After a failed security scan, later versions also wait for a reviewer.

| Field | Limit | Where to edit | Cost of a change | What is shown |
|---|---|---|---|---|
| `name`, `displayName` | `name` 64; lowercase, digits, hyphens. `displayName` in one writing system | `plugin.json` | New version | Name |
| Short description | Undocumented | `plugin.json` and the README | New version | Short description |
| Description | At least 40 words outside code blocks | README | New version | The README |
| `version` | Raise it with each release if set | `plugin.json` | Part of each new version | Installed copies use it to see an update |

If a reviewer edited the name or short description during review, the listing keeps the reviewer's text. The security scan looks for undisclosed behaviour, so a README rewrite keeps everything the plugin runs, sends or fetches.

## Preflight

Reject a draft plugin name that is non-ASCII, taken, presented as official, or reserved as a whole name (`claude`, `anthropic`, `official`, `plugin`, `mcp`, `test`); these block the version. A name made only of generic words, a look-alike, a well-known brand that isn't the user's, or a fork using its upstream name holds the version for a reviewer, so reject those too.

## Ordering

Documented by Anthropic: **Directory rank** in the portal counts distinct accounts that sent the server any MCP message in 30 days, including `initialize` and failed connections. **Used a tool** counts accounts with a `tools/call`, so it's the honest usage number. **Trending** marks the top 10 by growth in the rank's count. Placement and Verified have no application; Anthropic decides during review.

Unknown: whether public order follows Directory rank.

## Search

Anthropic doesn't document what directory search reads. In OpenApps' read of its results, the query sat in the name mostly near the top, and many results held it in neither the name nor the one-liner, so search reads more than those two fields. This is a correlation.

Placement that fits this: the main target word in the display name, the rest in the one-liner and description.

## Reading numbers

There are no `category:` charts. Use `connectors:popularity`, `community:popularity`, or a `popularity:<facet>/<value>` chart such as `popularity:object_acted_on/files-documents`; `stores_get store=claude` lists them all.

`listings_metrics ref=<ref>` gives what a listing carries, each with its basis. Installs are store_reported and absent from some listings.

A plugin owner's **Usage** tab has a directory funnel: listing views, install clicks and installs. Ask the user to note it before a rewrite ships, for a before-and-after.
