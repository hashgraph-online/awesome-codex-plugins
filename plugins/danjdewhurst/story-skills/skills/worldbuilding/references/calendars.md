# Calendars, Seasons, and Moons

A secondary world with its own calendar needs one written record, or dates
drift: a festival lands in two different months, a full moon rises twice in
a week, the harvest comes before the thaw. Keep two records: the `calendar`
list in `story.md`, which the CLI reads, and a system file for everything
the CLI does not (seasons, moons, holidays, how people tell time).

## Add the calendar to story.md

Ask the user for the month names and lengths in order, any days outside the
months (festivals), the week if the story names weekdays, how years are
counted, and how many hours a day has if not 24. Then add a `calendar` list
to the `story.md` frontmatter:

```yaml
calendar:
  - month: Thaw
    days: 30
  - month: Sowing
    days: 30
  # ...one entry per month, in calendar order
  - month: Frost
    days: 30
  - month: Hollow Days
    days: 5
  - weekdays: [Firstday, Seconday, Midweek, Fourthday, Fifthday, Restday]
    first-weekday: Midweek
  - era: Before the Founding
    abbrev: BF
    direction: backward
  - era: After the Founding
    abbrev: AF
```

- **Months** are listed in order, each with `days`. Festival days outside
  any month become a short month of their own (`Hollow Days`, 5 days).
  Every year is the sum of the months: there are no leap days.
- **Weekdays** are optional, listed once. `first-weekday` is the weekday of
  the first day of year 1 of the first forward era (default: the first one
  listed). Set it so a date the user already knows falls on the right day.
- **Eras** are optional, in order. A `direction: backward` era counts down
  toward the next one, as BC does, and only the first era may. Every
  forward era except the last needs `years` (how long it lasted).
- **Hours per day** is optional, listed once: add `- hours-per-day: 30` (a
  whole number from 1 to 100) when the world's day is not 24 hours long,
  and leave it out for a 24-hour day.
- Names must not start with a digit or contain a comma, and must be unique.

The full rules are in the project format reference, under Custom calendars
(`docs/project-format.md#custom-calendars` in the Story Skills repository).

## Dating scenes

With a calendar, scene and chapter `date` values are written in it:

- `3 Thaw 412 AF`, or `3rd of Thaw, 412 After the Founding`
- `412-01-03 AF` (year, month number, day)
- `3 Thaw 412` (no era: the last era)
- `Seconday, 3 Thaw 412 AF` (a stated weekday must be the right one)

`story add scene --date '3 Thaw 412 AF'` takes the same forms. Use `time`
for the time of day: `HH:MM` or a named part of the day (`dawn`,
`evening`). The clock has 24 hours, or the calendar's `hours-per-day`:
with `hours-per-day: 30`, times run from `00:00` to `29:59`, a journey
across midnight counts 30 hours a day, and each named part covers the same
share of the longer day. Record how people in the world name the hours in
the system file below.

`story timeline`, `story continuity`, the route check, `story knowledge`,
and progression order turn each date into a day count, so elapsed time
across months, years, and eras is right. A date that starts with a digit
or a weekday must be a real day of the calendar: `31 Thaw 412 AF` in a
30-day month is a `story validate` error that says why. Other text
(`the night of the fire`) is allowed, but nothing can order it, and
`story continuity` warns about it.

## Record the rest as a system file

```shell
story add system 'Reckoning of Vell' --type social
```

Fill `worldbuilding/systems/reckoning-of-vell.md` with what the `calendar`
list cannot hold:

```markdown
## Overview

Twelve months of 30 days plus five Hollow Days at midwinter (365 days).
Years are counted from the Founding (AF). The calendar itself is the
`calendar` list in story.md.

## Rules & Limitations

| # | Month | Season | Notes |
|---|-------|--------|-------|
| 1 | Thaw | spring | Year begins at the first thaw |
| 2 | Sowing | spring | |
| ... | | | |
| 12 | Frost | winter | |
| - | Hollow Days | winter | Festival; not part of any month |

- Week: markets on Firstday.
- Day: dawn bell, noon bell, dusk bell; hours not counted by commoners.
- Moons: Ser (29-day cycle), Oda (41-day cycle). Both full on 1 Thaw 412 AF.
```

Keep holidays, market days, tides, and anything the plot hangs on in the
same file. Keep the month names in the file and in `story.md` the same.

## Seasons and daylight

Record for each season: day length, weather, what grows, what travel is
possible (passes closed, rivers frozen or in flood), and what work people
are doing. Route `hours` assume normal conditions; note seasonal exceptions
in the location body.

## Moons and cycles

For each moon or cycle, record its period in days and one date when it was
full (or at any fixed phase). The phase on day N is
`(N - known full day) mod period`. Check any scene that mentions moonlight,
tides, or a moon-bound ritual against this. Two moons align every
least common multiple of their periods (29 and 41 days: every 1,189 days),
which makes a good rare event.

## Checking

- `story timeline .` lists dated scenes in story-time order and flags scenes
  read after events that happen later.
- `story diagram timeline` prints a Mermaid timeline of dated scenes and
  chapters.
- `story continuity .` checks clock order, `travel-hours`, and routes. It
  reads scene `date`, `time`, `location`, `characters`, and `pov`; chapter
  dates do not feed the route check. A named time is a span (`morning` is
  05:00-11:59 of a 24-hour day), an untimed scene spans its whole day, and
  only journeys impossible on every reading are errors. `travel-hours` on
  a scene is the minimum time since the latest moment the story has
  reached in reading order (a flashback does not reset it), not a journey
  within the scene. A `time` past the end of the calendar's day is a
  `malformed-time` warning.

After adding or changing the calendar or the calendar system file, run
`story reindex .`, `story wordcount . --write`, and `story check .`:
`check` validates the `calendar` list and every date against it, then runs
the continuity checks.
