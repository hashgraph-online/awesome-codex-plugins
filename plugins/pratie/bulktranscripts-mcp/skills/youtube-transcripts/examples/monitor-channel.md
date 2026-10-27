# Monitor a channel for new uploads

**Prompt**

> Every morning, check if @mkbhd posted a new video. If yes, summarize it for
> me.

**What the agent does**

1. Calls `get_latest_videos` with `@mkbhd`. It is always free.
2. Compares the returned video ids with the ones already seen. Use the publish
   date as a tie-breaker when it is present.
3. Only for new videos, calls `get_transcript` (1 credit each) and summarizes.

**Why this pattern**

The check itself is free, so a daily monitor only costs credits on days the
creator actually posts. Watching three channels daily for a month typically
costs a handful of credits.
