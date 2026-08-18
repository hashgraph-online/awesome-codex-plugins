# Copy-paste request examples

The exact requests from SKILL.md as runnable one-liners. Same endpoints, same parameters, same headers.

## Quick Examples

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/search\
?q=python+tutorial&type=video&limit=10" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## Quick Examples

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/transcript\
?video_url=dQw4w9WgXcQ&format=text&include_timestamp=true&send_metadata=true" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## Quick Examples

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/resolve?input=@TED" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## Quick Examples

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/latest?channel=@TED" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```

## Quick Examples

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/channel/videos?channel=@NASA" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
# Use continuation token from response for next pages
```

## Use continuation token from response for next pages

```bash
curl -s "https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=PL_PLAYLIST_ID" \
  -H "Authorization: Bearer $TRANSCRIPT_API_KEY" \
  -H "User-Agent: YourAgent/1.0"
```
