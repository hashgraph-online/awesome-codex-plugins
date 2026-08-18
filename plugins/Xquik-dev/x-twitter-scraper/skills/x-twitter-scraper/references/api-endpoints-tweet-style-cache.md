# Xquik REST API Endpoints: Tweet Style Cache

## Safety Boundary

Style creation, replacement, and deletion change persistent cached resources.
For analysis, show the username, estimated usage, and storage effect. For
custom saves, show the label, source tweets, and replacement effect. For
deletion, show the label or username and deletion effect. Proceed only after
explicit approval for that exact write.
Cached profiles and comparisons are account-scoped reads. Require exact-scope
approval before retrieving them.

### Analyze & Cache Style

`POST /styles`

Fetch recent tweets from an X account and cache them for style analysis. **Consumes metered API usage.**

**Approval required:** Confirm the username, metered usage, and intent to store
the resulting profile before creating the cache.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | X username to analyze (without @) |

**Response (201):**

```json
{
  "xUsername": "elonmusk",
  "tweetCount": 20,
  "isOwnAccount": false,
  "fetchedAt": "2026-02-24T10:30:00.000Z",
  "tweets": [
    {
      "id": "1893456789012345678",
      "text": "The future is now.",
      "authorUsername": "elonmusk",
      "createdAt": "2026-02-24T14:22:00.000Z"
    }
  ]
}
```

---

### List Cached Styles

`GET /styles`

List all cached tweet style profiles. Max 200 results, ordered by fetch date.

**Private read:** This endpoint returns the entire cached profile list, up to 200
entries. Show that scope, the purpose, downstream recipients, and retention plan.
List profiles only after explicit approval for that exact read.

**Response (200):**

```json
{
  "styles": [
    {
      "xUsername": "elonmusk",
      "tweetCount": 20,
      "isOwnAccount": false,
      "fetchedAt": "2026-02-24T10:30:00.000Z"
    }
  ]
}
```

---

### Save Custom Style

`PUT /styles/{id}`

Save a custom style profile from tweet texts. The body `label` controls the saved style label and replaces any existing style with that label.

**Approval required:** Preview the label and source texts. Warn when an existing
label will be replaced, then obtain explicit approval.

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | Yes | Style label name (1-30 characters) |
| `tweets` | object[] | Yes | Array of tweet objects (1-100). Each must have a `text` field |

**Response (200):** Style object with label, `tweetCount`, `isOwnAccount: false`, `fetchedAt`, and `tweets` array.

**Errors:** `400 invalid_input`

---

### Get Cached Style

`GET /styles/{id}`

Get a cached style profile with full tweet data. `id` is the cached style label or username.

**Private read:** Show the label or username. Retrieve its tweets only after
explicit approval for that exact read.

**Response (200):** Full style object with `tweets` array.

**Errors:** `404 style_not_found`

---

### Delete Cached Style

delete request to `/styles/{id}`

**Destructive action:** This permanently deletes the cached style profile.
Show the exact label or username and explain the lost cached data. Delete only
after explicit approval immediately before the call. Returns `204 No Content`.

**Errors:** `404 style_not_found`

---

### Compare Styles

`GET /styles/compare?username1=A&username2=B`

Compare two cached tweet style profiles side by side.

**Private read:** Show both labels or usernames. Compare only after explicit
approval for that exact read.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `username1` | string | Yes | First X username |
| `username2` | string | Yes | Second X username |

**Response (200):**

```json
{
  "style1": { "xUsername": "user1", "tweetCount": 20, "isOwnAccount": true, "fetchedAt": "...", "tweets": [...] },
  "style2": { "xUsername": "user2", "tweetCount": 15, "isOwnAccount": false, "fetchedAt": "...", "tweets": [...] }
}
```

**Errors:** `400 missing_params`, `404 style_not_found`

---

### Analyze Performance

`GET /styles/{id}/performance`

Get live engagement metrics for cached tweets for a cached style label or username. **Consumes metered API usage.**

**Private metered read:** Show the label or username and usage estimate.
Proceed only after explicit approval for that exact read.

**Response (200):**

```json
{
  "xUsername": "elonmusk",
  "tweetCount": 20,
  "tweets": [
    {
      "id": "1893456789012345678",
      "text": "The future is now.",
      "likeCount": 42000,
      "retweetCount": 8500,
      "replyCount": 3200,
      "quoteCount": 1100,
      "viewCount": 5000000,
      "bookmarkCount": 2400
    }
  ]
}
```

**Errors:** `404 style_not_found`

---
