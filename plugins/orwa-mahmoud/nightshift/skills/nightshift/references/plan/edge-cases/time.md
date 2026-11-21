# Time — an item that reads the clock, stores a date, or schedules something

## When it applies

The item compares, stores, formats or schedules a date or a time.

## Cases

- **Another time zone** — the user, the server and the stored value are not in the same zone, or
  the value carries no zone at all.
- **Daylight-saving change** — the hour that happens twice, the hour that never happens, and a
  day that is 23 or 25 hours long.
- **Period boundary** — the last moment of a day, a month or a year, and the first of the next.
- **Leap day** — 29 February, and the same date one year later.
- **Clock skew** — two machines disagree about the time, or the clock moves backwards mid-run.

## Example lines

- WHEN a report for March is run at 23:30 on 31 March in a zone behind UTC THEN it includes that day's rows
- WHEN a daily job is due in the hour daylight saving skips THEN it runs once that day and says when
