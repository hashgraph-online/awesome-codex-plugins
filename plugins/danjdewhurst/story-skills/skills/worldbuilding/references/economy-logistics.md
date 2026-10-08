# Economy, Logistics, and Costs

Readers forgive dragons but not armies that never eat. Work out what things
cost, how goods move, and what power costs its users, then keep the numbers
consistent.

## Prices and wages

Record in an `economic` system file:

- Currency units and their ratios (`1 crown = 20 marks = 240 pence`)
- A day's wage for a labourer, a skilled worker, and a soldier
- Prices of a meal, a night's lodging, a horse, a sword, a book, passage on
  a ship
- Who can afford what: a labourer saves for months to buy a horse

Anchor prices to wages, not to modern money. If the story uses a real
historical economy, record the figures as research notes (see the
`research` skill).

## Supply lines

For any city, army, siege, or expedition the plot depends on, answer:

- What does it eat and drink, and where does that come from?
- How is it carried (ships, wagons, pack animals, porters, portals)?
- How long does the supply take to arrive (use the location `routes`)?
- What happens when the line is cut, and how long do stores last?
- Who profits, and who controls the choke points?

A cut supply line is a plot engine: it sets a deadline in days.

## Magic and technology costs

Every power needs a price the story enforces:

- **Cost:** what the user spends (energy, blood, years, memory, money, rare
  materials)
- **Limit:** what it cannot do at any price
- **Recovery:** how long before it can be used again
- **Side effects:** who else pays (the land, bystanders, the future)
- **Scarcity:** who controls the materials or the training

Record these under `## Rules & Limitations` in the system file. When a
scene uses the power, pay the cost on the page, and record lasting effects
in `continuity/state.md` (`character-state` or `object-state`).

## Travel speeds by mode

Typical sustained speeds for setting route `hours`. Adjust for terrain,
weather, load, and rests; these are day averages, not sprints.

| Mode | km/h | Per day | Notes |
|------|------|---------|-------|
| On foot, road | 4-5 | 30-35 km | About 8 hours walking |
| On foot, rough terrain | 2-3 | 15-20 km | Hills, forest, snow |
| Army on the march | 2-3 | 15-25 km | Baggage sets the pace |
| Horse, sustained travel | 6-8 | 40-60 km | Horses need rest and fodder |
| Horse relay (post riders) | 15-20 | 150-250 km | Fresh horses at stations |
| Ox cart or wagon | 3 | 15-25 km | Roads only |
| Stagecoach | 8-12 | 80-120 km | Changes horses every 15-20 km |
| River barge, downstream | 5-10 | 50-100 km | Depends on the current |
| River barge, upstream | 2-4 | 20-40 km | Towed or poled |
| Sailing ship | 5-10 | 100-200 km | Depends on wind; sails day and night |
| Galley, rowed | 5-7 | 50-80 km | Crew fatigue |
| Steam train (19th century) | 30-50 | 300-600 km | Timetables and stations |
| Car, modern roads | 60-100 | 600-900 km | Traffic, fuel, rest stops |

Convert with `hours = distance in km / km/h` and add time for stops. Record
the result on the location's `routes` so `story continuity` checks journeys
between dated scenes (see `maps-and-routes.md`).

After editing economic or magic systems, run `story reindex .`,
`story wordcount . --write`, and `story check .`.
