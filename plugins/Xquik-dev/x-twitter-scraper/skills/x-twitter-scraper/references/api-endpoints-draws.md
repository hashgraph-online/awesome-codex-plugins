# Xquik REST API Endpoints: Draws

## Safety Boundary

Draw creation and participant exports are metered or privacy-sensitive actions.
Confirm the source tweet, eligibility rules, requested data type, export
audience, and retention plan. Use the smallest necessary dataset. Do not
export entries for surveillance, discrimination, harassment, or unrelated
secondary use.
Draw history and results are account-scoped private reads. Require exact-scope
approval before listing draws or retrieving winners.

### Create Draw

```
POST /draws
```

Run a giveaway draw from a tweet. Picks random winners from replies.

**Approval required:** Show the source tweet, winner count, backup count,
filters, and estimated usage. Also show the lawful purpose, participant-data
handling, export audience, and retention plan. Record every field before
persisting participant data.

**Body:**
```json
{
  "tweetUrl": "https://x.com/user/status/1893456789012345678",
  "winnerCount": 3,
  "backupCount": 2,
  "uniqueAuthorsOnly": true,
  "mustRetweet": true,
  "mustFollowUsername": "burakbayir",
  "filterMinFollowers": 100,
  "filterAccountAgeDays": 30,
  "filterLanguage": "en",
  "requiredKeywords": ["giveaway"],
  "requiredHashtags": ["#contest"],
  "requiredMentions": ["@xquik"]
}
```

All filter fields are optional. Only `tweetUrl` is required.

**Response:**
```json
{
  "id": "42",
  "tweetId": "1893456789012345678",
  "tweetUrl": "https://x.com/user/status/1893456789012345678",
  "tweetText": "Like & RT to enter! Picking 3 winners tomorrow.",
  "tweetAuthorUsername": "xquik",
  "tweetLikeCount": 4200,
  "tweetRetweetCount": 1800,
  "tweetReplyCount": 1500,
  "tweetQuoteCount": 120,
  "status": "completed",
  "totalEntries": 1500,
  "validEntries": 890,
  "createdAt": "2026-02-24T10:00:00.000Z",
  "drawnAt": "2026-02-24T10:01:00.000Z"
}
```

### List Draws

```
GET /draws
```

Cursor-paginated. Returns compact draw objects.

**Private read:** Show the exact account, requested page scope, and returned
field scope. List draws only after explicit approval for that exact read.

### Get Draw

```
GET /draws/{id}
```

Returns full draw details including winners.

**Private read:** Show the exact account, draw ID, and returned-data scope.
Retrieve details only after explicit approval for that exact read.

### Export Draw

```
GET /draws/{id}/export?format=csv&type=winners
```

Formats: `csv`, `json`, `md`, `md-document`, `pdf`, `txt`, `xlsx`. Types: `winners` (default), `entries`. Entry exports capped at 100,000 rows (PDF capped at 10,000).

**Approval required:** Full entry exports can contain participant identity and
activity data. Show the lawful purpose, exact draw, type, format, audience, and
retention period. Export only after explicit approval for that exact request.
Prefer winners-only output. Do not retain data beyond the approved purpose.

---
