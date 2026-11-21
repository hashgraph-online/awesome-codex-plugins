# Risk questions by kind of change

Questions a kickoff should answer before any code exists, grouped by the kind of change that raises them. Read the
sections that match your ticket during the context sweep, and turn each question that applies into a question for an
investigator or a line in the plan. Skip the rest: most tickets touch two or three sections at most.

## Stored data, migrations and repairs

- Has the bug already written wrong data? A fix that stops new damage leaves the old damage in place, so the repair
  (or the question of whether to repair) belongs in the plan.
- Does a batched update or delete still select the right rows after earlier batches have run?
- Can the app write the same column between the deploy and a backfill (a default applied on save, a running job)?
- Can a user undo the migration's change by hand later, and does the result still make sense?

## Renamed or changed contracts

- What have clients already stored from the old contract (saved settings, subscriptions, cached IDs, workflow
  state), as well as the calls they make today? How does each one upgrade?
- When a fix changes what a client sends, what does the consumer do with each new payload shape, including empty
  arrays and nulls?
- Which client versions still in use read the response or message you're changing, and how does each one handle it?
- Does every entry point that builds the request set the parameter you're gating on?

## Scripts people run by hand

- What happens on a second run, with steps done out of order, or with a mistyped argument?
- Does a failed run leave anything behind that stops the next run?

## Calls to external services

- For each error the service can return, is the outcome "definitely not done", "refused" or "unknown"? Never retry
  an unknown as if it had failed, and check whether the client library already retries.
- Does every path that reuses an existing row claim it atomically? A unique index guards inserts only.
- Are permanent refusals kept from being retried forever and from blocking the rest of the work?

## Concurrency: jobs, locks and saves

- When a job saves a record it loaded earlier, which other writers touch that row? Lock, reload and recheck before
  saving.
- When you add a lock, does every caller take locks in the same order?
- Does every path that changes what a guard protects also write the column the guard reads? Bulk updates and admin
  tools often skip callbacks.
- Do retries and duplicate jobs write to their own storage keys, and does cleanup delete only what nothing points at?

## Authentication, permissions and sessions

- Which permission does each entry point require for the new action?
- Does a new side effect of an authentication step (recording last use, counting attempts) happen before checks
  that can still reject the request?
- Does a new check in shared middleware cover every way a request can be authenticated (session, cookie, API token)?
  Run the tests for every request it now covers.
- Does a requirement keyed on a session value survive every place the session is reset?
- Do the tests cover the denied combinations as well as the allowed ones?

## Moving files, code or boot order

- Do CI config, lint configs and their ignore files, git hooks and cache lists name the old path?
- When code moves earlier or later in boot, what does it overwrite, and what overwrites it?
- When a ticket says "follow the pattern of X", what setup beyond X's main files does the pattern have (registries,
  CI lists, indexes)?

## Dependency, tool and runtime upgrades

- What do the release notes say for every version in the jump, not only the latest?
- Does every kind of input the app feeds the tool still work, in the shapes real inputs have?
- Which jobs and images call a shared script you're changing?

## Performance

- Which workloads does the change affect? Measure representative, approved ones in each environment the change
  affects, and record the setup, the variance and the scripts so someone else can repeat the comparison.
- Quote only numbers a saved run produced.

## Layout of text you didn't write

- What do the longest and oddest inputs do to the layout (a long word, a URL, unclosed markup), as well as today's
  data?

## Tests

- Does each new test fail when you break the behavior it covers? Give every acceptance criterion its own assertion.
- Do the test's inputs reach the mechanism being fixed, or would it pass either way?
- Does a validation test send a request through the real stack? Middleware may reject or rewrite the input first.
- Does the test read data back the way the app does? A reload can bypass scopes that the app's queries apply.
- Does a test that changes global configuration restore the original, rather than a hard-coded value?

## Removing or changing behavior

- Which flags, settings and code paths can still send work to a component you're removing?
- Where do the docs tell users how to use a setting whose behavior you're changing?

## Add your own

When a final review, a second reviewer, CI, QA or the user finds something the kickoff should have caught, write it up
like this, show it to the user, and add the question to the matching section above (or start a new section):

```
- Missed: <what the kickoff didn't look at>
- Found by: <self-review, second reviewer, CI, QA, the user>
- Question: <one question, general enough to apply to the next ticket of this kind>
```

Add only questions that would help the next ticket of the same kind. A fix for one unusual input, one library's quirk
or one environment belongs in the AGENTS.md next to that code instead. Leave out ticket numbers, dates, customer names,
and any detail of a weakness that is still open.
