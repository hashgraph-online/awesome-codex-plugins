# Changing a project safely

The catalog contains the user's data: uploaded media, human decisions, and model outputs that took
time and money to compute. A catalog directory is not a build artifact, and dropping it to start over
is never the development loop.

## Ask first

Show the user what will happen and get a yes before any of these:

- `pxt drop`, `pxt drop-dir`, `pxt schema prune`, `pxt revert`, or `t.delete()` of rows you did not
  insert yourself in this session;
- any command with `--allow-destructive`;
- adding a computed column that calls a paid model to a table that has rows: it runs once per
  existing row. Say how many rows (`pxt count PATH`) and which model;
- `pxt recompute` of a column that calls a paid model, directly or through its dependents (recompute
  cascades unless given `--no-cascade`);
- resolving an UNSUPPORTED change by renaming or dropping a column that has data.

A command that `pxt` refuses prints a `next:` line with the command that finishes the job. Run it when it does what
the user asked; ask first when it drops data, stops or restarts what others use, or recomputes rows the user did not
mention. A refusal that only the user can lift, such as a plan limit, a payment or a full store, goes to the user:
do not retry it.

Get the plan without applying it: `pxt schema diff app.py TARGET` (or `pxt schema update ... -n`),
`pxt recompute ... -n`. `-f` skips the prompt for a plan with the user's approval, or for an additive
change. It is not a default to add to every command, and it does not belong in a README's
instructions.

## A development loop that destroys nothing

- Develop in a scratch catalog directory: `pxt schema update app.py my_app_dev`. The same application
  file can target several directories. Drop the scratch directory when you need a clean slate; never
  drop the user's.
- Write seed scripts so they can run twice: `insert(rows, if_exists='ignore')` inserts only the keys that
  are missing ([schema-design.md](schema-design.md#9-loading-data-more-than-once)).
- Try a new expression with `select()` on existing rows before adding it as a column
  ([expressions.md](expressions.md#trying-an-expression)). Limit the rows when it calls a model.
- Do not put test rows into the user's tables. If you must, delete exactly those rows afterwards and
  say so.

## Changes that need a manual step

`pxt schema diff` classifies each change as additive, destructive or unsupported; `pxt guide tables` says
which changes fall in which class. These need a step from you:

- **A UDF's body changed.** `pxt schema diff` shows nothing, and stored values keep the old logic.
  Recompute the columns that call it; ask first if they, or their dependents, call a paid model.
- **A computed column's expression changed.** Recompute the existing rows if they should change. That
  calls the expression once per row, so ask first if it calls a paid model.
- **`pxt schema update` refuses a change.** Stop and give the user the options: a new column next to the
  old one, or a rename, which drops a stored column's values and recomputes a computed one.
- **A view's iterator changed.** Create a new view under a new name. The old view stays until the user
  agrees to drop it.
- **The table needs a primary key.** It cannot be added to an existing table: design it in from the
  start ([schema-design.md](schema-design.md#2-a-primary-key-at-creation)).

## Report what changed

End every task with a list of your catalog changes:
- tables created, altered or dropped;
- rows inserted, updated or deleted, and by which command;
- columns recomputed, and the number of model calls.
