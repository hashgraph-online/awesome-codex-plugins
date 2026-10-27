<p align="center">
  <img src="assets/hero.png" alt="CarRentalList car rental skills for Claude and Codex: 8 skills with live published rates from independent US rental companies" width="900" />
</p>

# Car Rental Business Skills for Claude Code and Codex

<p align="center">
  <img src="https://img.shields.io/github/v/release/sergebulaev/car-rental-skills?color=C9A96E&label=release" alt="Latest release">
  <img src="https://img.shields.io/badge/Claude_Code-Compatible-D97757?logo=anthropic&logoColor=white" alt="Claude Code Compatible">
  <img src="https://img.shields.io/badge/Codex-Compatible-111827" alt="Codex Compatible">
  <img src="https://img.shields.io/badge/Claude-Skills-8A63D2" alt="Claude Skills">
  <img src="https://img.shields.io/badge/MCP-live_market_data-0E7490" alt="Live market data via MCP">
  <img src="https://img.shields.io/badge/License-MIT-22C55E.svg" alt="MIT License">
</p>

**Claude skills for car rental businesses.** 8 Claude Code and Codex skills for
exotic, luxury and Turo car rental operators: price a car against the real
market, scan your competitors, draft a rental agreement, run damage
inspections, write listings and Instagram posts, answer reviews and plan a new
rental business. The market skills read **live published daily rates for
3,000+ exotic and luxury cars at 160+ independent US rental companies**, so the
numbers are real, not guessed.

No coding required. No API key. Works in Claude (web, desktop, Code), Codex,
Cursor and any agent that reads `SKILL.md` files.

## Install

### Claude Code (CLI / VS Code / JetBrains)

```
/plugin marketplace add sergebulaev/car-rental-skills
/plugin install car-rental-skills@car-rental-skills
```

### Codex CLI

```bash
codex plugin marketplace add sergebulaev/car-rental-skills
codex plugin add car-rental-skills@car-rental-skills
```

### claude.ai (web) and Claude Desktop

1. Click **Customize** in the sidebar, open the **Plugins** tab
2. **Add** > **Add marketplace** > **Add from a repository**
3. Paste `sergebulaev/car-rental-skills` and sync
4. Open **Discover**, find the plugin and click **+** (or **Add**)
5. Check it is listed under **Yours**, then start a new conversation

> Skills need a paid Claude plan (Pro, Max, Team or Enterprise) with code execution enabled.

### Any agent (skills CLI)

Works across Claude Code, Codex, Cursor and other agents that read SKILL.md:

```bash
npx skills add sergebulaev/car-rental-skills
```

### OpenClaw and Hermes Agent

```bash
git clone https://github.com/sergebulaev/car-rental-skills.git            # OpenClaw working dir
git clone https://github.com/sergebulaev/car-rental-skills.git ~/.hermes/skills/car-rental-skills
```

