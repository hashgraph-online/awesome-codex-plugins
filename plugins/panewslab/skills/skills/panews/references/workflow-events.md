# Events

**Trigger**: User wants to find crypto industry events — summits, hackathons, roadshows, online or offline.
Common phrases: "Any upcoming events", "Any summits in Singapore", "Are there any hackathons", "Any free events".

## Steps

### 1. List or search events

```bash
node cli.mjs list-events [--search "<keyword>"] [--category <type>] [--country <code>] [--online true|false] [--paid true|false] [--limit 15] [--sort status] [--as-of "<ISO 8601 time>"] --lang <lang>
```

Each invocation makes one event-list request and reads one page; it does not automatically fetch every page.

| Option | Behavior |
|--------|----------|
| `--limit` | Number of results, 1–100; default 15. It may change between pages. |
| `--cursor` | Opaque `nextCursor` from the previous response; omit for the first page. |
| `--sort status` | Ongoing → upcoming → ended; within each group, start time descending, then ID ascending. Omit to keep start time descending, then ID ascending. |
| `--as-of` | Optional fixed status time as ISO 8601 with `Z` or a time-zone offset, normalized to UTC. Omit on the first page for server time; on later pages, the cursor restores it. If supplied with a cursor, it must represent the same instant. |

`list-events` has removed `--take` and `--skip`; either option produces an error. Use `--limit` and the returned `--cursor` instead. Other commands keep their documented pagination parameters.

**Event categories (`--category`)**:

| Value | Meaning |
|-------|---------|
| SUMMIT | Summit |
| TECH_SEMINAR | Tech seminar |
| LECTURE_SALON | Lecture / salon |
| COCKTAIL_SOCIAL | Social / networking |
| ROADSHOW | Roadshow |
| HACKATHON | Hackathon |
| EXHIBITION | Exhibition |
| COMPETITION | Competition |
| OTHER | Other |

**Country / region codes (`--country`)**: AE CA CH CN DE FR GB JP KR SG TH TR US VN OTHER

### 2. Continue only when more results are needed

The CLI prints the activity details as Markdown followed by a separate JSON block with pagination metadata. For example:

```bash
node cli.mjs list-events --country SG --paid false --sort status --limit 15 --lang en
```

```json
{
  "nextCursor": "<opaque cursor>",
  "asOf": "2026-10-11T00:00:00.000Z",
  "query": {
    "limit": 15,
    "lang": "en",
    "sort": "status",
    "country": "SG",
    "paid": false
  }
}
```

`query` contains the resolved language and effective filters, using the CLI option names. Default sorting omits `sort`; absent filters are omitted. `nextCursor` and `asOf` come from the response headers and are `null` when the respective header is absent. The metadata does not echo the input cursor.

To continue, copy `nextCursor` and repeat the same filters, sort, and resolved language from `query`:

```bash
node cli.mjs list-events --country SG --paid false --sort status --limit 15 --lang en --cursor "<nextCursor>"
```

- Continue only while `nextCursor` is non-null; do not infer completion from the number of displayed records or an empty page.
- Do not decode or construct a cursor. Changing filters, sort, or language starts a new first-page request without the old cursor.
- `asOf` fixes the status time, not a database snapshot. Inserts, edits, or deletions can still affect later pages. If displaying status, use this time; the exact start and end instants count as ongoing.
- For an invalid or mismatched cursor (HTTP 400), restart from the first page with valid options; do not fall back to old API pagination. After a network failure, retry the same cursor and conditions.

### 3. View event details

The event list already contains full information (location, time, online/offline, paid/free, price, link, topic tags).
For more information, direct the user to the `url` field.

## Output requirements

- Include time, location, and type for each event
- Indicate if it's free (`isPaid=false`) or online (`isOnline=true`)
- Show price information if available
- Do not evaluate the quality or value of events
