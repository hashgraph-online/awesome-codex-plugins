# Summarize a video

**Prompt**

> Summarize this video and pull the five best quotes with timestamps:
> https://www.youtube.com/watch?v=VIDEO_ID

**What the agent does**

1. Calls `get_transcript` with the URL and `include_segments: true`, because
   the quotes need timestamps.
2. Summarizes from the paragraphs, and takes each quote's start time from the
   segments.
3. Cites the title, channel and URL from the response.

**Tips**

- For a summary without quotes, leave `include_segments` off. The response is
  much smaller.
- A video with no captions comes back as `no_transcript` and is never charged.
