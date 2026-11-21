# Report format

The audit writes one machine-checked file, `money-audit/findings.json`, and a readable report rendered from it. The schema is in [../assets/findings.schema.json](../assets/findings.schema.json).

## findings.json

```json
{
  "version": 1,
  "project": "tutorly",
  "date": "2026-11-13",
  "environment": "Started with docker compose -f compose.test.yml up, test keys from .env.test, empty PostgreSQL. Two students created through /signup.",
  "notes": ["Not proved: tutor payouts may round per lesson instead of per payout. The payout job could not be run locally."],
  "findings": [
    {
      "id": "MA-01",
      "class": "balance-races",
      "severity": "critical",
      "title": "Parallel bookings all succeed against one lesson credit",
      "location": {
        "file": "app/services/booking.py",
        "line": 48,
        "snippet": "wallet.credits = wallet.credits - lesson.price"
      },
      "impact": "Any signed-in student can book several lessons at the same moment and pay for one. Each extra lesson is a tutor payout the platform funds itself.",
      "proof": {
        "kind": "probe",
        "command": "node scripts/probe.mjs race book.json --parallel 10 --observe wallet.json",
        "result": "All 10 requests answered 201 and 10 bookings were created. The wallet fell from 1 credit to 0."
      },
      "fix": "Deduct with one conditional statement (UPDATE wallets SET credits = credits - :price WHERE id = :id AND credits >= :price) and create the booking only when a row changed."
    }
  ],
  "coverage": [
    { "class": "balance-races", "status": "finding", "examined": ["app/services/booking.py", "app/models/wallet.py"] },
    { "class": "payout-controls", "status": "clear", "examined": ["app/services/tutor_payouts.py"], "note": "Payouts are reserved in a transaction, capped per day and sent with the payout id as the idempotency key." },
    { "class": "promo-and-referral-abuse", "status": "not-applicable", "note": "The app has no coupons, trials, bonuses or referral program." }
  ]
}
```

## Fields

| Field | Rule |
| --- | --- |
| `environment` | Optional, top level. How the app was run for the probes and how test accounts were made. |
| `notes` | Optional, top level. A list of sentences: suspicions that could not be proved, and any serious issue outside the money path. |
| `id` | `MA-01`, `MA-02`, in the order found. Unique. |
| `class` | One of the ten class ids. If a bug fits two, pick the one whose fix removes it. |
| `severity` | `critical`, `high`, `medium` or `low`, by the table in `SKILL.md`. |
| `title` | One sentence that says what happens, not what is missing. 10 to 140 characters. |
| `location.file` | Path relative to the project root. |
| `location.line` | The line where the flaw is: the missing check, the unsafe write. |
| `location.snippet` | At least 12 characters copied from that line. The validator looks for it within two lines of `line`, ignoring whitespace differences. |
| `impact` | Who can do it and what is lost. Plain words, in money or value. |
| `proof` | See below. |
| `fix` | The smallest change that removes the flaw. |

Every object in the file is closed: the report, a finding, its location, its proof, each trace step and each coverage entry accept only the fields listed on this page, and the validator rejects any other. The schema follows the same rule.

### Proof

| `kind` | Required fields |
| --- | --- |
| `probe` | `command` (what was run, with placeholders such as `$TOKEN` instead of real tokens), `result` (what it showed, with the numbers). A proof of several steps lists its commands in order, separated by `;`. One run may support more than one finding. Optional `output_file`: a saved copy of the probe output inside the project, for example `money-audit/evidence/ma-01.json`. |
| `test` | `file` (the test, must exist), `command`, `result`. Optional `output_file`, as for `probe`. |
| `trace` | `steps`: two or more of `{ "file", "line", "snippet", "note" }`, from where the value enters to where money moves. Each snippet is checked like the location. No `output_file`. |

### Coverage

All ten classes appear exactly once. The example above is shortened to three.

| `status` | Meaning | Required |
| --- | --- | --- |
| `finding` | At least one finding has this class | `examined`: the files read. Optional `note` for paths in the class that were checked and are clear. |
| `clear` | Looked for it and found the guard | `examined`, and a `note` naming the guard |
| `not-applicable` | The app has no such feature | a `note` saying why |

## Validate, then render

```bash
node scripts/validate-findings.mjs money-audit/findings.json --root .
node scripts/render-report.mjs money-audit/findings.json --root . --out money-audit/REPORT.md
```

`--root` is the project directory that the file paths are relative to. The renderer refuses a file the validator rejects.

When the validator reports that a snippet is not at the stated line, it also says where in the file that text is, if anywhere. Reread the code. Either correct the line, or accept that the finding described code that is not there and withdraw it.

## Writing the findings

- One flaw, one finding. Two endpoints with the same flaw are two findings only if they need separate fixes.
- Put the number in the result: "balance rose from 0 to 1000", "5 gift cards were issued for one 1000-coin balance".
- Describe impact for the business, not the attacker's technique: "free credits for any signed-in user", not "IDOR".
- Do not soften or inflate. If the loss needs a valid partner key, say so and rate it high, not critical.
- Do not include secrets, tokens or real user data anywhere in the file.
