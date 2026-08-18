# Xquik Extraction Tools

23 bulk data extraction tools. Each requires a specific target parameter.

## Privacy and Acceptable Use

Bulk extraction and export can collect large amounts of public identity,
activity, and relationship data. Before creating a job, confirm the lawful
purpose, target, `resultsLimit`, intended recipients, and retention period.
Follow X rules and applicable privacy law. Do not use these tools for
credential collection, private data, surveillance, discrimination, harassment,
doxxing, or unrelated secondary use. Delete exported data when the approved
purpose ends.

Every extraction requires an estimate and explicit approval for the exact
bounded job. Never infer approval from a general request or increase a bound
without renewed approval.

The API accepts an omitted `resultsLimit`. This Skill must always send an
explicit finite positive bound. Use the same bound for estimate and create.

**Endpoint:** `POST /extractions`

**Always estimate first:** `POST /extractions/estimate` with the same body to preview `creditsRequired`, `creditsAvailable`, and whether the job is allowed.

## Contents

- [Tool Types](#tool-types)
- [Response](#response)
- [Retrieving Results](#retrieving-results)
- [Exporting Results](#exporting-results)
- [Estimating Usage](#estimating-usage)

## Tool Types

### Tweet-Based (require `targetTweetId`)

| Tool Type | Description |
|-----------|-------------|
| `reply_extractor` | Extract users who replied to a tweet |
| `repost_extractor` | Extract users who retweeted a tweet |
| `quote_extractor` | Extract users who quote-tweeted a tweet |
| `thread_extractor` | Extract all tweets in a thread |
| `article_extractor` | Extract article content linked in a tweet |
| `favoriters` | Extract users who favorited a tweet |

**Example:**
```json
{
  "toolType": "reply_extractor",
  "targetTweetId": "1893704267862470862"
}
```

### User-Based (require `targetUsername`)

| Tool Type | Description |
|-----------|-------------|
| `follower_explorer` | Extract followers of an account |
| `following_explorer` | Extract accounts followed by a user |
| `verified_follower_explorer` | Extract verified followers of an account |
| `mention_extractor` | Extract tweets mentioning an account |
| `post_extractor` | Extract posts from an account |

**Example:**
```json
{
  "toolType": "follower_explorer",
  "targetUsername": "elonmusk"
}
```

The `@` prefix is automatically stripped if included.

### User Timeline Tools (require `targetUsername`)

| Tool Type | Description |
|-----------|-------------|
| `user_likes` | Extract tweets liked by a user |
| `user_media` | Extract media tweets from a user |

**Example:**
```json
{
  "toolType": "user_likes",
  "targetUsername": "elonmusk"
}
```

### Community-Based (require `targetCommunityId`)

| Tool Type | Description |
|-----------|-------------|
| `community_extractor` | Extract members of a community |
| `community_moderator_explorer` | Extract moderators of a community |
| `community_post_extractor` | Extract posts from a community |
| `community_search` | Search posts within a community (also requires `searchQuery`) |

**Example:**
```json
{
  "toolType": "community_extractor",
  "targetCommunityId": "1234567890"
}
```

### List-Based (require `targetListId`)

| Tool Type | Description |
|-----------|-------------|
| `list_member_extractor` | Extract members of a list |
| `list_post_extractor` | Extract posts from a list |
| `list_follower_explorer` | Extract followers of a list |

**Example:**
```json
{
  "toolType": "list_member_extractor",
  "targetListId": "1234567890"
}
```

### Space-Based (require `targetSpaceId`)

| Tool Type | Description |
|-----------|-------------|
| `space_explorer` | Extract participants of a Space |

**Example:**
```json
{
  "toolType": "space_explorer",
  "targetSpaceId": "1YqKDqDXAbwKV"
}
```

### Search-Based (require `searchQuery`)

| Tool Type | Description |
|-----------|-------------|
| `people_search` | Search for users by keyword |
| `tweet_search_extractor` | Search and extract tweets by keyword or hashtag |

**Example (people search):**
```json
{
  "toolType": "people_search",
  "searchQuery": "machine learning engineer"
}
```

**Example (tweet search):**
```json
{
  "toolType": "tweet_search_extractor",
  "searchQuery": "#AI",
  "resultsLimit": 100
}
```

### Tweet Search Filters

`tweet_search_extractor` accepts structured filters. It combines them with
`searchQuery` before collection.

| Field | Type | Description |
|-------|------|-------------|
| `fromUser` | string | Author username |
| `toUser` | string | Directed to user |
| `mentioning` | string | Mentions user |
| `language` | string | Language code (e.g., `en`) |
| `sinceDate` | string | Start date (YYYY-MM-DD) |
| `untilDate` | string | End date (YYYY-MM-DD) |
| `mediaType` | string | `images`, `videos`, `gifs`, `media`, `links`, or `none` |
| `minFaves` | number | Minimum likes |
| `minRetweets` | number | Minimum retweets |
| `minReplies` | number | Minimum replies |
| `minQuotes` | number | Minimum quote count |
| `minViews` | number | Minimum view count |
| `minBookmarks` | number | Minimum bookmark count |
| `maxLikes` | number | Maximum likes |
| `maxRetweets` | number | Maximum reposts |
| `maxReplies` | number | Maximum replies |
| `maxQuotes` | number | Maximum quotes |
| `blueVerifiedOnly` | boolean | Blue-verified authors only |
| `cardName` | string | Match the Tweet card name |
| `source` | string | Match the source application |
| `excludeSource` | string | Exclude a source application |
| `geocode` | string | Match latitude, longitude, and radius |
| `sinceId` | string | Tweets newer than this ID |
| `maxId` | string | Tweets older than this ID |
| `near` | string | Match a place name |
| `within` | string | Radius for the `near` filter |
| `withinTime` | string | Recent time window |
| `nativeRetweets` | boolean | Native reposts only |
| `safe` | boolean | Enable safe search |
| `news` | boolean | News results only |
| `verifiedOnly` | boolean | Verified authors only |
| `replies` | string | `include`, `exclude`, or `only` |
| `retweets` | string | `include`, `exclude`, or `only` |
| `quotes` | string | `include`, `exclude`, or `only` |
| `exactPhrase` | string | Exact match text |
| `excludeWords` | string | Comma-separated words to exclude |
| `anyWords` | string | Terms where any one can match |
| `hashtags` | string | Hashtags separated by spaces, commas, or lines |
| `cashtags` | string | Cashtags separated by spaces, commas, or lines |
| `url` | string | URL substring or domain |
| `conversationId` | string | Conversation ID |
| `inReplyToTweetId` | string | Replies to one Tweet ID |
| `quotesOfTweetId` | string | Quotes of one Tweet ID |
| `retweetsOfTweetId` | string | Reposts of one Tweet ID |
| `listId` | string | Search within a list |
| `place` | string | Search within a place ID |
| `placeCountry` | string | Search within a country code |
| `pointRadius` | string | Geographic point and radius |
| `boundingBox` | string | Geographic bounding box |
| `advancedQuery` | string | Raw X search operators appended to query |

**Example with filters:**
```json
{
  "toolType": "tweet_search_extractor",
  "searchQuery": "AI",
  "fromUser": "elonmusk",
  "minFaves": 100,
  "sinceDate": "2026-01-01",
  "mediaType": "videos",
  "resultsLimit": 500
}
```

`resultsLimit` (optional): Maximum results to extract. Stops early instead of fetching all. Pass this on both `POST /extractions/estimate` and `POST /extractions` when you only need a specific count.

### Profile Filters

Profile-producing extractions also accept `minFollowers`, `maxFollowers`,
`minFollowing`, `maxFollowing`, `minPosts`, `maxPosts`,
`minAccountAgeDays`, `verifiedType`, `hasWebsite`, `hasLocation`,
`bioContains`, `locationContains`, and `usernameContains`.

## Response

```json
{
  "id": "77777",
  "toolType": "reply_extractor",
  "status": "completed",
  "totalResults": 150
}
```

Statuses: `pending`, `running`, `completed`, `failed`.

## Retrieving Results

```
GET /extractions/{id}
```

Returns paginated results (up to 1,000 per page). Each result includes:

- `xUserId`, `xUsername`, `xDisplayName`
- `xFollowersCount`, `xVerified`, `xProfileImageUrl`
- `tweetId`, `tweetText`, `tweetCreatedAt` (for tweet-based extractions)

## Exporting Results

```
GET /extractions/{id}/export?format=csv
```

Formats: `csv`, `json`, `md`, `md-document`, `pdf`, `txt`, `xlsx`. 100,000 row limit (10,000 for PDF).

Exports include enrichment columns not present in the API response.

The endpoint supports follower, following, post, engagement, profile, media,
language, search, and date filters. It does not project individual fields.

**Approval required:** Set the smallest approved `resultsLimit` when creating
the job. Before export, show the job, filters, format, row count, schema,
recipients, storage, and retention. Materialize or transmit the dataset only
after explicit approval. Delete it when the approved purpose ends.

## Estimating Usage

```
POST /extractions/estimate
```

Same body as create. Response:

```json
{
  "allowed": true,
  "source": "replyCount",
  "estimatedResults": 150,
  "creditsRequired": "150",
  "creditsAvailable": "50000"
}
```

If `allowed` is `false`, do not create the extraction. It requires more credits
than are currently available.

For common mistakes and tool selection rules, see [mcp-tools.md](mcp-tools.md#common-mistakes).
