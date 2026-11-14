---
name: ai-interview
description: Set up a QuestionPunk AI interview, in which an AI interviewer talks with each respondent by text chat or voice and asks follow-up questions, from a research goal or an existing discussion guide. Use for interview customers about why they cancelled, run voice interviews with our users, or turn my interview guide into an AI interview. Not for a fixed-question survey with no interviewer.
---

# Set up an AI interview

QuestionPunk's AI interviewer runs one conversation per respondent, in text or voice, from a goal you write. Your job is the brief it works from and the few fixed questions around it; the interviewer writes its own follow-ups during each interview.

Use the connected QuestionPunk tools. Host prefixes vary; resolve each tool by its unprefixed name, and search deferred or not-yet-loaded tools before deciding one is missing. Never invent a tool or parameter.

## When you can't save to the account

If `survey_create` or `question_create_bulk` is missing after that search, QuestionPunk isn't connected in this chat. The usual cause is that it is installed but not signed in. Do not search a connector directory or use another vendor's tools. In your reply:

- Say how to connect. If a QuestionPunk `authenticate` tool is listed, call it and give the sign-in link it returns. Otherwise: in Codex, run `codex mcp add questionpunk --url https://app.questionpunk.com/api/v1`, then `codex mcp login questionpunk`, and start a new chat; on another host, use its connector settings.
- Write the interview plan in the chat (steps 1 and 2 below). If `survey_draft_link` is available, make a link with it: two to four short questions, then one question of type `ai_interview` as the last question, whose text is the opening question the interviewer starts from. Give the link exactly as returned, and say it opens the draft as a guest, where QuestionPunk asks the opening question and then the AI interviewer follows up; the goal, topics to avoid, text or voice, and length are set in the editor after opening it, using the brief you wrote. Put only the interview in the link: no names, email addresses, customer lists or other confidential text from the conversation.

When the user says they connected, look for the tools again and carry on without asking for the request again.

## Steps

1. Get the goal: what decision the interviews inform and who is being interviewed. If the user gave a discussion guide or script, keep its intent and its must-ask topics. Ask one question only if the goal or audience is missing.
2. Write the brief:
   - **Interview goal** (`interviewGoal`): what to learn, the topics to cover in rough order, and what a good answer explains (for example the moment they decided, what they tried first, what it cost them). Plain sentences, no more than about 150 words.
   - **Greeting** (`greetingInstruction`): how the interviewer opens, in one or two sentences, including roughly how long it takes.
   - **Avoid** (`avoidTopics`): what the interviewer must not ask or promise (pricing commitments, medical or legal advice, identifying details the study does not need).
   - A few fixed questions before the interview only when the analysis needs them (for example plan type or how long they have been a customer). Ask no demographics without a reason. A choice that needs "Other" gets the built-in one (`otherOption: true` in a link, `itemDetails.other_option: true` when saving), not a plain "Other" option.
3. Choose text or voice. Use voice when the user asked for voice or spoken answers; otherwise text. Length: 3 to 5 follow-up exchanges for a short check-in, 8 to 10 for a discovery interview; say which you chose.
4. Call `survey_create` (title at most 50 characters), then `survey_get` for the language and `versions.current`.
5. Add everything with one `question_create_bulk` call: the fixed questions first, then one `answer_type: "ai_moderated_interview"` item whose `text` is the opening question, with `itemDetails` `{ "modality": "text" | "voice", "length": <exchanges> }` and `textItemDetails` `{ "interviewGoal": ..., "greetingInstruction": ..., "avoidTopics": ... }`. Use `ai_moderated_interview`, not the older `ai_interview` or `ai_audio_interview`. If the interviewer should see earlier answers, follow the tool description for `referenceSources` (voice reads only `referenceSources.perRespondent`).
6. Read the survey back with `survey_get` and check the interview question, its modality, length and brief are saved. Fix a setting with `question_update`, one write at a time with the version the last write returned.
7. Report the outline, text or voice, length, the brief in a few lines, the draft status and `editorUrl`. Suggest the owner try it once with the editor's preview before sending it. Publish only if the user asked to publish or for a link to send; then call `survey_publish` and give `shareUrl` exactly as returned.

Voice interviews and the AI interviewer may use the account's AI credits when respondents take them; say so when you report, without quoting prices you have not read from a tool. Creating a draft does not authorize publishing, sending invitations or paid recruitment. On authentication failure use the host's reconnect flow; never ask for a token in chat. If a create times out, look for the new survey with `survey_list` before creating another.
