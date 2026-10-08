# Read routes

All routes use `https://xquik.com/api/v1` and the `x-api-key` header. `{id}`
accepts a username without `@` or a numeric user ID unless noted. Tweet IDs are
numeric strings.

## Request example

Send reads through the Python `get_json` helper from [Retries](#retries):

```python
page = get_json(
    "/x/tweets/search",
    {"q": "climate policy", "sinceDate": "2026-09-01", "limit": 100},
)
```

## Tweets

| Route | Key parameters |
| --- | --- |
| `GET /x/tweets/search` | `q` (required), `queryType` (`Latest` default, or `Top`), `limit` (1 to 10,000, default 20), `cursor` |
| `GET /x/tweets/{id}` | Tweet ID |
| `GET /x/tweets?ids=` | Up to 100 comma-separated tweet IDs |
| `GET /x/tweets/{id}/replies` | `pageSize` (1 to 300), `sort` (`relevance`, `latest`, `oldest`, `likes`), `excludeOriginalAuthor`, `includeOriginalPost`, `hasMediaOnly`, `scope`, `cursor` |
| `GET /x/tweets/{id}/quotes` | `pageSize` (1 to 300), `sinceTime`, `untilTime`, `includeReplies`, `cursor` |
| `GET /x/tweets/{id}/thread` | Visible posts in the conversation thread, from any author: `pageSize` (1 to 100), `cursor` |
| `GET /x/tweets/{id}/retweeters` | `pageSize` (1 to 200), profile filters, `cursor` |
| `GET /x/tweets/{id}/favoriters` | `pageSize` (1 to 200), profile filters, `cursor` |
| `GET /x/articles/{tweetId}` | Full X Article content |

Search, replies, quotes, thread, and user timelines accept the same tweet
filters as named query parameters. Send only the ones the user asked for:

- Authors and targets: `fromUser`, `toUser`, `mentioning`, `verifiedOnly`,
  `blueVerifiedOnly`
- Text: `exactPhrase`, `anyWords`, `excludeWords`, `hashtags`, `cashtags`, `url`
- Time: `sinceDate` and `untilDate` (`YYYY-MM-DD`), `sinceTime` (ISO,
  inclusive) and `untilTime` (ISO, exclusive, so end 2023 with
  `2024-01-01T00:00:00Z`), `withinTime` (such as `7d`)
- Language: `language` (such as `en`)
- Media: `mediaType` (`images`, `videos`, `gifs`, `media`, `links`, `none`)
- Engagement: `minLikes`, `minRetweets`, `minReplies`, `minQuotes`,
  `minViews`, `minBookmarks`, `maxFaves`, `maxRetweets`, `maxReplies`
- Post types: `replies`, `retweets`, `quotes`, each `include`, `exclude`, or `only`
- Conversation: `conversationId`, `inReplyToTweetId`, `quotesOfTweetId`
- Raw operators: `advancedQuery` for a known X search operator string, on search only

Tweet responses hold `tweets`, `has_next_page`, and `next_cursor`. Each tweet
has `id`, `text`, `createdAt`, `lang`, `likeCount`, `retweetCount`,
`replyCount`, `quoteCount`, `viewCount`, `bookmarkCount`, `media`, and
`author` with `id`, `username`, and `name`. Optional fields are omitted when X
does not return them. A filtered page can be empty and still have a next page.

## Users

Use the user timeline for an account's latest posts. Its path accepts a
username or numeric ID.

| Route | Key parameters |
| --- | --- |
| `GET /x/users/{id}` | Profile: `followers`, `following`, `description` (bio), `verified`, `isVerified`, `isBlueVerified`, `verifiedType`, `statusesCount`, `location`, `createdAt` |
| `GET /x/users/search` | `q` (required), `pageSize` (1 to 100), profile filters, `cursor` |
| `GET /x/users/batch` | `ids` (comma-separated user IDs), profile filters |
| `GET /x/users/{id}/tweets` | `pageSize` (1 to 300, default 20), `sinceTime`, `untilTime`, `includeReplies` (default `false`), tweet filters, `cursor` |
| `GET /x/users/{id}/replies` | With Replies timeline: `pageSize` (1 to 300), `sinceTime`, `untilTime`, tweet filters, `cursor` |
| `GET /x/users/{id}/media` | `pageSize` (1 to 100), tweet filters, `cursor` |
| `GET /x/users/{id}/mentions` | `pageSize` (1 to 100), `sinceTime`, `untilTime`, tweet filters, `cursor` |
| `GET /x/users/{id}/likes` | `pageSize` (1 to 100), tweet filters, `cursor`. Needs a connected X account for the owner's likes |

Verification: `isBlueVerified` means X shows the blue badge. `isVerified` and
`verified` mean X marks the profile as verified. `verifiedType` names the kind,
such as `Business`. Report only the values the response returns.

## Relationships

| Route | Key parameters |
| --- | --- |
| `GET /x/users/{id}/followers` | `pageSize` (1 to 300), `cursor`, profile filters |
| `GET /x/users/{id}/following` | Same as followers |
| `GET /x/users/{id}/verified-followers` | Same as followers |
| `GET /x/followers/check` | `source` and `target` usernames. Returns `isFollowing` and `isFollowedBy` |

Profile filters, applied before billing: `minFollowers`, `maxFollowers`,
`minFollowing`, `maxFollowing`, `minStatuses`, `maxStatuses`,
`minAccountAgeDays`, `verifiedOnly`, `hasWebsite`, `hasLocation`,
`bioContains` (any comma-separated term, ignoring case), `locationContains`,
`usernameContains`. Profile pages return
`users`, `has_next_page`, and `next_cursor`. Use a `follower_explorer`
extraction for a complete follower list.

## Lists, communities, Spaces, and trends

| Route | Notes |
| --- | --- |
| `GET /x/lists/{id}/members`, `/followers`, `/tweets` | List ID |
| `GET /x/communities/{id}/info`, `/members`, `/moderators`, `/tweets` | Community ID |
| `GET /x/communities/search` | Search posts inside a community |
| `GET /x/trends` | `woeid`, a Yahoo WOEID (default 1, worldwide), and `count` (1 to 50, default 30) |
| `GET /radar` | Trending topics from curated sources: `category`, `region`, `hours`, `limit` |

Xquik documents and tests trends for these 12 regions. `GET /x/trends` passes
other WOEIDs to X, which may return no trends for them. The `GET /trends`
alias accepts only these 12.

| Region | WOEID | Region | WOEID |
| --- | --- | --- | --- |
| Worldwide | 1 | France | 23424819 |
| United States | 23424977 | Japan | 23424856 |
| United Kingdom | 23424975 | India | 23424848 |
| Turkey | 23424969 | Brazil | 23424768 |
| Spain | 23424950 | Canada | 23424775 |
| Germany | 23424829 | Mexico | 23424900 |

Spaces use the `space_explorer` extraction.

## Media

`POST /x/media/download` with JSON `{"tweetInput": "<tweet URL or ID>"}` for
one tweet, or `{"tweetIds": ["<id>", "..."]}` for up to 50 tweets.

- One tweet returns `tweetId`, `galleryUrl`, and `cacheHit`.
- Several tweets return `galleryUrl`, `totalTweets`, and `totalMedia`.
- `galleryUrl` is the page where the user saves the files.
- A tweet without media returns `400 no_media`.

A download grants no reuse rights. Tell the user to confirm permission before
using the media in their own work.

## AI analysis

These routes read posts and answer questions about each one with AI. Send a
JSON body with `POST`. Each analyzed post bills 2 credits, read included.

| Route | Answers |
| --- | --- |
| `POST /x/analysis/sentiment` | `sentiment`, `intensity`, `sarcasm` |
| `POST /x/analysis/brand` | `relevance`, `sentiment`, `experience` for the brand in `analysis.targets` |
| `POST /x/analysis/news` | `format`, `attribution`, `relevance` for the topic in `analysis.targets` |
| `POST /x/analysis/market-signals` | `stance`, `content`, `conviction`, `relevance`, plus bullish & bearish counts per cashtag |
| `POST /x/analysis/viral-score` | 8 wording traits, `viralScore` from 0 to 100 & `viralVerdict` |
| `POST /x/analysis/classify` | 1 to 8 questions you write in `analysis.questions` |

Send exactly 1 source:

- `tweetIds`: up to 100 post IDs or URLs.
- `texts`: up to 100 texts of the user's, such as drafts. Nothing is read
  from X.
- A search: `query`, `username`, `listId`, `quotesOf`, or `repliesTo`, alone
  or together, with `sinceTime`, `untilTime`, `queryType`, `limit` (1 to 100,
  default 20), and `cursor`.

`analysis` is optional: `targets` (names with `aliases`), `context`,
`questions`, or a `preset`. Question IDs and category names are lower case
with underscores.

Send each analysis once with the helpers from [Retries](#retries). A refused
call bills nothing. Ask the user before sending it again.

```python
response = requests.post(
    f"{BASE}/x/analysis/brand",
    headers=HEADERS,
    json={"username": "Sony", "limit": 50, "analysis": {"targets": [{"name": "Sony"}]}},
    timeout=60,
    allow_redirects=False,
)
page = read_body(response)
if not 200 <= response.status_code < 300 or isinstance(page, str):
    raise XquikError(f"{response.status_code}: {page}", response.status_code, page)
```

The response holds `results` (each post with its `answers`), `unanalyzed`
(free, with a `reason`), `analysisSummary` (totals per question, target and
cashtag), `has_next_page`, and `next_cursor`. Answers describe what posts say.
They do not verify claims or give investment advice.

## Private reads

These need a connected X account:

- `GET /x/dm/{userId}/history?account=<connected handle>`: `userId` is the
  other person's numeric ID. Resolve it with `GET /x/users/{username}`. It
  bills 1 credit per returned message and has no page size, so the last page
  can go past a message target. Give the cost per message, not a hard cap.
- `GET /x/bookmarks`, `GET /x/bookmarks/folders`, `GET /x/notifications`,
  `GET /x/timeline`
- `GET /x/accounts` lists connected accounts.

## Pagination and errors

- Follow `next_cursor` while `has_next_page` is true. Stop at the user's bound.
  Never build or decode a cursor.
- `409 coverage_cursor_unavailable`: wait the exact `Retry-After` seconds,
  then retry the same cursor. The helper below does this.
- `410 coverage_cursor_gone` or `400 invalid_coverage_cursor`: restart once
  without a cursor and deduplicate by ID. The paging loop below catches
  `XquikError` from the helper and restarts with the remaining budget.
- Generated paging code keeps one result budget across the entire run. Count
  every returned row before deduplication, including refetched rows after a
  restart. Lower later page sizes to the remaining budget. Persist IDs
  already appended across cron runs. An empty page can still have a cursor.
- `429`, `5xx`, and failed connections: retry as [Retries](#retries) shows.

## Retries

- Retry `GET` on `429`, `409 coverage_cursor_unavailable` with `Retry-After`, `5xx`, and
  connection failures, such as a refused or reset connection or a timeout.
- Wait `Retry-After` when the response has it. Otherwise back off
  exponentially from about 1 second, cap each wait at 30 seconds, and add
  jitter. Stop after about 5 minutes and report the last error.
- Retry the same URL and cursor, so pages are not skipped or repeated.
- Set a request timeout, such as 30 seconds, so a stalled connection cannot
  hang a run.
- Do not retry other `4xx` errors. Fix the request, or handle the cursor
  errors above.
- Parse bodies safely. An outage can return an HTML page, even with a `2xx`
  status, so parsing it as JSON throws. Retry that case.
- Never retry `POST`, `PATCH`, or `DELETE` automatically. See
  [writes](writes.md#responses-and-retries).

In JavaScript, `fetch` rejects on a refused or reset connection, so catch that
as a retryable failure. Read `await response.text()` and parse it inside
`try`.

```python
import os
import random
import time
from email.utils import parsedate_to_datetime

import requests

BASE = "https://xquik.com/api/v1"
API_KEY = os.environ.get("XQUIK_API_KEY", "").strip()
if not API_KEY or not API_KEY.isascii() or not API_KEY.isprintable():
    raise ValueError("Set XQUIK_API_KEY to a valid API key.")
HEADERS = {"x-api-key": API_KEY}
NETWORK_ERRORS = (
    requests.ConnectionError,
    requests.Timeout,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.ContentDecodingError,
)


class XquikError(Exception):
    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status, self.body = status, body


def redact(value):
    """Replace the API key in text, lists, and dictionary keys and values."""
    if isinstance(value, str):
        return value.replace(API_KEY, "[redacted]")
    if isinstance(value, dict):
        return {redact(key): redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def retry_after(response):
    value = response.headers.get("Retry-After", "")
    if value.isdigit():
        return float(value)
    try:
        return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
    except (TypeError, ValueError):
        return None


def read_body(response):
    """Return redacted JSON, or up to 200 characters of a redacted non-JSON body."""
    try:
        return redact(response.json())
    except ValueError:
        return redact(response.text)[:200]


def get_json(path, params=None, budget_s=300):
    """GET with retries for reads only. Never use it for POST, PATCH, or DELETE."""
    deadline = time.monotonic() + budget_s
    attempt = 0
    while True:
        wait, status, body = None, None, None
        try:
            response = requests.get(
                f"{BASE}{path}", headers=HEADERS, params=params,
                timeout=30, allow_redirects=False,
            )
        except NETWORK_ERRORS as exc:
            problem = redact(f"connection failed: {exc}")
        else:
            status, body = response.status_code, read_body(response)
            if 200 <= status < 300 and not isinstance(body, str):
                return body
            wait = retry_after(response)
            problem = f"{status}: {body}"
            busy_cursor = (
                status == 409
                and isinstance(body, dict)
                and body.get("error") == "coverage_cursor_unavailable"
                and wait is not None
            )
            if not (200 <= status < 300 or status >= 500 or status == 429 or busy_cursor):
                raise XquikError(problem, status, body)
        if wait is None:
            wait = min(30.0, 2.0**attempt) * random.uniform(0.5, 1.0)
        attempt += 1
        if time.monotonic() + wait > deadline:
            raise XquikError(
                f"Gave up after {attempt} attempts. Last: {problem}", status, body
            )
        time.sleep(wait)
```

A paging loop on that helper. It restarts once on a gone or invalid cursor.
It counts every returned tweet toward the user's number, refetched ones
included, so the bill never passes that cap. Load `seen_ids` from earlier
output, and make `append_row` save each row before it returns:

```python
def append_search_tweets(q, cap, seen_ids, append_row):
    billed, cursor, restarted, cursors = 0, None, False, set()
    while billed < cap:
        params = {"q": q, "limit": cap - billed}
        if cursor:
            params["cursor"] = cursor
        try:
            page = get_json("/x/tweets/search", params)
        except XquikError as err:
            code = err.body.get("error") if isinstance(err.body, dict) else None
            restartable = (err.status, code) in (
                (410, "coverage_cursor_gone"),
                (400, "invalid_coverage_cursor"),
            )
            if restarted or not restartable:
                raise
            cursor, restarted = None, True
            cursors.clear()
            continue
        billed += len(page["tweets"])
        for tweet in page["tweets"]:
            if tweet["id"] not in seen_ids:
                append_row(tweet)
                seen_ids.add(tweet["id"])
        if not page["has_next_page"] or billed >= cap:
            break
        cursor = page["next_cursor"]
        if not isinstance(cursor, str) or not cursor or cursor in cursors:
            raise XquikError("Invalid or repeated search cursor")
        cursors.add(cursor)
    return billed
```
