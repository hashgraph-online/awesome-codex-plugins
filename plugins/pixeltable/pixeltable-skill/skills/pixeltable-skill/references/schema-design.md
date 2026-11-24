# Designing the schema

Settle these points before the first `pxt schema update`. Keys, types and nullability are hard to
change once a table has rows: a wrong choice is fixed by migrating data, not by editing a line.

## 1. One table per entity

- An entity is a business object: a recording, a trip, a sample, a station, a review.
- A detail with many rows per parent and no life of its own is an iterator view of the parent (chunks,
  frames, segments, pages), or a typed Json list on the parent (the stops of one trip).
- Records that people create on their own schedule get their own table, with the parent's key as a
  column: assignments, review decisions, chat turns.
- One wide table for several entities, or one table per screen, is wrong.

## 2. A primary key at creation

- Use the natural key when the business already has a stable, unique id (`accession_no`, `trip_id`,
  an image file name): `code = pxt.Column(type=pxt.String, primary_key=True)`.
- Otherwise use a surrogate: `id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)`. The insert
  route's `outputs` (or `insert(..., return_rows=True)`) return the new id. Do not add a second
  "token" column to find the row again.
- A primary key cannot be added to an existing table, and updating or looking up a row by key needs
  one.
- Inserting a duplicate key raises.

## 3. Types

- Every value used for filtering, grouping, sorting or joining is its own typed column, not a field
  inside Json.
- Timestamps are `pxt.Timestamp`. Store UTC and convert when reading: `departs_at.astimezone(tz).hour`. Calendar dates are `pxt.Date`. Never store
  either as a String: strings sort and compare as text.
- Lists are `pxt.Json[list[str]]`, parsed once at insert, not comma- or pipe-separated strings that
  every UDF splits again.
- Nested payloads are Json typed with a TypedDict, so paths return typed values (`pxt guide json`).

## 4. Nullability

- `T` means every row has a value, and an insert without one fails. `T | None` means the value can be
  missing: an optional cover image, a sample that has not arrived yet.
- Decide nullability before the table has rows; `pxt guide tables` says whether `pxt schema update`
  can change a column's nullability in place. A field that becomes "required from now on" on a table with
  old rows is `T | None`, plus validation on new inserts.
- A non-nullable UDF parameter skips the call for a null argument, so a nullable column feeding it
  yields null without an error. Annotate the parameter `T | None` when the UDF should see the null.

## 5. Stored, computed or queried

| The value | Kind |
|-----------|------|
| What the outside world tells you: inputs, uploads, human decisions | stored (an annotation) |
| What you derive from the row's own values | computed (an assignment) |
| What depends on the current time, on other rows or on another table | queried (`@pxt.query`) |

Overdue, age and "in the last 2 days" are queries too: a stored copy goes stale the moment the clock
moves. `pxtf.timestamp.now()` is evaluated when the query runs:

```python
@pxt.query
def overdue() -> pxt.Query:
    age = pxtf.timestamp.now().posix_timestamp() - Assignments.received_at.posix_timestamp()
    return Assignments.where((Assignments.status != 'done') & (age > Assignments.target_hours * 3600)).select(...)
```

A per-row value that depends on the clock can also be a computed column with `stored=False`, which is
evaluated whenever a query reads it: `past_due = pxt.Column(value=pxtf.timestamp.now() > due_at, stored=False)`.

## 6. References between tables

Store the other row's key, not its attributes: an assignment stores `station_code`, not the station's
name or capacity, which would go stale on the assignment when the station changes. Read the
attributes at query time:

```python
assignments = pxt.get_table('my_app/assignments')
stations = pxt.get_table('my_app/stations')
assignments.join(stations, on=assignments.station_code == stations.code).select(
    assignments.id, stations.name, stations.capacity
)
```

Pixeltable has no foreign keys, so nothing checks that `station_code` exists. Check it in the route
handler, and say in your report that only the handler enforces it.

## 7. History

- Pixeltable versions every table: `pxt history PATH`, `pxt revert PATH`, `t.history()`. A revert
  undoes the last N operations on that one table, for everyone.
- Undoing one actor's changes after other people have made theirs is impossible with versions, and so
  is an audit trail per row. Use an append-only events table instead, one row per decision with who
  and when. Derive the current state at query time, and mark a reversal with a column (`revoked_at`)
  instead of deleting the row.
- A list of past values inside the current row (`history: [...]`) is wrong: it cannot be queried,
  indexed or undone per actor.

## 8. Validation

There are no CHECK or foreign-key constraints. A computed column whose UDF raises rejects the insert
and stores nothing, so a validating UDF works as a constraint:

```python
@pxt.udf
def checked_priority(priority: str) -> str:
    if priority not in ('STAT', 'URGENT', 'ROUTINE'):
        raise ValueError(f'unknown priority {priority!r}')
    return priority


class Samples(TableModel, name='samples'):
    ...
    priority: pxt.String
    priority_ok = checked_priority(priority)
```

Checking a key in another table needs a lookup, which a UDF cannot do: check it in the route handler.

## 9. Loading data more than once

The primary key makes a repeated load fail on the first duplicate. Load only the rows with new keys:
`insert(rows, if_exists='ignore')` leaves existing rows and their computed columns alone. An
upsert of rows that did not change can still recompute their computed columns, paid model calls
included: `pxt guide tables` says what each write recomputes.

## 10. Creation time

A stored computed column records the time of the insert:

```python
class Samples(TableModel, name='samples'):
    ...
    created_at = pxtf.timestamp.now()
```

The column has no inputs, so updates never recompute it. An explicit `pxt recompute` of
`created_at` overwrites it with the time of the recompute.

## 11. Indexes

`pxt.BtreeIndex(col)` on columns used for lookups (a user id, a status, a foreign key);
`pxt.EmbeddingIndex` for similarity search. Both go in `__indexes__`.

## 12. Claims and other races

An update whose `where` includes the expected state is a compare-and-set; its `num_rows` reports
whether it won:

```python
status = assignments.update(
    {'status': 'claimed', 'claimed_by': tech},
    where=(assignments.id == assignment_id) & (assignments.status == 'queued'),
)
if status.num_rows == 0:
    raise HTTPException(409, 'already claimed')
```

Reading the row first and updating it afterwards is a race. If an update route cannot express the
condition (`pxt guide serving`), write a custom handler.
