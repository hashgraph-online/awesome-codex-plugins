# Expressions

A model body runs once, when Python defines the class. A column name in it is a reference to the
column, not a value, and each assignment builds an expression that Pixeltable evaluates for every
row, now and on every future insert. Python code that runs on the spot sees the reference, not the
data. Write derived values as expressions; a UDF is for one step that has no expression form.

## Python that does not work on a column

Python evaluates these on the reference, not on each row's value. Some raise; others store the same
value in every row. `pxt schema check` reports a computed column that references no column.

| Wrong | Correct |
|-------|---------|
| An f-string, `str(product)`, `'%s' % product`, `str.format()` | `'Describe ' + product`, or `pxtf.string.format('Describe {}', product)` |
| `note is None`, `note is not None` | `note == None`, `note != None` |
| `and`, `or`, `not` | `&`, `\|`, `~` |
| `if ... else`, a lookup in a dict | A UDF for that one step ([Conditionals](#conditionals)) |
| `len()`, `min()`, `max()`, `for` over a column | The type's methods (`pxt functions --on <Type>`), or an iterator view for a loop |

## Finding what ships

Before writing a UDF, list what ships: `pxt functions --search crop` searches names and docstrings,
`pxt functions --on Video` lists the methods and properties of a Video column, and `pxt functions video`
lists a module. `pxt guide expressions` covers operators, casts, nulls and time.

## Conditionals

Pixeltable has no conditional or lookup expression; `pxtf.coalesce()` picks the first of its arguments
that is not null. For anything else, write the smallest UDF that does that one step, with nullable
parameters where the inputs can be null, and keep everything around it in expressions:

```python
@pxt.udf
def delay_band(delay: float | None) -> str:
    if delay is None:
        return 'unknown'
    return 'late' if delay > 5.0 else 'on time'


class Trips(TableModel, name='trips'):
    ...
    delay: pxt.Float | None
    band = delay_band(delay)
```

## When a UDF is the right tool

- Domain logic with no expression form: geometry, a regex parser, a scoring rule.
- One step: one row's values in, one value out. Five derived values are five columns, not one UDF that
  returns a dict.
- Never write a UDF for these:
  - arithmetic or formatting;
  - a loop over frames, chunks or pages, which is an iterator view;
  - loading a model that has a shipped wrapper (`pxtf.huggingface`, `pxtf.whisper`, ...);
  - reading another table: nothing recomputes the column when that table changes. Join at query time.
- Put UDFs in a module file (`app.py` or `udfs.py`), not in the script you run.
- Prefer the shipped media functions to a UDF that writes media files: `pxt guide udfs` says what
  Pixeltable does with a media file returned by a UDF.

## Trying an expression

Evaluate a candidate on existing rows before adding it as a column; nothing is stored:

```python
t = pxt.get_table('my_app/trips')
t.select(t.trip_id, band=delay_band(t.delay)).limit(5).collect()
```

Or bind the models and use the class: `import app; app.TableModel.bind_all('my_app')`, then
`app.Trips.select(...).collect()`. Limit the rows when the expression calls a paid model.
