# Contexts and addressing

> Verified 2026-11-12. Decide fields from the **method and the context**, never by copying a
> universal payload. Code: `examples/python/tgkit/topics.py`; recipe
> [08 multi-topic bot](../recipes/08-multi-topic-bot.md).

## Context matrix

| Context | Address fields | Drafts | Ephemeral callback reply | Reply keyboard | Widgets (prod) |
|---|---|:-:|:-:|:-:|:-:|
| Private chat | `chat_id` | yes | yes (10.4) | yes | **yes** |
| Private chat with topics (bot topic mode) | `chat_id` + `message_thread_id` | yes (+thread) | yes | yes | yes |
| Group / supergroup | `chat_id` | no | yes | yes (`selective`) | test server |
| Forum topic | `chat_id` + `message_thread_id` | no | yes | yes | test server |
| Channel | `chat_id` | no | — | **no** | no (forwards: test) |
| Channel direct-messages chat (`chat.is_direct_messages`) | `chat_id` + `direct_messages_topic_id` (from `message.direct_messages_topic.topic_id`) | no | **no** (10.4 exception) | — | — |
| Business chat | + `business_connection_id` | — | — | no | — |
| Inline message | `inline_message_id` (edits) | no | yes, 10.4 form | — | test server |

`MessageGenerationStopped` carries `chat` + optional `message_thread_id` + `draft_id` — match all
three. Per-conversation state (generation, form, panel) keys on
`(chat_id, message_thread_id or 0, direct_messages_topic_id or 0)`.

## Private-chat topics and topic links

10.4: `https://t.me/<bot_username>/<message_thread_id>` opens that topic **only for the user whose
private chat has it** — use it as a "go to the other conversation" button inside that user's chat;
it is useless to anyone else, so never post it publicly. Each topic runs its own operations; a
second generation in a busy topic is refused or queued, never interleaved.

## Channel direct messages

Use `direct_messages_topic_id` (never `message_thread_id`), no ephemeral callback replies, and
no inline-query switch buttons (validator `--context channel_dm`).
