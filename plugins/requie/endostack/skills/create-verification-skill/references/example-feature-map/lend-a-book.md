# Lend a book

A user marks a book on their shelf as lent to a friend, with an optional due date. The book shows a "Lent to Rosa" badge on the shelf, appears on the friend's page under "Has borrowed", and moves back to the shelf when the user marks it returned. Overdue loans show a red due date.

## Sub-features

- `lend.create`: lend a shelved book to a friend.
- `lend.due`: set a due date while lending.
- `lend.return`: mark a lent book returned.
- `lend.guard`: refuse to lend a book that is already out.

## Entry points

- The **Lend** button on a book's detail page.
- The `L` keyboard shortcut while a book card is selected on the shelf.
- `shelf lend <book-id> --to <friend-id> [--due YYYY-MM-DD]` on the CLI.
- `shelf return <book-id>` on the CLI (for `lend.return`).

## Driving

Preconditions:

- Baseline from the README is in place.
- `bk_fixture_lhod` is on the shelf and `fr_fixture_rosa` has no loans (`shelf show bk_fixture_lhod --json` prints `"status": "shelved"`).

Steps:

- Open the book's page: `shelf-drive web open /books/bk_fixture_lhod`. The title and a **Lend** button are visible.
- Start lending from the button: `shelf-drive web click 'button "Lend"'`. A dialog titled "Lend this book" opens with a friend picker.
- Pick the friend and a due date: `shelf-drive web fill 'combobox "Friend"' "Rosa Diaz"` then `shelf-drive web fill 'textbox "Due date"' 2026-11-15`. Both fields show the chosen values.
- Confirm: `shelf-drive web click 'button "Lend book"'`. The dialog closes and the page shows a "Lent to Rosa" badge with "Due 15 Nov 2026".
- Read the loan back: `shelf show bk_fixture_lhod --json`. Output has `"status": "lent"`, `"borrower": "fr_fixture_rosa"`, `"due": "2026-11-15"`.
- Check the friend's page: `shelf-drive web open /friends/fr_fixture_rosa`. "The Left Hand of Darkness" is listed under "Has borrowed".
- Try to lend it again (`lend.guard`): `shelf lend bk_fixture_lhod --to fr_fixture_rosa`. Exit code 3, stderr says the book is already lent to Rosa Diaz, and `shelf show` still prints the original due date.
- Return it: `shelf return bk_fixture_lhod`. Exit code 0. `shelf show bk_fixture_lhod --json` prints `"status": "shelved"` and no borrower.
- Lend with the shortcut: `shelf-drive web open /shelf`, `shelf-drive web click 'article "The Left Hand of Darkness"'`, `shelf-drive web key L`. The same "Lend this book" dialog opens. Cancel it with `shelf-drive web key Escape` and confirm `shelf show` still prints `"status": "shelved"`.
- Lend from the CLI: `shelf lend bk_fixture_lhod --to fr_fixture_rosa --json`. Exit code 0, JSON includes the new loan id.
- Capture: `shelf-drive capture lend` saves the a11y dump, screenshot, and CLI recordings under `./verify-artifacts/lend/`.
- Restore: `shelf-drive seed --reset`.

## Gotchas

- `L` types the letter into any focused text field instead of opening the dialog. Click a book card first so focus is on the card.
- The friend picker filters as you type and needs about 200 ms. Wait for `option "Rosa Diaz"` to appear before pressing Enter; do not sleep a fixed time.
- The "Book lent" toast appears even when the save request later fails. It is not proof. Read the loan back with `shelf show`.
- The due date renders in the browser's locale. Assert on the read-back JSON value, not on the rendered text, unless the recipe pins the locale with `shelf-drive web open --locale en-GB`.
- `seed --reset` restores fixtures but must not clear `./verify-artifacts/`. If artifacts disappear after a reset, the seed script is wrong; report it.
