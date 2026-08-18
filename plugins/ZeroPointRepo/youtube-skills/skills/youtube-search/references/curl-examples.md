# Copy-paste request examples

The exact requests from SKILL.md as runnable one-liners. Same endpoints, same parameters, same headers.

## GET /api/v2/youtube/search — 1 credit

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/search?q=QUERY&type=video&limit=20" \
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

## GET /api/v2/youtube/channel/resolve — FREE

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/resolve?input=@TED" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## Workflow: Search → Transcript

```bash
# 1. Search for videos
curl -s "https://transcriptapi.com/api/v2/youtube/search\
?q=python+web+scraping&type=video&limit=5" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"

# 2. Get transcript from result
curl -s "https://transcriptapi.com/api/v2/youtube/transcript\
?video_url=VIDEO_ID&format=text&include_timestamp=true&send_metadata=true" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```
