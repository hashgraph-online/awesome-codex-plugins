# Django Validation Patterns

## Validation Ownership

| Rule Type | Preferred Home | Test Boundary |
| --- | --- | --- |
| Required input, field shape | Form | Instantiate form and inspect errors |
| Cross-field user input rule | Form clean method | Form test with valid and invalid data |
| Database uniqueness or relationship integrity | Constraint/model | Model or database test |
| Request branch, redirect, template selection | View | Django client test |
| User sees error and can recover | Browser or client/template test | One high-value integration check |

## Model Validation Caveat

Django model `save()` does not automatically call full validation. If a rule must be enforced for every write, prefer database constraints or ensure all write paths call the validation boundary intentionally.

When testing constraint failures inside `TestCase`, use an inner transaction if needed so the test can continue after the expected database error.

## Form Refactor Sequence

1. Characterize current view behavior with a client test.
2. Add form tests for valid data, invalid data, and rendered field attributes that matter.
3. Move parsing and validation into the form.
4. Update the view to delegate to the form.
5. Keep a view-level test that proves the form is wired into GET/POST paths.

## ModelForm Tradeoffs

ModelForms are valuable when the UI maps naturally to the model. Be cautious when:

- The model field names or IDs should not become the public HTML contract.
- The form save behavior needs extra context.
- Presentation classes or labels would couple domain fields to the page design.

Use explicit fields and tests when choosing ModelForm.

## Duplicate Handling

Cover duplicates at multiple levels only when each level owns something different:

- Constraint/model: duplicates cannot persist.
- Form: duplicate input produces a useful field or non-field error.
- View/template: invalid input redisplays the page with the user's attempted data.
- Functional test: a user can recover from the duplicate submission.

## Invalid Save Checklist

- [ ] Error text or form errors are visible.
- [ ] No invalid row was created.
- [ ] Existing valid data remains untouched.
- [ ] Status code or redirect matches the contract.
- [ ] The test fails for the intended reason before the fix.
