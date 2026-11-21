# Limits and splitting

> **Pull current limits from official docs — do not hardcode remembered numbers.**
> Limits change between Bot API versions. The values below are a starting point;
> confirm them for the project's Bot API version. See `official-sources.md`.

## Reference limits (verify before relying on them)

| Limit | Value | Source status |
|---|---|---|
| Regular message text | 4096 chars | stable, historical |
| Media caption | 1024 chars | stable, historical |
| Rich message text | 32,768 UTF-8 chars (incl. custom emoji alt text, formula source) | official: Rich Message Limits (2026-11-12) |
| Rich "Show More" cutoff | ~8,000 chars shown, rest collapsed | official blog |
| Blocks per rich message (nested blocks, list items, **table rows**, quotations and details count) | 500 | official: Bot API "Rich Message Limits" (2026-11-12) |
| Nesting depth | 16 levels | official: Bot API "Rich Message Limits" (2026-11-12) |
| Media attachments per rich message | 50 | official: Bot API "Rich Message Limits" (2026-11-12) |
| Table columns | 20 | official: Bot API "Rich Message Limits" (2026-11-12) |
| Media group size | 10 items | stable, historical |
| Rich button row | 1–8 buttons | official: InputRichBlockButtons (10.3) |
| Widget HTML | 32,768 bytes, ≤ 4096 after zlib-9 | official: sendWidget (10.4) |
| Widget chat_data / public_data, answer data | 1024 UTF-8 bytes each | official (10.4) |
| Quote of a rich message | ≤ 32 texts, ≤ 1024 chars | official: ReplyParameters (10.4) |
| Message rate (per chat) | ~1/sec sustained; bursts limited | verify; drives streaming |

Keep these constants in **one place** in the project; never scatter magic
numbers across call sites.

## When to split

Split when content exceeds the applicable text/caption limit, or when a single
message would be unreadable. For Rich Messages, prefer fitting within one message
(the 32,768 budget + "Show More" is generous) before splitting; split only when
genuinely over budget or when logical sections are better as separate messages.

## Safe split boundaries (in priority order)

1. Between **sections/headings**.
2. Between **paragraphs / blocks**.
3. Between **list items**.
4. At sentence boundaries.
5. Only as a last resort, mid-paragraph at a whitespace boundary.

## Never split through

- An **open HTML tag** or between a tag and its close.
- A **Markdown/MarkdownV2 construct** (bold/italic/link/spoiler run).
- A **link** (`[text](url)`, `<a href>`, or a bare URL entity).
- A **code block / fenced block** — keep the whole fence together, or close and
  reopen it with the same language on the next part.
- A **Unicode grapheme / surrogate pair / combining sequence** — never between a
  base char and its combining marks, never between the two halves of an emoji.
- A **MessageEntity span** — recompute offsets per part after splitting; entities
  must not cross a part boundary.
- A **rich block** — split between blocks, not inside one.

## Preserve on split

- **Keyboards / reply markup:** attach to the correct part (usually the last),
  never dropped.
- **Reply/topic context:** carry `reply_parameters` / `message_thread_id` /
  business connection to each part as the project requires.
- **Meaning:** don't reorder or drop content; keep numbering continuous across
  list splits; repeat table headers if a table must span parts.

## Splitting algorithm (format-aware)

1. Choose the limit for the target format/version.
2. Walk the structure (AST/blocks/lines), accumulating into a part while under
   the limit.
3. When adding the next unit would exceed the limit, close the current part at
   the highest-priority safe boundary available.
4. For formats with open/close constructs (HTML tags, code fences), close them at
   the part end and reopen at the next part start.
5. Recompute entity offsets per part (UTF-16 code units).
6. Attach markup/reply/topic context per the preservation rules.
7. Send parts in order; if one part fails, apply the fallback ladder
   (`errors-and-fallbacks.md`) without losing subsequent parts silently.

## Streaming interaction

When streaming AI output, prefer updating a single `sendRichMessageDraft` rather
than sending many split messages; only finalize/split when the content is
complete or exceeds limits. See `streaming-and-editing.md`.
