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

## Recording geography

Routes need a journey time for every pair of places. Geography records
where places are, or how far apart, and lets the CLI work out whether a
journey fits the `travel-hours` a scene gives it. Use it when the user has
a map or a table of distances. Do not assume Earth: an invented world has
its own map and its own units.

First ask for the distance unit and the ways people travel, then set them
in `story.md`:

```yaml
distance-unit: leagues
map-scale: 4
travel-modes:
  - mode: on foot
    speed: 1
    per-day: 8
  - mode: horse
    speed: 3
    per-day: 15
  - mode: wyvern
    speed: 12
```

- `distance-unit` - free text printed in findings (default `units`)
- `map-scale` - distance units per map unit (default `1`)
- `travel-modes` - each `mode` once, with `speed` in distance units an hour
  while moving, and an optional `per-day`, the most one day of travel
  covers. Take both from the speeds table in `economy-logistics.md`, or
  from the world's own rules (a wyvern, a portal network)

Then give locations `coordinates`, `distances`, or both:

```yaml
---
name: "Stonebridge"
type: town
coordinates: [12, 40]
distances:
  - to: greyhaven
    distance: 30
---
```

- `coordinates` - `[x, y]` read off the user's map, in any grid: squares,
  centimetres, or pixels. `map-scale` turns them into distance. The straight
  line is the shortest possible way, so it never makes a journey look
  slower than it is
- `distances` - how far it is by the way people go, in the distance unit;
  two-way unless the other place lists its own distance back. A listed
  distance wins over the straight line, so list one where a mountain or a
  river makes the real way longer

`story add location 'Stonebridge' --coordinates 12,40` writes the
coordinates. `story links .` reports a `distances` entry that names an
unknown location or the location itself.

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

## The distance travel check

Once `story.md` lists a travel mode, `story continuity .` compares each
scene that has `travel-hours` above 0 with the previous scene in reading
order. When the two scenes are at different places, the hours must cover
the distance at the speed of the scene's `travel-mode`, for the characters
(scene `characters` and `pov`) who are in both scenes:

```yaml
location: stonebridge
travel-hours: 30
travel-mode: horse
```

Without `travel-mode`, or with a mode `story.md` does not list, the check
uses the fastest mode, so the warning then means no way of travel in the
world could make the journey. The finding is a warning, `travel-too-far`.
Undated scenes count; a flashback scene is skipped; after a scene with no
`location`, the next scene has no place to start from.

To fix a finding:

1. Raise `travel-hours`, and move a dated scene later so the clock allows it
2. Choose a faster `travel-mode` the story supports, and show it on the page
3. Correct the distance, the coordinates, or the mode's speed if they are
   wrong

After editing routes, geography, or travel modes, run `story reindex .`,
`story wordcount . --write`, and `story check .` (which includes the
continuity route and distance checks).
