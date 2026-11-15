# Reference Sites

Read this reference when a run reads UIBowl or Mobbin. It records what each site showed to a browser without an account on the date below, and what each site's published pages say about using its material. Every statement here is a dated observation, not a standing fact.

## Contents

1. How to Use This File
2. UIBowl
3. Mobbin
4. What This Means for a Run
5. When These Facts Expire

## 1. How to Use This File

- Use the tables to decide which pages are worth opening and where reading will stop.
- The reading rules themselves are in [../rules/reference-use.md](../rules/reference-use.md); this file adds no permission.
- Quote a row in the notes only with its read date. When the page in front of you differs from a row, the page is right: record what you saw and treat the row as stale.
- A row marked `not read` means the page was not read, so nothing is claimed about it.

## 2. UIBowl

A Korean-language library of screens from shipped apps and websites, at <https://uibowl.io/>.

| Page | Without an account, on 2026-11-15 |
|---|---|
| Home `https://uibowl.io/` | Opens. Shows the menu, a monthly-active-user range filter, and UI pattern categories with a count per pattern. |
| Explore `https://uibowl.io/explore` | Opens. Lists patterns, components, and categories. |
| Pattern filter `https://uibowl.io/?patterns=<pattern name>` | Opens with the filter applied. |
| App page `https://uibowl.io/name/<app name>` | Opens with the app's monthly users, capture month, and per-pattern counts. A login modal appeared, stating that the free version shows only the three most recent patterns. |
| Membership `https://uibowl.io/membership` | Opens. The free plan lists browsing of the three most recent apps and websites; a paid plan lists browsing of all of them and unlimited use of the site's connector. |

Published statements read on the same date:

| Topic | What the page says |
|---|---|
| Ownership | The service policy page says the copyright of captured content belongs to the owners of the original apps and websites, that the service exists for education and reference, and that it does not reuse brand assets such as logos and illustrations. |
| Footer notice | The site footer says the copyright of the content belongs to the copyright holder or provider and that unauthorized use can carry legal liability under copyright law. |
| Connector | The connector guide describes a read-only search connector that requires sign-up, with free members seeing the three most recent results per search. |
| `robots.txt` | Allows `/` and disallows `/admin`, `/api-doc`, `/oauth/`, `/payments/`, `/membership/payment`, `/user/`, `/signin`, and `/layout/`. |
| Terms of use | `not read`: the general provisions page did not yield its restriction clauses, so no clause is stated here. |

## 3. Mobbin

An English-language library of screens and flows from shipped apps and sites, at <https://mobbin.com/>.

| Page | Without an account, on 2026-11-15 |
|---|---|
| Explore `https://mobbin.com/explore` | Redirects to `/explore/mobile` and opens. Shows Mobile, Web, and Sites tabs, category browsing (categories, screens, UI elements, flows), popular collections, and trending cards with element and flow tags. |
| Discover `https://mobbin.com/discover` | Redirects to the home page with a return parameter; it needs a login. |
| Pricing `https://mobbin.com/pricing` | Opens. The free plan lists limited app access; the paid plans list all apps and sites, flows, and the site's connector. |
| Glossary `https://mobbin.com/glossary` | Opens. Defines UI component terms. |
| Colors `https://mobbin.com/colors` | Opens. Lists brand colors with hex values and color meanings. |
| Terms `https://mobbin.com/terms`, copyright `https://mobbin.com/copyright` | Open. |

Clauses read in the terms (effective 2026-05-16) on the same date:

| Topic | What the terms say |
|---|---|
| Copying | Modifying, copying, or creating derivative works of the materials is not permitted. |
| Automation | Unauthorized use of scrapers, bots, crawlers, or other automated means is not permitted. |
| Rehosting | Mirroring, caching, or rehosting the materials on another site or server is not permitted. |
| AI use | The user warrants not to use AI or machine-learning tools to create derivative works from the materials, or to train, test, or index models with them, outside what the terms or written consent allow. |
| Accounts | Account sharing is strictly prohibited. |
| Ownership | Rights in the listed screens stay with each intellectual-property holder; quoting or showing them elsewhere is limited and requires crediting the holder. |
| Connector and API | For personal or internal business use, or integration into the subscriber's own product. |
| `robots.txt` | Allows `/` for all agents; one named AI crawler is limited to the site's Markdown document paths. |

## 4. What This Means for a Run

- UIBowl: the home, explore, and pattern pages are enough to see which patterns exist and how common each is. An app page may stop at the login modal; when it does, stop there and log it.
- Mobbin: the public explore page shows what kinds of screens and flows exist and their tags. Individual screens and flows mostly need an account. Use what the user shares, and the glossary for component vocabulary.
- For both: read a few pages, write the pattern in your own words, keep links instead of images, and never feed a screen from either site to the image tool. The terms above are the reason the abstraction rule is strict, not a list of everything either site forbids.
- Neither site's connector is set up or signed in to by this skill. A connector the user already runs under their own account returns user-supplied material.

## 5. When These Facts Expire

Access limits, plan contents, and terms change without notice. Treat every row as stale after 90 days, or sooner when a page looks different. A stale row is re-read and re-dated in the notes for the run; it is not repeated from this file. Updating this file is a maintenance edit to the skill, made with the new read date.

## Sources

> Checked 2026-11-15.

| Claim | Source |
|---|---|
| UIBowl home, explore, pattern filter, and app page behavior without an account | <https://uibowl.io/>, <https://uibowl.io/explore> (read 2026-11-15) |
| UIBowl plan contents | <https://uibowl.io/membership> (read 2026-11-15) |
| UIBowl ownership and purpose statement | <https://blossom-browser-536.notion.site/142bc17e4311807a921cfc216fd4973a> (read 2026-11-15) |
| UIBowl connector guide | <https://blossom-browser-536.notion.site/MCP-390bc17e4311801998d5c555d092a267> (read 2026-11-15) |
| UIBowl crawl rules | <https://uibowl.io/robots.txt> (read 2026-11-15) |
| Mobbin explore and discover behavior without an account | <https://mobbin.com/explore> (read 2026-11-15) |
| Mobbin plan contents | <https://mobbin.com/pricing> (read 2026-11-15) |
| Mobbin terms clauses | <https://mobbin.com/terms> (effective 2026-05-16, read 2026-11-15) |
| Mobbin copyright page, glossary, and colors pages are public | <https://mobbin.com/copyright>, <https://mobbin.com/glossary>, <https://mobbin.com/colors> (read 2026-11-15) |
| Mobbin crawl rules | <https://mobbin.com/robots.txt> (read 2026-11-15) |

### Evidence grade

`PRIMARY`, single dated observation per row, read in a browser without logging in. The clauses are paraphrased, not quoted, and are not a complete summary of either site's terms. The 90-day staleness window is `LOCAL`. Nothing here is legal advice.
