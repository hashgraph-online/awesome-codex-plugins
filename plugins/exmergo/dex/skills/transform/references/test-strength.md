# Writing tests that would catch the defect, and measuring them

A passing test shows that the test ran. It does not show that the test would fail
if the model were wrong. A unit test whose fixture never reaches a boundary passes
whichever side of the boundary the model puts a row. Measure the tests before you
tell anyone a model is covered.

## The loop

1. **Scaffold.** `dex transform test --scaffold <model>` plans a `unit_tests:`
   skeleton. It has a `given` block per input, holding only the columns the model
   reads. For a calendar window it holds rows on the window's boundary (see
   below). Fill in `expect:` with what the model should return for those rows.
   Work it out from the rule the model implements, never by running the model,
   or the test only pins what the model already does. Apply the plan.
2. **Measure.** Run `dex transform test --mutate <model>`. Each mutant is one
   standard defect planted in the model's compiled SQL: a flipped boundary, a
   dropped filter, a swapped join, a removed `CASE` branch, an inverted ratio, a
   shifted window frame, or `sum` for `max`. Each comes back `killed` (a test
   failed), `survived`, `caught_downstream`, `rejected` or `not_run`.
3. **Strengthen.** Read every survivor's `defect`, `suggested_test` and, for a
   window, `frame`. Add the fixture rows or the assertion it names, through
   `transform plan` like any other edit.
4. **Measure again.** A survivor you fixed is now `killed`. Report the survivors
   that remain, with the reason each one does.

Read `equivalence` on a survivor when it is there. `distinguishable` means the dev
data already differs, so an assertion over that data would catch it today.
`equivalent` means no assertion over today's data can tell it apart, so only a
fixture that reaches the case can.

The score covers only the defects Dex plants, on one model. It is evidence about
the suite, not proof that the model is right. Do not quote it as a quality
metric, and do not compare it across models.

## Calendar windows

Take a trailing seven-day count:

```sql
sum(parcels) over (
    partition by depot
    order by pickup_date
    range between interval '6 day' preceding and current row
)
```

Its boundary carries two defects, and Dex plants both. Widened, the window counts
seven days back, so a row on the first day it should exclude gets in. Narrowed,
it stops at five days, so the row on the last day it should include falls out. A
third defect is the window written as `rows between 6 preceding`: on consecutive
days it gives the same answer, and on gapped days it does not.

A fixture on consecutive days, all inside the window, passes all three. The
fixture that catches them has, in one partition:

| Date | What it tests |
|---|---|
| 2024-01-17 | The gap. Seen from 01-24, this row is outside a six-day window but is the row just before, so a six-row frame would count it |
| 2024-01-24 | The first day the window excludes, seen from 01-31 |
| 2024-01-25 | The last day the window includes, seen from 01-31 |
| 2024-01-31 | The current row |

Number the measured column `1, 10, 100, 1000`, so each expected sum says which
rows were counted: `1`, `10`, `110`, `1100`. `transform test --scaffold` places
exactly these rows for a `RANGE` frame with a day or week interval, ordered by a
date or timestamp column of one input. `data.window_boundaries` says what each
date tests. Write `expect:` yourself; Dex never does.

A window survivor's `frame` has the numbers to build this by hand when the
scaffold cannot: `last_included` and `first_excluded` are offsets from the
current row, in `unit`, on the bound's `side`.

## What is not measured

`data.unsupported_sites` lists every window bound no mutant moved, each with a
`reason_code`:

- `non_literal_offset`: a column or expression (`interval (lookback) day`).
- `fractional_offset`: not a whole number.
- `compound_interval`: more than one unit (`'1 day 12 hours'`).
- `string_offset`: a quoted number.
- `negative_offset`: a negative offset.
- `unknown_unit`: a unit Dex has not reviewed.
- `other_bound_of_mutated_frame`: the frame's other bound, when Dex moved the
  first.

These boundaries are untested by the run. Say so, and write the boundary fixture
by hand if the request depends on them. `UNBOUNDED` and `CURRENT ROW` are not
listed, because they have no offset to be off by one.

The scaffold notes a window it could not place rows for, and that input keeps
one example row. The reasons are: an `ORDER BY` that is an expression other than
a whole-day function of a date column, a month or year unit, a non-temporal
ordering column, or a `RANGE` bound that is a bare number over an arbitrary
expression. BigQuery's day window over `unix_date(d)` or `date_diff(d, ..., day)`
is recognized and gets the same four boundary rows as an interval frame.