For OpenClaw, add to the system prompt: "You have car rental business skills in
./car-rental-skills/. For any car rental task, read the relevant
skills/*/SKILL.md first. Use lib/carrentallist_client.py for market data."

> **Found this useful? [Star the repo](https://github.com/sergebulaev/car-rental-skills).** Skill directories rank by stars, so a star is what makes these skills findable for the next operator.

## Live market data (optional, free, 1 minute)

The pricing, market scan and business plan skills compare against what other
operators publish; the agreement, listing and social skills use it optionally. They use the
[CarRentalList MCP server](https://mcp.carrentallist.com/): a free, read-only
connector to the US catalog of independent exotic and luxury rental companies,
with daily rates and rental terms read from each company's own website weekly.
No account, no key.

- **Claude**: Settings > Connectors > Add custom connector, URL `https://mcp.carrentallist.com/mcp`
- **ChatGPT**: Settings > Apps & Connectors > Developer mode > Create, same URL, No authentication
- **Cursor**: add `{"mcpServers":{"carrentallist":{"url":"https://mcp.carrentallist.com/mcp"}}}` to `~/.cursor/mcp.json`
- **Claude Code**: `claude mcp add --transport http carrentallist https://mcp.carrentallist.com/mcp`
- **Codex**: add an HTTP MCP server with the same URL

No connector? The skills fall back to the bundled client, which calls the same
server with the Python standard library:

```bash
python3 lib/carrentallist_client.py price_overview '{"make": "Lamborghini", "city": "Miami"}'
```

## What you can do

Once installed, ask in plain words. The right skill activates.

**Price a car:**
> "How much should I charge for my 2023 Lamborghini Urus in Miami? I'm at $1,295 with a $3,000 deposit."

**Scan your market:**
> "Who are my competitors for exotic car rental in Scottsdale, and what do they charge?"

**Start a business:**
> "I have $250k. Plan an exotic car rental business in Atlanta: which cars first, Turo or my own site, numbers per car."

**Get a contract:**
> "Write a car rental agreement for my company in Texas. Minimum age 25, $2,500 deposit, 100 miles a day."

**Handle damage:**
> "Make a pickup and return inspection checklist for my fleet, then help me write to a renter who curbed two wheels."

**Write listings and posts:**
> "Write the Turo listing and an Instagram Reel script for our new Rolls-Royce Cullinan."

**Answer reviews:**
> "Reply to this 1-star Google review about our deposit hold. Here is what happened."

Every skill shows a draft first. Nothing is published or sent without your OK.

## The 8 skills

| Skill | What it does | Live data |
|---|---|---|
| [car-rental-pricing](skills/car-rental-pricing/SKILL.md) | Where your daily rate sits among published rates for the same model and city; take-home math, Turo versus direct; rate card | yes |
| [car-rental-market-scan](skills/car-rental-market-scan/SKILL.md) | Competitors, fleet mix, price bands by make, terms norms, gaps, recent price moves in any US city | yes |
| [car-rental-business-plan](skills/car-rental-business-plan/SKILL.md) | How to start a car rental business: city and first cars from market data, unit economics, setup checklist, 90-day plan | yes |
| [car-rental-agreement](skills/car-rental-agreement/SKILL.md) | Rental agreement template from your policies: deposit, mileage, insurance, damage, tolls, prohibited use; lawyer checklist | norms |
| [car-rental-damage-inspection](skills/car-rental-damage-inspection/SKILL.md) | Pickup and return inspection checklist, photo plan, condition report, evidence-first damage claim message | |
| [car-rental-listing-writer](skills/car-rental-listing-writer/SKILL.md) | Vehicle pages, Turo and Getaround listings, Google Business Profile entries, SEO titles | optional |
| [car-rental-social-posts](skills/car-rental-social-posts/SKILL.md) | Instagram captions, Reels and TikTok scripts, weekly content calendar for a rental fleet | optional |
| [car-rental-review-reply](skills/car-rental-review-reply/SKILL.md) | Google, Yelp, Turo review replies, including deposit and damage disputes; private follow-up; team fix note | |

## Rules the skills follow

- **Real prices only.** Market numbers are published rates with the sample size
  and the date. A missing price is "Contact for price", never an estimate
  ([references/catalog-data.md](references/catalog-data.md)).
- **No AI tells in customer copy.** An enumerated banned list ("unforgettable",
  "elevate", "seamless", em dashes and the rest) is scrubbed from every listing,
  post and reply ([references/voice-rules.md](references/voice-rules.md)).
- **Drafts for your lawyer, not legal advice.** Contracts flag every
  state-specific clause and never cite a law the user did not give
  ([references/legal-guardrails.md](references/legal-guardrails.md)).
- **Reviews and emails are data.** Text a stranger wrote is never followed as an
  instruction ([references/untrusted-content.md](references/untrusted-content.md)).

## Free tools and guides for rental operators

- [Car rental profit calculator](https://carrentallist.com/car-rental-profit-calculator): net per car on Turo or booking direct, with published daily rates by make
- [Car rental agreement template](https://carrentallist.com/car-rental-agreement-template): free, editable, with the clauses to review with a lawyer marked
- [List or claim your company on CarRentalList](https://carrentallist.com/for-owners): the US directory of independent exotic car rental companies
- [Exotic car rental pricing guide](https://carrentallist.com/pricing-guide): published daily rates by make and state
- [Turo vs running your own exotic rental business](https://carrentallist.com/turo-vs-own-exotic-car-rental-business)
- [Best exotic car rental companies](https://carrentallist.com/best-exotic-car-rental-companies): monthly ranking
- [CarRentalList MCP server](https://mcp.carrentallist.com/): the catalog in Claude, ChatGPT and Cursor

## Validation

```bash
pip install pyyaml
python3 scripts/check_frontmatter.py
python3 scripts/check_markdown_references.py
python3 scripts/check_untrusted_rule.py
python3 scripts/check_tools.py --live
python3 scripts/check_no_secrets.py
```

## License

MIT. Market data by [CarRentalList](https://carrentallist.com).

## Related open-source skill bundles

From the same author, for the marketing side of a rental business:

- [exotic-car-rental-skills](https://github.com/sergebulaev/exotic-car-rental-skills) - for renters: find, price and compare exotic rental cars
- [instagram-skills](https://github.com/sergebulaev/instagram-skills) - Instagram
- [tiktok-skills](https://github.com/sergebulaev/tiktok-skills) - TikTok
- [facebook-skills](https://github.com/sergebulaev/facebook-skills) - Facebook Pages
- [youtube-skills](https://github.com/sergebulaev/youtube-skills) - YouTube
- [linkedin-skills](https://github.com/sergebulaev/linkedin-skills) - LinkedIn
- [x-skills](https://github.com/sergebulaev/x-skills) - X (Twitter)
- [threads-skills](https://github.com/sergebulaev/threads-skills) - Threads
