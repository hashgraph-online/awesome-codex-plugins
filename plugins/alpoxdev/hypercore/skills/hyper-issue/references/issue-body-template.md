# Issue Body Template

Use this reference when writing the body. Copy the skeleton and replace every placeholder. Keep the `##` names and the `hyper:` keys exactly as written. Write the title and every placeholder replacement in English (`rules/issue-contract.md` §2a); the title takes the commit-subject form `type(scope): imperative summary`.

## Contents

- Skeleton
- Worked example
- Rules

## Skeleton

```markdown
## What

<One paragraph. What is wrong, or what is wanted. Who is affected and what changes for them.>

## Evidence

- `<path>:<line>` - <what this shows>
- `<command>` -> <the observed output, trimmed to the lines that matter>

<Assumption lines, when anything above is inferred:>
- Assumption: <the inferred statement> - Confirm by: <what would confirm it>

## Cause

<bug: the confirmed cause, tied to the paths above. State the symptom, the trigger, and the cause separately.>

## Intended behavior

<feature or task: the decided behavior, including the error path and the unchanged behavior.>

## Scope

<The exact change boundary in one or two sentences. What is edited, added, or removed.>

```yaml
hyper:
  touches:
    - <path or glob>
  depends_on: []
  conflicts_with: []
  lane_hint: <kebab-case>
  verify: "<literal command>"
  size: <s | m | l>
```

## Out of scope

- <Something a reader might assume is included and is not>

## Acceptance

- [ ] <Binary check with its command and expected result>
- [ ] <Error-path check>

## Verify

```sh
<the literal command from hyper.verify>
```

Pass: <what the output looks like when the work is done>.
```

## Worked Example

Real issues are written in English, so the example is the exact text an issue carries.

Title: `fix(orders): return 409 on idempotency key replay`

```markdown
## What

`POST /api/orders` returns 500 instead of 409 when the same idempotency key is replayed within the retry window. Callers retrying after a timeout create duplicate orders.

## Evidence

- `src/api/orders.ts:88` - the idempotency key is read after the insert attempt
- `bun test src/api/orders.test.ts` -> `1 fail: replays a duplicate key` with `duplicate key value violates unique constraint`
- `docs/contracts/orders.md:14` - the contract requires 409 on replay

## Cause

The insert runs before the key lookup at `src/api/orders.ts:88`, so a replay reaches the database unique constraint and the unhandled error becomes a 500. The contract lookup was added later at `:95` and never moved ahead of the insert.

## Scope

Move the key lookup before the insert and return 409 with the stored order id when a replay is found. The insert path and the response shape for new orders stay unchanged.

```yaml
hyper:
  touches:
    - src/api/orders.ts
    - src/api/orders.test.ts
  depends_on: []
  conflicts_with: []
  lane_hint: orders-idempotency
  verify: "bun test src/api/orders.test.ts"
  size: s
```

## Out of scope

- Changing the retry window length
- Backfilling duplicate orders already created

## Acceptance

- [ ] `bun test src/api/orders.test.ts` passes, including the replay case asserting 409 and the original order id
- [ ] A first request still returns 201 with a new order id

## Verify

```sh
bun test src/api/orders.test.ts
```

Pass: every case green, and the replay case logs `409` rather than `500`.
```

## Rules

- The body stands alone: no "as discussed", no link required to understand it, and English throughout except quoted output.
- Keep quotes short and attributed; redact secrets.
- One `hyper:` block per body, and it is the only fenced `yaml` block in `## Scope`.
- `verify` must be runnable without a browser, credentials, or a network call unless the issue says otherwise.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The body sections, the `hyper:` keys, and the worked example shape | this package's design over the issue-authoring prior art, 2026-11-07 |
| A body that stays actionable after its logs and sessions are gone | [kdy1-scripts add-issue](https://github.com/kdy1/kdy1-scripts) |

### Evidence grade

`LOCAL` - the template and the example are this package's own, written for this repository's issue flow.
