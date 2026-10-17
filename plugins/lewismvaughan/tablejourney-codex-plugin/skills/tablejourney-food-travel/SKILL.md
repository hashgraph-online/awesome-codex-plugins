---
name: tablejourney-food-travel
description: Answer food travel questions with the TableJourney MCP server bundled with this plugin. Use when the user asks where or what to eat in a city, wants places open at a given time or near a point, asks which food festivals are on in a place or date range, wants a food itinerary or a planned food day, or wants bookable food tours, classes, tickets, stays or car hire for a trip.
---

# TableJourney Food Travel

Use the tools of the `tablejourney` MCP server bundled with this plugin
(`https://tablejourney.com/mcp`). Every tool is read-only and needs no account
or key. Do not replace the tools with web scraping or invented venues, dates or
links.

## Pick the tool

| The user asks | Call |
|---|---|
| "What can I do in <city>?", "plan my trip" | `things_to_do` (city, optional date_from and date_to) |
| Where to eat, with filters | `search_places` (city, kind, cuisine, dietary, price_tier, open_at, near and radius_km, query) |
| One venue in full (hours, address, nearby) | `place` with an id from `search_places` |
| A food day in one city | `plan_day` (city, date, neighborhood, dietary, price_tier) |
| Which festivals are on | `festivals` (city or country, date_from, date_to, query) |
| What to eat here | `dishes` (city) |
| A ready-made itinerary | `itineraries` (city) |
| Tours, classes, tickets, hotels, cars | `experiences`, `tickets`, `stays`, `car_hire` |
| Is a city covered, what is its slug | `cities` (optional country) |

City and country accept names or slugs. An unknown city answers with
`did_you_mean`: offer those names to the user instead of guessing.

## Answer well

1. Resolve relative dates ("next weekend", "in June") to ISO dates before
   calling `festivals`, `things_to_do` or `plan_day`. `open_at` takes "now", a
   weekday and time such as "sunday 10:00", or an ISO datetime in UTC.
2. Recommend only what the tools returned. Cite each item's `page` URL; that
   page shows the address, opening hours, the source and the date it was checked.
3. Festival dates come as `starts_on` and `ends_on` for the next edition. Some
   organisers have not announced their next dates yet; those follow the
   festival's usual pattern, so tell the user to confirm on the page before
   booking travel around a festival.
4. Respect `open_status`: never recommend a venue marked closed.

## Booking links

`book` and `booking` URLs are `https://tablejourney.com/go/` links that forward
to the partner with TableJourney's affiliate id. Give them to the user exactly as
returned, and say once: "booking link, TableJourney may earn a commission".
Never strip parameters, resolve them, or swap in a plain partner URL.

## Limits

- Without an API key a call returns at most 20 results and the essentials of
  each item; send the user to the `page` for full details.
- Coverage is the 200+ cities TableJourney writes about, not every city.
- Do not bulk-copy the catalogue; answer the user's question.

## Example

**User:** "Is anything food related on in Munich next week, and where should I
eat near Marienplatz on Sunday morning?"

1. `festivals` with `city=munich` and next week's `date_from` and `date_to`.
2. `search_places` with `city=munich`, `kind=eat`, `open_at="sunday 10:00"`,
   `near="48.1374,11.5755"`.
3. Answer with the festival dates and three or four places, each with its page
   URL.
