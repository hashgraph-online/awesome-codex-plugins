# Craft: sheets (type sheet)

How to lay out a sheet people work in. Plinth draws every sheet the same clean way (a sticky
header, type-aware alignment, formats), so a good sheet comes from its columns, their order and
their types.

## Important columns first

- People see the first few columns: on a phone about two and a half columns of the default width,
  on a laptop seven or eight. Put the column that names each row first (Item, Task, Name), then the
  ones people act on (Status, Owner, Due, Amount), then the detail, with notes last. Leave none out;
  order them.
- Freeze the naming column (`"freeze":{"cols":1}`) when the table is wider than the screen. One or
  two frozen columns are plenty: on a narrow screen they scroll with the rest anyway.
- One row per record and one column per attribute. Row 1 is always the header and every viewer can
  sort and filter, so never stack two tables, a title or notes in the rows.

## A build order

1. **Columns from the ask.** A name, a type and a format for each, with the unit in the name
   ("Hours") or in the number format (currency).
2. **The header line,** with the widths and the freeze.
3. **The rows,** in the order people will read them: dated rows newest first, or by status or
   priority.
4. **Formulas last,** written against the header (data starts at row 2), then a total row only if
   people need one (below).
5. **Read it back** with `read_sheet` to see what the formulas compute, and fix every error value
   before you hand over the link.

Later changes go through `edit_sheet`, touching only the cells, rows and columns you were asked
about.

## Column types and widths

- **Give every column its real type.** `number` with a `format`: `currency` with its code and
  2 decimals, `percent`, or `plain` with the decimals that matter. `date` for dates, `checkbox` for
  yes or no, `select` with `options` for a closed set (status, priority), `url` for links, `text`
  for the rest. Typed columns sort, filter and download correctly, and Plinth refuses a literal
  cell that does not fit its column, so a typo cannot slip in.
- **Keep numbers numbers.** Never "€12" or "12 hrs" as text in a number column: the format and the
  column name carry the unit. Ids, phone numbers and codes with leading zeros are text.
- **Set widths from the content.** Cells do not wrap: text that does not fit is cut with "…", and
  the whole value shows in the bar above the grid when the cell is selected. A default column
  (120 px) holds about 14 characters. Give a column about 8 px per character of the longest value
  people need to read, plus 16, between 40 and 800.

## A notes column

- Free text (comments, reasons, where a figure came from) goes in one `Notes` column at the right
  end, 280 to 400 px wide, never squeezed into the cells of other columns.
- Keep each note to a line or two. Longer writing belongs in a doc, linked from a `url` column.

## Totals and summaries

- Nothing can sit above the header, so a total row goes last, with "Total" in the first column and
  ranges that stop at the last data row (`=SUM(D2:D40)`). A whole-column range in the total's own
  column (`=SUM(D:D)` in column D) takes in the total itself and shows `#CYCLE!`.
- A viewer's sort moves a total row in among the records. For a list people will sort, leave the
  total out and give it in your reply from `read_sheet`, unless they ask for the row.

## Only real values

- Never pad a sheet with sample rows. A tracker people will fill in starts with its header and the
  rows the person gave you.
- A sheet has no charts. For a view of the numbers, make an HTML page from the same data
  (`craft/html.md`) and say so.
