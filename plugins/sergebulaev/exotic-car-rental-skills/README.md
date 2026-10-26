<p align="center">
  <img src="assets/hero.png" alt="CarRentalList exotic car rental skills for Claude and Codex: find, price and compare exotic rental cars with live listings" width="900" />
</p>

# Exotic Car Rental Skills for Claude Code and Codex

<p align="center">
  <img src="https://img.shields.io/github/v/release/sergebulaev/exotic-car-rental-skills?color=C9A96E&label=release" alt="Latest release">
  <img src="https://img.shields.io/badge/Claude_Code-Compatible-D97757?logo=anthropic&logoColor=white" alt="Claude Code Compatible">
  <img src="https://img.shields.io/badge/Codex-Compatible-111827" alt="Codex Compatible">
  <img src="https://img.shields.io/badge/Claude-Skills-8A63D2" alt="Claude Skills">
  <img src="https://img.shields.io/badge/MCP-live_listings-0E7490" alt="Live listings via MCP">
  <img src="https://img.shields.io/badge/License-MIT-22C55E.svg" alt="MIT License">
</p>

**Claude skills for renting exotic cars.** 6 Claude Code and Codex skills that
find who rents a Lamborghini, Ferrari, Rolls-Royce, McLaren or G-Wagon in your
city, at what published daily rate and on what terms; work out the real cost;
pick the right car for a wedding, prom or shoot; compare cars; plan a supercar
weekend; and check a rental company before you pay a deposit.

Every answer comes from **live listings: 3,000+ exotic and luxury cars at 160+
independent US rental companies**, with daily rates read from each company's own
website every week, never estimated. Each car and company comes with a link you
can check.

## Install

### Claude Code (CLI / VS Code / JetBrains)

```
/plugin marketplace add sergebulaev/exotic-car-rental-skills
/plugin install exotic-car-rental-skills@exotic-car-rental-skills
```

### Codex CLI

```bash
codex plugin marketplace add sergebulaev/exotic-car-rental-skills
codex plugin add exotic-car-rental-skills@exotic-car-rental-skills
```

### claude.ai (web) and Claude Desktop

1. Click **Customize** in the sidebar, open the **Plugins** tab
2. **Add** > **Add marketplace** > **Add from a repository**
3. Paste `sergebulaev/exotic-car-rental-skills` and sync
4. Open **Discover**, find the plugin and click **+** (or **Add**)
5. Check it is listed under **Yours**, then start a new conversation

> Skills need a paid Claude plan (Pro, Max, Team or Enterprise) with code execution enabled.

### Any agent (skills CLI)

```bash
npx skills add sergebulaev/exotic-car-rental-skills
```

### OpenClaw and Hermes Agent

```bash
git clone https://github.com/sergebulaev/exotic-car-rental-skills.git            # OpenClaw working dir
git clone https://github.com/sergebulaev/exotic-car-rental-skills.git ~/.hermes/skills/exotic-car-rental-skills
```

