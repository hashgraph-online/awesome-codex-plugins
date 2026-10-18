---
name: linkedin-inbox-followup
description: "Find LinkedIn conversations with no new message for 7 days or more and draft short follow-up messages, with the LinkMCP connector. It finds the threads where the other person stopped answering the user, and the threads where the user did not answer yet. Use when the user asks to follow up on LinkedIn messages or to find unanswered LinkedIn conversations. Shows each draft first, and sends a message only after the user approves that exact message."
license: MIT
compatibility: "Needs the LinkMCP connector (remote MCP server) in the AI client and a paid LinkMCP plan with a connected LinkedIn account."
metadata:
  author: LinkMCP
  version: "1.0.0"
---

# LinkedIn inbox follow-up

Find the conversations that wait for an answer, and draft a short message for each. Send only the messages that the user approves, one message at a time.

## Rules for sending

- Do not send a message without the approval of the user for that exact message.
- Ask for approval of one message at a time. Show the name of the recipient, the conversation and the full text. Send only after a clear yes for that message.
- If you do not know the name of the recipient, say so. Then show the date and the text of the last messages, so that the user can recognize the conversation.
- One approval is for one message. If the user says "send all", still confirm each message before you send it.
- Send the text exactly as the user approved it. If you or the user change the text, show the new text and ask again.
- Reply only in the existing conversation: call `linkedin_send_message` with `chat_id`. Do not start new conversations and do not send InMail in this skill.
- Do not schedule messages. Do not plan automatic follow-ups.
- Draft 10 messages or fewer in one run.
- Draft a follow-up only in a conversation where the other person wrote before. Do not follow up on a first message that never got an answer.
- Do not draft a follow-up when the other person said no, asked the user to stop, or closed the topic. Do not draft a follow-up when the user already sent two or more messages in a row with no answer. Do not draft a reply to an advertisement or a mass message. Put these threads in the summary as "No follow-up" with the reason.
- If LinkMCP refuses a message because of the daily limit, stop sending. Give the user the message of LinkMCP.
- If LinkMCP asks you to wait a short time, it did not send the message. Tell the user, and ask before you try again.

## Tools

This skill uses these LinkMCP tools. These tools only read: `linkedin_list_conversations`, `linkedin_get_conversation_messages`, `linkedin_get_profile`, `linkedin_get_person_posts`. One tool writes: `linkedin_send_message`. Use it only after the approval of the user, as the rules above say.

Your client can show a tool name with a prefix, for example `mcp__linkmcp__linkedin_list_conversations`. Use the tool whose name ends with the name in this skill.

## Steps

1. Make sure that the LinkMCP tools are available, for example `linkedin_list_conversations`. If they are not available, stop and tell the user how to connect LinkMCP:
   - With the LinkMCP plugin: connect the LinkMCP connector of the plugin and sign in. In Claude, the connector is on the Connectors tab of the plugin.
   - Without the plugin: add LinkMCP as a remote MCP server with the URL `https://app.linkmcp.io/api/mcp?ref=skills` and sign in. Setup steps for each AI client: https://app.linkmcp.io/docs/quick-start
2. Use the settings of the user, or these defaults: no new message for 7 days or more, and conversations from the last 60 days.
3. Call `linkedin_list_conversations` with `after` set to today minus 60 days and `before` set to today minus 7 days.
   - For the next page, call the tool again with the same `after` and `before`, and with `cursor` set to `next_cursor`. Read 3 pages or fewer.
   - If the tool says that LinkedIn is not connected or that a paid plan is necessary, give its message to the user. Then stop.
   - Skip conversations where `isReadOnly` or `isArchived` is true.
4. For each conversation, call `linkedin_get_conversation_messages` with `chat_id` and `limit` 5. Check 10 conversations or fewer, unless the user asks for more.
   - The messages come newest first. `isSender` is true for a message that the user sent. Ignore messages where `isEvent` is true.
   - Skip a conversation when its messages come from more than one other person.
   - If the newest message is from the user, and an older message is from the other person, the thread is "No answer from them".
   - If all the messages are from the user, the thread is "No follow-up" (no answer to the first message).
   - If the newest message is from the other person, the thread is "No answer from you".
5. For each thread that needs a follow-up, get the context:
   - Call `linkedin_get_profile` with `identifier` set to `urn:li:fsd_profile:` followed by the `attendeeProviderId` of the conversation. Use the name and the current role.
   - If `attendeeProviderId` is empty, or LinkMCP cannot find the profile, do not guess the name. Write "Name not known".
   - Optional: if you know the profile, call `linkedin_get_person_posts` one time to find a recent post that the message can refer to.
6. Draft one message for each thread:
   - Two to four short sentences in plain words. Use the language and the tone of the thread.
   - Refer to the last message in the thread. Add one useful thing: an answer, a question or a recent post of the person.
   - Do not push the person to answer. Do not say that something is urgent when it is not. Do not add links unless the user asks.
   - Do not invent facts, meetings or offers.
7. Show the list: name (or "Name not known"), type of thread, date of the last message, a summary in one line, and the draft. Then ask the user about the first message: send, edit or skip.
8. For each approved message, call `linkedin_send_message` with the `chat_id` of the conversation and the approved `text`. Tell the user the result. Then ask about the next message.
9. At the end, show a summary: messages sent, messages skipped, and threads with "No follow-up" and the reason.

## When a tool fails

- If a tool reports a limit or tells you to wait, do what it says. Do not call the tool again and again. If the wait is long, stop and show what you have.
- If a message fails to send, tell the user. Do not send it again unless the user asks.
