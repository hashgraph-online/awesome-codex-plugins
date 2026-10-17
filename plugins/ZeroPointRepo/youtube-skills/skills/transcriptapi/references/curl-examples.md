# Copy-paste request examples

The exact requests from SKILL.md as runnable one-liners. Same endpoints, same parameters, same headers.

## GET /api/v2/youtube/transcript — 1 credit

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/transcript\
?video_url=VIDEO_URL&format=text&include_timestamp=true&send_metadata=true" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## GET /api/v2/youtube/search — 1 credit

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/search?q=QUERY&type=video&limit=20" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## GET /api/v2/youtube/channel/resolve — FREE (0 credits)

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/resolve?input=@TED" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## GET /api/v2/youtube/channel/videos — 1 credit/page

```bash
# First page (100 videos)
curl -s "https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"


# Most-viewed first (channel Videos tab, ~30 per page)
curl -s "https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA&sort=popular" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"

# Oldest first
curl -s "https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA&sort=oldest" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"

# Next pages (repeat the same tab AND sort)
curl -s "https://transcriptapi.com/api/v2/youtube/channel/videos?continuation=TOKEN&sort=popular" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

Sort a channel's videos by latest, popular, or oldest, for example most-popular first. Sorted pages return about 30 videos (unsorted about 100); each page costs 1 credit.


## GET /api/v2/youtube/channel/latest — FREE (0 credits)

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@TED" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## GET /api/v2/youtube/channel/search — 1 credit

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/search\
?channel=@TED&q=climate+change&limit=30" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## GET /api/v2/youtube/playlist/videos — 1 credit/page

```bash
# First page
curl -s "https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=PL_PLAYLIST_ID" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"

# Next pages
curl -s "https://transcriptapi.com/api/v2/youtube/playlist/videos?continuation=TOKEN" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```