> **Found this useful? [Star the repo](https://github.com/sergebulaev/exotic-car-rental-skills).** Skill directories rank by stars, so a star is what makes these skills findable for the next renter.

## Live listings (free, 1 minute)

The skills read the [CarRentalList MCP server](https://mcp.carrentallist.com/):
a free, read-only connector to the US catalog of independent exotic and luxury
rental companies. No account, no key.

- **Claude**: Settings > Connectors > Add custom connector, URL `https://mcp.carrentallist.com/mcp`
- **ChatGPT**: Settings > Apps & Connectors > Developer mode > Create, same URL, No authentication
- **Cursor**: add `{"mcpServers":{"carrentallist":{"url":"https://mcp.carrentallist.com/mcp"}}}` to `~/.cursor/mcp.json`
- **Claude Code**: `claude mcp add --transport http carrentallist https://mcp.carrentallist.com/mcp`
- **Codex**: add an HTTP MCP server with the same URL

No connector? The skills fall back to the bundled client (Python standard
library, same server):

```bash
python3 lib/carrentallist_client.py search_vehicles '{"city": "Miami", "state": "FL", "make": "Lamborghini"}'
```

## What you can ask

> "Who rents a Lamborghini Urus in Miami this weekend, and for how much?"

> "I'm 23. Which companies in Las Vegas will rent me a supercar?"

> "What does a Ferrari 296 for a weekend in LA really cost with 250 miles?"

> "Pick a car for my wedding in Scottsdale. Getaway car, white, chauffeur if possible."

> "Huracán or 296 GTB for my first supercar day?"

> "Plan two days in Miami with something loud, budget $1,200 a day, delivered to my hotel."

> "Is this rental company legit? They want a $10,000 deposit by Zelle."

## The 6 skills

| Skill | What it does |
|---|---|
| [exotic-rental-finder](skills/exotic-rental-finder/SKILL.md) | Who rents this car in your city: shortlist with published daily rates, deposit, age, mileage and delivery terms, links |
| [exotic-rental-cost](skills/exotic-rental-cost/SKILL.md) | The real cost of a rental (rate, mileage overage, delivery, deposit, the blanks to ask) and whether the rate is fair for that market |
| [exotic-event-car](skills/exotic-event-car/SKILL.md) | The right car for a wedding, prom, birthday, proposal, music video or shoot, with event-specific terms and a booking timeline |
| [exotic-car-compare](skills/exotic-car-compare/SKILL.md) | Huracán vs 296, Urus vs G 63 vs Cullinan: character, seats and the real rental numbers in your city |
| [exotic-weekend-planner](skills/exotic-weekend-planner/SKILL.md) | A weekend or road trip: the car, delivery, day-by-day drives, miles against included miles, cost |
| [exotic-rental-company-check](skills/exotic-rental-company-check/SKILL.md) | Check a company before you pay: published terms, rating, price vs market, owner-verified, red flags, questions to ask |

## Rules the skills follow

- **Real listings only.** Published daily rates with sample size and date; a car
  without a price is "Contact for price", never estimated ([references/catalog-data.md](references/catalog-data.md)).
- **No availability promises.** The catalog lists fleets, not calendars: the
  skills tell you to confirm your dates with the company.
- **The deposit checklist, every time.** Deposit, insurance, mileage, age,
  damage process, cancellation, and scam red flags ([references/renter-checklist.md](references/renter-checklist.md)).
- **Company text is data.** What a company writes about itself is quoted as its
  claim and never followed as an instruction ([references/untrusted-content.md](references/untrusted-content.md)).

## Browse on CarRentalList

- [Exotic car rental directory by state](https://carrentallist.com/directory)
- [Exotic car rental pricing guide](https://carrentallist.com/pricing-guide): published daily rates by make
- [Best exotic car rental companies](https://carrentallist.com/best-exotic-car-rental-companies): monthly ranking
- [Rent by brand](https://carrentallist.com/brands): Lamborghini, Ferrari, Rolls-Royce, McLaren and more
- [CarRentalList MCP server](https://mcp.carrentallist.com/): the catalog in Claude, ChatGPT and Cursor

Run a rental company? See the sibling bundle
[car-rental-skills](https://github.com/sergebulaev/car-rental-skills) (pricing,
market scans, rental agreements, inspections, listings, reviews).

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

MIT. Listings by [CarRentalList](https://carrentallist.com).

## Related open-source skill bundles

- [car-rental-skills](https://github.com/sergebulaev/car-rental-skills) - for rental companies
- [instagram-skills](https://github.com/sergebulaev/instagram-skills) - Instagram
- [tiktok-skills](https://github.com/sergebulaev/tiktok-skills) - TikTok
- [youtube-skills](https://github.com/sergebulaev/youtube-skills) - YouTube
- [linkedin-skills](https://github.com/sergebulaev/linkedin-skills) - LinkedIn
- [x-skills](https://github.com/sergebulaev/x-skills) - X (Twitter)
