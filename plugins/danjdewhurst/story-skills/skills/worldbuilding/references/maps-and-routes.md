# Maps and Routes

A story map is a graph before it is a picture: which places connect, how
long the journey takes, and by what means. Record that graph in location
frontmatter so the CLI can draw it and check travel against the timeline.

## Recording routes

Add `routes` to a location file, one entry per direct connection:

```yaml
---
name: "Vell Harbour"
type: city
routes:
  - to: saltmarsh-fort
    hours: 9
    mode: coach
  - to: the-narrows
    hours: 4
    mode: boat
---
```

- `to` - the id of another location file; `story links .` reports unknown ids
- `hours` - travel time as a number (decimals allowed: `0.5` is thirty minutes)
- `mode` - free text: `on foot`, `horse`, `coach`, `river barge`, `airship`

Routes are two-way unless the other location declares its own route back.
Declare the return route only when it differs: against the current, uphill,
or slower in a season (note the season in the location body).

Record only direct connections. A journey through an intermediate place is
two routes, which lets the map show the waypoint.

## Setting plausible hours

Measure distance on the user's map or a real map, then divide by the speed
for the mode (see the travel speeds table in `economy-logistics.md`). Add
time for rests, border crossings, changing horses, tides, and weather.
Real settings deserve a research note: walk the route or check a journey
planner, then record the source (see the `research` skill).

## Drawing the map-graph

```shell
story diagram locations
story diagram locations --out dist/locations.mmd
```

The output is Mermaid source: each location is a node and each route an
edge labelled with its hours. GitHub, many editors, and mermaid.live render
it. Read it for:

- Isolated locations with no routes (fine for a far-off place only
  mentioned, suspicious for one characters visit)
- Shortcuts that make a set-piece journey pointless
- Hubs that should be politically or economically important but are not
  treated that way in the world notes

The diagram is generated; regenerate it after route changes rather than
editing it by hand.

## The continuity travel check

`story continuity .` uses routes together with scene `date`, `time`, and
`location`, and the scene's `characters` and `pov`. Chapter dates and
locations are not read. When a character appears in two dated scenes at
locations linked by routes, and the story time between the scenes is less
than the fastest route (possibly through other places), it reports an
error: the character could not have made the trip. A named `time` covers a
span (`dawn` 04:00-06:59, `morning` 05:00-11:59, `midday` 11:00-13:59,
`afternoon` 12:00-17:59, `evening` 17:00-21:59, `night` 20:00-23:59, or
the same share of a calendar's longer or shorter `hours-per-day`), and
a scene with a `date` but no `time` spans its whole day. The gap is taken
at its most generous reading, so only a journey impossible on every
reading is an error. A character at two different places at the same
exact `HH:MM` is an error even with no route between them.

To fix a finding:

1. Move the later scene's `date` or `time` later
2. Change the route's mode and hours if a faster means exists in the story,
   and show that means on the page
3. Remove the character from one scene's `characters` (list them in
   `mentions` if they are only referred to)

Scene `travel-hours` is separate from routes: it asserts the minimum time
since the latest moment the story has reached in reading order (both
need a `time`; a flashback does not reset it), not a journey inside the
scene. A scene with no `pov` counts its chapter's `pov` as present. `story timeline .` and `story diagram timeline` show dated scenes in
story-time order, which helps when adjusting dates.

After editing routes, run `story reindex .`, `story wordcount . --write`,
and `story check .` (which includes the continuity route checks).
