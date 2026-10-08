# Extraction jobs

Use an extraction for a complete list, a large dataset, or a file export.
Each job bills 1 credit per delivered tweet or profile, and
`article_extractor` 5 per article. So 10,000 tweets cost 10,000 credits, or
$1.50.

## Flow

| Call | Contract |
| --- | --- |
| `POST /extractions/estimate` | Free. Creates nothing. Takes the job body: `toolType`, its target, the requested filters & `resultsLimit`. Without a cap the API uses 10,000. Returns `allowed`, `estimatedResults`, `creditsRequired`, `creditsAvailable` & `source` |
| `POST /extractions` | Same body plus a new `Idempotency-Key`. A retry with that key returns the original job. `202` returns the job `id`, `status` & `statusUrl` |
| `GET /extractions/{id}` | Returns `job`, `results`, `hasMore`, `nextCursor` & `pollAfterMs`. `job.status` ends as `completed`, `failed`, or `canceled`. Rows come 100 per page, up to 1,000 with `limit=1000`. Send `nextCursor` back as `cursor` |
| `GET /extractions/{id}/export?format=csv` | Formats: `csv`, `json`, `md`, `md-document`, `pdf`, `txt`, `xlsx`. 1 export holds up to 100,000 rows, and PDF up to 10,000 |

- `creditsRequired` & `creditsAvailable` are numeric strings. Convert them
  before any math.
- `creditsRequired` is a charge ceiling, not an exact bill. Skipped or
  filtered rows cost nothing.
- `estimatedResults` is a conservative billing count, such as the follower
  count or the `resultsLimit` cap. It is not a count of matching posts.
  `source` names which one it used.
- `allowed: false` means the balance cannot fund the job. Lower
  `resultsLimit`, or the user adds credits in the dashboard.
- Show the estimate & get a yes before `POST /extractions`. Create nothing
  before that yes.
- Wait `pollAfterMs` between status reads.
- Always give the download call. For a job over the export limit, page
  `GET /extractions/{id}?limit=1000` from the start instead, so no row
  appears twice.

`DELETE /extractions/{id}` cancels a running job.

```json
{
  "toolType": "follower_explorer",
  "targetUsername": "nasa",
  "resultsLimit": 5000
}
```

## Tools and targets

| Target field | Tools |
| --- | --- |
| `targetTweetId` | `reply_extractor` (reply authors), `repost_extractor`, `quote_extractor`, `favoriters` (needs a connected X account), `thread_extractor`, `article_extractor` |
| `targetUsername` | `follower_explorer`, `following_explorer`, `verified_follower_explorer`, `mention_extractor`, `post_extractor`, `user_media`, `user_likes` (needs a connected X account) |
| `targetCommunityId` | `community_extractor` (members), `community_moderator_explorer`, `community_post_extractor`, `community_search` (also needs `searchQuery`) |
| `targetListId` | `list_member_extractor`, `list_post_extractor`, `list_follower_explorer` |
| `targetSpaceId` | `space_explorer` (participants) |
| `searchQuery` | `tweet_search_extractor`, `people_search` |

Multi-target jobs use `targetUsernames`, `targetTweetIds`, `searchQueries`,
`targetCommunityIds`, or `targetListIds`, with `maxItemsPerTarget`.

## Search filters

`tweet_search_extractor` takes the query in `searchQuery` and these optional
top-level filters: `fromUser`, `toUser`, `mentioning`, `language`,
`sinceDate`, `untilDate`, `mediaType`, `minFaves`, `minRetweets`,
`minReplies`, `minQuotes`, `verifiedOnly`, `replies`, `retweets`, `quotes`,
`exactPhrase`, `excludeWords`, `anyWords`, `hashtags`, `cashtags`, `url`, and
`queryType` (`Latest` default, or `Top`). Send only the filters the user asked
for.

```json
{
  "toolType": "tweet_search_extractor",
  "searchQuery": "solar panels",
  "language": "en",
  "sinceDate": "2026-01-01",
  "untilDate": "2026-06-30",
  "retweets": "exclude",
  "resultsLimit": 20000
}
```

Profile tools accept `minFollowers`, `maxFollowers`, `verifiedOnly`,
`bioContains`, `locationContains`, and `minAccountAgeDays`.

## Results

Rows keep stable IDs. Store the job ID, body, and collection time with the
file. Deleted, protected, or unavailable content can be missing, so counts can
differ from the numbers X shows on a profile or post.
