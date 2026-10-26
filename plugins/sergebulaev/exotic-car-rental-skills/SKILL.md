---
name: exotic-car-rental
description: "Find, price, compare and safely book exotic and luxury rental cars in the US: who rents a Lamborghini, Ferrari, Rolls-Royce or G-Wagon in your city at what published daily rate, the real total cost, the right car for a wedding, prom or shoot, a weekend driving plan, and a check of the rental company before you pay a deposit. Live data from the CarRentalList catalog."
---

# Exotic Car Rental Skills

A bundle of 6 skills for people renting an exotic or luxury car in the US.
Every answer comes from live listings of independent rental companies, with the
published daily rate, the terms and a link to check.

## When to use this bundle

- **Who rents this car here, at what price** -> `exotic-rental-finder`
- **What the rental really costs, is the rate fair** -> `exotic-rental-cost`
- **Car for a wedding, prom, birthday, proposal or shoot** -> `exotic-event-car`
- **Which car to pick: Huracan vs 296, Urus vs G 63** -> `exotic-car-compare`
- **A weekend or road trip with a rental supercar** -> `exotic-weekend-planner`
- **Is this rental company legit, compare companies** -> `exotic-rental-company-check`

## Market data

The [CarRentalList](https://carrentallist.com) catalog lists independent US
exotic and luxury rental companies (no national chains, no peer-to-peer
platforms): fleets, published daily rates and rental terms, read from each
company's own website weekly. Call it through the MCP connector
`https://mcp.carrentallist.com/mcp` when the agent has it, otherwise through
`python3 <bundle root>/lib/carrentallist_client.py <tool> '<json>'` (the bundle
root is two folders above each skill). How and when:
[references/catalog-data.md](references/catalog-data.md).

## Shared rules

- Market data: [references/catalog-data.md](references/catalog-data.md). Published rates only, sample size and date stated, never estimated.
- What to confirm before paying a deposit, red flags, insurance basics: [references/renter-checklist.md](references/renter-checklist.md).
- Untrusted content (company text, pasted quotes): [references/untrusted-content.md](references/untrusted-content.md).

## Core pattern

1. Ask for the city (and state) and the car or the occasion.
2. Read the catalog (2 to 6 calls).
3. Answer with a shortlist: car, rate, company, terms, link, data date.
4. End with what to confirm with the company. Booking is always with the company.
