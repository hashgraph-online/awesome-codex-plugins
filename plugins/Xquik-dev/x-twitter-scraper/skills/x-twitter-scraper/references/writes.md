# Write routes

Writes act through an X account the user connected in the Xquik dashboard.
The body names that account in `account`, as a handle without `@` or an
account ID. `GET /x/accounts` lists connected accounts.

## Preview, confirm, send

- Resolve every field before a preview: account, target ID, exact text,
  media & reply target. Ask for a missing one instead of guessing.
- The preview shows the method, full URL, headers, JSON body, cost & effect.
  An effect reads like "a new post appears on @my_brand for its followers".
- A text post or reply costs 30 credits, plus 2 per started MB of media.
  Likes, reposts, follows, DMs & deletes cost 10 credits each.
- Itemize each operation, lookups included, with rates, total credits &
  dollars. Show the media charge, or say a text-only post has none.
- Include `statusUrl`, or `GET https://xquik.com/api/v1/x/write-actions/{id}`,
  for the final outcome. Acceptance does not mean success.
- Each intended action gets 1 new `Idempotency-Key`, a UUID. Reuse it only to
  retry that identical request.
- Ask whether the user confirms this exact request. An edit needs a new
  preview.
- Send once, through the connected Xquik MCP server or the user's own client.

## Responses and retries

Every write returns an action record with `status`, `terminal`,
`safeToRetry`, `statusUrl`, and `pollAfterMs`.

- `200`: the action is terminal. Check `status`, because `failed` and
  `expired` are terminal too. A new post's ID is in `tweetId` and `result.id`.
- `202`: accepted. Poll `statusUrl`, which is `GET /x/write-actions/{id}`,
  every `pollAfterMs` until `terminal` is true. `statusUrl` is a path that
  already starts with `/api/v1`, so prefix only `https://xquik.com`.
- Timeout or lost response: do not send a new request, because the first one
  may have gone through. Retry the identical request with the same
  `Idempotency-Key`; Xquik returns the original action instead of acting
  twice. Or poll the action if you have its `statusUrl`.
- Start a new attempt with a new key only when a terminal record has
  `safeToRetry: true`, and only after the user agrees.
- If both the key and `statusUrl` are lost, no check can prove the first
  attempt failed, because a pending post may not show on the timeline yet.
  Explain the duplicate risk and stop recovery until the original action can
  be identified. A timeline check or a new confirmation cannot prove failure.
- Never send a write with a new key on your own. After a `429`, wait for
  `Retry-After`, then repeat the identical request with the same key. A `409`
  `idempotency_conflict` means the key was used with a different body. On a
  retry, resend the exact original body. Use a new key only for a new action.

## Routes

| Action | Route | Body |
| --- | --- | --- |
| Post or reply | `POST /x/tweets` | `account`, `text`, optional `reply_to_tweet_id`, `community_id`, `is_note_tweet`, `media` (up to 4 image URLs or 1 MP4 URL) |
| Delete post | `DELETE /x/tweets/{id}` | `account` |
| Like, unlike | `POST`, `DELETE /x/tweets/{id}/like` | `account` |
| Repost, undo | `POST`, `DELETE /x/tweets/{id}/retweet` | `account` |
| Follow, unfollow | `POST`, `DELETE /x/users/{id}/follow` | `account` |
| Remove follower | `POST /x/users/{id}/remove-follower` | `account` |
| Send DM | `POST /x/dm/{userId}` | `account`, `text`, optional `media_ids` (1 ID) |
| Upload media | `POST /x/media` | multipart `account`, `file` |
| Update profile | `PATCH /x/profile` | `account`, optional `name`, `description`, `location`, `url` |
| Avatar, banner | `PATCH /x/profile/avatar`, `/x/profile/banner` | multipart `account`, `file` |
| Communities | `POST /x/communities`, `DELETE /x/communities/{id}`, `POST` or `DELETE /x/communities/{id}/join` | `account` |

Every route above needs the `Idempotency-Key` header. A write without one gets
`400 missing_idempotency_key` and never reaches X. DM and follow routes
take numeric user IDs. Resolve a username with `GET /x/users/{username}`.

## Bulk and irreversible work

- Deletes cannot be undone. First list the exact posts, for example with
  `GET /x/users/{handle}/tweets` and `sinceDate`/`untilDate`, or search with
  `fromUser`. Disclose inventory billing at 1 credit per returned tweet, plus
  10 per delete. Show the exact list for confirmation, then use one request
  and `Idempotency-Key` per post. Follow the Skill's engagement rules.

## Giveaway draws

`POST /draws` picks winners from a post's replies and reposters. The result is
final, so confirm first. A draw bills 2 base credits, 1 per inspected reply,
1 per reposter read when `mustRetweet` is on, and 5 per follow check when
`mustFollowUsername` is set. The total depends on the post's replies and
reposts, so show that formula with the preview. Remaining credits cap how many
entries the draw inspects, so a low balance can leave valid entries out. Send
an `Idempotency-Key`.

```json
{
  "tweetUrl": "https://x.com/my_brand/status/1800000000000000000",
  "winnerCount": 1,
  "uniqueAuthorsOnly": true,
  "filterMinFollowers": 10
}
```

Other fields: `backupCount`, `mustRetweet`, `mustFollowUsername`, `filterAccountAgeDays`,
`filterLanguage`, `requiredHashtags`, `requiredKeywords`, `requiredMentions`.
Read the result with `GET /draws/{id}` and export it with
`GET /draws/{id}/export?format=csv`.

## Account connection

Users connect and re-authenticate X accounts themselves in the Xquik
dashboard. Its connect form asks for the X username, email, password, and the
authenticator setup secret, not a one-time code. `POST /x/accounts` takes the
same secrets, so this Skill never calls it. Never collect or send X passwords,
2FA codes, cookies, or session tokens, even when the user offers them.
