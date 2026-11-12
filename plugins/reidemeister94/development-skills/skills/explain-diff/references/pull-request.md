# Pull request description

The reader is a teammate who knows nothing about the project or the task, and who has a few minutes.
After reading, the reviewer knows what changed from before and the ideas behind it.
The reviewer also knows why it was built this way, what happens in a real case, and what happens on a failure.
Short is better, as long as nothing the reviewer needs is missing.
Aim for about 30 lines for planned work, and under 10 for a small fix.
State each fact once. A diagram replaces the list it would repeat, and a reason appears only under the reasons.

## Content

Use the five parts of the explanation in the language of the project's pull requests, then add one part:

- **How it was checked:** one or two lines on what ran, on which data, and what the reviewer can still try.

Leave out what the reviewer already has or does not need:

- the list of changed files, and a retelling of the diff;
- counts without meaning, such as "48 passed";
- the story of the work, and words such as "comprehensive" or "robust";
- internal names, except the one place where the reviewer should start reading.

Take the example and the error cases from tests, data, or logs. Ask no questions.
When new commits change the behavior, rewrite the whole description so it matches the branch.
Write the body to a temporary file outside the repository, and pass it with `gh pr create --body-file` or `gh pr edit --body-file`.

## Example

The shape, for an invented change:

```markdown
## What changes

Before, an order over the customer's credit limit reached the ERP and failed in the nightly job. Sales found out the next morning.
Now the order screen refuses it at once and shows how much credit is left.

## Concepts

- **Credit limit:** the most a customer may owe us. Finance sets it in the ERP.
- **Exposure:** what the customer owes now: unpaid invoices plus open orders.

## Example

Customer C-1042 has a limit of 50,000 EUR and an exposure of 46,000 EUR. A seller enters an order of 6,000 EUR.
`POST /orders` computes 52,000 EUR, above the limit, and answers 422 "Credit limit exceeded: 4,000 EUR available". No order is saved.

## Errors

- The ERP does not answer within 5 s: the order is saved as "to check" and finance sees it in the morning list.
- The customer has no limit in the ERP: the order passes, as before.

## Why

The check runs when the order is entered, because the nightly job finds the problem too late.
The limit is read live: finance changes limits during the day, so a cached copy would be stale.

## How it was checked

Tests cover an order exactly at the limit, one above it, and an ERP timeout. Tried on staging with C-1042.
```
