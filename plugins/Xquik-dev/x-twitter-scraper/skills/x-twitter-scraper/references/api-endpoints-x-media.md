# Xquik REST API Endpoints: X Media (Download)

### Download Media

```
POST /x/media/download
```

Download images, videos, and GIFs from tweets. Single or bulk (up to 50). Returns a shareable gallery URL.

**External disclosure and approval required:** This operation copies requested
media to a shareable Xquik gallery. Anyone who receives the unlisted gallery URL
may access it. Confirm the exact tweets, media rights, bulk bound, and intended
recipients before calling. Never use private or access-restricted media. Do not
share the returned URL beyond the approved audience.

**Body:** Provide either `tweetInput` (single tweet) or `tweetIds` (bulk). Exactly 1 is required.

| Field | Type | Description |
|-------|------|-------------|
| `tweetInput` | string | Tweet URL or numeric tweet ID for a single download. Accepts `x.com` and `twitter.com` URL formats |
| `tweetIds` | string[] | Array of tweet URLs or IDs for bulk download. Maximum 50 items. Returns a single combined gallery |

**Response (single):**
```json
{
  "tweetId": "1893456789012345678",
  "galleryUrl": "https://xquik.com/g/abc123",
  "cacheHit": false
}
```

**Response (bulk):**
```json
{
  "galleryUrl": "https://xquik.com/g/def456",
  "totalTweets": 3,
  "totalMedia": 7
}
```

First download is metered. Subsequent requests for the same tweet return cached URLs when `cacheHit: true`. All downloads are saved to shareable gallery pages under `https://xquik.com/g/{token}`.

Treat every gallery URL as externally accessible disclosure, not a private
local download. The skill does not promise expiry or revocation. Ask the user to
use another workflow when a shareable gallery is inappropriate.

Returns `400 no_media` if the tweet has no downloadable media. Returns `400 too_many_tweets` if bulk array exceeds 50 items.

---
