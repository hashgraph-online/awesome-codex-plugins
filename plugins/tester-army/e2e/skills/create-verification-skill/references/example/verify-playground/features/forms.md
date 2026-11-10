# Profile form

A profile form with text, textarea, select, a typeahead, checkboxes,
validation, and a save status.

## Sub-features

- `Full name`, a `Bio` textarea (placeholder `Tell us about yourself`), a
  `City` field with a `City suggestions` list that fills as you type, a
  `Team` select with options such as `Web` and `Mobile`, and a
  `Notifications` group with `Email notifications` and `Weekly digest`.
- `Save profile` reports in the `Save result` status. An empty
  `Full name` reports `Name is required`; the other fields are optional.

## How to get to it (user POV)

Nav link `Forms`, or `/forms`. No account.

## Driving it with e2e

`tests/forms.e2e.ts` pins fill, clear, select, check, submit, validation,
and the typeahead. Locators: `screen.getByLabel('Full name')`,
`screen.getByPlaceholder('Tell us about yourself')`,
`screen.getByLabel('City')` with
`screen.getByRole('list', 'City suggestions')`,
`screen.getByLabel('Team')` with `selectOption('Web')`,
`screen.getByRole('group', 'Notifications')`,
`screen.getByRole('button', 'Save profile')`,
`screen.getByRole('status', 'Save result')`.

## Proof

`Save result` reads `Saved profile for <name>` with the name as typed, and
the `Team` select holds the chosen value. The server stores nothing;
there is no side effect beyond the screen.

## Charters

```
forms-input|web|fuzzer|Starting at /forms, submit each field empty, too long, with unicode, and with leading spaces; report validation that is missing or wrong, and any saved value that differs from what was typed
```

## Gotchas

- The save status is the whole proof; a reload clears the form by design.
- The `City` field reacts to key events, not to a plain fill; the test
  shows the `press` sequence.
