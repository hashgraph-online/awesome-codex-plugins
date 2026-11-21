# Feature map

One file per user-facing feature of the playground, from the user's point
of view. Each names the test that pins it, the locators that matter, the
proof, and its bug-bash charters. The nav lists more pages (Wizard,
Checkout, Network, Dialogs, Board, Pointer, Frames, Canvas, Keypad, Canvas
wizard, Canvas form, Downloads, Release notes, Controls, Scroll, Browser,
Speed, About); map them when they matter to a change.

| Feature | Route | Test | Status |
| --- | --- | --- | --- |
| [Todos](todos.md) | `/todos` | `tests/todos.e2e.ts` | tested |
| [Profile form](forms.md) | `/forms` | `tests/forms.e2e.ts` | tested |
| [Sign in and dashboard](login.md) | `/login`, `/dashboard` | `tests/auth.setup.e2e.ts`, `tests/dashboard.e2e.ts` | tested |
