# Feature map: Shelfwise (example)

This is a worked example of the `features/` folder a generated verify skill contains. Shelfwise is a fictional app for tracking a home library and books lent to friends. It has a browser UI and a companion CLI named `shelf`. Both are driven through a fictional wrapper, `shelf-drive`, with a `web` subcommand (browser automation over the Chrome DevTools Protocol) and a `cli` subcommand (runs `shelf` in a fresh PTY and records it). Copy the structure, not the product.

## Baseline for every recipe

Each recipe starts from this state. If any item is false, run the health check, then fix the baseline before driving.

- The verification instance serves `http://127.0.0.1:4310`. Port 4310 is reserved for verification; the user's own instance uses 4300.
- `SHELFWISE_DATA_DIR` points at a fresh temporary folder created for this run (`mktemp -d`). Parallel runs never share a data folder.
- Two fixtures are loaded by `shelf-drive seed`: the book "The Left Hand of Darkness" (id `bk_fixture_lhod`, on the shelf) and the friend "Rosa Diaz" (id `fr_fixture_rosa`, no loans).
- `shelf`, `shelf-drive`, and `sqlite3` are on `PATH`.
- `shelf-drive doctor` prints the expected URL, the data folder for this run, and a build revision that matches `git rev-parse --short HEAD`. Do not drive until all three match.
- Only drive an instance this run started. If `shelf-drive doctor` reports a process owned by another run or by the user, stop and report it.

## Conventions

- Begin every recipe from the baseline above.
- Locate elements by accessible role and name (`button "Lend"`), then by `data-testid`. Never by CSS class, position, or tab order.
- Run commands exactly as written. They are the tested form.
- After any recipe that changes data, restore the fixtures with `shelf-drive seed --reset`.
- Teardown (`shelf-drive down`) stops the server it started and removes `SHELFWISE_DATA_DIR`. It never touches `./verify-artifacts/`.

## Proof rules

- Record the action the user took and the state that followed.
- Browser proof is a pair: an accessibility-tree dump (`shelf-drive web a11y`) and a screenshot in which the Shelfwise header is visible.
- CLI proof records the full command line, stdout, stderr, and the exit code.
- Confirm every write by reading the stored value back through a separate view with no side effects: the read-only `shelf show` command, or `sqlite3 -readonly`.
- Save each artifact under `./verify-artifacts/<feature-id>/<entry-point>/`, so every artifact names the feature and the entry point it proves.
- If a path cannot be reached, report the command you ran and the precondition that was missing.
- An entry point you skipped is not covered, even if a different entry point for the same feature passed.
- Redact the session cookie from any saved HTTP trace with `shelf-drive redact <file>` before keeping it.

## Feature files

Each file has a title, one paragraph on what the user sees, and then exactly four sections in this order: Sub-features, Entry points, Driving, Gotchas. The Driving section opens with a list of preconditions, followed by bullets that each pair one user action with its exact command and the result a user would observe. Implementation details (table names, component names) stay out of the map except where a read-back command needs them.

| Id | Feature | File |
| --- | --- | --- |
| `lend` | Lend a book to a friend and get it back | [lend-a-book.md](lend-a-book.md) |
| `import` | Import a catalog from a CSV file | [import-catalog.md](import-catalog.md) |
