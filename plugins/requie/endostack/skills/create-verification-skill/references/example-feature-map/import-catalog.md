# Import a catalog

A user uploads a CSV of books (title, author, ISBN, optional shelf location) and sees a preview of what will be added, what is a duplicate, and which rows have errors. After confirming, the new books appear on the shelf. Bad rows are skipped and listed with a reason.

## Sub-features

- `import.preview`: parse the file and show added, duplicate, and error counts before anything is saved.
- `import.commit`: save the previewed rows.
- `import.dupes`: skip a row whose ISBN already exists.
- `import.reject`: refuse files that are not CSV, are larger than 2 MB, or contain spreadsheet formulas in any cell.

## Entry points

- **Import** in the shelf's toolbar menu.
- Dragging a file onto the shelf page.
- `shelf import <file.csv> [--dry-run] [--json]` on the CLI.

## Driving

Preconditions:

- Baseline from the README is in place.
- The test files exist in the skill's `fixtures/` folder: `three-books.csv` (two new books and one row with the fixture's ISBN), `formula.csv` (one cell starting with `=HYPERLINK(`), and `big.csv` (2.5 MB).

Steps:

- Open the importer: `shelf-drive web open /shelf`, `shelf-drive web click 'button "Toolbar menu"'`, `shelf-drive web click 'menuitem "Import"'`. A dialog titled "Import books" with a file chooser opens.
- Choose the file: `shelf-drive web upload 'button "Choose file"' fixtures/three-books.csv`. The preview reads "2 to add, 1 duplicate, 0 errors".
- Confirm: `shelf-drive web click 'button "Import 2 books"'`. The dialog closes and both new titles appear on the shelf.
- Read back: `shelf list --json | jq 'length'` prints the fixture count plus 2. `shelf show --isbn 9780441478125 --json` still prints `bk_fixture_lhod`, showing the duplicate row did not create a second book.
- Reset with `shelf-drive seed --reset`, then drag the same file: `shelf-drive web drop /shelf fixtures/three-books.csv`. The same preview opens. Close it with `shelf-drive web key Escape` and confirm `shelf list --json | jq 'length'` is back to the fixture count.
- Dry run from the CLI: `shelf import fixtures/three-books.csv --dry-run --json`. Exit code 0, JSON has `"added": 2, "duplicates": 1`, and `shelf list` is unchanged.
- Reject a formula cell: `shelf import fixtures/formula.csv --json`. Exit code 4, the error names row 2 and column `title`, and nothing is saved.
- Reject a large file from the browser: upload `fixtures/big.csv` through the dialog. The preview shows "File is larger than 2 MB" and the **Import** button is disabled.
- Capture: `shelf-drive capture import` saves artifacts under `./verify-artifacts/import/`.
- Restore: `shelf-drive seed --reset`.

## Gotchas

- The preview runs in the browser and saves nothing. Clicking away from the dialog after the preview is not an import; only the confirm button writes.
- The drop target is the shelf grid, not the page header. Dropping on the header does nothing and gives no error.
- `shelf import` without `--json` prints a human table whose column widths change with title length. Parse only the `--json` form.
- The CLI treats a missing `--dry-run` as a real import. Always reset fixtures after a CLI import step, even one you expected to fail.
- `formula.csv` must be rejected on both entry points. A pass on the CLI does not cover the browser path, which uses a different parser.
