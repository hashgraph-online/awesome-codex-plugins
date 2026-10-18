# Research a channel

**Prompt**

> What has @TED said about artificial intelligence? Read the three most
> relevant talks and compare their arguments.

**What the agent does**

1. Calls `search_channel` with `@TED` and "artificial intelligence" instead of
   listing the whole archive (1 credit).
2. Picks the best candidates by title and fetches only those with
   `get_transcripts`.
3. Compares the transcripts and answers with a citation per video.

**Variants**

- Every talk on the channel: `start_bulk_extract` with the channel URL, then
  read what you need from the results.
- Topic discovery across all of YouTube: `search_youtube`, with `type` set to
  `channel` to find channels worth following.

**Cost note**: a transcript costs 1 credit the first time it enters this
account's library, and repeat reads are free. A transcript someone else fetched
is not free for you. Tell the user the video count before a big job.
