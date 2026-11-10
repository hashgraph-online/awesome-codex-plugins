# Todos

A todo list kept in the browser: add, complete, filter, delete, with a
remaining count.

## Sub-features

- Add with the `Add` button or Enter in the `New todo` field; an empty
  submission adds nothing.
- Complete with the checkbox labelled by the todo's title.
- Filter with the `Filter` tablist: All, Open, Done.
- Delete with the `Delete <title>` button; the list persists across
  reloads.

## How to get to it (user POV)

Nav link `Todos`, or `/todos`. No account.

## Driving it with e2e

`tests/todos.e2e.ts` pins all of it. Locators, checked with `locate`:
`screen.getByLabel('New todo')`, `screen.getByRole('button', 'Add')`,
`screen.getByTestId('todo')`, `screen.getByRole('status', 'Remaining')`,
`screen.getByRole('tablist', 'Filter').getByRole('tab', 'Open')`,
`screen.getByLabel('<title>')` for a todo's checkbox,
`screen.getByRole('button', 'Delete <title>')`. Live walk:
`open_session`, `navigate /todos`, `type` into the `New todo` node,
`press Enter`, `observe`.

## Proof

On screen: one `todo` item per title in order, `Remaining` reads
`<n> remaining`, the selected tab hides the others' items. Store:
`localStorage.todos` holds the same titles and done flags
(`browser.evaluate(() => localStorage.getItem('todos'))`).

## Charters

```
todos-flow|web|skeptic|Starting at /todos, add, complete, filter, and delete todos; check the remaining count and every filter tab against the list
todos-input|web|fuzzer|Starting at /todos, submit the new todo field empty, with 300 characters, with unicode, and with leading spaces; report what is accepted, trimmed, or lost
```

## Gotchas

- Within one session or explore run, todos survive navigation and reload
  by design. Every test and every `open_session` starts from a fresh
  browser context, so a list that is not empty at the start of one is a
  bug.
